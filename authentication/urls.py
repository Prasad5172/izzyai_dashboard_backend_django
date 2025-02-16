"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from .views import AdminAndSaleDirectorSignupAPIView ,SlpSignupAPIView , Sales_Person_SignupAPIView , ClinicSignupAPIView , SendOTPForSignupView ,VerifyOTPView, UpdatePasswordView , LoginAPIView
urlpatterns = [
   path('signup/',AdminAndSaleDirectorSignupAPIView.as_view(),name="signup"),
   path('slp_signup/',SlpSignupAPIView.as_view(),name="slp_signup"),
   path('sale_person_signup/',Sales_Person_SignupAPIView.as_view(),name="sales_person_signup"),
   path('clinic_signup/',ClinicSignupAPIView.as_view(),name="clinc_signup"),
   path('sendotp/',SendOTPForSignupView.as_view(),name="sendotp"),
   path('verifyotp/',VerifyOTPView.as_view(),name="verifyotp"),
   path('update_password/' , UpdatePasswordView.as_view(), name="update_password"),
   path('login/' , LoginAPIView.as_view(), name="login")
  

]
