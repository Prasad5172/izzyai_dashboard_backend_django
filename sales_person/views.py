from django.db.models import Sum, Count, F, Q, FloatField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.models import UserProfile, CustomUser
from clinic.models import Clinics
from payment.models import Payment
from sales_director.models import Sales
from utils.sendregisteration import send_clinic_signup_link_email
from rest_framework import status
from .models import SalePersonActivityLog,SalePersonPipeline
class SalespersonSalesApiView(APIView):
    def get(self, request):
        sale_person_id = request.query_params.get('sale_person_id', None)
        date_condition = request.query_params.get('date_condition', None)

        # Base QuerySet for Clinics
        clinics_qs = Clinics.objects.all()

        if sale_person_id:
            clinics_qs = clinics_qs.filter(sale_person_id=sale_person_id)

        # Annotate each clinic using the proper reverse relation ("user_profiles")
        clinics_qs = clinics_qs.annotate(
            revenue_per_clinic=Coalesce(
                Sum(
                    F('user_profiles__user__user_payment__amount'),
                    filter=Q(user_profiles__user__user_payment__payment_status='Completed') &
                           (Q(user_profiles__user__user_payment__payment_date__gte=date_condition) if date_condition 
                            else Q(user_profiles__user__user_payment__payment_status='Completed')),
                    output_field=FloatField()
                ),
                0.0
            ),
            number_of_patients=Count(
                'user_profiles__user', distinct=True,
                filter=Q(user_profiles__user__user_type='Patient')
            ),
            commission_amount=Coalesce(
                Sum(
                    # Convert constants to floats by using Value() with an explicit output_field:
                    F('sales__subscription_count') * Value(53.0, output_field=FloatField()) *
                    (F('sales__commission_percent') / Value(100.0, output_field=FloatField())),
                    output_field=FloatField()
                ),
                0.0
            )
        )

        # Serialize results
        clinic_details_list = [
            {
                'ClinicID': clinic.clinic_id,
                'ClinicName': clinic.clinic_name,
                'RevenuePerClinic': clinic.revenue_per_clinic,
                'NumberOfPatients': clinic.number_of_patients,
                'CommissionAmount': clinic.commission_amount
            }
            for clinic in clinics_qs
        ]

        return Response(clinic_details_list, status=200)

class SalepersonClincRegister(APIView):
    def post(self , request ):
        """
        Sends a clinic registration signup link to the specified email.

        This endpoint allows sending a registration link to a clinic, with the given salesperson ID and email address. The 
        link will allow the clinic to complete the registration process.

        Request (POST):
            - Body (JSON):
                {
                    "email": string,               # The email address to send the registration link
                    "sale_person_id": int          # The ID of the salesperson associated with the clinic
                }

        Response (JSON):
            - Success (201):
                {
                    "message": "Clinic registration link sent successfully!"
                }
            - Error (400):
                {
                    "error": "All fields are required"
                }
            - Error (500):
                {
                    "error": "Error occurred: <error_message>"
                }

        Status Codes:
            - 201 Created: Registration link sent successfully to the provided email.
            - 400 Bad Request: If either the email or sale_person_id is missing in the request.
            - 500 Internal Server Error: If an error occurs while sending the registration email.

    """
        email = request.data.get("email")
        sale_person_id = request.data.get('sale_person_id')
        if not email or not sale_person_id :
            return Response({"error": "All fields are required"} , status=status.HTTP_400_BAD_REQUEST)
        try :
            signup_link = "https://frontend.izzyai.com/signup"
            send_clinic_signup_link_email(email , sale_person_id , signup_link)
            return Response({'message': 'Clinic registration link sent successfully!'} , status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SalespersonPipelineProgress(APIView):
    def post(self , request ):
        """
        Inserts pipeline progress data for a specific salesperson.

        This endpoint allows the insertion of a salesperson's pipeline progress, including details about qualified sales, 
        closed sales, prospective sales, renewals, and the associated date.

        Request (POST):
            - Body (JSON):
                {
                    "sale_person_id": int,         # The ID of the salesperson
                    "qualified_sales": int,        # The number of qualified sales
                    "closed_sales": int,           # The number of closed sales
                    "prospective_sales": int,      # The number of prospective sales
                    "renewals": int,               # The number of renewals
                    "date": string                 # The date of the pipeline data (format: 'YYYY-MM-DD')
                }

        Response (JSON):
            - Success (201):
                {
                    "message": "Pipeline progress inserted successfully"
                }
            - Error (400):
                {
                    "error": "Missing one or more required fields"
                }
            - Error (500):
                {
                    "error": "Error occurred: <error_message>"
                }

        Status Codes:
            - 201 Created: Pipeline progress inserted successfully.
            - 400 Bad Request: If one or more required fields are missing in the request body.
            - 500 Internal Server Error: If an error occurs while inserting the data into the database.

        """
        sale_person_id = request.data.get('sale_person_id')
        qualifying_calls = request.data.get('qualifying_calls')
        closed_calls = request.data.get('closed_calls')
        proposals_sent = request.data.get('proposals_sent')
        renewal_calls = request.data.get('renewal_calls')
        date = request.data.get('date')

        if not sale_person_id or not qualifying_calls  or not proposals_sent or not renewal_calls or not date:
            return Response({"error": "Missing one or more required fields"} , status=status.HTTP_400_BAD_REQUEST)
        if(not CustomUser.objects.filter(user_id=sale_person_id).exists()):
            return Response({"error": "Not Registered"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            SalePersonPipeline.objects.create(
                sale_person_id=sale_person_id,
                qualified_sales=qualifying_calls,
                closed_sales = closed_calls ,
                prospective_sales=proposals_sent,
                renewals=renewal_calls,
                date=date
            ) 
            return Response({'message': ' Pipeline progess inserted successfully'} , status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SalespersonActivityLog(APIView):
    def post(self , request ):
        """
        Inserts activity log data for a specific salesperson.

        This endpoint allows the insertion of activity log data for a salesperson, including details about their qualifying calls, 
        meetings, proposals sent, renewal calls, and the associated date.

        Request (POST):
            - Body (JSON):
                {
                    "sale_person_id": int,         # The ID of the salesperson
                    "qualifying_calls": int,       # The number of qualifying calls made
                    "meetings": int,               # The number of meetings held
                    "proposals_sent": int,         # The number of proposals sent
                    "renewal_calls": int,          # The number of renewal calls made
                    "date": string                 # The date of the activity log (format: 'YYYY-MM-DD')
                }

        Response (JSON):
            - Success (201):
                {
                    "message": "Activity log inserted successfully"
                }
            - Error (400):
                {
                    "error": "Missing one or more required fields"
                }
            - Error (500):
                {
                    "error": "Error occurred: <error_message>"
                }

        Status Codes:
            - 201 Created: Activity log inserted successfully.
            - 400 Bad Request: If one or more required fields are missing in the request body.
            - 500 Internal Server Error: If an error occurs while inserting the data into the database.
        """
        sale_person_id = request.data.get('sale_person_id')
        qualified_sales = request.data.get('qualified_sales')
        closed_sales = request.data.get('closed_sales')
        meetings = request.data.get('meeting')
        prospective_sales = request.data.get('prospective_sales')
        renewals = request.data.get('renewals')
        date = request.data.get('date')

        if not sale_person_id or not qualified_sales or not closed_sales  or not prospective_sales or not renewals or not date :
            return Response({'error': 'Missing one or more required fields'} , status = status.HTTP_400_BAD_REQUEST )

        try:
            SalePersonActivityLog.objects.create(
                    sale_person_id = sale_person_id,
                    meetings =meetings , 
                    qualifying_calls = qualified_sales , 
                    renewal_calls = renewals ,
                    proposals_sent = prospective_sales , 
                    date = date
            )
            return Response({'message': 'Pipeline progress inserted successfully'} , status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    