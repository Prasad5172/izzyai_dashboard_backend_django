import random
import string

from django.shortcuts import get_object_or_404
from payment.models import Payment
from clinic.models import Clinics

from django.utils.timezone import now, timedelta,datetime
from django.utils import timezone
from datetime import date
from authentication.models import CustomUser,UserProfile
from django.db.models import Sum, F,Value,CharField,Count,Func,Q,FloatField,OuterRef,Subquery,Case,When,ExpressionWrapper,IntegerField,Avg,fields,Max,DateTimeField,Prefetch
from django.utils.dateformat import DateFormat
from django.db.models.functions import TruncDate,TruncTime,Cast,Round,Coalesce,ExtractYear,TruncMonth,TruncYear
from utils.MonthsShortHand import MONTH_ABBREVIATIONS
from sales_person.models import SalePersons
from clinic.models import DemoRequested,Tasks
from rest_framework import status
from rest_framework.response import Response
from slp.models import Slps,SlpAppointments
from clinic.models import TreatmentData,TherapyData,ClinicAppointments,Sessions,Disorders,ClinicUserReminders
from collections import defaultdict
from authentication.models import UserExercises,UsersInsurance
from payment.models import Subscriptions,Invoice,Payment
import json
import re
import time
from itertools import chain
from faker import Faker
from sales_director.models import Sales,SalesDirector
from clinic.models import AssessmentResults
from authentication.models import UserFiles
import os
import boto3
import mimetypes
import environ
env = environ.Env()
environ.Env.read_env()

def printlist(list):
    for i in list:
        print(i)

def get_date_filter(time_filter):
    date_filter =None
    if time_filter == 'last_month':
        date_filter = now() - timedelta(days=30)
    elif time_filter == 'annual':
        date_filter = now() - timedelta(days=365)
    return date_filter

def get_assessment_articulation(user_assessments,session_order):
    response_data = []

    for assessment in user_assessments:
        session_id = assessment["session_id"]
        emotion_data =  json.loads(assessment["emotion"]) if assessment["emotion"] else {}
        score = assessment["score"]
        date = assessment["assessment_date"]

        if emotion_data is not None:
            if isinstance(emotion_data, str):
                emotion_data = json.loads(emotion_data) 
        
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
def get_assessment_stammering(user_assessments,session_order):
    response_data = []

    for assessment in user_assessments:
        session_id = assessment["session_id"]
        emotion_data =  json.loads(assessment["emotion"]) if assessment["emotion"] else {None}
        score = assessment["score"]
        date = assessment["assessment_date"]

        # Ensure emotion_data is either None or an empty dictionary
        emotion_data = json.loads(assessment["emotion"]) if assessment["emotion"] else {}

        if emotion_data:  # Ensure emotion_data is not None or empty before processing
            if isinstance(emotion_data, str):
                emotion_data = json.loads(emotion_data)

            expressions = emotion_data.get("expressions", [])
            incorrect = emotion_data.get("incorrect", 0)
            correct = emotion_data.get("correct", 0)
            questions_array = emotion_data.get("questions_array", [])

            #word_texts = [question["question_text"] for question in questions_array]
            response_data.append({
                "Number of Session": session_order.get(session_id),
                "facial Expression": expressions,
                "Incorrect Facial Expression": incorrect,
                "Stammering": score,
                "Date": date
            })
        else:
            # If emotion_data is empty, append default values
            response_data.append({
                "Number of Session": session_order.get(session_id),
                "facial Expression": [],
                "Incorrect Facial Expression": 0,
                "Stammering": score,
                "Date": date
            })

    return response_data
def get_assessment_voice(user_assessments,session_order):
    response_data = []

    for assessment in user_assessments:
        session_id = assessment["session_id"]
        emotion_data =  json.loads(assessment["emotion"]) if assessment["emotion"] else {}
        score = assessment["score"]
        date = assessment["assessment_date"]
        
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
def get_assessment_expressive(user_assessments,session_order):
    response_data = []
    for assessment in user_assessments:
        session_id = assessment["session_id"]
        emotion_data =  json.loads(assessment["emotion"]) if assessment["emotion"] else {}
        score = assessment["score"]
        date = assessment["assessment_date"]
        
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
def get_assessment_receptive(user_assessments,session_order):
    response_data = []

    for assessment in user_assessments:
        session_id = assessment["session_id"]
        emotion_data =  json.loads(assessment["emotion"]) if assessment["emotion"] else {}
        score = assessment["score"]
        date = assessment["assessment_date"]
        
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




# need to optimize with select_related and prefetch_related to all queries
def run():
    fake: Faker = Faker()
    sales_person_id = 1
    user_id = 21
    disorder_id = 4
    slp_id = 1
    clinic_id = 8
    date_str = fake.date()
    time_str = fake.time()
    time_filter = "last_month"
    user_type = "clinic"
    date_filter =get_date_filter(time_filter)
    
    
    file_path = "jhon.jpg"
    file_url = upload_to_s3(file_path,AWS_STORAGE_BUCKET_NAME)
    print(file_url)

