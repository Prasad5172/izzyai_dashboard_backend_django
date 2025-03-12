from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
import time
from authentication.models import UserProfile , CustomUser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from datetime import timedelta
from django.utils.timezone import now
from authentication.models import CustomUser ,UserProfile
from clinic.models import Clinics, PatientFiles ,Sessions, AssessmentResults
from payment.models import Payment
from django.core.exceptions import ObjectDoesNotExist
import json 



class PatientDetails(APIView):
    def get(self , request  , UserID):
        """
        Retrieves the profile information of a specific user.

        This endpoint fetches the user's type, email, username from the "Users" table and 
        fetches additional profile details (age, gender, contact number) from the "UserProfile" table.

        Args:
            UserID (int): The ID of the user whose profile is being retrieved.

        Returns:
            JSON response with:
                - 'Email': The email address of the user.
                - 'UserName': The username of the user.
                - 'Age': The age of the user.
                - 'Gender': The gender of the user.
                - 'ContactNumber': The contact number of the user.
            - 404: If the user or user profile is not found.
            - 400: If the user is not a 'Patient' type.
            - 500: If an error occurs while processing the request.

        """
        try:
            user = CustomUser.objects.get(user_id = UserID)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.user_type != "Patient":
            return Response({"error": "User is not a Patient"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Email": user.email, "UserName": user.username, "Age": profile.age, "Gender": profile.gender, "ContactNumber": profile.contact_number ,  "profilephoto": profile.profilephoto}, status=status.HTTP_200_OK)
    


    def put(self , request , UserID):
        """
        Updates the profile information of a specific user.

        This endpoint allows updating the user's email, username in the "Users" table, 
        and the user's age, gender, contact number in the "UserProfile" table. If the profile does not exist,
        a new profile is created.

        Args:
            UserID (int): The ID of the user whose profile is being updated.

        Form Parameters (optional):
            - 'Email' (str): The new email address of the user.
            - 'UserName' (str): The new username of the user.
            - 'Age' (int): The new age of the user.
            - 'Gender' (str): The new gender of the user.
            - 'ContactNumber' (str): The new contact number of the user.

        Returns:
            JSON response with:
                - 'message': Success message if the profile is updated successfully.
            - 500: If an error occurs while processing the request.
        """
        try:
            user = CustomUser.objects.get(user_id = UserID)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.user_type != "Patient":
            return Response({"error": "User is not a Patient"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        data = request.data
        user.email = data.get('Email') 
        user.username = data.get('UserName')
        profile.age = data.get('Age')
        profile.gender = data.get('Gender')
        profile.contact_number = data.get('ContactNumber')
        profile.save()
        user.save()
        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)

class PatientsUpload(APIView):
    def post(self , request):
        """
        This endpoint handles the uploading of patient documents. It validates the input, saves the uploaded file to the server, and stores file details in the database.

        Args:
            None (but accepts data via the `request.files` and `request.form`):
                - file (File): The document file to be uploaded.
                - UserID (str): The ID of the user to associate the document with.
                - Role (str): The role of the user (e.g., patient, doctor).
                - DocumentType (str): The type of the document (e.g., diagnosis report).
                - DiagnosisName (str, optional): The name of the diagnosis, if applicable.

        Returns:
            Response: 
                - Success: A JSON response with a success message, the details of the uploaded document (UserID, Role, DocumentType, DiagnosisName, FileName, and FilePath).
                - Failure: A JSON response with an error message and appropriate HTTP status code (e.g., 400 or 500).

        Raises:
            Exception: In case of any file processing errors, database errors, or unexpected exceptions.
        """
        try:
            user = CustomUser.objects.get(user_id = request.data.get('UserID'))
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.user_type != "Patient":
            return Response({"error": "User is not a Patient"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        file = request.FILES['file']
        file_name = file.name
        document_type = request.data.get('DocumentType')
        diagnosis_name = request.data.get('DiagnosisName')
        role = request.data.get('Role')
        file_path = request.data.get('FilePath')
        try:
            patient_file = PatientFiles.objects.create(
                file_name=file_name,
                document_type = document_type,
                diagnosis_name = diagnosis_name,
                role=role,
                file_path=file_path,
                user_id=user,
                upload_timestamp=now(),
            )
            patient_file.file.save(file_name, file)
            return Response({"message": "File uploaded successfully", "details": {
                "UserID": user.user_id,
                "Role": role,
                "DocumentType": document_type,
                "DiagnosisName": diagnosis_name,
                "FileName": file_name,
                "FilePath": file_path,
            }}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PatientAssessment(APIView):
    def get(self , request , user_id, disorder_id):
        try:
        # Fetch sessions for the user that are either 'Completed' or 'quick_assessment_status'
            sessions = Sessions.objects.filter(
                    user_id=user_id,
                    session_status__in=['Completed', 'quick_assessment_status']
                ).order_by('session_id')
                
            session_order = {session.session_id: index + 1 for index, session in enumerate(sessions)}
                
                # Fetch assessment results based on session IDs and disorder ID
            results = AssessmentResults.objects.filter(
                    user_id=user_id, 
                    disorder_id=disorder_id
                ).select_related('session_id')
        
            if results.exists():
                    response_data = []
                    for result in results:
                        emotion_data = result.emotion
                
                        if emotion_data:
                            if isinstance(emotion_data, str):
                                emotion_data = json.loads(emotion_data)
                    
                        expressions = emotion_data.get("expressions", [])
                        incorrect = emotion_data.get("incorrect", 0)
                        questions_array = emotion_data.get("questions_array", [])
                        word_texts = [question["WordText"] for question in questions_array]
                    
                        response_data.append({
                        "SessionNo": session_order.get(result.session_id.session_id),
                        "facial_expressions": expressions,
                        "expressions_incorrect": incorrect,
                        "Incorrect_pronunciations": word_texts,
                        "Score": result.score,
                        "Date": result.assessment_date
                             })
            
                    return JsonResponse(response_data, safe=False)
            else:
                return JsonResponse({"message": "No data found for the given UserID and DisorderID"}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

