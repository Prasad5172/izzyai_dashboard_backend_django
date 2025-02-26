import random
import string

from django.shortcuts import get_object_or_404
from payment.models import Payment
from clinic.models import Clinics

from django.utils.timezone import now, timedelta,datetime
from django.utils import timezone
from datetime import date
from authentication.models import CustomUser,UserProfile
from django.db.models import Sum, F,Value,CharField,Count,Func,Q,FloatField,OuterRef,Subquery,Case,When,ExpressionWrapper,IntegerField,Avg,fields
from django.utils.dateformat import DateFormat
from django.db.models.functions import TruncDate,TruncTime,Cast,Round,Coalesce
from utils.MonthsShortHand import MONTH_ABBREVIATIONS
from sales_person.models import SalePersons
from clinic.models import DemoRequested,Tasks
from rest_framework import status
from rest_framework.response import Response
from slp.models import Slps,SlpAppointments
from clinic.models import TreatmentData,TherapyData,ClinicAppointments,Sessions,Disorders,ClinicUserReminders
from collections import defaultdict
from authentication.models import UserExercises,UsersInsurance
from payment.models import Subscriptions,Invoice
import json
import re
from faker import Faker
def printlist(list):
    for i in list:
        print(i)

def run():
    fake: Faker = Faker()
    sales_person_id = 1
    user_id = 2
    slp_id = 1
    clinic_id = 7
    date_str = fake.date()
    time_str = fake.time()
    #date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert to date object
    #time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
    # Fetch the patient object
    # Extract data
    reminder_appointment = 1
    reminder_description = "description"
    reminder_to = "prasad"
    reminder_date = fake.date()  # Expected format: YYYY-MM-DD
    reminder_time = fake.time()  # Expected format: HH:MM:SS
    status_filter = "Paid"
    # Count active and inactive users
    # Extract query parameters
    start_date = "2025-01-01"
    end_date = "2025-01-31"

    # Build the filter dynamically
    filters = {'clinic_id': clinic_id}

    if start_date and end_date:
        filters['appointment_date__range'] = [start_date, end_date]
    elif start_date:
        filters['appointment_date__gte'] = start_date
    elif end_date:
        filters['appointment_date__lte'] = end_date

    # Query clinic appointments
    clinic_appointments = ClinicAppointments.objects.filter(**filters).annotate(
        session_duration=ExpressionWrapper(
            F("appointment_end") - F("appointment_start"),
            output_field=fields.DurationField()
        )
    ).values(
        "user_id",
        "appointment_date",
        "appointment_start",
        "appointment_end",
        "appointment_status",
        "session_duration"
    )

    # Process data into response format
    attendance_list = []
    for appointment in clinic_appointments:
        start_time = appointment["appointment_start"]
        end_time = appointment["appointment_end"]
        duration_seconds = appointment["session_duration"].total_seconds()
        duration_hours = duration_seconds / 3600  # Convert to hours

        attendance_list.append({
            "UserID": appointment["user_id"],
            "SessionDate": appointment["appointment_date"].strftime('%Y-%m-%d'),
            "SessionTime": f'{start_time.strftime("%H:%M")} - {end_time.strftime("%H:%M")}',
            "SessionDuration": f'{duration_hours:.2f} hours',
            "Status": "Attended" if appointment["appointment_status"] == "Attended" else "Missed"
        })

    print(attendance_list)