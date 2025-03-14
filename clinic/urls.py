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
from .views import ClinicPatients,GetClinicRegistractionPercentage,GetTotalClinicsOverview,DemoRequests,PatientOverview,AssignSalePersonToDemoRequest,GetClinicsWithIdName
urlpatterns = [
   
   path('get_patient_details/<int:clinic_id>' , ClinicPatients.as_view() , name="get_patient_details") ,
   path('demo_requests/' , DemoRequests.as_view() , name="get_patient_details") ,
   path('assign_salesperson/' , AssignSalePersonToDemoRequest.as_view() , name="get_patient_details") ,
   path('get_clinics/' , GetClinicsWithIdName.as_view() , name="get_patient_details") ,
   path('patient_overview/' , PatientOverview.as_view() , name="get_patient_details") ,
   path('total_clinics/' , GetTotalClinicsOverview.as_view() , name="get_patient_details") ,
   path('clinic_reg_percentage/',GetClinicRegistractionPercentage.as_view() , name="get_patient_details") ,

]
