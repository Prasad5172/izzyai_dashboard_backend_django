from django.contrib import admin
from .models import (
    Clinics, Disorders, SessionType, ClinicAppointments, ClinicUserReminders,
    Tasks, Sessions, DemoRequested, PatientFiles, TherapyData, TreatmentData,
    AssessmentResults
)

admin.site.register(Clinics)
admin.site.register(Disorders)
admin.site.register(SessionType)
admin.site.register(ClinicAppointments)
admin.site.register(ClinicUserReminders)
admin.site.register(Tasks)
admin.site.register(Sessions)
admin.site.register(DemoRequested)
admin.site.register(PatientFiles)
admin.site.register(TherapyData)
admin.site.register(TreatmentData)
admin.site.register(AssessmentResults)