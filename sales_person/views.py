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
from django.db.models import Case,Sum,When,IntegerField
from authentication.models import UserProfile, CustomUser
from clinic.models import Clinics
from payment.models import Payment
from sales_director.models import Sales
from utils.sendregisteration import send_clinic_signup_link_email
from rest_framework import status
from .models import SalePersonActivityLog,SalePersonPipeline,SalesTarget,SalePersons
from clinic.models import DemoRequested
from utils.MonthsShortHand import MONTH_ABBREVIATIONS
from django.shortcuts import get_object_or_404

#/get_salesperson_details/<int:_id>
class SalesPersonView(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get("sales_person_id")
            sales_person = SalePersons.objects.filter(sales_person_id=sales_person_id).values("user__username","country","state","user__email","phone").first()
            print(sales_person)
            if len(sales_person) == 0:
                return Response({"error":"SalePerson not found"},status=status.HTTP_404_NOT_FOUND)
            
            data = {
                "name":sales_person["user__username"],
                "email":sales_person["user__email"],
                "phone":sales_person["phone"],
                "country":sales_person["country"],
                "state":sales_person["state"]
            }
            return Response(data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)


#/generate_demo_credentials
class GenerateDemoCredentials(APIView):
    def post(self , request ):
        try:
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
                user_type = "demo_user",
            )
            demo_user.expiration_date = expiration_date
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
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)





#/clinic_register_link
class SendClinicRegistredLinkAfterDemo(APIView):
    def post(self,request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({"message":"Enter valid email"},status=400)
            sales_person_id = request.data.get('sales_person_id')
            signup_link = "https://frontend.izzyai.com/signup"
            #send_clinic_signup_link_email(email, sales_person_id, signup_link) # need to check email function 
            return Response({'message': 'Clinic registration link sent successfully!'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#get ,post
#/get_activity_log
#/insert_activity_log
class ActivityLog(APIView):
    def get(self,request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            if not sales_person_id:
                return Response({"message":"provide sales person"},status=400)
            sales_activity_log = SalePersonActivityLog.objects.filter(sales_person_id=sales_person_id).order_by('-date').first() 

            if not sales_activity_log:
                return Response({'message': 'No activity log data found for the given SalePersonID'},status=status.HTTP_404_NOT_FOUND)
            
            return Response({
            'sales_person_id': sales_person_id,
            'qualifying_calls': sales_activity_log.qualifying_calls,
            'meetings': sales_activity_log.meetings,
            'proposals_sent': sales_activity_log.proposals_sent,
            'renewal_calls': sales_activity_log.renewal_calls,
            'date': sales_activity_log.date
        },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self,request):
        try:
            sales_person_id = request.data.get('sales_person_id')
            qualifying_calls = request.data.get('qualifying_calls')
            meetings = request.data.get('meetings')
            proposals_sent = request.data.get('proposals_sent')
            renewal_calls = request.data.get('renewal_calls')
            date = request.data.get('date')

            sales_person = get_object_or_404(SalePersons, sales_person_id=sales_person_id)

            SalePersonActivityLog.objects.create(
                sales_person=sales_person,
                qualifying_calls=qualifying_calls,
                renewal_calls=renewal_calls,
                proposals_sent=proposals_sent,
                meetings=meetings,
                date=date
            )
            return Response({'message': 'Activity log inserted successfully'},status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


#/get_monthly_registrations,#verified
class GetMonthlyRegistrationsPatientsClinics(APIView):
    def get(self, request):
        try:
            year = int(request.GET.get("year", datetime.now().year))

            # Optimized Query with Conditional Aggregation
            registrations = (
                CustomUser.objects
                .filter(created_account__year=year)
                .annotate(
                    month_number=ExtractMonth('created_account')
                )
                .values('month_number')
                .annotate(
                    total_patients=Sum(
                        Case(
                            When(user_type='patient', then=1),
                            default=0,
                            output_field=IntegerField()
                        )
                    ),
                    total_clinics=Sum(
                        Case(
                            When(user_type='clinic', then=1),
                            default=0,
                            output_field=IntegerField()
                        )
                    )
                )
                .order_by('month_number')
            )
            # Construct monthly registration data efficiently
            monthly_registrations = [
                {
                    'month': MONTH_ABBREVIATIONS[i + 1],
                    'total_patients': next((row['total_patients'] for row in registrations if row['month_number'] == i + 1), 0),
                    'total_clinics': next((row['total_clinics'] for row in registrations if row['month_number'] == i + 1), 0),
                }
                for i in range(12)
            ]

            return Response(monthly_registrations, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/get_pipeline_progress
#/insert_pipeline_progress
class PipeLineProgress(APIView):
    def get(self,request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            pipeline_date = SalePersonPipeline.objects.filter(sales_person_id=sales_person_id).order_by('-date').first()
            return Response({
                'sales_person_id': sales_person_id,
                'qualified_sales': pipeline_date.qualified_sales,
                'closed_sales': pipeline_date.closed_sales,
                'prospective_sales': pipeline_date.prospective_sales,
                'renewals': pipeline_date.renewals,
                'date': pipeline_date.date
            },status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self,request):
        try:
            sales_person_id = request.data.get('sales_person_id')
            qualified_sales = request.data.get('qualified_sales')
            closed_sales = request.data.get('closed_sales')
            prospective_sales = request.data.get('prospective_sales')
            renewals = request.data.get('renewals')
            date = request.data.get('date')
            sales_person = get_object_or_404(SalePersons,sales_person_id=sales_person_id)
            SalePersonPipeline.objects.create(
                sales_person=sales_person,
                qualified_sales=qualified_sales,
                closed_sales=closed_sales,
                prospective_sales=prospective_sales,
                renewals=renewals,
                date=date
                )
            return Response({"message":'Pipeline progress inserted successfully'},status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#/get_clinic_revenue_by_saleperson,#verified
# if subscriptioncount and commissionpercent should be verified while inserting-Imp
class GetClinicRevenueBySalesPerson(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get('sales_person_id',None)
            time_filter = request.GET.get('time_filter',None)

            if sales_person_id is None:
                return Response({"message":"you need to provide sales_person_id"})

            date_filter = 0
            # Correct date filter logic
            if time_filter == "last_month":
                date_filter = now() - timedelta(days=30)
            elif time_filter == "annual":
                date_filter = now() - timedelta(days=365)
            else:
                date_filter = None  # No filter applied if invalid filter
            
            revenue_per_clinic_subquery = (
                Payment.objects
                .filter(
                    user__user_profiles__clinic=OuterRef('clinic_id'),
                    payment_status='Paid',
                    payment_date__gte=date_filter if date_filter else now() - timedelta(days=365)  # Default annual filter
                )
                .values('user__user_profiles__clinic')  # Group by clinic
                .annotate(total_revenue=Sum('amount'))
                .values('total_revenue')
            )

            clinics_queryset = (
                Clinics.objects
                .select_related('sales_person')
                .prefetch_related('user_profiles__user__payments')
                .filter(sales_person__sales_person_id=sales_person_id)
                .annotate(
                    revenue_per_clinic=Subquery(revenue_per_clinic_subquery),
                    commission_amount=Coalesce(
                        Sum(
                            F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                            (F('sales__commission_percent') / 100.0),
                            output_field=FloatField()
                        ),
                        Value(0.0, output_field=FloatField())
                    ),
                    patients_count=Count('user_profiles', distinct=True)
                )
                .values('clinic_id', 'clinic_name', 'commission_amount', 'revenue_per_clinic', 'patients_count')
            )


            clinic_details_list = [{
                'clinic_id': row['clinic_id'],
                'clinic_name': row['clinic_name'],
                'revenue_per_clinic': row['revenue_per_clinic'],
                'number_of_patients': row['patients_count'],
                'commission_amount': row['commission_amount']
            } for row in clinics_queryset]

            return Response(clinic_details_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#function to get weekly,monthly,quarterly sales in sqllite

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
            user__user_profiles__clinic__sales_person=sales_person_id,
            payment_status='Paid'
        )
        .annotate(period=period_field)
        .values(
            sales_person_id=F("user__user_profiles__clinic__sales_person_id"),
            period=F("period")
        )
        .annotate(total_sales=Sum('amount'))
        .order_by("period")
    )


    # Convert queryset to list of dictionaries
    return [
        {
            'sales_person_id': row["sales_person_id"],
            period_label.capitalize(): row["period"],  
            'total_sales': row["total_sales"]
        }
        for row in sales_data
    ]


#again query verified and modified by prasad
#/track_weekly_sales_by_saleperson
#/track_monthly_sales_by_saleperson
#/track_quarterly_sales_by_saleperson
class GetWeeklyMonthlyQuaterlySalesBySalesPerson(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            clinic_details_list = {
                'weekly_sales': get_sales_by_period_and_salesperson(sales_person_id, "weekly"),
                'monthly_sales': get_sales_by_period_and_salesperson(sales_person_id, "monthly"),
                'quarterly_sales': get_sales_by_period_and_salesperson(sales_person_id, "quarterly")
            }
            return Response(clinic_details_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/track_sales_by_saleperson in flask code
#again query verified by prasad,
class GetSalesBySalesPerson(APIView):
    def get(self,request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            sales_by_sales_person = get_sales_by_period_and_salesperson(sales_person_id,"monthly")
            return Response(sales_by_sales_person,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/salespersons_ids,
#/get_salespersons ,from managament route
class GetSalesPersonsIdsNames(APIView):
    def get(self , request ):
        try:
            salespersons = SalePersons.objects.select_related('user').values("sales_person_id", "user__username")

            result = [
                {
                    "SalePersonID": sp["sales_person_id"],
                    "Name": sp["user__username"]
                }
                for sp in salespersons
            ]
            return Response({"salespersons": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/update_country/<int:sales_person_id>,/update_comission_percent/<int:sale_person_id>
class UpdateSalesPersonProfile(APIView):
    def put(self, request):
        try:
            sales_person_id = request.data.get("sales_person_id")
            # Fetch the salesperson object
            salesperson = SalePersons.objects.filter(sales_person_id=sales_person_id).first()
            if not salesperson:
                return Response({'error': 'SalePerson not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fields to update
            updatable_fields = ["phone", "state", "country", "status", "subscription_count", "commission_percent"]

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

#/get_sales_overview
class TotalSalesBySalesPersons(APIView):
    def get(self,request):
        try:
           SUBSCRIPTION_PRICE = 53.0  

           sales_by_salepersons = SalePersons.objects.annotate(
                username=F("user__username"),
                subscription_coun=Coalesce(Sum("sales__subscription_count"), Value(0.0, output_field=FloatField())),
                commission_perc=Coalesce(F("sales__commission_percent"), Value(0.0, output_field=FloatField())),
                payment_status=F("sales__payment_status"),
                clinic_id=F("sales__clinic_id"),
                sales_made=Coalesce(
                    Sum(F("sales__subscription_count") * Value(SUBSCRIPTION_PRICE, output_field=FloatField())), 
                    Value(0.0, output_field=FloatField())
                ),
                commission_amount=Coalesce(
                    Sum(F("sales__subscription_count") * Value(SUBSCRIPTION_PRICE, output_field=FloatField()) * 
                        F("sales__commission_percent") / Value(100.0, output_field=FloatField())), 
                    Value(0.0, output_field=FloatField())
                )
            ).values(
                "user_id",
                "username",
                "subscription_coun",
                "commission_perc",
                "payment_status",
                "clinic_id",
                "sales_made",
                "commission_amount"
            )

           sales_overview = list(sales_by_salepersons)

           return Response({sales_overview},status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/saleperson_register_link
class SendSalesPersonRegistrationLink(APIView):
    def post(self,request):
        try:
           email = request.data.get("email")
           signup_link= "https://frontend.izzyai.com/signup"
           #send_saleperson_signup_link_email(email, signup_link)  
           return Response({'message': 'Clinic registeration link'},status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)