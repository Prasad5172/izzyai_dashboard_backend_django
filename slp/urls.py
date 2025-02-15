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
from .views import SlpApiView ,SlpUsersLog , SlpPatients,SlpAppointments , SlpReschedule,SlpTasks,SlpAppointmentsGoal,SlpTherapyPatients  ,SlpTreatment
urlpatterns = [
   
   path('get_slp_details/<int:SlpID>' , SlpApiView.as_view() , name="slp_details"),
   path('update_slp/<int:SlpID>' , SlpApiView.as_view() , name="slp_update") , 
   path('get_users_logs/<int:SlpID>' , SlpUsersLog.as_view() , name="slp_log"),
   path('get_patient/<int:UserID>/' , SlpPatients.as_view() , name="slp_patient") , 
   path('/update_patient/<int:UserID>/', SlpPatients.as_view() , name="slp_update_patient") ,
   path('create_slps_appointment' ,SlpAppointments.as_view() , name="slp_create_appointment"),
   path('/get_slp_appointments_details/<int:slp_id>/' , SlpAppointments.as_view() , name="slp_appointment_details"),
   path('/status_appointment/<int:appointment_id>/' , SlpAppointments.as_view() , name="slp_attend_appointment"),
   path('/reschedule_appointment/<int:appointment_id>' ,SlpReschedule.as_view() , name="slp_reschedule_appointment"),
   path('get_tasks_by_slp' , SlpTasks.as_view() , name="slp_tasks"),
   path('update_task_status' , SlpTasks.as_view() , name="slp_update_task"),
   path('/get_appointments_goals/<int:slp_id>' , SlpAppointmentsGoal.as_view() , name="slp_appointment_goals"),
   path('get_patients_by_slp/<int:slp_id>' , SlpTherapyPatients.as_view() , name= "slp_treatment_patients"),
   path('add_therapy_data/' ,SlpTherapyPatients.as_view() , name="slp_add_therapy_data"),
   path('create_treatment_data/', SlpTreatment.as_view() , name="slp_treatment") 

]
