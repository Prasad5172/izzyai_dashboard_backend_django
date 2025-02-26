from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count, F, Q, FloatField,Value,CharField,OuterRef,Subquery,Case,When,IntegerField,Avg
from django.db.models.functions import TruncDate,TruncTime
from django.utils.crypto import get_random_string
from django.conf import settings
import re
from datetime import timedelta
from django.utils.timezone import now 
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
import json
from slp.models import Slps,SlpAppointments
from authentication.models import UserProfile , CustomUser,UserExercises
from rest_framework.permissions import IsAuthenticated
from clinic.models import Clinics , ClinicAppointments , Tasks , TherapyData,TreatmentData,Disorders,Sessions
from django.shortcuts import get_object_or_404
from datetime import datetime
from slp.models import Slps
from authentication.models import CustomUser ,UserProfile
from collections import defaultdict
#/get_slp_details,
#/update_slp/<int:SlpID>
class Slp(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self , request , SlpID ):

        """
        Get details of a specific Speech-Language Pathologist (SLP).

        This endpoint retrieves the details of an SLP, including their name, contact information, 
        clinic assignment, the number of users assigned to them, and their profile picture path. 

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP).

        Returns:
        JSON:
            - SlpID: The unique ID of the SLP.
            - SlpName: The name of the SLP.
            - Phone: The phone number of the SLP.
            - Email: The email address of the SLP.
            - Country: The country where the SLP is based.
            - State: The state where the SLP is based.
            - ClinicName: The name of the clinic assigned to the SLP, or 'No Clinic Assigned' if none is assigned.
            - UsersAssigned: The number of users currently assigned to the SLP.
            - ProfilePicture: The file path to the SLP's profile picture.

        Error Responses:
            - 500 Internal Server Error: If there is an issue with the database connection or a query failure.
            Example: {"error": "Database connection error"}
            - 404 Not Found: If no SLP is found with the provided SlpID.
            Example: {"message": "SLP not found"}
        """
        
        try:
            slp = Slps.objects.filter(slp_id=SlpID).annotate(
                users_assigned=Count("user_profiles__user")
            ).values("slp_id", "slp_name", "phone", "email", "country", "state","clinic__clinic_id","users_assigned","profile_image_path").first()
            
            response = {
                "SlpID": slp.slp_id,
                "SlpName": slp.slp_name,
                "Phone": slp.phone,
                "Email": slp.email,
                "Country": slp.country,
                "State": slp.state,
                "ClinicName": slp.clinic.clinic_name if slp.clinic else "No Clinic Assigned",
                "UsersAssigned": slp.users_assigned,
                "ProfileImagePath":slp.profile_image_path
            }
            return Response(response, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "SLP not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, SlpID):
        try:
            # Fetch the salesperson object
            salesperson = Slps.objects.filter(sale_person_id=SlpID).first()
            if not salesperson:
                return Response({'error': 'SalePerson not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fields to update
            updatable_fields = ["slp_name", "phone", "email","country", "state"]

            # Loop through provided fields and update them
            for field in updatable_fields:
                value = request.data.get(field)
                if value is not None:  # Update only if field is provided
                    setattr(salesperson, field, value)

            # Save only if any field is updated
            salesperson.save()

            return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/get_completed_patients,/get_assign_patients/<int:SlpID>
class CompletedPatients(APIView):
    def get(self , request , SlpID ):
        try:
            count = Slps.objects.filter(slp_id=SlpID).annotate(
                completed_patients = Count(
                    "user_profiles"
                    ,filter=Q(user_profiles__status="Archived")),
                patients = Count("user_profiles"),
            ).values_list("patients","completed_patients")
            return Response({"patients":count[0],"completed_patients":count[2]}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_patients_by_slp/<int:slp_id>
#/update_patient_details/<int:UserID>
#/get_users_by_slp/<int:SlpID>
class Patients(APIView):
    def get(self , request , slp_id ):
        try:
            patients = UserProfile.objects.filter(
                slp_id=slp_id
            ).values_list("user_id","full_name","age")
            return Response(patients, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, UserID):
        try:
            email = request.data.get('Email')
            username = request.data.get('UserName')
            #age = request.data.get('Age')
            #gender = request.data.get('Gender')
            #country = request.data.get('Country')
            status = request.data.get('Status')
            user_profile = get_object_or_404(UserProfile, user_id=UserID)
            user = user_profile.user 
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if email:
                user.email = email
            if username:
                user.username = username
            user.save()

            updatable_fields = ["age", "gender", "country", "status"]
            for field in updatable_fields:
                value = request.data.get(field)
                if value is not None:
                    setattr(user_profile, field, value)
            user_profile.save()
            return Response({'message': 'User updated successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#/get_users_logs/<int:SlpID>
class UserLogs(APIView):
    def get(self , request , SlpID ):
        try:
            time_filter = request.GET.get('time_filter')
            date_filter = None
            if time_filter == 'last_month':
                date_filter = now() - timedelta(days=30)
            elif time_filter == 'annual':
                date_filter = now() - timedelta(days=365)

            logins = UserProfile.objects.filter(slp_id=8).annotate(
                login_date=TruncDate("user__last_login"),
                login_time=TruncTime("user__last_login")
            ).values("user_id", "login_date", "login_time","user__username")
            return Response({logins}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_attendance_tracking_over_time/<int:slp_id>
#check at date_filter from flask code
class AttendanceTracking(APIView):
    def get(self,request,SlpID):
        start_date_str = request.GET.get('start_date') #'YYYY-MM-DD' format
        end_date_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            # Base query filtering by SLP ID
            appointments = ClinicAppointments.objects.filter(slp_id=8)

            # Apply date filters if provided
            if start_date and end_date:
                appointments = appointments.filter(appointment_date__date__range=[start_date, end_date])
            elif start_date:
                appointments = appointments.filter(appointment_date__date__gte=start_date)
            elif end_date:
                appointments = appointments.filter(appointment_date__date__lte=end_date)

            # Aggregate attendance data by appointment date
            attendance_data = appointments.annotate(
                appointment_day=TruncDate('appointment_date')
            ).values('appointment_day').annotate(
                PresentDays=Count(Case(When(appointment_status='Attended', then=1), output_field=IntegerField())),
                AbsentDays=Count(Case(When(appointment_status='NotAttended', then=1), output_field=IntegerField()))
            ).order_by('appointment_date').values(
                date = F('appointment_day'),
                present_days = F('PresentDays'),
                absent_days = F('AbsentDays')
            )

            if not attendance_data:
                return Response({'error': 'No attendance data found for the provided date range'}, status=status.HTTP_404_NOT_FOUND)

            return Response(attendance_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#/update_patient_status_under_slp/<int:user_id>
class UpdatePatientStatus(APIView):
    def put(self , request , UserID ):
        try:
            user = UserProfile.objects.get(user_id=UserID)
            user.patient_status = "Completed"
            user.save()
            return Response({'message': f'PatientStatus updated to Completed for UserID {UserID}'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

#/get_users_and_disorders_by_slp/<int:SlpID>
class GetUsersAndDisordersBySLP(APIView):
    def get(self , request , SlpID ):
        try:
            users = UserProfile.objects.filter(slp_id=SlpID)
            disorders = Disorders.objects.all()
            return Response({"users":users,"disorders":disorders}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/create_slps_appointment,
#/get_slp_appointments_details/<int:slp_id>
#/attend_appointment/<int:appointment_id>
#/cancel_appointment/<int:appointment_id>
#need to check at start and end time
class SlpAppoinment(APIView):
    def post(self,request):
        try:
            slp_id = request.data.get("SlpID")
            user_id = request.data.get('UserID')
            disorder_ids = request.data.get('DisorderID') 
            session_type = request.data.get('SessionType')
            appointment_date = request.data.get('AppointmentDate')
            start_time = request.data.get('StartTime')
            end_time = request.data.get('EndTime')

            # Convert strings to datetime format (YYYY-MM-DD HH:MM:SS)
            start_timestamp = datetime.strptime(f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M:%S")
            end_timestamp = datetime.strptime(f"{appointment_date} {end_time}", "%Y-%m-%d %H:%M:%S")

            SlpAppointments.objects.create(
                slp_id=slp_id,
                user_id=user_id,
                disorder_id=disorder_ids,
                session_type=session_type,
                appointment_date=appointment_date,
                start_time=start_timestamp,
                end_time=end_timestamp
            )
            return Response({'message': 'Appointment created successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

    def get(self,request,slp_id):
        try:
            slp_id = request.GET.get('SlpID')
            appointments = SlpAppointments.objects.filter(slp_id=slp_id).annotate(
                appointment_date=TruncDate("appointment_date"),
                start_time=TruncTime("start_time"),
                end_time=TruncTime("end_time")
            ).values("appointment_id","appointment_date","start_time","end_time","appointment_status")
            return Response({"appointments": list(appointments)}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

    def put(self,request,appointment_id):
        try:
            appointment_status = request.data.get('AppointmentStatus')
            if(appointment_status == "Cancelled" or appointment_status == "Attend" or appointment_status == "Pending"):
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            SlpAppointments.objects.filter(appointment_id=appointment_id).update(appointment_status=appointment_status)
            return Response({'message': 'Appointment status updated successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/reschedule_appointment/<int:appointment_id>
class RescheduleAppoinment(APIView):
    def put(self,request,appointment_id):
        try:
            appointment_date = request.data.get('AppointmentDate')
            start_time = request.data.get('StartTime')
            end_time = request.data.get('EndTime')

            # Convert strings to datetime format (YYYY-MM-DD HH:MM:SS)
            start_timestamp = datetime.strptime(f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M:%S")
            end_timestamp = datetime.strptime(f"{appointment_date} {end_time}", "%Y-%m-%d %H:%M:%S")

            SlpAppointments.objects.filter(appointment_id=appointment_id).update(
                appointment_date=appointment_date,
                start_time=start_timestamp,
                end_time=end_timestamp
            )
            return Response({'message': 'Appointment rescheduled successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_slp_tasks/<int:slp_id>
#/update_slp_task_status
class SlpTasks(APIView):
    def get(self , request , SlpID ):
        try:
            tasks = Tasks.objects.filter(slp_id=SlpID).values("task_name","task_id","description","status","slp_id","clinic_id")
            return Response(tasks, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

    def put(self,request):
        try:
            task_id = request.data.get('TaskID')
            slp_id = request.data.get('SlpID')
            status = request.data.get('Status')
            Tasks.objects.filter(task_id=task_id).update(status=status)
            return Response({'message': 'Task status updated successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_treatment_data,/get_treatment_ids,/create_treatment_data
class TreatmentData(APIView):
    def get(self , request ):
        try:
            user_id = request.data.get('UserID')
            diagnosis_name = request.data.get('DiagnosisName')
            treatment_data_id = request.data.get('TreatmentDataID')
            filters = {
                "user_id": user_id,
                "diagnosis_name": diagnosis_name
            }

            # Conditionally add treatment_data_id if it exists
            if treatment_data_id:
                filters["treatment_data_id"] = treatment_data_id
            treatment_data = TreatmentData.objects.filter(filters).values(
                "patient_name",
                "patient_age",
                "diagnosis_name",
                "therapist_name",
                "date",
                "goal",
                "interventions",
                "user_id",
                "slp_id",
                "treatment_data_id"
            )
            return Response(treatment_data, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

    def post(self,request):
        try:
            patient_name = request.data.get('PatientName')
            patient_age = request.data.get('PatientAge')
            diagnosis_name = request.data.get('DiagnosisName')
            therapist_name = request.data.get('TherapistName')
            date = request.data.get('Date')
            goal = request.data.get('Goal')
            interventions = request.data.getlist('Interventions')  
            user_id = request.data.get('UserID')  
            slp_id = request.data.get('SlpID')
            # Verify user_id
            user = get_object_or_404(CustomUser, user_id=user_id)

            # Verify slp_id
            slp = get_object_or_404(Slps, slp_id=slp_id)

            treatmentData = TreatmentData.objects.create(
                patient_name=patient_name,
                patient_age=patient_age,
                diagnosis_name=diagnosis_name,
                therapist_name=therapist_name,
                date=date,
                goal=goal,
                interventions=interventions,
                user=user,
                slp=slp
            )
            return Response({'message': 'Treatment data created successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_therapy_ids
class TherapyDataIds(APIView):
    def get(self , request ):
        try:
            therapy_ids = TherapyData.objects.values("therapy_data_id","submit_date")
            
            return Response(therapy_ids, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#/get_therapy_data   
#/add_therapy_data 
#need to check what's the use of user_id if therapy_data_id is given
class TherapyData(APIView):
    def get(self , request ):
        try:
            user_id = request.data.get('UserID')
            therapy_data_id = request.data.get('TherapyDataID')
            therapy_data = TherapyData.objects.filter(
                therapy_data_id=therapy_data_id,user_id=user_id
            ).values_list(
                "therapy_data_id",
                "patient_name",
                "submit_date",
                "slp_name",
                "resources",
                "performance",
                "condition",
                "criterion",
                "response_one",
                "response_two",
                "response_three",
                "response_four",
                "response_five",
                "objective",
                "user_id",
                "slp_id"
                )
            return Response(therapy_data, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

    def post(self,request):
        try:
            patient_name = request.data.get('PatientName')
            submit_date = request.data.get('SubmitDate')
            slp_name = request.data.get('SlpName')
            resources = request.data.get('Resources')
            performance = request.data.get('Performance')
            condition = request.data.get('Condition')
            criterion = request.data.get('Criterion')
            response_one = request.data.get('ResponseOne')
            response_two = request.data.get('ResponseTwo')
            response_three = request.data.get('ResponseThree')
            response_four = request.data.get('ResponseFour')
            response_five = request.data.get('ResponseFive')
            objective = request.data.get('Objective')
            user_id = request.data.get('UserID')  
            slp_id = request.data.get('SlpID')
            # Verify user_id
            user = get_object_or_404(CustomUser, user_id=user_id)

            # Verify slp_id
            slp = get_object_or_404(Slps, slp_id=slp_id)

            therapyData = TherapyData.objects.create(
                patient_name=patient_name,
                submit_date=submit_date,
                slp_name=slp_name,
                resources=resources,
                performance=performance,
                condition=condition,
                criterion=criterion,
                response_one=response_one,
                response_two=response_two,
                response_three=response_three,
                response_four=response_four,
                response_five=response_five,
                objective=objective,
                user=user,
                slp=slp
            )
            return Response({'message': 'Therapy data created successfully.'}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)

#//get_slp_tasks/<int:slp_id>    
class GetSLPTasks(APIView):
    def get(self,request,slp_id):
        try:
            slp_appoinment = SlpAppointments.objects.filter(
                slp_id= slp_id
            ).annotate(
                username = F("user__username")
            ).values("user_id","session_type","appointment_date","username")
            return Response({slp_appoinment},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_appointments_goals/<int:slp_id>
class SLPAppointmentsGoals(APIView):
    def get(self,request,slp_id):
        try:
            # Fetch all appointment data
            slp_appointments = SlpAppointments.objects.filter(slp_id=8).select_related('user', 'disorder').values(
                "user_id", "user__username", "disorder__disorder_name","session_type", "appointment_date"
            )

            if not slp_appointments:
                return Response({'message': 'No appointments found for the given SlpID.'}, status=status.HTTP_404_NOT_FOUND)

            # Dictionary to group by user_id
            grouped_appointments = defaultdict(lambda: {
                "disorder_names": set(),  # Use a set to avoid duplicate disorder names
                "user_id": None,
                "username": None,
                "session_type": None,
                "appointment_date": None
            })

            for appointment in slp_appointments:
                user_id = appointment["user_id"]

                # Initialize the user if not already in the dict
                if grouped_appointments[user_id]["user_id"] is None:
                    grouped_appointments[user_id]["user_id"] = user_id
                    grouped_appointments[user_id]["username"] = appointment["user__username"]
                    grouped_appointments[user_id]["session_type"] = appointment["session_type"]
                    grouped_appointments[user_id]["appointment_date"] = appointment["appointment_date"]

                # Add disorder names
                disorder_name = appointment["disorder__disorder_name"]
                if disorder_name:
                    grouped_appointments[user_id]["disorder_names"].add(disorder_name)

            # Convert sets to lists and return response
            appointment_list = [
                {
                    "user_id": data["user_id"],
                    "username": data["username"],
                    "disorder_names": list(data["disorder_names"]),
                    "session_type": data["session_type"],
                    "appointment_date": data["appointment_date"]
                }
                for data in grouped_appointments.values()
            ]


            if not slp_appointments:
                return Response({'message': 'No appointments found for the given SlpID.'}, status=status.HTTP_404_NOT_FOUND)

            return Response(list(appointment_list), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_slp_report/<int:SlpID>
#need to check time filter dought, ask shafi brother.
class SLPReport(APIView):
    def get(self,request,slp_id):
        try:
            time_filter = request.GET.get("time_filter")

            # Step 3: Set Time Filters
            today = datetime.today()
            
            if time_filter == "daily":
                start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif time_filter == "weekly":
                start_time = today - timedelta(days=today.weekday())  # Monday of the current week
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            elif time_filter == "monthly":
                start_time = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)

            start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
            end_time = timezone.make_aware(end_time, timezone.get_current_timezone())

            # Step 4: Fetch Appointments Data
            appointment_data = (
                    SlpAppointments.objects
                    .filter(
                        slp_id=slp_id,
                        appointment_status="Attended",
                        #appointment_date__range=(start_time, end_time)
                    )
                    .values("session_type")  # Grouping by session_type
                    .annotate(
                        count=Count("appointment_id",distinct=True),  # Counting appointments per session_type
                        average_age=Avg("slp__user_profiles__age") , # Average age of patients
                        patients = Count("slp__user_profiles"),
                        clinic_name = F("slp__clinic__clinic_name"),
                        state = F("slp__state"),
                        country = F("slp__country"),
                        slp_name = F("slp__slp_name"),
                        phone = F("slp__phone"),
                        email = F("slp__email")
                    )
                )
            if appointment_data.exists():
                data = appointment_data[0]  # Get the first record

                location = f"{data['clinic_name']}, {data['state']}, {data['country']}"


                disorders_assessed = sum(item["count"] for item in appointment_data if item["session_type"] == "Assessment")
                disorders_treated = sum(item["count"] for item in appointment_data if item["session_type"] == "Treatment")

                # Step 5: Prepare Response Data
                result = {
                    "SLP Name": data["slp_name"],
                    "Workstation/Location": location,
                    "Average Age of Patients": data["average_age"],
                    "Number of Patients": data["patients"],
                    "Number of Disorders Assessed": disorders_assessed,
                    "Number of Disorders Treated": disorders_treated,
                    "SLP Phone No": data["phone"],
                    "SLP Email": data["email"],
                }
                
            return Response({result},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

#/get_user_attendance/<int:slp_id>
class SLPPatinetAttendance(APIView):
    def get(self,request,slp_id):
        try:
            appoinment_list = ClinicAppointments.objects.filter(slp_id=slp_id).values("appointment_date","appointment_status").order_by("appointment_date")
            return Response({
                "slp_id":slp_id,
                "attendance_details":appoinment_list
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

def get_excerise_articulation(user_exercises,session_order):
    response_data = []

    for exercise in user_exercises:
        session_id = exercise["session_id"]
        emotion_data =  json.loads(exercise["emotion"]) if exercise["emotion"] else {}
        score = exercise["score"]
        date = exercise["exercise_date"]
        
        expressions = emotion_data.get("expressions", [])
        incorrect = emotion_data.get("incorrect", 0)
        questions_array = emotion_data.get("questions_array", [])
        
        word_texts = [question["WordText"] for question in questions_array]

        response_data.append({
            "SessionNo": session_order.get(session_id),
            "facial_expressions": expressions,
            "expressions_incorrect": incorrect,
            "Incorrect_pronunciations": word_texts,
            "Score": score,
            "Date": date
        })
    return response_data
def get_excerise_stammering(user_exercises,session_order):
    response_data = []

    for exercise in user_exercises:
        session_id = exercise["session_id"]
        emotion_data =  json.loads(exercise["emotion"]) if exercise["emotion"] else {}
        score = exercise["score"]
        date = exercise["exercise_date"]
        
        expressions = emotion_data.get("expressions", [])
        correct = emotion_data.get("correct", 0)
        incorrect = emotion_data.get("incorrect", 0)
        questions_array = emotion_data.get("questions_array", [])
        
        word_texts = [question["Sentence"] for question in questions_array]

        response_data.append({
            "Number of Session": session_order.get(session_id),  # Session order from get_report API
            "facial Expression": expressions,
            "Incorrect Facial Expression": incorrect,
            "Incorrect Questions": word_texts,
            "Stammering": score , # Include the Score in the response
            "Date":date
        })
    return response_data
def get_excerise_voice(user_exercises,session_order):
    response_data = []

    for exercise in user_exercises:
        session_id = exercise["session_id"]
        emotion_data =  json.loads(exercise["emotion"]) if exercise["emotion"] else {}
        score = exercise["score"]
        date = exercise["exercise_date"]
        
        expressions = emotion_data.get("expressions", [])
        correct = emotion_data.get("correct", 0)
        incorrect = emotion_data.get("incorrect", 0)
        questions_array = emotion_data.get("questions_array", [])
        
        questions_with_voice_disorder = [
                    {
                        "wordtext": question["wordtext"],
                        "Voice-Disorder": question.get("Voice-Disorder", "0.0%")  # Default to "0.0%" if missing
                    }
                    for question in questions_array
                ]
        response_data.append({
            "Number of Session": session_order.get(session_id),  # Session order from get_report API
            "facial Expression": expressions,
            "Incorrect Facial Expression": incorrect,
            "Questions with Voice Disorder": questions_with_voice_disorder,
            "Voice Disorder Score": score  ,# Include the Score in the response
            "Date":date
        })
    return response_data
def get_excerise_expressive(user_exercises,session_order):
    response_data = []
    for exercise in user_exercises:
        session_id = exercise["session_id"]
        emotion_data =  json.loads(exercise["emotion"]) if exercise["emotion"] else {}
        score = exercise["score"]
        date = exercise["exercise_date"]
        
        expressions = emotion_data.get("expressions", [])
        correct = emotion_data.get("correct", 0)
        incorrect = emotion_data.get("incorrect", 0)
        questions_array = emotion_data.get("questions_array", [])
        
        word_texts = []
        for question in questions_array:
            question_text = question["questiontext"]
            # Stop at the first question mark and clean the question text
            cleaned_text = re.sub(r'\?.*$', '?', question_text)  
            cleaned_text = cleaned_text.strip()  

            # Add the cleaned question only if it's not already in the list
            if cleaned_text not in word_texts:
                word_texts.append(cleaned_text)

        # Remove duplicates if any
        word_texts = list(set(word_texts))  

        # Append this row's data to the response list
        response_data.append({
            "Number of Session": session_order.get(session_id),  
            "facial Expression": expressions,
            "Incorrect Facial Expression": incorrect,
            "Incorrect Questions": word_texts,  
            "Expressive Language Disorder": score, 
            "Date":date
        })
    return response_data
def get_excerise_receptive(user_exercises,session_order):
    response_data = []

    for exercise in user_exercises:
        session_id = exercise["session_id"]
        emotion_data =  json.loads(exercise["emotion"]) if exercise["emotion"] else {}
        score = exercise["score"]
        date = exercise["exercise_date"]
        
        expressions = emotion_data.get("expressions", [])
        correct = emotion_data.get("correct", 0)
        incorrect = emotion_data.get("incorrect", 0)
        questions_array = emotion_data.get("questions_array", [])
        
        word_texts = [question["question_text"] for question in questions_array]

        response_data.append({
            "Number of Session": session_order.get(session_id),  # Session order from get_report API
            "Incorrect Questions": word_texts,
            "Receptive Language Disorder": score , # Include the Score in the response
            "Date":date
        })
    return response_data

#/get_exercise_articulation/<int:user_id>/<int:disorder_id>
#/get_exercise_receptive/<int:user_id>/<int:disorder_id>
#/get_exercise_stammering/<int:user_id>/<int:disorder_id>
#/get_exercise_voice/<int:user_id>/<int:disorder_id>
#/get_exercise_expressive/<int:user_id>/<int:disorder_id>
class GetExcerise(APIView):
    def get(self,request,user_id,disorder_id):
        try:
            # Step 1: Fetch Sessions for the user
            sessions = (
                Sessions.objects
                .filter(user_id=user_id, session_status__in=['Completed', 'quick_assessment_status'])
                .order_by("session_id")
                .values("session_id","session_status","session_type")
            )
            # Step 2: Create a session order mapping
            session_order = {session["session_id"]: index + 1 for index, session in enumerate(sessions)}

            print(session_order)
            # Step 3: Fetch UserExercises related to the given disorder_id
            user_exercises = (
                UserExercises.objects
                .filter(user_id=user_id, disorder_id=disorder_id)
                .select_related("session")
                .values("session_id", "emotion", "score", "exercise_date")  # Selecting required fields
            )
            if(len(user_exercises) == 0):
                return Response({"message": "No data found for the given UserID and DisorderID"},status=status.HTTP_204_NO_CONTENT)
            #print(user_exercises)
            
            
            if(disorder_id == 1):
                response_data = get_excerise_articulation(user_exercises,session_order)
            elif(disorder_id == 2):
                response_data = get_excerise_stammering(user_exercises,session_order)
            elif(disorder_id == 3):
                response_data = get_excerise_voice(user_exercises,session_order)
            elif(disorder_id == 4):
                response_data = get_excerise_expressive(user_exercises,session_order)
            elif(disorder_id == 5):
                response_data = get_excerise_receptive(user_exercises,session_order)
            else:
                return Response({"message": "No Disorder found for the id"},status=status.HTTP_204_NO_CONTENT)

            return Response({response_data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)