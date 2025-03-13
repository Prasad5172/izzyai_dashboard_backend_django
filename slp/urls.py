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
from .views import SlpView,GetExceriseResults,CompletedPatientsCountView,SlpTasksView,TreatmentDataView,TherapyDataIds,TherapyDataView,PatientsBySlpView,UserLogsView,SLPPatinetAttendance,SLPReport,SLPAppointmentsGoals,GetSLPAppointmentsTask,RescheduleAppoinment,AttendanceTracking,UpdatePatientStatus,GetUsersAndDisordersBySLP,SlpAppoinmentView

urlpatterns = [
   path('get_slp_details/' , SlpView.as_view() , name="generate-demo-credentials"),
   path('get_slp_patients/' , CompletedPatientsCountView.as_view() , name="generate-demo-credentials"),
   path('user_logs/' , UserLogsView.as_view() , name="generate-demo-credentials"),
   path('get_attendance_tracking_over_time/' , AttendanceTracking.as_view() , name="generate-demo-credentials"),
   path('update_patient_status_under_slp/' , UpdatePatientStatus.as_view() , name="generate-demo-credentials"),
   path('get_users_and_disorders_by_slp/' , GetUsersAndDisordersBySLP.as_view() , name="generate-demo-credentials"),
   path('slp_appointments/' , SlpAppoinmentView.as_view() , name="generate-demo-credentials"),
   path('reschedule_slp_appointments/' , RescheduleAppoinment.as_view() , name="generate-demo-credentials"),
   path('get_slp_appointments/' , GetSLPAppointmentsTask.as_view() , name="generate-demo-credentials"),
   path('get_appointments_goals/' , SLPAppointmentsGoals.as_view() , name="generate-demo-credentials"),
   path('slp_report/' , SLPReport.as_view() , name="generate-demo-credentials"),
   path('slp_patient_attendance/' , SLPPatinetAttendance.as_view() , name="generate-demo-credentials"),
   path('slp_patient/' , PatientsBySlpView.as_view() , name="generate-demo-credentials"),
   path('therapy_data/' , TherapyDataView.as_view() , name="generate-demo-credentials"),
   path('therapy_data_ids/' , TherapyDataIds.as_view() , name="generate-demo-credentials"),
   path('treatment_data/' , TreatmentDataView.as_view() , name="generate-demo-credentials"),
   path('slp_tasks/' , SlpTasksView.as_view() , name="generate-demo-credentials"),
   path('slp/' , SlpView.as_view() , name="generate-demo-credentials"),
   path('user_exercise/', GetExceriseResults.as_view() , name="generate-demo-credentials"),
]
