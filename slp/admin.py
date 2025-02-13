from django.contrib import admin
from .models import Slps, SlpAppointments

@admin.register(Slps)
class SlpsAdmin(admin.ModelAdmin):
    list_display = ('slp_id', 'slp_name', 'email', 'phone', 'status', 'clinic_id', 'country', 'state')
    search_fields = ('slp_name', 'email', 'phone')
    list_filter = ('status', 'country', 'state')

@admin.register(SlpAppointments)
class SlpAppointmentsAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'slp_id', 'user_id', 'disorder_id', 'appointment_date', 'session_type', 'appointment_status', 'start_time', 'end_time')
    search_fields = ('appointment_id', 'slp_id__slp_name', 'user_id__email')
    list_filter = ('appointment_status', 'session_type', 'appointment_date')

