from django.core.mail import EmailMessage
from django.conf import settings

def send_clinic_signup_link_email(recipient_email, sales_person_id, signup_link):
    try:
        subject = "Welcome to IzzyAI - Complete Your Registration"
        message_body = f"""\
        Dear User,

        Welcome to IzzyAI! A sales representative (ID: {sales_person_id}) has referred you to our platform. To complete your registration, please click the following link:

        Sign-up Link: {signup_link}

        Please follow the instructions on the page to complete your registration.

        If you did not expect this email or believe it was sent in error, please contact our support team.

        Thank you for choosing IzzyAI.

        Best regards,  
        The IzzyAI Team  

        [Note: This is an automated message. Please do not reply directly to this email.]
        """

        email = EmailMessage(
            subject=subject,
            body=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,  # Use the configured sender email
            to=[recipient_email],  
        )
        
        email.send(fail_silently=False)
        print(f"Signup link email successfully sent to {recipient_email}")

    except Exception as e:
        print(f"Failed to send sign-up link email: {e}")
