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
from clinic.models import Clinics
from payment.models import Payment
# Create your views here.
class ClinicPatients(APIView):
    def get(self , request , clinic_id , time_filter):
        """
        Fetches patient details for a specific clinic.

        This endpoint retrieves a list of patients associated with a clinic, along with their revenue generated (from completed payments) and additional details such as country, state, and status. It allows the user to filter the results by time (last month or annual) using a query parameter. The data is returned as a JSON response.

        Steps performed by this endpoint:
        - Accepts the `clinic_id` as a URL parameter to identify the specific clinic.
        - Optionally accepts a query parameter `time_filter` to filter the results by time:
        - 'last_month': Filters for patients who have made payments in the last month.
        - 'annual': Filters for patients who have made payments in the last 12 months.
        - If no filter is provided, all patient details are returned without a time filter.
        - Retrieves user details, including revenue generated (sum of completed payments), country, state, and status for each patient in the clinic.
        - Returns the result as a list of patient details, including `UserID`, `RevenueGenerated`, `Country`, `State`, and `Status`.
        - If no patients are found, it will return an empty list.

        URL Parameters:
        - clinic_id (int): The unique ID of the clinic whose patient details are being retrieved.

        Query Parameters (Optional):
        - time_filter (string): The time filter for revenue calculations. Options include:
        - 'last_month': Limits results to the last month.
        - 'annual': Limits results to the last 12 months.

        Response:
        - 200 OK: Successfully retrieves the patient details for the clinic.
        Example:
        [
            {
            "UserID": 123,
            "RevenueGenerated": 1500.00,
            "Country": "USA",
            "State": "California",
            "Status": "Active"
            },
            ...
        ]
        
        - 500 Internal Server Error: If a database error occurs during the query execution.
        Example:
        {
            "error": "Error occurred: <error_message>"
        }
        """
        date_filter = {}
        if time_filter == 'last_month':
            date_filter['payment_date__gte'] = now() - timedelta(days=30)
        elif time_filter == 'annual':
            date_filter['payment_date__gte'] = now() - timedelta(days=365)
    
        # Fetch user details with revenue calculation for patients in the given clinic
        users = UserProfile.objects.filter(
                    clinic_id=clinic_id,
                    user__user_type='Patient'
                ).annotate(
                revenue_generated=Coalesce(
                Sum(
                    F('user__user_payment__amount'),
                    filter=F('user__user_payment__payment_status') == 'Completed',
                    **date_filter
                ),
                Value(0)
                )
                 ).values(
                     'user__user_id', 'revenue_generated', 'country', 'state', 'status'
                )
    
        return JsonResponse(list(users), safe=False)
        


