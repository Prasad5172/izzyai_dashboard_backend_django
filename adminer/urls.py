from django.contrib import admin
from django.urls import path , include
from .views import TotalUsersWithRevenue,RevenuePercentage,RegistrationPercentage

urlpatterns = [
   path('get_users_overview/' , TotalUsersWithRevenue.as_view() , name="generate-demo-credentials"),
   path('revenue_percentage/' , RevenuePercentage.as_view() , name="generate-demo-credentials"),
   path('registration_percentage/' , RegistrationPercentage.as_view() , name="generate-demo-credentials"),
   
]