from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import random
from datetime import datetime,date
from django.core.files.storage import FileSystemStorage
from django.db.models import Count,Q,Sum,Value,Max,F,Case,OuterRef,Subquery,DateTimeField,FloatField,When
from django.db.models.functions import Coalesce
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import authenticate
from authentication.models import CustomUser,UsersInsurance,UserProfile
from slp.models import Slps
from sales_person.models import SalePersons
from clinic.models import Clinics,Tasks
from sales_director.models import SalesDirector
from adminer.models import Adminer
from payment.models import Subscriptions,Payment
from utils.otp import generate_otp_for_signup
from django.shortcuts import get_object_or_404
from clinic.models import AssessmentResults,Sessions
import json
import os
from django.core.files.storage import default_storage
from clinic.models import PatientFiles
from authentication.models import UserExercises,UserFiles

def get_date_filter(time_filter):
    date_filter =None
    if time_filter == 'last_month':
        date_filter = now() - timedelta(days=30)
    elif time_filter == 'annual':
        date_filter = now() - timedelta(days=365)
    return date_filter

######## ----- AUTHENTICATION ----- ########
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def generate_tokens_for_user(user):
    """
    Generates a new access and refresh token for a given user.

    Args:
        user (User): The user object for whom the tokens are being generated.

    Returns:
        dict: A dictionary containing the new access and refresh tokens.
    """
    # Create a new refresh token for the user
    refresh = RefreshToken.for_user(user)
    
    # Adding custom claims to the access token
    access_token = refresh.access_token
    access_token['user_id'] = str(user.id)  # Convert UUID to string
    
    # Set custom expiration if needed (Optional)
    access_token.set_exp(lifetime=timedelta(minutes=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']))
    
    return {
        'access': str(access_token),
        'refresh': str(refresh)
    }


# Function to refresh tokens when a valid refresh token is provided
def refresh_tokens(refresh_token):
    """
    Refreshes the access and refresh tokens using a provided refresh token.

    Args:
        refresh_token (str): The refresh token used to generate new tokens.

    Returns:
        dict: A dictionary containing the new access and refresh tokens.
    """
    try:
        # Attempt to create a new RefreshToken instance
        old_refresh = RefreshToken(refresh_token)
        
        # Extract the user ID from the token and convert to string
        user_id = old_refresh['user_id']
        
        # Retrieve the user instance based on the user ID
        user = User.objects.get(id=user_id)
        
        # Generate a new refresh token for the user
        new_refresh = RefreshToken.for_user(user)
        
        # Adding custom claims to the new access token
        new_access_token = new_refresh.access_token
        new_access_token['user_id'] = str(user.id)  # Convert UUID to string
        
        return {
            'access': str(new_access_token),
            'refresh': str(new_refresh)
        }

    except (TokenError, InvalidToken):
        # If the token is invalid or expired, raise an appropriate error
        raise InvalidToken("Invalid or expired refresh token.")
    except CustomUser.DoesNotExist:
        # If the user is not found in the database, raise an appropriate error
        raise InvalidToken("User not found for the provided token.")

"""
Note:All the required field are validate in the frontend to faster response from server,we are not implemented in the code(it saves time)
"""

# this is for signup for admin and sales_director
class AdminAndSaleDirectorSignupAPIView(APIView):
    
    def post(self, request):
        """
            Handles user signup by accepting the required details (username, email, password, and confirm password).
            Perdatas the necessary validations, such as checking if all required fields are provided, ensuring
            passwords match, and verifying that the email and username are not already taken. If all checks pass,
            the function creates a new user, stores their indataation in the database, and sends an OTP email for verification.

            Returns:
                dict: A JSON response containing the message, newly created user ID, and access token.
                
            Raises:
                Exception: In case of any errors during database operations or OTP email sending.
        """
        email = request.data.get('email')
        #source = request.data.get('source', 'unknown')
        user_type = request.data.get('userType')
        department = request.data.get('department')
        designation = request.data.get('designation')

        
        
        if user_type not in ['admin', 'sales_director']:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except Clinics.DoesNotExist:
            raise InvalidToken("Not Registred")
        if(user and not user.verified):
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        

        if( user_type == 'admin'):
            Adminer.objects.create(
                user_id = user,
                department = department,
                designation = designation
            )
            user.user_type = user_type
            user.save()
        elif( user_type == 'sales_director'):
            SalesDirector.objects.create(
                user_id = user,
                department = department,
                designation = designation
            )
            user.user_type = user_type
            user.save()
        else:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

        access_token = get_tokens_for_user(user)
        
        return Response({
            "message": "User created successfully",
            'user_type': user_type,
            "user_id": user.user_id,
            "access_token": access_token
        }, status=status.HTTP_201_CREATED)


class SlpSignupAPIView(APIView):
    
    def post(self, request):
        """
            Handles user signup by accepting the required details (username, email, password, and confirm password).
            Perdatas the necessary validations, such as checking if all required fields are provided, ensuring
            passwords match, and verifying that the email and username are not already taken. If all checks pass,
            the function creates a new user, stores their indataation in the database, and sends an OTP email for verification.

            Returns:
                dict: A JSON response containing the message, newly created user ID, and access token.
                
            Raises:
                Exception: In case of any errors during database operations or OTP email sending.
        """
        email = request.data.get('email')
        user_type = "slp"
        slp_name = request.data.get('Name')
        phone = request.data.get('Phone')
        state = request.data.get('State')
        country = request.data.get('Country')
        clinic_id = request.data.get('ClinicID')

        try:
            user = CustomUser.objects.get(email=email)
        except Clinics.DoesNotExist:
            raise InvalidToken("Not Registred")
        if(user and not user.verified):
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            clinic = Clinics.objects.get(clinic_id=clinic_id)
        except Clinics.DoesNotExist:
            raise InvalidToken("clinic not found for the provided token.")
        
        try:
            Slps.objects.create(
                slp_name=slp_name,
                phone=phone,
                state=state,
                country=country,
                user_id=user,
                clinic_id = clinic
            )
            user.user_type = user_type
            user.save()

            # need to send notification to the clinic
            
            access_token = get_tokens_for_user(user)

            return Response({
                "message": "User created successfully",
                "user_type": user_type,
                "user_id": user.user_id,
                "access_token": access_token
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class Sales_Person_SignupAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')

        # saleperson-specific fields
        phone = request.data.get('Phone')
        state = request.data.get('State')
        country = request.data.get('Country')
        user_type = "sales_person"
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
        if(user and not user.verified):
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        subscription = Subscriptions.objects.get(subscription_id=1) #ask jayanth
        try:
            SalePersons.objects.create(
                phone=phone,
                state=state,
                country=country,
                user_id=user,
                subscription_id = subscription
            )
            user.user_type = user_type
            user.save()

            access_token = get_tokens_for_user(user)

            return Response({
                "message": "User created successfully",
                "user_type": user_type,
                "user_id": user.user_id,
                "access_token": access_token
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClinicSignupAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        # Clinic-specific fields
        clinic_name = request.data.get('ClinicName')
        address = request.data.get('Address')
        phone = request.data.get('Phone')
        state = request.data.get('State')
        country = request.data.get('Country')
        sales_person_id = request.data.get('SalePersonID')  
        slp_count = request.data.get('SlpCount')
        total_patient = request.data.get('TotalPatients')
        izzyai_patients = request.data.get('IzzyAiPatients')
        ein_number = request.data.get('EINNumber')
        user_type = "clinic"

        

        try:
            user = CustomUser.objects.get(email=email)
        except Clinics.DoesNotExist:
            raise InvalidToken("Not Registred")
        if(user and not user.verified):
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        sales_person = SalePersons.objects.get(sales_person_id=sales_person_id)
        # Create the user
        try :
            Clinics.objects.create(
                clinic_name=clinic_name,
                phone=phone,
                state=state,
                country=country,
                email=email,
                address=address,
                user_id=user,
                slp_count=slp_count,
                ein_number=ein_number,
                izzyai_patients = izzyai_patients,
                sales_person_id = sales_person
            )

            user.user_type = user_type
            user.save()
            # notification message require
            access_token = get_tokens_for_user(user)

            return Response({
                "message": "User created successfully",
                "user_type": user_type,
                "user_id": user.user_id,
                "access_token": access_token
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#need to test all cases
class SendOTPForSignupView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username', '').lower().strip()
        password = request.data.get('password')


        user = CustomUser.objects.filter(email=email).first()
        otp = 1234
        if user and user.verified:
            return Response({"error": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)
        elif(user and not user.verified):
            otp = generate_otp_for_signup()
            user.otp = otp
            user.save()
        else:
            otp = generate_otp_for_signup()
            user = CustomUser.objects.create(
                username=username,
                email=email,
                is_otp_verified=False,
                is_setup_profile=False,
            )
            user.set_password(password)
            user.otp = otp
            user.save()
        print(password)
        print(user.password)
        #need to send otp to email
        #send_otp_email(email, otp) 
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.verified:
            return Response({"error": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)

        if user.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        user.verified = True
        user.save()

        return Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)


class UpdatePasswordView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Update user's password.

        This endpoint allows a user to update their password. The user must provide the new password and confirm it.
        The password is then hashed and updated in the database.

        Args:
            email (str): The email address of the user.
            newPassword (str): The new password entered by the user.
            

        Returns:
            Response:
            - 200 OK if the password is updated successfully.
            - 400 Bad Request if the new password or confirmation password are missing, or if the passwords do not match.
            - 500 Internal Server Error if a database operation fails.
        """
        email = request.data.get('email')
        new_password = request.data.get('newPassword')

        if not email or not new_password :
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
      
class LoginAPIView(APIView):
    def post(self, request):
        """
        Handles the login process for users. It verifies the provided email and password, checks if the user exists, and 
        generates an access token if the login credentials are correct. It also retrieves additional user information based on 
        the user role (e.g., Clinic, Slp, Salesperson) and stores relevant session data. The login process ensures that OTP 
        verification status and profile setup status are returned as part of the response.

        Returns:
            dict: A JSON response containing the user ID, access token, OTP verification status, user role, primary key 
            (if applicable), warning count, and profile setup status. If login fails, an error message with the appropriate 
            status code is returned.
        """
        email = request.data.get('email')
        password = request.data.get('password')
        print(password)


        user = authenticate(email=email, password=password) #debug showing error if user and password is present in db 
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if user and not user.verified: #for demo user verified flag is set to true while creating demo credentails
            return Response({"error": "Email not verified"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if(user.user_type == "DemoUser" and user.expiration_date < now()):
            return Response({"error": "Demo User is expired"}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = get_tokens_for_user(user)

        return Response({
            "message": "Login successful",
            "user_id": user.user_id,
            "access_token": access_token,
            "is_verified": user.verified,
            "role": user.user_type,
            "warningcount": user.warning_count,
            "IsSetupProfile":user.is_setup_profile 
        }, status=status.HTTP_200_OK)

# APIView to handle token refresh requests
class CustomTokenRefreshView(APIView):

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Refresh the tokens using the provided refresh token
            tokens = refresh_tokens(refresh_token)
            return Response(tokens, status=status.HTTP_200_OK)
        
        except InvalidToken as e:
            # If the refresh token is invalid or expired, return an error response
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # If an unexpected error occurs during token refresh, return an error response
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

######## ----- END OF AUTHENTICATION ----- ########


######## ----- USER ROUTES ----- ########
#/get_all_user_insurance
#/get_user_insurance/<int:user_id> #query paramate of userid
#/update_user_insurance
#/get_patient_insurance/<int:user_id> #management screen
class UserInsurancesView(APIView):
    def get(self, request):
        try:
            user_id = request.GET.get('user_id', None)
            if user_id:
                user_insurances = UsersInsurance.objects.filter(
                    user_id=user_id
                ).values(
                    'insurance_id',"claim_date","insurance_status","user_id","insurance_provider","policy_number","cpt_number"
                )
            else:
                # Retrieve all user insurance claims
                user_insurances = UsersInsurance.objects.all().values(
                    'insurance_id',"claim_date","insurance_status","user_id","insurance_provider","policy_number","cpt_number"
                )
            return Response(user_insurances,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    def put(self,request):
        try:
            user_id = request.data.get('user_id')
            claim_date = request.data.get('claim_date')
            insurance_status = request.data.get('insurance_status')
            rows_effected = UsersInsurance.objects.filter(
                user_id=user_id,
            ).update(
                claim_date=claim_date,
                insurance_status=insurance_status
            )
            if rows_effected == 0:
                return Response({'message': 'User not found'},status=status.HTTP_404_NOT_FOUND)
            return Response({'message': 'User insurance updated successfully'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_insurance_claim_percent
class InsuranceClaimPercantageView(APIView):
    def get(self, request):
        try:
            # Query to get today's registrations where InsuranceStatus is 'Processing'
            claims = UsersInsurance.objects.filter(
                insurance_status='Processing'
            ).aggregate(
                todays_claims=Count('insurance_id', filter=Q(claim_date=date.today())),
                total_claims=Count('insurance_id',distinct=True)
            )
            print(claims)
            # Calculate percentage
            registration_percentage = round((claims['todays_claims'] * 100.0) / claims['total_claims'], 2) if claims['total_claims'] > 0 else 0.0
            
            return Response({registration_percentage},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)


#/get_patient/<int:UserID>
#/update_user_location/<int:user_id>
#/update_patient/<int:UserID>
#/get_patient_ids/<int:clinic_id>
#/update_user_location_by_admin/<int:UserID>
#/get_user_details/<int:user_id>
#/get_patient_clinic_details/<int:user_id>
#/get_user_profile/<int:UserID>
#/update_user_profile/<int:UserID>
class UserProfileView(APIView):
    def get(self,request,user_id):
        try:
            user_id = request.GET.get('user_id')
            user = UserProfile.objects.filter(user_id=user_id).select_related("clinic",'user').values("full_name",'user__username','dob','user__email','status',"age","gender","country","state","clinic_id","contact_number","clinic__clinic_name","clinic__address").first()
            user_details = {
                'user_id': user_id,
                'full_name': user['full_name'],
                'age': user['age'],
                'dob': user['dob'],
                'gender': user['gender'],
                'country': user['country'],
                'state': user['state'],
                'status': user['status'],
                'clinic_id': user['clinic_id'],
                'clinic_name':user['clinic__clinic_name'],
                'address': user['clinic__address'],
                'contract_number':user['contact_number'],
                'email': user['user__email'],
                'username': user['user__username'],
            }
            return Response(user_details,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)
    def put(self,request,user_id):
        try:
            # Fetch the UserProfile object with related User model in a single query
            user_profile = UserProfile.objects.select_related("user").get(user_id=user_id)

            # Fields to update in UserProfile
            updatable_fields = ["full_name", "gender", "country", "state", "contact_number", "dob", "age"]
            updated_fields = {}

            for field in updatable_fields:
                if field in request.data:
                    updated_fields[field] = request.data[field]

            if updated_fields:
                for field, value in updated_fields.items():
                    setattr(user_profile, field, value)
                user_profile.save(update_fields=updated_fields.keys())  # Save only updated fields

            # Update User model fields (username & email)
            user = user_profile.user
            user_updated_fields = {}
            username = request.data["username"]
            email = request.data["email"]
            if "username" in request.data and username != user.username:
                user_updated_fields["username"] = username

            if "email" in request.data and email != user.email:
                user_updated_fields["email"] = email

            if user_updated_fields:
                for field, value in user_updated_fields.items():
                    setattr(user, field, value)
                user.save(update_fields=user_updated_fields.keys()) 

            return Response({'message': 'Patient Profile updated successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_users_details
class CustomeUserOverview(APIView):
    def get(self,request):
        try:
            time_filter = request.GET.get("time_filter", None)
            date_filter =get_date_filter(time_filter)

            # Subquery to get latest payment date per user
            latest_payment_subquery = Payment.objects.filter(
                user_id=OuterRef("user_id"),
                payment_status="Paid"
            ).order_by("-payment_date").values("payment_date")[:1]

            # Subquery to get the latest plan per user
            latest_plan_subquery = Payment.objects.filter(
                user_id=OuterRef("user_id"),
                payment_status="Paid"
            ).order_by("-payment_date").values("plan")[:1]

            user_profile_subquery = UserProfile.objects.filter(
                user_id=OuterRef("user_id")
            ).values("country","state")[:1]
            
            # Query users including those with zero revenue
            users = CustomUser.objects.filter(
                user_type="patient",
                created_account__gte=date_filter if date_filter else None
            ).select_related(
                "user_profile"
            ).prefetch_related(
                "payments"
            ).annotate(
                revenue_generated=Coalesce(
                    Sum("payments__amount", filter=Q(payments__payment_status="Paid")), 
                    Value(0.0 ,output_field=FloatField())  # Default to zero if no payments exist
                ),
                latest_payment_date=Coalesce(Subquery(latest_payment_subquery), Value(None),output_field=DateTimeField()),
                latest_plan=Coalesce(Subquery(latest_plan_subquery),Value(None),),
                country=Coalesce(Subquery(user_profile_subquery.values("country")),Value(None)),
                state=Coalesce(Subquery(user_profile_subquery.values("state")), Value(""),),
            ).values(
                "user_id","revenue_generated","latest_plan","latest_payment_date","country","state","created_account"
            )

            # Determine user status dynamically
            user_status_updates = []
            for user in users:
                status = "Inactive"
                if user["latest_payment_date"] and user["latest_plan"]:
                    if user["latest_plan"] == "Monthly" and user["latest_payment_date"] >= now() - timedelta(days=30):
                        status = "Active"
                    elif user["latest_plan"] == "Annual" and user["latest_payment_date"] >= now() - timedelta(days=365):
                        status = "Active"

                # Append updates instead of querying one by one
                user_status_updates.append((user["user_id"], status))

            # Perform Bulk Update in One Query
            UserProfile.objects.filter(user_id__in=[user[0] for user in user_status_updates]).update(
                status=Case(
                    *[When(user_id=user_id, then=Value(status)) for user_id, status in user_status_updates],
                    default=F("status")  # Keep existing status if no change
                )
            )
            #  Generate response list
            user_list = [
                {
                    "UserID": user["user_id"],
                    "RevenueGenerated": user["revenue_generated"],
                    "Country": user["country"],
                    "State": user["state"],
                    "Status": dict(user_status_updates).get(user["user_id"], "Inactive"),
                    "CreatedAccount": user["created_account"],
                }
                for user in users
            ]

            return Response(user_list, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#/get_users_revenue_details
class CustomUserRevenueView(APIView):
    def get(self,request):
        try:
            time_filter = request.GET.get("time_filter", None)
            date_filter =get_date_filter(time_filter)
            
            # Query users including those with zero revenue
            users = CustomUser.objects.filter(
                user_type="patient",
                created_account__gte=date_filter if date_filter else None
            ).annotate(
                revenue_generated=Coalesce(
                    Sum("payments__amount", filter=Q(payments__payment_status="Paid")), 
                    Value(0.0 ,output_field=FloatField())  # Default to zero if no payments exist
                ),
            ).values(
                "user_id","revenue_generated","username","created_account"
            )
            return Response(users,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_total_users_revenue
class TotalUsersTotalRevenue(APIView):
    def get(self,request):
            try:
                time_filter = request.GET.get("time_filter", None)
                date_filter =get_date_filter(time_filter)
                
                query_result = CustomUser.objects.filter(
                    user_type="patient"
                ).aggregate(
                    total_users = Count("user_id",distinct=True),
                    total_revenue=Coalesce(
                        Sum(
                            "payments__amount",  # Correct field reference
                            filter=Q(payments__payment_status="Paid") & Q(payments__payment_date__gte=date_filter)
                        ),
                        Value(0.0, output_field=FloatField())  # Ensure correct type
                    )
                )
                return Response(query_result,status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_user_entries
class GetUserEntriesView(APIView):
    def get(self,request):
        try:
            user_type = request.GET.get('user_type')  # Use request.GET for Django, not request.args

            if user_type not in ['Clinic', 'Patient']:
                return Response({'error': 'Invalid UserType. Must be "Clinic" or "Patient".'}, status=400)

            # Optimized Query
            if user_type == 'clinic':
                # Get clinic users
                user_data = Clinics.objects.filter(
                    user__user_type='clinic'
                    ).values('user_id','clinic_name')
            else:
                # Get patient users
                user_data = UserProfile.objects.filter(
                    user__user_type='patient'
                    ).values('user_id','full_name')

            return Response(user_data,status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

class UploadFileView(APIView):
    def post(self,request):
        try:
            file = request.data.get('file')
            user_id = request.GET.get('user_id')
            role = request.GET.get('role')
            document_type = request.GET.get('document_type')
            diagnosis_name = request.GET.get('diagnosis_name', None)  # Optional field
            file_name = file.name #better to implement the file and '_count' count-count of userfiles till now

            # Validate input fields
            if not file:
                return Response({'error': 'No file provided'}, status=400)
            print(user_id,role,document_type)
            if not user_id or not role or not document_type:
                return Response({'error': 'UserID, Role, and DocumentType are required'}, status=400)
            user = CustomUser.objects.get(user_id=user_id)  # Fetch user object

            # Secure the filename
            file_extension = os.path.splitext(file.name)[1]
            if diagnosis_name:
                filename = f"{document_type}_{diagnosis_name}{file_extension}"
            else:
                filename = f"{document_type}{file_extension}"

            # Save the file using Django's storage system
            file_path = default_storage.save(f"uploads/{role}/{user_id}/{filename}", file)

            # Save file details in the database
            patient_file = PatientFiles.objects.create(
                user=user,
                role=role,
                document_type=document_type,
                diagnosis_name=diagnosis_name,
                file_path=file_path,
                file_name=filename,
            )
            return Response({
                'message': 'File uploaded successfully',
                'user_id': user_id,
                'role': role,
                'document_type': document_type,
                'diagnosis_name': diagnosis_name,
                'file_name': filename,
                'file_path': file_path
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetFilesView(APIView):
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return Response({'error': 'UserID is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch user files using Django ORM
            files = UserFiles.objects.filter(user_id=user_id)

            if not files.exists():
                return Response({'message': 'No files found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            # Convert query results to JSON
            files_list = [{
                'FileID': file.file_id,  # Assuming `id` is the primary key
                'FileName': file.file_name,
                'FilePath': file.file_path if file.file_path else None,  # If using FileField
                'UploadTimestamp': file.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } for file in files]

            return Response({'UserID': user_id, 'Files': files_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
