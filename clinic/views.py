from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
import time
from datetime import date
from authentication.models import UserProfile , CustomUser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q, FloatField,Value,CharField,OuterRef,Subquery,When,Case,ExpressionWrapper,fields,Prefetch
from django.db.models.functions import Coalesce
from itertools import chain
from datetime import timedelta,datetime
from django.utils.timezone import now
from django.utils import timezone
from authentication.models import CustomUser ,UserProfile
from clinic.models import Clinics,DemoRequested,ClinicAppointments,Disorders,ClinicUserReminders,Tasks
from payment.models import Payment,Invoice
from slp.models import Slps
from .models import AssessmentResults
from slp.models import SlpAppointments

def get_date_obj(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None
def get_time_obj(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        return None

def get_date_filter(time_filter):
    date_filter =None
    if time_filter == 'last_month':
        date_filter = now() - timedelta(days=30)
    elif time_filter == 'annual':
        date_filter = now() - timedelta(days=365)
    return date_filter

#/get_clinics
#/get_clinics_ids
class GetClinicsWithIdName(APIView):
    def get(self,request):
        try:
            clinics = Clinics.objects.values("clinic_id", "clinic_name").order_by("clinic_name")
            return Response(clinics,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/get_patient_contact_details/<int:clinic_id>
class ClinicPatients(APIView):
    def get(self,request,clinic_id):
        try:
            clinic_patients = UserProfile.objects.filter(
                clinic_id=clinic_id,
                user__user_type = "patient"
            ).values("full_name","contact_number","user_id")
            return Response({clinic_patients},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)
#/get_patient_overview/<int:clinic_id>
class ClinicOverview(APIView):
    def get(self , request , clinic_id):
        try:
            time_filter = request.GET.get("time_filter")
            date_filter = get_date_filter(time_filter)

            # Prefetch related users and payments efficiently
            user_profiles_prefetch = Prefetch(
                "user_profiles",
                queryset=UserProfile.objects.select_related("user").prefetch_related(
                    Prefetch(
                        "user__payments",
                        queryset=Payment.objects.filter(payment_status="Paid"),
                        to_attr="filtered_payments"
                    )
                ),
                to_attr="prefetched_user_profiles"
            )

            revenue_per_clinic_subquery = Clinics.objects.prefetch_related(user_profiles_prefetch).filter(
                clinic_id=clinic_id
            ).annotate(
                revenue=Coalesce(
                    Sum(
                        'user_profiles__user__payments__amount',
                        filter=Q(user_profiles__user__payments__payment_status='Paid'),
                        output_field=FloatField()
                    ),
                    Value(0.0, output_field=FloatField())
                ),
                patients=Count(
                    "user_profiles",
                    filter=Q(user_profiles__user__created_account__date__gte=date_filter)
                )
            ).values('revenue', "patients").first()
            return Response(revenue_per_clinic_subquery,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/get_patient_details/<int:clinic_id>
#/get_payment_tracking/<int:clinic_id>
class PatientOverview(APIView):
    def get(self,request,clinic_id):
        try:
            time_filter = request.GET.get("time_filter")
            date_filter = get_date_filter(time_filter)

            revenue_per_patient = UserProfile.objects.filter(
                clinic_id=clinic_id, 
                user__payments__payment_status="Paid"
                ).annotate(
                    revenue_generated=Sum("user__payments__amount",filter=Q(user__payments__payment_date__gte=date_filter)),
                    username = F("user__username"),
                    created_account = F("user__created_account")
                ).values("user_id", "username","country","state","status", "revenue_generated","created_account")
            return Response(revenue_per_patient,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_patient_reg_percent/<int:clinic_id>
#check the time filter once whether it's from monthly starting date or last 30days for monthly
class RegistrationPercentage(APIView):
    def get(self,request,clinic_id):
        try:
            # Get the current time in the correct timezone
            today = timezone.now()
            time_filter = request.GET.get("time_filter")
            # Set the time range based on the filter
            # Set the time range for Monthly or Annual
            if time_filter == "monthly":
                start_time = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # Start of the month
            elif time_filter == "annual":
                start_time = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)  # Start of the year
            else:
                return {"error": "Invalid time filter. Use 'monthly' or 'annual'."}
            

            # **1️⃣ Get the total number of patients in the clinic**
            clinic_patient_stats = UserProfile.objects.filter(
                clinic_id=clinic_id,
                user__user_type="patient"
            ).aggregate(
                total_patients=Count("profile_id",distinct=True,filter=Q(user__date_joined__gte=start_time)), #registration for monthly/daily/weekly
                new_registrations=Count("profile_id",distinct=True,filter=Q(user__date_joined__date=today.date())) # today's registrations
            )
            

            total_patients = clinic_patient_stats["total_patients"]
            new_registrations = clinic_patient_stats["new_registrations"]

            # **3️⃣ Calculate the percentage**
            if total_patients == 0:
                percentage = 0  # Avoid division by zero
            else:
                percentage = (new_registrations / total_patients) * 100
            
            return Response({"registration_percentage":percentage},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_200_OK)

#/get_patient_revenue_percent/<int:clinic_id>
#need to check at date filter 
class RevenuePercentage(APIView):
    def get(self,request,clinic_id):
        try:
            today = timezone.now()
            time_filter = request.GET.get("time_filter")
            # Set the time range for Monthly or Annual
            if time_filter == "monthly":
                start_time = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # Start of the month
            elif time_filter == "annual":
                start_time = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)  # Start of the year
            else:
                return {"error": "Invalid time filter. Use 'monthly' or 'annual'."}
            
            clinic_patient_statistics = Clinics.objects.filter(
                clinic_id = clinic_id
            ).annotate(
                total_revenue=Coalesce(
                    Sum(
                        'user_profiles__user__payments__amount',
                        filter=Q(user_profiles__user__payments__payment_date__gte=start_time) & Q(user_profiles__user__payments__payment_status='Paid'),
                        output_field=FloatField()
                    ), Value(0.0, output_field=FloatField())
                ),
                todays_revenue=Coalesce(
                    Sum(
                        'user_profiles__user__payments__amount',
                        filter=Q(user_profiles__user__payments__payment_date__date=today.date()) & Q(user_profiles__user__payments__payment_status='Paid'),
                        output_field=FloatField()
                    ), Value(0.0, output_field=FloatField())
                )
            ).values("todays_revenue","total_revenue").first()
            
            total_revenue = clinic_patient_statistics["todays_revenue"]
            todays_revenue = clinic_patient_statistics["total_revenue"]
            if total_revenue == 0:
                percentage = 0  # Avoid division by zero
            else:
                percentage = (todays_revenue / total_revenue) * 100
            return Response({percentage},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_200_OK)

#/attend_appointment_clinic/<int:appointment_id>
#/cancel_appointment_clinic/<int:appointment_id>
#/update_appointment_status/<int:appointment_id>
#/create_clinic_appointment
# need to implement sendnotification
class ClinicAppointmentView(APIView):
    def post(self,request):
            try:
                clinic_id = request.data.get('clinic_id')
                slp_id = request.data.get('slp_id')
                user_id = request.data.get('user_id')
                disorder_ids = request.data.getlist('disorder_id')  # Accept multiple disorder IDs directly
                session_type = request.data.get('session_type')
                appointment_date = request.data.get('appointment_date') #format 2013-09-27
                start_time = request.data.get('start_time') #format 20:17:28
                end_time = request.data.get('end_time')
                # Convert date & time strings to datetime objects
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                    start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
                    end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()
                except ValueError:
                    return Response({'error': 'Invalid date or time format.'}, status=400)
                clinic = get_object_or_404(Clinics, id=clinic_id)
                slp = get_object_or_404(Slps, id=slp_id)
                user = get_object_or_404(CustomUser, id=user_id)

                appointments = [
                        ClinicAppointments(
                            clinic=clinic,
                            slp=slp,
                            user=user,
                            disorder_id=disorder,
                            session_type=session_type,
                            appointment_date=date_obj,
                            appointment_start=start_time_obj,
                            appointment_end=end_time_obj
                        ) for disorder in disorder_ids
                    ]
                ClinicAppointments.objects.bulk_create(appointments)
                # Send notifications to SLP and User
                message = f"New appointment scheduled for {appointment_date} from {start_time} to {end_time}."
                
                # Get SLP's UserID from the Slps table
                if slp_id:
                    slp_user_id = Slps.objects.filter(slp_id=slp_id).values_list("user_id", flat=True).first()
                    if slp_user_id:
                        #send_notification(user_id=slp_user[0],section="SLP", notification_type='New Appointment', message=message)
                        print(f"Notification sent to SLP UserID {slp_user_id}: {message}")

                # Notify user
                #send_notification(user_id=int(user_id),section="User", notification_type='New Appointment', message=message)
                print(f"Notification sent to User UserID {user_id}: {message}")

                return Response({'message': 'Clinic appointment created successfully.'},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)
            
    def put(self,request,appointment_id):
        try:
            status = request.data.get("status")
            
            if status not in ["pending","completed","rescheduled"]:
                return Response({"error":"Invalid status"},status=status.HTTP_400_BAD_REQUEST)
                        # Fetch the salesperson object
            clinic_appointment = ClinicAppointments.objects.filter(appointment_id=appointment_id).first()
            if not clinic_appointment:
                return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

            clinic_appointment.appointment_status = status
            # Save only if any field is updated
            clinic_appointment.save()
            return Response({clinic_appointment},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

    def get(self,request,appointment_id):
            try:
                return Response({},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_clinic_appointments_details/<int:clinic_id>
#/get_clinic_appointments/<int:clinic_id> #query paramater status = pending
class ClinicAppointmentsApi(APIView):
    def get(self,request,clinic_id):
            try:
                status = request.GET.get("status", None)
                if status is None:
                    clinic_appointments = ClinicAppointments.objects.filter(
                        clinic_id=clinic_id
                        ).values("appointment_id","appointment_date","appointment_start","appointment_end","session_type","appointment_status","disorder_id").order_by("-appointment_id")
                elif status == "pending":
                    clinic_appointments = ClinicAppointments.objects.filter(
                        clinic_id=clinic_id,
                        appointment_status="pending"
                    ).values("appointment_id","appointment_date","appointment_start","appointment_end","session_type","appointment_status","user_id").order_by("-appointment_id")
                else:
                    return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({clinic_appointments},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/reschedule_appointment_clinic/<int:appointment_id>
class ResecheduleAppointment(APIView):
    def put(self, request,appointment_id):
        reschedule_date = request.GET.get('RescheduleDate')
        appointment_start = request.GET.get('AppointmentStart')
        appointment_end = request.GET.get('AppointmentEnd')

        if not appointment_id or not reschedule_date or not appointment_start or not appointment_end:
            return Response({'error': 'All required fields must be provided for rescheduling.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update the appointment status
            date_obj = datetime.strptime(appointment_start, "%Y-%m-%d").date()  # Convert to date object
            time_obj = datetime.strptime(appointment_end, "%H:%M:%S").time()

            rows_affected = ClinicAppointments.objects.filter(appointment_id=appointment_id).update(
                appointment_status="Rescheduled",
                appointment_date=reschedule_date,
                appointment_start=appointment_start,
                appointment_end=(datetime.combine(date_obj, time_obj) + timedelta(hours=1)).time()
            )

            if rows_affected > 0:
                appointment_data = ClinicAppointments.objects.filter(appointment_id=appointment_id).values("user_id", "slp_id","slp__user_id").first()
            else:
                return Response({"message":"No appointment found with appointment_id=1"},status=status.HTTP_404_NOT_FOUND)

            # Fetch UserID and SlpID for notification
            if not appointment_data:
                return JsonResponse({'message': 'Appointment not found for notification.'}, status=404)

            user_id = appointment_data["user_id"]
            slp_id = appointment_data["slp_id"]
            slp_user_id = appointment_data["slp__user_id"]


            # Send notifications to SLP and User
            message = f"Appointment rescheduled to {reschedule_date} from {appointment_start} to {appointment_end}."

            if slp_user_id:
                #send_notification(user_id=slp_user_id, section="SLP", notification_type='Rescheduled Appointment', message=message)
                print(f"Notification sent to SLP UserID {slp_user_id}: {message}")

            if user_id:
                #send_notification(user_id=user_id, section="User", notification_type='Rescheduled Appointment', message=message)
                print(f"Notification sent to User UserID {user_id}: {message}")

            return JsonResponse({'message': 'Appointment rescheduled successfully.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

#/get_slps_patients_and_disorders_by_clinic/<int:ClinicID>
class ClinicSlpsPatientsDisorders(APIView):
    def get(self,request,clinic_id):
        try:
            disorder_list = Disorders.objects.values("disorder_id","disorder_name") 
            #or hardcode value because same always same 
            disorder_list_hardcoded = [
                {'disorder_id': 1, 'disorder_name': 'Articulation'},
                  {'disorder_id': 2, 'disorder_name': 'Stammering'}, 
                  {'disorder_id': 3, 'disorder_name': 'Voice'},
                {'disorder_id': 4, 'disorder_name': 'Expressive Language'}, 
                {'disorder_id': 5, 'disorder_name': 'Receptive Language'}
                ]
            slp_list = Slps.objects.filter(
                clinic_id=clinic_id
                ).values("slp_id","slp_name")
            patients_list = UserProfile.objects.filter(
                clinic_id=clinic_id
            ).values("user_id","username")
            return Response({"slps":slp_list,"patients":patients_list,"disorders":disorder_list_hardcoded},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/add_clinic_user_reminder
#/get_reminders_by_clinic/<int:clinic_id>
class ClinicUserRemindersApi(APIView):
    def post(self, request, clinic_id):
        try:
            # Extract data
            reminder_appointment = request.data.get('reminder_appointment')
            reminder_description = request.data.get('reminder_description')
            reminder_to = request.data.get('reminder_to')
            reminder_date = request.data.get('date')  # Expected format: YYYY-MM-DD
            reminder_time = request.data.get('time')  # Expected format: HH:MM:SS

            # Validate required fields
            if not all([reminder_appointment, reminder_description, reminder_to, reminder_date, reminder_time]):
                return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Convert date & time strings to datetime objects
            try:
                reminder_date_obj = datetime.strptime(reminder_date, "%Y-%m-%d").date()
                reminder_time_obj = datetime.strptime(reminder_time, "%H:%M:%S").time()
            except ValueError:
                return Response({"error": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

            reminder_datetime = timezone.make_aware(datetime.combine(reminder_date_obj, reminder_time_obj))

            clinic = get_object_or_404(Clinics, clinic_id=clinic_id)
            reminder_appointment = get_object_or_404(ClinicAppointments, appointment_id=reminder_appointment)

            # Create a new reminder
            reminder = ClinicUserReminders.objects.create(
                clinic=clinic,
                reminder_appointment=reminder_appointment,
                reminder_description=reminder_description,
                reminder_to=reminder_to,
                date=reminder_datetime,
                time=reminder_datetime
            )

            return Response({"message": "Reminder added successfully!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request,clinic_id):
            try:
                clinic_remainders = ClinicUserReminders.objects.filter(
                    clinic_id=clinic_id
                ).values("reminder_id","reminder_appointment","reminder_description","reminder_to","date","time","clinic_id")
                return Response({clinic_remainders},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)
#/get_slps_by_clinic/<int:clinic_id>
#/get_slps_ids_by_clinic
class ClinicSlps(APIView):
    def get(self,request,clinic_id):
            try:
                clinic_slps = Slps.objects.filter(
                    clinic_id=clinic_id
                ).values("slp_id","slp_name","clinic_id","country","state","status")
                return Response({clinic_slps},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/slp_register_link
#need to implement email function
class SLPRegisterLink(APIView):
    def post(self,request):
            try:
                email = request.data.get('email')
                clinic_id = request.data.get('clinic_id')
                signup_link = "https://frontend.izzyai.com/signup"
                #send_slp_signup_link_email(email, clinic_id, signup_link)
                return Response({'message': 'Clinic registration link sent successfully!'},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_clinic_tasks/<int:clinic_id>
class ClinicAppointmentsTasks(APIView):
    def get(self,request,clinic_id):
            try:
                fullname_query = UserProfile.objects.filter(
                    user_id=OuterRef("user_id")
                ).values("full_name")[:1] 
                clinic_appointment_tasks = ClinicAppointments.objects.filter(
                    clinic_id=clinic_id
                ).annotate(
                    full_name = Subquery(fullname_query),
                    slp_name = F("slp__slp_name")
                ).values("slp_name","full_name","user_id").order_by("user_id")

                return Response({clinic_appointment_tasks},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_invoices_by_clinic/<int:clinic_id>
class GetInvoiceByClinic(APIView):
    def get(self,request,clinic_id):
        try:
            status_filter = request.GET.get('status')  # Use GET for query params

            # Base query for invoices related to a specific clinic
            invoices = Invoice.objects.filter(clinic_id=clinic_id).annotate(
                effective_status=Case(
                    When(Q(due_date__lt=datetime.now()) & ~Q(invoice_status='Paid'), then=Value('Past Due')),
                    default=F('invoice_status'),
                    output_field=CharField()
                )
            ).values(
                'invoice_id',
                "effective_status"
            )

            # Apply status filter if provided
            if status_filter:
                invoices = invoices.filter(effective_status=status_filter)

            # Format response
            invoice_list = [
                {
                    "invoice_id": invoice.invoice_id,
                    "total_amount": invoice.amount,
                    "paid_amount": invoice.paid_amount,
                    "invoice_status": invoice.invoice_status,
                    "due_date": invoice.due_date.strftime('%Y-%m-%d'),
                    "effective_status": invoice.effective_status
                }
                for invoice in invoices
            ]
            return Response({},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/create_task
#/get_tasks_by_clinic
class CreateTask(APIView):
    def post(self,request):
            try:
                task_name = request.data.get('task_name')
                description = request.data.get('description')
                status = request.data.get('status')
                slp_id = request.data.get('slp_id')
                clinic_id = request.data.get('clinic_id')
                slp = get_object_or_404(Slps, slp_id=slp_id)
                clinic = get_object_or_404(Clinics, clinic_id=clinic_id)
                task = Tasks.objects.create(
                    task_name=task_name,
                    description=description,
                    status=status,
                    slp=slp,
                    clinic=clinic
                )
                return Response({'message': 'Task created successfully.', 'TaskID': task.task_id},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        try:
            clinic_id = request.GET.get('clinic_id')
            clinic_tasks = Tasks.objects.filter(
                clinic_id=clinic_id
            ).values(
                "task_id",
                "task_name",
                "description",
                "status",
                "slp_id",
                "clinic_id"
            )
            
            return Response({"clinic_id":clinic_id,"tasks":list(clinic_tasks)},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/generate_invoice_report/<int:clinic_id>
class ClinicInvoiceReport(APIView):
    def get(self,request,clinic_id):
        try:
            # Aggregate invoices by status
            report_data = (
                Invoice.objects.filter(clinic_id=clinic_id)
                .annotate(
                    effective_status=Case(
                        When(Q(due_date__lt=datetime.now().astimezone()) & ~Q(invoice_status='Paid'), then=Value('Past Due')),
                        default=F('invoice_status'),
                        output_field=CharField()
                    )
                )
                .values("effective_status")
                .annotate(
                    count=Count("invoice_id"),
                    total_amount=Sum("amount"),
                    total_paid=Sum("paid_amount")
                )
                .order_by("effective_status")
            )
            report = {
                "ClinicID": clinic_id,
                "Summary": [
                    {
                        "Status": row["effective_status"],
                        "Count": row["count"],
                        "TotalAmount": row["total_amount"],
                        "TotalPaid": row["total_paid"]
                    }
                    for row in report_data
                ]
            }
            return Response(report,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/get_utilization_metrics/<int:clinic_id>
class ClinicUtilizationMetrics(APIView):
    def get(self,request,clinic_id):
        try:
            active_users = UserProfile.objects.filter(clinic_id=clinic_id, status='Active').count()
            inactive_users = UserProfile.objects.filter(clinic_id=clinic_id).exclude(status='Active').count()

            # Calculate total users and utilization percentage
            total_users = active_users + inactive_users
            utilization_percentage = round((active_users * 100.0) / total_users, 2) if total_users > 0 else 0.0

            # Prepare response data
            result = {
                'utilization_percentage': utilization_percentage,
                'active_users': active_users,
                'inactive_users': inactive_users
            }
            return Response(result,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/get_attendance_tracking/<int:clinic_id>
class ClinicAttendanceTracking(APIView):
    def get(self,request,clinic_id):
        try:
            start_date = request.data.get("start_date")
            end_date = request.data.get("end_date")

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
            return Response(attendance_list,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/demo_requests,GET
# if request param SlpId is None, returns all demo requests else return demo requests for particular salesperson
    #/update_country,/update_comission_percent, need to verify it's best way to implement assigning in same function
class DemoRequests(APIView):
    def get(self , request):
        try:
            sales_person_id = request.GET.get('sales_person_id', None)
            # Fetch the salesperson object
            if(sales_person_id is None):
                result = DemoRequested.objects.all().values()
                return Response(list(result), status=status.HTTP_200_OK)
            
            salesperson_demo_requests = DemoRequested.objects.filter(sales_person_id=sales_person_id)
            if len(salesperson_demo_requests)==0:
                return Response({'demo_requests': [], "message": "No demo requests found"}, status=status.HTTP_200_OK)
            
            return Response(list(salesperson_demo_requests.values()), status=status.HTTP_200_OK) 

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, demo_request_id):
        try:
            # Fetch the demo request object
            demo_request = DemoRequested.objects.filter(demo_request_id=demo_request_id).first()
            if not demo_request:
                return Response({'error': 'Demo Request not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fields to update
            updatable_fields = ["clinic_name","first_name","last_name","country","comments","contact_number","email","patients_count"]

            # Track if any updates were made
            updated = False

            # Loop through provided fields and update them
            for field in updatable_fields:
                value = request.data.get(field)
                if value is not None:
                    setattr(demo_request, field, value)
                    updated = True  # Mark as updated

            # Save only if any field is updated
            if updated:
                demo_request.save()
                return Response({'message': 'Demo Request updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No changes were made'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/assign_salesperson
class AssignSalePersonToDemoRequest(APIView):
    def put(self, request):
        try:
            demo_request_id = request.data.get('demo_request_id')
            sales_person_id = request.data.get("sales_person_id")
            
            if(sales_person_id is None):
                return Response({"error":"sale_person_id is required"},status=status.HTTP_400_BAD_REQUEST)
            # Fetch the demo request object
            demo_request = DemoRequested.objects.filter(demo_request_id=demo_request_id).first()
            if not demo_request:
                return Response({'error': 'Demo Request not found'}, status=status.HTTP_404_NOT_FOUND)


            # Loop through provided fields and update them
            demo_request.sales_person_id = sales_person_id
            demo_request.save()

            # Save only if any field is updated
            return Response({'message': 'Demo Request updated successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
############### Clinics Screen ##########################
#/get_total_clinics
#/get_total_clinic_revenue

class GetTotalClinics(APIView):
    def get(self,request):
            try:
                location = request.GET.get('location', None)

                # Filter clinics by location
                clinics_by_location = Clinics.objects.filter(state=location).prefetch_related(
                    "user_profiles__user__payments"
                )
                # Annotate each clinic with its stats
                clinics = clinics_by_location.annotate(
                    patients_per_clinic=Count("user_profiles__user", distinct=True),
                    slps_per_clinic=Count("user_profiles__slp", distinct=True),
                    revenue_per_clinic=Coalesce(
                        Sum(
                            "user_profiles__user__payments__amount",
                            filter=Q(user_profiles__user__payments__payment_status="Paid"),
                            output_field=FloatField(),
                        ),
                        Value(0.0, output_field=FloatField()),
                    ),
                    location=F("state"),
                ).values(
                    "clinic_name", "location", "patients_per_clinic", "slps_per_clinic", "revenue_per_clinic"
                )
                
                # Single query to get total revenue and clinic count
                clinic_totals = clinics_by_location.aggregate(
                    total_clinics=Count("clinic_name", distinct=True),
                    total_revenue=Coalesce(
                        Sum(
                            "user_profiles__user__payments__amount",
                            filter=Q(user_profiles__user__payments__payment_status="Paid"),
                            output_field=FloatField(),
                        ),
                        Value(0.0, output_field=FloatField()),
                    ),
                )

                response_data = {
                    "total_clinics": clinic_totals["total_clinics"],
                    "total_revenue": clinic_totals["total_revenue"],
                    "clinics": list(clinics),
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_clinic_revenue_percentage
class GetClinicRevenuePercentage(APIView):
    def get(self,request):
        try:
            time_filter = request.GET.get('time_filter')  # Get time filter from request
            date_filter =get_date_filter(time_filter)

            query_result = CustomUser.objects.filter(
                user_type="clinic",
            ).aggregate(
                todays_revenue=Coalesce(
                    Sum('payments__amount', filter=Q(payments__payment_date__date=date.today()) & Q(payments__payment_status='Paid')),
                    Value(0.0, output_field=FloatField())
                    ),
                total_revenue=Coalesce(
                    Sum('payments__amount', filter=Q(payments__payment_date__gte=date_filter) & Q(payments__payment_status='Paid')),
                    Value(0.0, output_field=FloatField())
                    ),
            )
            todays_revenue = query_result['todays_revenue']
            total_revenue = query_result['total_revenue']
            if total_revenue > 0:
                revenue_percentage = round((todays_revenue * 100.0) / total_revenue,2)
            else:
                revenue_percentage = 0.0

            return Response({revenue_percentage}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/get_clinic_reg_percentage
class GetClinicRegistractionPercentage(APIView):
    def get(self,request):
            try:
                time_filter = request.GET.get('time_filter')  # Get time filter from request
                date_filter = get_date_filter(time_filter)

                query_result = CustomUser.objects.filter(
                    user_type="clinic",
                ).aggregate(
                    todays_registrations=Count('user_id', filter=Q(created_account__date=date.today())),
                    total_registrations=Count("user_id", filter=Q(created_account__gte=date_filter) if date_filter else Q())
                )
                todays_registrations = query_result['todays_registrations']
                total_registrations = query_result['total_registrations']
                if total_registrations > 0:
                    registration_percentage = round((todays_registrations * 100.0) / total_registrations,2)
                else:
                    registration_percentage = 0.0

                return Response({registration_percentage},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_clinic_details
class ClinicDetails(APIView):
    def get(self,request):
            try:
                location = request.GET.get("location", None)
                clinics_by_location = Clinics.objects.filter(state=location).prefetch_related(
                    "user_profiles__user__payments"
                )
                if(location):
                    query_result = clinics_by_location.annotate(
                        total_users=Count('user_profiles',distinct=True),
                        total_slps = Count('slps',distinct=True),
                        revenue_per_clinic = Coalesce(
                            Sum(
                                "user_profiles__user__payments__amount",
                                filter=Q(user_profiles__user__payments__payment_status="Paid"),
                                output_field=FloatField(),
                            ),
                            Value(0.0, output_field=FloatField()),
                        )
                    ).values("clinic_name","clinic_id","total_users","total_slps","revenue_per_clinic")
                else:
                    query_result = clinics_by_location.annotate(
                        total_users=Count('user_profiles',distinct=True),
                        total_slps = Count('slps',distinct=True),
                        revenue_per_clinic = Coalesce(
                            Sum(
                                "user_profiles__user__payments__amount",
                                filter=Q(user_profiles__user__payments__payment_status="Paid"),
                                output_field=FloatField(),
                            ),
                            Value(0.0, output_field=FloatField()),
                        )
                    ).values("clinic_name","clinic_id","total_users","total_slps","revenue_per_clinic")            
                    
                return Response({query_result},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#get_clinic_revenue_details
class ClinicRevenue(APIView):
    def post(self,request):
        try:
            time_filter = request.GET.get('time_filter')  # Get time filter from request
            date_filter = get_date_filter(time_filter)
            clinic_revenue = Clinics.objects.annotate(
                revenue=Coalesce(
                    Sum(
                        'user_profiles__user__payments__amount',
                        filter=Q(user_profiles__user__payments__payment_date__gte=date_filter) & Q(user_profiles__user__payments__payment_status='Paid'),
                        output_field=FloatField()
                    ), Value(0.0, output_field=FloatField())
                )
            ).values('revenue',"clinic_id","clinic_name")
            return Response({clinic_revenue},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/update_clinic_location_name/<int:ClinicID>
#/get_clinic_details_popup/<int:clinic_id>
class ClinicView(APIView):
    def put(self,request,clinic_id):
        try:
            # Fetch the salesperson object
            clinic = Clinics.objects.filter(clinic_id=clinic_id).first()
            if not clinic:
                return Response({'error': 'SalePerson not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fields to update
            updatable_fields = ["state", "country", "email", "ein_number", "phone","address"]

            # Loop through provided fields and update them
            updated = False 
            for field in updatable_fields:
                value = request.data.get(field, getattr(clinic, field))
                if value is not None:  # Update only if field is provided
                    setattr(clinic, field, value)
                    updated = True

            # Save only if any field is updated
            if updated:
                clinic.save()
        
            return Response({'message': 'Clinic updated successfully'}, status=status.HTTP_200_OK)
            return Response({},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    def get(self,request,clinic_id):
        try:
            clinic = Clinics.objects.filter(clinic_id=clinic_id)\
                    .values("clinic_id","clinic_name","state","country","email","phone","address").first()

            return Response({clinic},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/get_total_clinic_revenue_with_time_filter
class AllClinicsRevenue(APIView):
    def post(self,request):
        try:
           all_clinics_revenue = Payment.objects.filter(
                payment_status='Paid',
                user__user_profiles__user__user_type='clinic'  # Filters only clinic payments
            ).aggregate(
                total_revenue=Coalesce(Sum('amount', output_field=FloatField()), Value(0.0, output_field=FloatField()))
            )
           return Response(all_clinics_revenue,status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_disorder_id/<int:user_id> 
#/get_disorder_details/<int:UserID>
class UserDisordersView(APIView):
    def get(self,request,user_id):
        try:
            # Fetch unique DisorderIDs for the given UserID
            disorder_ids = AssessmentResults.objects.filter(user_id=user_id).values_list("disorder_id", flat=True).distinct()

            # Fetch DisorderNames for the unique DisorderIDs
            disorders = Disorders.objects.filter(disorder_id__in=disorder_ids).values("disorder_id", "disorder_name")
            # Format the response
            disorder_details = [
                {
                    'user_id': user_id,
                    'disorder_id': disorder["disorder_id"],
                    'disorder_name': disorder["disorder_name"]
                }
                for disorder in disorders
            ]
            return Response(disorder_details, status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_next_appointments/<int:UserID>
#need to check at SlpAppointments.appointment_date received a naive datetime ,slp start time in datetimefield not timefield need to ask them and modity model and change filter
class UserNextAppointment(APIView):
    def get(self,request,user_id):
        try:
            today = date.today()

            # Fetch upcoming clinic appointments
            clinic_appointments = ClinicAppointments.objects.filter(
                user_id=user_id, appointment_date__gte=today
            ).values(
                "session_type", "appointment_start", "appointment_end", "appointment_date"
            ).annotate(appointment_source=Value("Clinic"))

            # Fetch upcoming SLP appointments
            slp_appointments = SlpAppointments.objects.filter(
                user_id=user_id, appointment_date__gte=today
            ).values(
                "session_type", "start_time", "end_time", "appointment_date"
            ).annotate(appointment_source=Value("SLP"))

            # Combine both queryset results
            all_appointments = list(chain(clinic_appointments, slp_appointments))

            # Standardize field names and format response
            formatted_appointments = [
                {
                    "user_id": user_id,
                    "session_type": appt["session_type"],
                    "start_time": appt.get("appointment_start", appt.get("start_time")),
                    "end_time": appt.get("appointment_end", appt.get("end_time")),
                    "appointment_date": appt["appointment_date"],
                    "appointment_source": appt["appointment_source"],
                }
                for appt in all_appointments
            ]

            # Sort combined appointments by date & start time
            formatted_appointments.sort(key=lambda x: (x["appointment_date"], x["start_time"]))
            if not formatted_appointments:
                return Response({'message': 'No upcoming appointments found for this UserID'}, status=status.HTTP_200_OK)

            return Response(formatted_appointments, status=status.HTTP_200_OK)

        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)