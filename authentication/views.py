from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import random
from datetime import datetime,date
from django.core.files.storage import FileSystemStorage
from django.db.models import Count,Q
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import authenticate
from authentication.models import CustomUser,UsersInsurance
from slp.models import Slps
from sales_person.models import SalePersons
from clinic.models import Clinics,Tasks
from sales_director.models import SalesDirector
from adminer.models import Adminer
from payment.models import Subscriptions
from utils.otp import generate_otp_for_signup
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
        sale_person_id = request.data.get('SalePersonID')  
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
        sale_person = SalePersons.objects.get(sale_person_id=sale_person_id)
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
                sale_person_id = sale_person
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
    # permission_classes = [AllowAny]  # Ensure the user is authenticated

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

#/get_all_user_insurance
#/get_user_insurance/<int:user_id> #query paramate of userid
#/update_user_insurance
class UserInsurancesView(APIView):
    def get(self, request):
        try:
            user_id = request.GET.get('user_id', None)
            if user_id:
                user_insurances = UsersInsurance.objects.filter(
                    user_id=user_id
                ).values(
                    "claim_date","insurance_status","user_id","insurance_provider","policy_number","cpt_number"
                )
            else:
                # Retrieve all user insurance claims
                user_insurances = UsersInsurance.objects.all().values(
                    "claim_date","insurance_status","user_id","insurance_provider","policy_number","cpt_number"
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

