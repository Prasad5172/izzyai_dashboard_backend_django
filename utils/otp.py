import random 
def generate_otp_for_signup():
    otp = str(random.randint(100000, 999999))
    print(f"OTP generated: {otp}")
    return otp