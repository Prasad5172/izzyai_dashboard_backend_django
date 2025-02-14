from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import random
from django.core.files.storage import FileSystemStorage
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from authentication.models import CustomUser
import time 
from slp.models import Slps
from sales_person.models import SalePersons
from clinic.models import Clinics
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


class SignupAPIView(APIView):
    
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
        username = request.data.get('username', '').lower().strip()
        email = request.data.get('email')
        password = request.data.get('password')
        source = request.data.get('source', 'unknown')
        user_type = request.data.get('userType' )

        
        if  not username  or not email or not password or not user_type:
            return Response({"error": "One or more required fields are missing"}, status=status.HTTP_400_BAD_REQUEST)
        if user_type not in ['admin', 'sales_director', 'sales_person' , 'clinic', 'slp']:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)
        
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        otp = random.randint(100000, 999999)
        user = CustomUser.objects.create(
            username=username,
            email=email,
            password_hash=password,
            otp_for_signup=otp,
            is_otp_verified=False,
            is_setup_profile=False,
            source=source,
            user_type=user_type
        )
        
        send_mail(
                subject="Your OTP Code",
                message=f"Your OTP code is {otp}.",
                from_email="your_email@example.com",
                recipient_list=[email],
        )      
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
        username = request.data.get('username', '').lower().strip()
        email = request.data.get('email')
        password = request.data.get('password')
        user_type = request.data.get('userType' )    
        clinic_name = request.data.get('ClinicID')
        slp_name = request.data.get('Name')
        phone = request.data.get('Phone')
        state = request.data.get('State')
        country = request.data.get('Country')

        if not clinic_name or not slp_name or not phone or not state or not country or not sale_person_id or not slp_count or not total_patient or not user_patient or not ein_number:
            return Response({"error": "One or more required fields are missing"}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.create(
                username=username,
                email=email,
                password_hash=password,
                is_otp_verified=False,
                is_setup_profile=False,
                user_type=user_type
            )

            slp = Slps.objects.create(
                clinic_name=clinic_name,
                slp_name=slp_name,
                phone=phone,
                state=state,
                country=country,
                user_id=user,
                sale_person_id=sale_person_id,
                slp_count=slp_count,
                total_patient=total_patient,
                user_patient=user_patient,
                ein_number=ein_number
            )

            # # Notification message require 
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
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')

        # saleperson-specific fields
        sale_person_name = request.data.get('Name')
        phone = request.data.get('Phone')
        state = request.data.get('State')
        country = request.data.get('Country')
        # Check for missing fields for basic user indataation
        if not all([name, email, password, role]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Check for missing fields for saleperson-specific indataation
        if role == 'sales_person':
            if not all([sale_person_name, phone, state, country]):
                return Response({"error": "Missing required saleperson fields"}, status=status.HTTP_400_BAD_REQUEST)
        else :
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if username already exists
        if CustomUser.objects.filter(username=name).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user

        try:
            user = CustomUser.objects.create_user(
                username= name ,
                email=email,
                password_hash=password,
                is_otp_verified=False,
                is_setup_profile=False,
                user_type=user_type
            )
            if role == 'sales_person':
                Slps.objects.create(
                    sale_person_name=sale_person_name,
                    phone=phone,
                    state=state,
                    country=country,
                    user_id=user
                )

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
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')

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


        # Check for missing fields for basic user indataation
        if not all([name, email, password, role , clinic_name, address, phone, state, country, sale_person_id, slp_count, total_patient, ein_number , izzyai_patients]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if username already exists
        if CustomUser.objects.filter(username=name).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user
        try :
            user = CustomUser.objects.create_user(
                username=name,
                email=email,
                password_hash=password,
                is_otp_verified=False,  
                is_setup_profile=False,
                user_type=user_type
            )

            Clinics.objects.create(
                clinic_name=clinic_name,
                phone=phone,
                state=state,
                country=country,
                email=email,
                address=address,
                user_id=user,
                sale_person_id=sale_person_id,
                slp_count=slp_count,
                total_patient=total_patient,
                ein_number=ein_number,
                izzyai_patients = izzyai_patients
            )
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

class SendOTPView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.verified:
            return Response({"error": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)

        otp = generate_otp_for_signup()
        user.otp = otp
        user.save()

        send_otp_email(email, otp)

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

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

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

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