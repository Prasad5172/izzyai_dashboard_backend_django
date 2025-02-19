from django.db.models import Sum, Count, F, Q, FloatField,Value,CharField,OuterRef,Subquery
from django.db.models.functions import Coalesce,Cast
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
import random
import string
from django.utils.timezone import now
from django.utils.dateformat import DateFormat
from django.db.models.functions import ExtractYear, ExtractMonth,ExtractWeek,Concat,ExtractQuarter
from authentication.models import UserProfile, CustomUser
from clinic.models import Clinics
from payment.models import Payment
from sales_director.models import Sales
from utils.sendregisteration import send_clinic_signup_link_email
from rest_framework import status
from .models import SalePersonActivityLog,SalePersonPipeline,SalesTarget
from clinic.models import DemoRequested
from utils.MonthsShortHand import MONTH_ABBREVIATIONS

#/insert_pipeline_progress
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

#/generate_demo_credentials
class GenerateDemoCredentials(APIView):
    def post(self , request ):
        demo_request_id = request.data.get('demo_request_id')

        if not demo_request_id:
            return Response({"error": "Demo request ID is required"},status=status.HTTP_400_BAD_REQUEST)
        
        demo_request = DemoRequested.objects.filter(demo_request_id=demo_request_id).first()
        if not demo_request:
            return Response({"error": "Demo request not found"},status=status.HTTP_400_BAD_REQUEST)
        
        email = demo_request.email
        clinic_name = demo_request.clinic_name
        

        username = f"{clinic_name.replace(' ', '_').lower()}_demo"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        expiration_date = now() + timedelta(days=7)

        demo_user = CustomUser.objects.create(
            username=username,
            email=email,
            is_otp_verified=True,
            is_setup_profile=True,
            user_type = "DemoUser",
            expiration_date=expiration_date
        )
        demo_user.set_password(password)
        demo_user.save()

        #need to implement send email with credential to the clinic
        #send_demo_request_email(email, clinic_name, username, password, expiration_date)

        return Response({
            "message": "Demo credentials generated successfully",
             "data": {
                "user_id": demo_user.user_id,
                "username": username,
                "password": password,
                "email": email,
                "expiration_date": expiration_date
            }
            },status=status.HTTP_201_CREATED)



#/clinic_register_link
class SendClinicRegistredLinkAfterDemo(APIView):
    def post(self,request):
        try:
            email = request.data.get('email')
            sale_person_id = request.data.get('sale_person_id')
            signup_link = "https://frontend.izzyai.com/signup"
            send_clinic_signup_link_email(email, sale_person_id, signup_link) # need to check email function 
            return Response({'message': 'Clinic registration link sent successfully!'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#get ,post
#/get_activity_log
#/insert_activity_log
class ActivityLog(APIView):
    def get(self,request):
        try:
            sale_person_id = request.POST.get('SalePersonID')
            sales_activity_log = SalePersonActivityLog.objects.filter(sale_person_id=sale_person_id).first() 

            if not sales_activity_log:
                return Response({'message': 'No activity log data found for the given SalePersonID'},status=status.HTTP_404_NOT_FOUND)
            return Response({
            'SalePersonID': sale_person_id,
            'QualifyingCalls': sales_activity_log.qualifying_calls,
            'Meetings': sales_activity_log.meetings,
            'ProposalsSent': sales_activity_log.proposals_sent,
            'RenewalCalls': sales_activity_log.renewal_calls,
            'Date': sales_activity_log.date
        },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self,request):
        try:
            sale_person_id = request.data.get('sale_person_id')
            qualifying_calls = request.data.get('qualifying_calls')
            meetings = request.data.get('meetings')
            proposals_sent = request.data.get('proposals_sent')
            renewal_calls = request.data.get('renewal_calls')
            date = request.data.get('date')
            SalePersonActivityLog.objects.create({
                sale_person_id,
                qualifying_calls,
                renewal_calls,
                proposals_sent,
                meetings,
                date
            })
            return Response({'message': 'Activity log inserted successfully'},status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


#/get_monthly_registrations,#verified
class GetMonthlyRegistrationsPatientsClinics(APIView):
    def get(self,request):
        try:
            year = request.GET.get("year")
            if not year:
                year = datetime.now().year
            else:
                # Cast year to integer
                year = int(year)
            patient_registrations = (
                CustomUser.objects
            .filter(created_account__year=year, user_type='patient')
            .annotate( 
                month_number=ExtractMonth('created_account') 
            )
            .values('month_number')
            .annotate(total_patients=Count('user_id'))
            .order_by('month_number')
            )
            clinic_registrations = (
                Clinics.objects
                .filter(user_id__created_account__year=year, user_id__user_type='Clinic')
                .annotate(
                    month_number=ExtractMonth('user_id__created_account')  # Extract month number (1-12)
                )
                .values( 'month_number')
                .annotate(total_clinics=Count('clinic_id'))
                .order_by('month_number')
            )
            monthly_registrations = []
            for i in range(12):  # Assuming 12 months in the year
                month = MONTH_ABBREVIATIONS[i+1]
                # Extract patient and clinic counts for the current month, defaulting to 0 if not found
                patient_count = next(
                    (row['total_patients'] for row in patient_registrations if row['month_number'] == i+1), 
                    0
                )
                
                clinic_count = next(
                    (row['total_clinics'] for row in clinic_registrations if row['month_number'] == i+1),
                    0
                )
                monthly_registrations.append({
                    'month': month,
                    'total_patients': patient_count,
                    'total_clinics': clinic_count
            })
            return Response({monthly_registrations},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/get_pipeline_progress
#/insert_pipeline_progress
class PipeLineProgress(APIView):
    def get(self,request):
        try:
            sale_person_id = request.GET.get('SalePersonID')
            pipeline_date = SalePersonPipeline.objects.filter(sale_person_id=sale_person_id).first()
            return Response({
                'SalePersonID': sale_person_id,
                'QualifiedSales': pipeline_date.qualified_sales,
                'ClosedSales': pipeline_date.closed_sales,
                'ProspectiveSales': pipeline_date.prospective_sales,
                'Renewals': pipeline_date.renewals,
                'Date': pipeline_date.date
            },status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self,request):
        try:
            sale_person_id = request.data.get('sale_person_id')
            qualified_sales = request.data.get('qualified_sales')
            closed_sales = request.data.get('closed_sales')
            prospective_sales = request.data.get('prospective_sales')
            renewals = request.data.get('renewals')
            date = request.data.get('date')
            SalePersonPipeline.objects.create({
                sale_person_id,
                qualified_sales,
                closed_sales,
                prospective_sales,
                renewals,
                date
            })
            return Response({"message":'Pipeline progress inserted successfully'},status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#/get_clinic_revenue_by_saleperson,#verified
# if subscriptioncount and commissionpercent should be verified while inserting-Imp
class GetClinicRevenueBySalesPerson(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            time_filter = request.GET.get('time_filter')
            date_filter = {}
            if time_filter == 'last_month':
                date_filter['payment_date__gte'] = now() - timedelta(days=30)
            elif time_filter == 'annual':
                date_filter['payment_date__gte'] = now() - timedelta(days=365)
            
            revenue_per_clinic_subquery = Clinics.objects.filter(
                    clinic_id=OuterRef('clinic_id')
                ).annotate(
                    revenue=Coalesce(
                        Sum(
                            'user_profiles__user__payments__amount',
                            filter=Q(user_profiles__user__payments__payment_status='Paid'),
                            output_field=FloatField()
                        ), Value(0.0, output_field=FloatField())
                    )
                ).values('revenue')[:1]
            
            clinics_queryset = (
                    Clinics.objects
                    .filter(sale_person_id=sales_person_id)
                    .annotate( 
                        revenue_per_clinic=Subquery(revenue_per_clinic_subquery),
                        commission_amount=Coalesce(
                            Sum(
                                F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                                (F('sales__commission_percent') / 100.0),
                                output_field=FloatField()
                            ),
                            Value(0.0, output_field=FloatField())
                        )
                    )
                    .values('clinic_id', 'clinic_name', 'revenue_per_clinic', 'commission_amount')
                )
            clinic_details_list = [{
                'ClinicID': row[0],
                'ClinicName': row[1],
                'RevenuePerClinic': row[2],
                'NumberOfPatients': row[3],
                'CommissionAmount': row[4]
            } for row in clinics_queryset]
            return Response(clinic_details_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#function to get weekly,monthly,quarterly sales
"""
SELECT 
    c.sale_person_id AS "SalesPersonId",
    strftime('%Y-%W', p.payment_date) AS "Week",
    COALESCE(SUM(p.amount), 0) AS "TotalSales"
FROM payment_payment p
-- JOIN authentication_customuser u ON p.user_id = u.user_id
JOIN authentication_userprofile up ON p.user_id = up.user_id
JOIN clinic_clinics c ON up.clinic_id = c.clinic_id 
WHERE c.sale_person_id = 1
AND p.payment_status = 'Paid'
GROUP BY c.sale_person_id, strftime('%Y-%W', p.payment_date)
ORDER BY "Week";
"""

def get_sales_by_period_and_salesperson(sales_person_id, period):
    """Fetch sales data for a given salesperson based on a specified period."""
    
    # Determine which date function to use based on the period
    if period == "weekly":
        period_field = Concat(
            Cast(ExtractYear('payment_date'), CharField()),
            Value('-'),  
            Cast(ExtractWeek('payment_date'), CharField())
        )
        period_label = "weekly"
    
    elif period == "monthly":
        period_field = Concat(
            Cast(ExtractYear('payment_date'), CharField()),
            Value('-'),  
            Cast(ExtractMonth('payment_date'), CharField())
        )
        period_label = "monthly"
    
    elif period == "quarterly":
        period_field = Concat(
            Cast(ExtractYear('payment_date'), CharField()),
            Value('-'),  
            Cast(ExtractQuarter('payment_date'), CharField())
        )
        period_label = "quarterly"

    else:
        raise ValueError("Invalid period. Choose from 'weekly', 'monthly', or 'quarterly'.")

    # Query sales data
    sales_data = (
        Payment.objects
        .filter(
            user__userprofile__clinic__sale_person=sales_person_id,
            payment_status='Paid'
        )
        .annotate(period=period_field)
        .values(
            sales_person_id=F("user__userprofile__clinic__sale_person_id"),
            period=F("period")
        )
        .annotate(total_sales=Sum('amount'))
        .order_by("period")
    )

    # Convert queryset to list of dictionaries
    return [
        {
            'SalePersonID': row["sales_person_id"],
            period_label.capitalize(): row["period"],  
            'TotalSales': row["total_sales"]
        }
        for row in sales_data
    ]


#again query verified and modified by prasad
class GetWeeklyMonthlyQuaterlySalesBySalesPerson(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            clinic_details_list = {
                'WeeklySales': get_sales_by_period_and_salesperson(sales_person_id, "weekly"),
                'MonthlySales': get_sales_by_period_and_salesperson(sales_person_id, "monthly"),
                'QuarterlySales': get_sales_by_period_and_salesperson(sales_person_id, "quarterly")
            }
            return Response(clinic_details_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/track_sales_by_saleperson in flask code
#again query verified by prasad,
class GetSalesBySalesPerson(APIView):
    def get(self,request):
        try:
            sale_person_id = request.GET.get('SalePersonID')
            sales_by_sales_person = get_sales_by_period_and_salesperson(sale_person_id,"monthly")
            return Response(sales_by_sales_person,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        