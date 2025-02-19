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
from .views import  SalespersonPipelineProgress,GenerateDemoCredentials,SendClinicRegistredLinkAfterDemo,ActivityLog
urlpatterns = [
   path('salesperson-pipeline-progress' , SalespersonPipelineProgress.as_view() , name="salesperson-pipeline-progress"),
   path('generate-demo-credentials/' , GenerateDemoCredentials.as_view() , name="generate-demo-credentials"), #/generate_demo_credentials
   path('clinic-register-link/' , SendClinicRegistredLinkAfterDemo.as_view() , name="send-registred-link"),#/clinic_register_link
   path('get_activity_log/' , ActivityLog.as_view() , name="send-registred-link"), #get_activity_log/
   path('insert-pipeline-progress/' , ActivityLog.as_view() , name="send-registred-link"), #insert_pipeline_progress

   

]
