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
from .views import  GenerateDemoCredentials,SendClinicRegistredLinkAfterDemo,ActivityLog,SalesPersonView,UpdateSalesPersonProfile,GetSalesPersonsIdsNames,PipeLineProgress,GetMonthlyRegistrationsPatientsClinics,GetClinicRevenueBySalesPerson,GetWeeklyMonthlyQuaterlySalesBySalesPerson,GetSalesBySalesPerson
urlpatterns = [
   path('generate_demo_credentials/' , GenerateDemoCredentials.as_view() , name="generate-demo-credentials"),
   path('get_salesperson_details/' , SalesPersonView.as_view() , name="send-registred-link"),
   path('update_profile_sales_person/' , UpdateSalesPersonProfile.as_view() , name="send-registred-link"),
   path('salespersons_ids/' , GetSalesPersonsIdsNames.as_view() , name="send-registred-link"),
   path('clinic_register_link/' , SendClinicRegistredLinkAfterDemo.as_view() , name="send-registred-link"),
   path('activity_log/' , ActivityLog.as_view() , name="send-registred-link"),
   path('pipeline_progress/' , PipeLineProgress.as_view() , name="send-registred-link"),
   path('get_monthly_registrations/' , GetMonthlyRegistrationsPatientsClinics.as_view() , name="send-registred-link"),
   path('get_clinic_revenue_by_saleperson/' , GetClinicRevenueBySalesPerson.as_view() , name="send-registred-link"),
   path('track_sales_by_saleperson_graph/' , GetWeeklyMonthlyQuaterlySalesBySalesPerson.as_view() , name="send-registred-link"),
   path('track_sales_by_saleperson/' , GetSalesBySalesPerson.as_view() , name="send-registred-link"),

   

]
