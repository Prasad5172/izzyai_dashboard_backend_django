from django.contrib import admin
from django.urls import path , include
from .views import PatientDetails , PatientsUpload
urlpatterns = [
   
        path('get_user_profile/<int:UserID>' , PatientDetails.as_view() , name="get_user_profile") , 
        path('update_user_profile/<int:UserID>', PatientDetails.as_view() , name="update_user_profile") , 
        path('upload_patient_documents' , PatientsUpload.as_view() , name="upload_patient_documents")

]