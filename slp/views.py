from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from authentication.models import CustomUser
import time
from slp.models import Slps,SlpAppointments
from authentication.models import UserProfile , CustomUser
from rest_framework.permissions import IsAuthenticated
from clinic.models import Clinics , ClinicAppointments , Tasks , TherapyData

class SlpApiView(APIView):
    permission_classes = [IsAuthenticated]

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
            slp = get_object_or_404(Slps, slp_id=SlpID)
            response = {
                "SlpID": slp.slp_id,
                "SlpName": slp.slp_name,
                "Phone": slp.phone,
                "Email": slp.email,
                "Country": slp.country,
                "State": slp.state,
                "ClinicName": slp.clinic_name,
                "UsersAssigned": slp.users_assigned,
            }
            user_profile = UserProfile.objects.get(user_id=slp.user_id)
            response["ProfilePicture"] = user_profile.profilephoto
            return Response(response, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "SLP not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, SlpID):
        """
        Updates the details of a Speech-Language Pathologist (SLP) identified by SlpID.

        This endpoint allows an SLP's details to be updated, including their name, email, phone number, country, state, and profile picture.

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP) whose details need to be updated.

        Request Form Data:
        - SlpName (str): The name of the SLP.
        - Email (str): The email address of the SLP.
        - Phone (str): The phone number of the SLP.
        - Country (str): The country where the SLP is located.
        - State (str): The state where the SLP is located.
        - profile_picture (file, optional): The new profile picture of the SLP (if provided).

        Returns:
        JSON:
            - 200 OK: If the SLP details are successfully updated.
            Example:
            {
                "message": "SLP details updated successfully"
            }
            - 400 Bad Request: If any required fields (SlpName, Email, Phone, Country, State) are missing or invalid.
            Example:
            {
                "error": "Missing field: SlpName"
            }
            - 404 Not Found: If the given SlpID does not exist in the database.
            Example:
            {
                "error": "SLP not found"
            }
            - 500 Internal Server Error: If there is a database issue or any other error occurs.
            Example:
            {
                "error": "Error occurred: Error message"
            }

        """
        try:
            slp = Slps.objects.get(slp_id=SlpID)
            slp.slp_name = request.data.get("SlpName", slp.slp_name)
            slp.email = request.data.get("Email", slp.email)
            slp.phone = request.data.get("Phone", slp.phone)
            slp.country = request.data.get("Country", slp.country)
            slp.state = request.data.get("State", slp.state)
            profphoto = request.data.get("profile_picture")
            if profphoto:
                user_profile = UserProfile.objects.get(user_id=slp.user_id)
                user_profile.profilephoto = request.data.get("profile_picture", user_profile.profilephoto)
                user_profile.save()
            slp.save()

            return Response({"message": "SLP details updated successfully"}, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"error": "SLP not found"}, status=status.HTTP_404_NOT_FOUND)

class SlpUsersLog(APIView):
    def get(self , request , SlpID  , time_filter ):
        """
        Get the login logs of users assigned to a specific Speech-Language Pathologist (SLP).

        This endpoint retrieves the login logs of users assigned to a particular SLP, based on a given time filter (e.g., last month, annual). It shows the last login details of users including their UserID, UserName, date, and time of login.

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP).
        - time_filter (str, optional): The time filter for the login logs. Accepts values:
        - 'last_month': Filters logs for the previous month.
        - 'annual': Filters logs for the current year.
        - 'None': Fetches all available login data without any time filtering.

        Returns:
        JSON:
            - A list of objects with the following fields for each user:
                - UserID (int): The unique identifier of the user.
                - UserName (str): The name of the user.
                - Date (str): The date of the last login, formatted as 'YYYY-MM-DD'.
                - OnTime (str): The time of the last login, formatted as 'HH:MM:SS'. If no login is available, both Date and OnTime will show 'N/A'.

        Error Responses:
            - 500 Internal Server Error: If there is an issue with the database connection or query execution.
            Example: {"error": "Error occurred: <error message>"}
            - 404 Not Found: If no users are found for the given SLP ID.
            Example: {"message": "No users found for the given SlpID"}
        """
        try:
            slp = Slps.objects.get(slp_id=SlpID)
            if time_filter == 'last_month':
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            elif time_filter == 'annual':
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            else:
                start_date = None
                end_date = None
            users = CustomUser.objects.filter(userprofile__slp_id=slp.slp_id)
            response = []
            for user in users:
                last_login = user.last_login
                if last_login:
                    date = last_login.strftime('%Y-%m-%d')
                    time = last_login.strftime('%H:%M:%S')
                else:
                    date = 'N/A'
                    time = 'N/A'
                response.append({
                    'UserID': user.user_id,
                    'UserName': user.username,
                    'Date': date,
                    'OnTime': time
                })
            return Response(response, status=status.HTTP_200_OK)
        except Slps.DoesNotExist:
            return Response({"message": "No users found for the given SlpID"}, status=status.HTTP_404_NOT_FOUND)



class SlpPatients(APIView):
    def get(self , request , UserID ):
        """
        Retrieves detailed information for a specific patient by their UserID.

        This endpoint fetches a patient's basic information such as their UserType, Email, UserName, and profile details (Date of Birth, Gender, Country, Status) based on the provided UserID. The user is required to have a UserType of 'Patient' to proceed.

        Steps performed by this endpoint:
        - Accepts a UserID as a parameter to query data specific to that user.
        - Retrieves the user's basic details (UserType, Email, UserName) from the 'Users' table.
        - Verifies that the user is of type 'Patient'.
        - Retrieves additional profile details such as Date of Birth (DOB), Gender, Country, and Status from the 'UserProfile' table.
        - Returns the combined user details as a JSON response.

        URL Parameters:
        - UserID (int): The ID of the patient whose details are being retrieved.

        Response:
        - 200 OK: Returns a JSON object containing the patient's details if found.
        Example:
        {
            "UserID": 123,
            "Email": "patient@example.com",
            "UserName": "John Doe",
            "Dob": "1990-05-15",
            "Gender": "Male",
            "Country": "USA",
            "Status": "Active"
        }
        - 400 Bad Request: If the user is not a 'Patient'.
        - 404 Not Found: If no user or user profile is found for the given UserID.
        - 500 Internal Server Error: Returns an error message in case of database or internal issues.

        Error Responses:
        - 500: Database connection error or other internal errors.

        """
        try:
            user = CustomUser.objects.get(user_id=UserID)
            user_profile = UserProfile.objects.get(user_id=UserID)
            return Response({
                "UserID": user.user_id,
                "Email": user.email,
                "UserName": user.username,
                "Dob": user_profile.dob,
                "Gender": user_profile.gender,
                "Country": user_profile.country,
                "Status": user_profile.status
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self , request , UserID ):
        """
        Updates the details of a patient.

        This endpoint allows the updating of a patient's information, including Email, UserName, Date of Birth (Dob), Gender, and Country. It ensures that the user exists, is a 'Patient', and that the new email is unique before updating the database.

        Steps performed by this endpoint:
        - Accepts a JSON payload containing the patient's updated details.
        - Ensures that all required fields (Email, UserName, Dob, Gender, and Country) are provided in the request.
        - Verifies the user exists and is a 'Patient'.
        - Ensures that if the email is changed, it does not conflict with other users' emails.
        - Updates the patient’s data in both the "Users" and "UserProfile" tables.
        - Returns a success message with the updated user details.

        URL Parameters:
        - UserID (int): The ID of the user whose details are being updated.

        Request Body (JSON):
        - Email (str): The new email address of the user.
        - UserName (str): The new username of the user.
        - Dob (str): The new date of birth of the user (in format YYYY-MM-DD).
        - Gender (str): The new gender of the user.
        - Country (str): The new country of the user.

        Response:
        - 200 OK: Returns a success message and the updated user details if the update is successful.
        - 500 Internal Server Error: Returns an error in case of a server or database issue.
        Error Responses:
        - 400: Missing fields, invalid user type, or email conflict.
        - 404: User not found.
        - 500: Database or internal errors.
        """
        try:
            user = CustomUser.objects.get(user_id=UserID)
            user_profile = UserProfile.objects.get(user_id=UserID)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data
        if not all(key in data for key in ['Email', 'UserName', 'Dob', 'Gender', 'Country']):
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
        if user.user_type != 'Patient':
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.exclude(user_id=UserID).filter(email=data['Email']).exists():
            return Response({"error": "Email conflict"}, status=status.HTTP_400_BAD_REQUEST)
        user.email = data['Email']
        user.username = data['UserName']
        user.save()
        user_profile.dob = data['Dob']
        user_profile.gender = data['Gender']
        user_profile.country = data['Country']
        user_profile.save()
        return Response({"message": "User updated successfully", "user": {
            "UserID": user.user_id,
            "Email": user.email,
            "UserName": user.username,
            "Dob": user_profile.dob,
            "Gender": user_profile.gender,
            "Country": user_profile.country,
            "Status": user_profile.status
        }}, status=status.HTTP_200_OK)
    
    
class SlpAppointments(APIView):
    premission_classes = [IsAuthenticated]
    def post(self , request):
        """
        Create a new SLP appointment for a patient.

        This endpoint allows for the creation of appointments for patients under a specific Speech-Language Pathologist (SLP). It takes in the SLP ID, User ID, Disorder IDs, session type, appointment date, and session start and end times to create one or more appointments in the `SlpAppointments` table.

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP).
        - UserID (int): The unique identifier of the user (patient).
        - DisorderID (list of int): A list of disorder IDs assigned to the user for the appointment.
        - SessionType (str): The type of session (e.g., "Therapy", "Assessment").
        - AppointmentDate (str): The date of the appointment in 'YYYY-MM-DD' format.
        - StartTime (str): The start time of the appointment in 'HH:MM:SS' format.
        - EndTime (str): The end time of the appointment in 'HH:MM:SS' format.

        Returns:
        JSON:
            - A success message if the appointment is created successfully.
            Example: {"message": "Appointment created successfully."}
            - 400 Bad Request: If any required field is missing.
            Example: {"error": "All fields are required."}
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
        """
        data = request.data
        if not all(key in data for key in ['SlpID', 'UserID', 'DisorderID', 'SessionType', 'AppointmentDate', 'StartTime', 'EndTime']):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            appointment = SlpAppointments.objects.create(
                slp_id=data['SlpID'],
                user_id=data['UserID'],
                disorder_id=data['DisorderID'],
                session_type=data['SessionType'],
                appointment_date=data['AppointmentDate'],
                appointment_start=data['StartTime'],
                appointment_end=data['EndTime'] ,
                appointment_status="pending"
            )
            return Response({"message": "Appointment created successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self , request , SlpID ):
        """
        Get all appointments for a specific Speech-Language Pathologist (SLP).

        This endpoint retrieves all the appointments scheduled for a particular SLP based on their unique ID. The data returned includes the appointment ID, appointment date, start and end times, and the appointment status.

        Args:
        - slp_id (int): The unique identifier of the Speech-Language Pathologist (SLP).

        Returns:
        JSON:
            - A list of appointment details for the specified SLP, each including:
                - AppointmentID (int): Unique ID for the appointment.
                - AppointmentDate (str): The date of the appointment in 'YYYY-MM-DD' format.
                - StartTime (str): The start time of the appointment in 'HH:MM:SS' format.
                - EndTime (str): The end time of the appointment in 'HH:MM:SS' format.
                - AppointmentStatus (str): The current status of the appointment (e.g., "Pending", "Completed").
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
        """
        try:
            appointments = SlpAppointments.objects.filter(slp_id=SlpID)
            data = []
            for appointment in appointments:
                data.append({
                    "AppointmentID": appointment.appointment_id,
                    "AppointmentDate": appointment.appointment_date,
                    "StartTime": appointment.appointment_start ,
                    "EndTime": appointment.appointment_end,
                    "AppointmentStatus": appointment.appointment_status
                })
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self , request , AppointmentID ):
        """
        Update the status of an appointment to 'Attended and Canceled'.

        This endpoint is used by a Speech-Language Pathologist (SLP) to mark an appointment as attended. When the appointment is attended, the status is updated to 'Attended'.

        Args:
        - appointment_id (int): The unique identifier of the appointment to be updated.
        -status : The status of the appointment to be updated.

        Returns:
        JSON:
            - 200 OK: If the appointment status is successfully updated to 'Attended'.
            Example: {"message": "Appointment status updated to Attended."}
            - 404 Not Found: If the provided AppointmentID does not exist.
            Example: {"message": "AppointmentID not found."}
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
        """
        try:
            status = request.data.get('status')
            appointment = SlpAppointments.objects.get(appointment_id=AppointmentID)
            if(status == "Attended"):
                    appointment.appointment_status = "Attended"
                    appointment.save()
            
            if(status == "Canceled" ):
                appointment.appointment_status = "Canceled"
                appointment.save()

            return Response({"message": "Appointment status updated to Attended."}, status=status.HTTP_200_OK)
        except SlpAppointments.DoesNotExist:
            return Response({"message": "AppointmentID not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SlpReschedule(APIView):
    premission_classes = [IsAuthenticated]
    def put(self , request , AppointmentID ):
        """
        Reschedule an appointment by updating its status and details.

        This endpoint allows an SLP to reschedule an existing appointment. The status is updated to 'Rescheduled' and the appointment date, start time, and end time are modified.

        Args:
        - appointment_id (int): The unique identifier of the appointment to be rescheduled.

        Request Form Parameters:
        - RescheduleDate (str): The new date for the rescheduled appointment (in 'YYYY-MM-DD' format).
        - AppointmentStart (str): The new start time for the rescheduled appointment (in 'HH:MM:SS' format).
        - AppointmentEnd (str): The new end time for the rescheduled appointment (in 'HH:MM:SS' format).

        Returns:
        JSON:
            - 200 OK: If the appointment is successfully rescheduled and status is updated to 'Rescheduled'.
            Example: {"message": "Appointment status updated to Rescheduled. New date: 2025-02-10."}
            - 400 Bad Request: If any required fields (RescheduleDate, AppointmentStart, AppointmentEnd) are missing.
            Example: {"error": "RescheduleDate is required for rescheduling."}
            - 404 Not Found: If the provided AppointmentID does not exist.
            Example: {"message": "AppointmentID not found."}
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
      """
        data = request.data
        if not all(key in data for key in ['RescheduleDate', 'AppointmentStart', 'AppointmentEnd']):
            return Response({"error": "RescheduleDate is required for rescheduling."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            appointment = SlpAppointments.objects.get(appointment_id=AppointmentID)
            appointment.appointment_status = "pending"
            appointment.appointment_date = data['RescheduleDate']
            appointment.appointment_start = data['AppointmentStart']
            appointment.appointment_start = data['AppointmentEnd']
            appointment.save()
            return Response({"message": "Appointment status updated to Rescheduled. New date: " + data['RescheduleDate']}, status=status.HTTP_200_OK)
        except SlpAppointments.DoesNotExist:
            return Response({"message": "AppointmentID not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SlpTasks(APIView):
    premission_classes = [IsAuthenticated]
    def get(self , request , SlpID ):
        """
        Fetches tasks associated with a specific SlpID.

        This endpoint retrieves a list of tasks assigned to a given SLP (Speech-Language Pathologist) by their SlpID.

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP) whose tasks are to be fetched.

        Returns:
        JSON:
            - 200 OK: The tasks associated with the given SlpID.
            Example: 
            {
                "SlpID": 12345, 
                "Tasks": [
                    {
                        "TaskID": 1,
                        "TaskName": "Speech Therapy Session",
                        "Description": "Conduct therapy for speech improvement.",
                        "Status": "In Progress",
                        "SlpID": 12345,
                        "ClinicID": 6789
                    },
                    {
                        "TaskID": 2,
                        "TaskName": "Patient Follow-up",
                        "Description": "Follow-up with patients after therapy.",
                        "Status": "Completed",
                        "SlpID": 12345,
                        "ClinicID": 6789
                    }
                ]
            }
            - 400 Bad Request: If SlpID is missing or invalid.
            Example: {"error": "SlpID is a required parameter."}
            - 404 Not Found: If no tasks are found for the given SlpID.
            Example: {"message": "No tasks found for the given SlpID."}
            - 500 Internal Server Error: If there is a database issue or any other error occurs.
            Example: {"error": "Error occurred: Error message"}
        """
        try:
            tasks = Tasks.objects.filter(slp_id=SlpID)
            data = []
            for task in tasks:
                data.append({
                    "TaskID": task.task_id,
                    "TaskName": task.task_name,
                    "Description": task.description,
                    "Status": task.status,
                    "SlpID": task.slp_id,
                    "ClinicID": task.clinic_id
                })
            return Response({"SlpID": SlpID, "Tasks": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self , request ):
        """
        Updates the status of a specific task assigned to an SLP.

        This endpoint updates the status of a task associated with a given SLP (Speech-Language Pathologist) by TaskID and SlpID.

        Args:
        - SlpID (int): The unique identifier of the Speech-Language Pathologist (SLP) whose task is to be updated.
        - TaskID (int): The unique identifier of the task to update.
        - Status (str): The new status for the task (e.g., "In Progress", "Completed", etc.).

        Returns:
        JSON:
            - 200 OK: If the task status is successfully updated.
            Example: 
            {
                "message": "Task status updated successfully."
            }
            - 400 Bad Request: If SlpID, TaskID, or Status is missing or invalid.
            Example: 
            {
                "error": "SlpID, TaskID, and Status are required."
            }
            - 404 Not Found: If no task is found with the given SlpID and TaskID.
            Example: 
            {
                "message": "No task found with the given SlpID and TaskID."
            }
            - 500 Internal Server Error: If there is a database issue or any other error occurs.
            Example: 
            {
                "error": "Error occurred: Error message"
            }
        """
        try:
            SlpID = request.data.get('SlpID')
            TaskID = request.data.get('TaskID')
            Status = request.data.get('Status')
            if not SlpID or not TaskID or not Status:
                return Response({"error": "SlpID, TaskID, and Status are required."}, status=status.HTTP_400_BAD_REQUEST)
            
            task = Tasks.objects.get(task_id=TaskID , slp_id=SlpID)
            task.status = Status
            task.save()
            return Response({"message": "Task status updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SlpAppointmentsGoal(APIView):
    def get(self , request , slp_id ):
        """
        Get a list of appointments, disorders, and goals (objectives) for an SLP based on their SlpID.

        This endpoint retrieves appointments for a specific Speech-Language Pathologist (SLP), including the associated disorder(s), user name, session type, and the appointment date. The goal is to return the details that align with the specific SLP's appointments and disorders they are treating.

        Args:
        - slp_id (int): The unique identifier of the SLP whose appointments and goals are being retrieved.

        Returns:
        JSON:
            - 200 OK: A list of appointments with the appointment date, disorder names, user name, session type, and user ID for each appointment.
            Example:
            [
                {
                    "AppointmentDate": "2025-02-12",
                    "DisorderNames": ["Speech Disorder", "Stammering"],
                    "UserName": "Jane Smith",
                    "SessionType": "Therapy",
                    "UserID": 101
                },
                {
                    "AppointmentDate": "2025-02-15",
                    "DisorderNames": ["Voice Disorder"],
                    "UserName": "John Doe",
                    "SessionType": "Consultation",
                    "UserID": 102
                }
            ]
            - 404 Not Found: If no appointments are found for the provided SlpID.
            Example: {"message": "No appointments found for the given SlpID."}
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
        """
        try:
            appointments = SlpAppointments.objects.filter(slp_id=slp_id)
            data = []
            for appointment in appointments:
                 # Get the DisorderNames based on the DisorderIDs
                disorder_names = [disorder.disorder_name for disorder in appointment.disorder_id.all()]
                # Get the username  based on the user id 
                username = UserProfile.objects.get(user_id=appointment.user_id).full_name
                goal =TreatmentData.objects.get(user_id=appointment.user_id).goal

                data.append({
                    "AppointmentDate": appointment.appointment_date,
                    "DisorderNames": disorder_names,
                    "UserName": username , 
                    "SessionType": appointment.session_type,
                    "UserID": appointment.user_id ,
                    "goal": goal,
                    "StartTime": appointment.start_time,
                    "EndTime": appointment.end_time
                })
            if not data:
                return Response({"message": "No appointments found for the given SlpID."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SlpTherapy(APIView):
#     premission_classes = [IsAuthenticated]
#     def post(self , request):
#         """
#         Adds therapy data for a specific user and session.

#         This endpoint allows a therapist (SLP) to submit therapy data for a specific patient. The data includes objective, patient information, therapy resources, performance, condition, responses, and more.

#         Args:
#         - None (request body required)

#         Request Body:
#             - UserID (int): The unique identifier of the user (patient).
#             - SlpID (int): The unique identifier of the therapist (SLP).
#             - Objective (str): The objective of the therapy session.
#             - PatientName (str): The full name of the patient.
#             - SubmitDate (str): The date the therapy data was submitted (in DD-MM-YYYY format).
#             - SlpName (str): The full name of the therapist (SLP).
#             - Resources (str): Resources used during the therapy session.
#             - Performance (str): The performance assessment of the patient.
#             - Condition (str): The patient's condition during the session.
#             - Criterion (str): The criterion for the therapy session.
#             - ResponseOne (str): Response to the first question.
#             - ResponseTwo (str): Response to the second question.
#             - ResponseThree (str): Response to the third question.
#             - ResponseFour (str): Response to the fourth question.
#             - ResponseFive (str): Response to the fifth question.

#         Returns:
#         JSON:
#             - 201 Created: Success message indicating the therapy data was added.
#             Example: {"message": "Therapy data added successfully!"}
#             - 400 Bad Request: If required fields are missing or date format is invalid.
#             Example: {"error": "Invalid date format. Please use DD-MM-YYYY."}
#             - 500 Internal Server Error: If there is a database issue or any other error occurs.
#             Example: {"error": "Error occurred: Error message"}
#         """
#         try:
#             UserID = request.data.get('UserID')
#             SlpID = request.data.get('SlpID')
#             Objective = request.data.get('Objective')
#             PatientName = request.data.get('PatientName')
#             SubmitDate = request.data.get('SubmitDate')
#             SlpName = request.data.get('SlpName')
#             Resources = request.data.get('Resources')
#             Performance = request.data.get('Performance')
#             Condition = request.data.get('Condition')
#             Criterion = request.data.get('Criterion')
#             ResponseOne = request.data.get('ResponseOne')
#             ResponseTwo = request.data.get('ResponseTwo')
#             ResponseThree = request.data.get('ResponseThree')
#             ResponseFour = request.data.get('ResponseFour')
#             ResponseFive = request.data.get('ResponseFive')

class SlpReport(APIView):
    def get(self , request , slp_id  , time_filter = "daily" ):
        """
        Generate a report for an SLP, including patient statistics, assessment/treatment count, and clinic details.

        This endpoint generates a report for a specific Speech-Language Pathologist (SLP) based on their unique SlpID, which includes details such as clinic name, patient statistics, average age, and the number of disorders assessed and treated. The report also allows filtering by daily, weekly, or monthly time periods for the appointments' date ranges.

        Args:
        - SlpID (int): The unique identifier of the SLP for whom the report is being generated.
        - time_filter (optional str): The time range for the report, can be one of 'daily', 'weekly', or 'monthly'. Defaults to 'daily'.

        Returns:
        JSON:
            - 200 OK: A detailed report for the SLP with the clinic location, patient stats, and appointment counts.
            Example:
            {
                "SLP Name": "John Doe",
                "Workstation/Location": "Doe Clinic, California, USA",
                "Average Age of Patients": 30.5,
                "Number of Patients": 15,
                "Number of Disorders Assessed": 10,
                "Number of Disorders Treated": 5,
                "SLP Phone No": "+1234567890",
                "SLP Email": "johndoe@example.com"
            }
            - 404 Not Found: If the provided SlpID does not exist.
            Example: {"message": "SLP not found."}
            - 400 Bad Request: If an invalid time filter is provided.
            Example: {"error": "Invalid time filter."}
            - 500 Internal Server Error: If there is an issue with the database query or connection.
            Example: {"error": "Error message"}
        """
        try:
            # Step 1: Get SLP and Clinic Details
            slp = Slps.objects.select_related('clinic_id').filter(slp_id=slp_id).first()
            
            if not slp:
                return Response({'message': 'SLP not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            location = f"{slp.clinic_id.clinic_name}, {slp.state}, {slp.country}"
            
            # Step 2: Get User Profiles under this SLP
            users = UserProfile.objects.filter(slp_id=slp)
            number_of_patients = users.count()
            
            valid_ages = users.exclude(age__isnull=True).values_list('age', flat=True)
            average_age = sum(valid_ages) / len(valid_ages) if valid_ages else 0
            
            # Step 3: Define Time Range based on the filter
            today = datetime.today()
            
            if time_filter == 'daily':
                start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif time_filter == 'weekly':
                start_time = today - timedelta(days=today.weekday())
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            elif time_filter == 'monthly':
                start_time = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                return Response({'error': 'Invalid time filter.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 4: Get Completed Appointments within Time Range
            appointments = SlpAppointments.objects.filter(
                slp_id=slp,
                appointment_status='Completed',
                appointment_date__range=(start_time, end_time)
            )
            
            disorders_assessed = appointments.filter(session_type='Assessment').count()
            disorders_treated = appointments.filter(session_type='Treatment').count()
            
            result = {
                "SLP Name": slp.slp_name,
                "Workstation/Location": location,
                "Average Age of Patients": round(average_age, 2),
                "Number of Patients": number_of_patients,
                "Number of Disorders Assessed": disorders_assessed,
                "Number of Disorders Treated": disorders_treated,
                "SLP Phone No": slp.phone,
                "SLP Email": slp.email
            }
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

