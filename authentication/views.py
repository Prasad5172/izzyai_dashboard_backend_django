# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth import authenticate
# from django.core.mail import send_mail
# import random
# from django.core.files.storage import FileSystemStorage
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from django.core.exceptions import ObjectDoesNotExist
# from django.utils.crypto import get_random_string
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.conf import settings
# from datetime import timedelta
# from django.contrib.auth import authenticate, get_user_model
# from authentication.models import Users
# def get_tokens_for_user(user):
#     refresh = RefreshToken.for_user(user)

#     return {
#         'refresh': str(refresh),
#         'access': str(refresh.access_token),
#     }

# def generate_tokens_for_user(user):
#     """
#     Generates a new access and refresh token for a given user.

#     Args:
#         user (User): The user object for whom the tokens are being generated.

#     Returns:
#         dict: A dictionary containing the new access and refresh tokens.
#     """
#     # Create a new refresh token for the user
#     refresh = RefreshToken.for_user(user)
    
#     # Adding custom claims to the access token
#     access_token = refresh.access_token
#     access_token['user_id'] = str(user.id)  # Convert UUID to string
    
#     # Set custom expiration if needed (Optional)
#     access_token.set_exp(lifetime=timedelta(minutes=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']))
    
#     return {
#         'access': str(access_token),
#         'refresh': str(refresh)
#     }


# # Function to refresh tokens when a valid refresh token is provided
# def refresh_tokens(refresh_token):
#     """
#     Refreshes the access and refresh tokens using a provided refresh token.

#     Args:
#         refresh_token (str): The refresh token used to generate new tokens.

#     Returns:
#         dict: A dictionary containing the new access and refresh tokens.
#     """
#     try:
#         # Attempt to create a new RefreshToken instance
#         old_refresh = RefreshToken(refresh_token)
        
#         # Extract the user ID from the token and convert to string
#         user_id = old_refresh['user_id']
        
#         # Retrieve the user instance based on the user ID
#         user = User.objects.get(id=user_id)
        
#         # Generate a new refresh token for the user
#         new_refresh = RefreshToken.for_user(user)
        
#         # Adding custom claims to the new access token
#         new_access_token = new_refresh.access_token
#         new_access_token['user_id'] = str(user.id)  # Convert UUID to string
        
#         return {
#             'access': str(new_access_token),
#             'refresh': str(new_refresh)
#         }

#     except (TokenError, InvalidToken):
#         # If the token is invalid or expired, raise an appropriate error
#         raise InvalidToken("Invalid or expired refresh token.")
#     except User.DoesNotExist:
#         # If the user is not found in the database, raise an appropriate error
#         raise InvalidToken("User not found for the provided token.")


# class SignupAPIView(APIView):
#     def post(self, request):
#         username = request.data.get('username', '').lower().strip()
#         email = request.data.get('email')
#         password = request.data.get('password')
#         confirm_password = request.data.get('confirmPassword')
#         source = request.data.get('source', 'unknown')
        
#         if not username or not email or not password or not confirm_password:
#             return Response({"error": "One or more required fields are missing"}, status=status.HTTP_400_BAD_REQUEST)
        
#         if password != confirm_password:
#             return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
        
#         if Users.objects.filter(email=email).exists():
#             return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
#         if Users.objects.filter(username=username).exists():
#             return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
#         otp = random.randint(100000, 999999)
#         user = Users.objects.create(
#             username=username,
#             email=email,
#             password_hash=password,
#             otp_for_signup=otp,
#             is_otp_verified=False,
#             is_setup_profile=False,
#             created_account=now(),
#             source=source
#         )
        
#         send_otp_email_for_signup(email, otp)
        
#         access_token = AccessToken.for_user(user)
        
#         return Response({
#             "message": "User created successfully",
#             "user_id": user.user_id,
#             "access_token": str(access_token)
#         }, status=status.HTTP_201_CREATED)

