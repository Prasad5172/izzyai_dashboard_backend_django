from django.shortcuts import render
from django.db.models import Count, Sum, F, Q,FloatField,Value,Case,When,ExpressionWrapper,Prefetch
from django.db.models.functions import Coalesce, Round
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sales_person.models import SalePersons
from authentication.models import CustomUser,UserProfile
from payment.models import Payment
from sales_person.models import SalesTarget
from clinic.models import Clinics,DemoRequested
from .models import Sales,SalesDirector

def activeClinicsForSalesPerson(sales_person_id):
    return Clinics.objects.filter(sales_person_id=sales_person_id)

# Create your views here.
#/get_all_salespersons_overview
#query verified
class SalesPersonDetails(APIView):
    def get(self, request):
        try:
            # Step 1: Optimized Sales Data Query
            salespersons = SalePersons.objects.select_related('user').prefetch_related(
                Prefetch(
                    'clinics__user_profiles__user__payments',
                    queryset=Payment.objects.filter(payment_status='Paid').only('amount')
                )
            ).alias(
                active_clinics_count=Count("clinics", distinct=True),
                total_revenue=Coalesce(
                    Sum(
                        "clinics__user_profiles__user__payments__amount",
                        filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")
                    ),
                    Value(0.0, output_field=FloatField())
                ),
                total_users=Count("clinics__user_profiles", distinct=True)
            ).annotate(
                sales_per_clinic=Case(
                    When(
                        active_clinics_count__gt=0,
                        then=ExpressionWrapper(
                            F("total_users") / F("active_clinics_count"),
                            output_field=FloatField()
                        )
                    ),
                    default=Value(0),
                    output_field=FloatField()
                ),
                name=F("user__username"),
                active_clinics=F("active_clinics_count"),
                revenue_generated=F("total_revenue"),
                total_users = F("total_users")
            ).values(
                "sales_person_id",
                "country",
                "name",
                "active_clinics",
                "sales_per_clinic",
                "revenue_generated",
                "total_users"
            )

            # Step 2: Optimized Commission Data Query
            commission_data = SalePersons.objects.annotate(
                commission_amount=Coalesce(
                    Sum(
                        F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                        (F('sales__commission_percent') / 100.0),
                        distinct=True,
                        output_field=FloatField()
                    ),
                    Value(0.0, output_field=FloatField())
                )
            ).values("sales_person_id", "commission_amount")

            # Step 3: Combine Results
            sales_dict = {item['sales_person_id']: item for item in salespersons}
            for commission in commission_data:
                sales_id = commission['sales_person_id']
                if sales_id in sales_dict:
                    sales_dict[sales_id]['commission_amount'] = commission['commission_amount']

            # Step 4: Final Result
            result = list(sales_dict.values())
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#/get_sales_target,/insert_sales_target
class SalesTargetView(APIView):
    def post(self,request):
        sales_person_id = request.data.get('sales_person_id')
        month = request.data.get('month')
        year = request.data.get('year')
        target = request.data.get('target')

        month_mapping = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        month_int = month_mapping.get(month)
        if month_int is None:
            return Response({'error': 'Invalid month provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            SalesTarget.objects.create(
                sales_person_id=sales_person_id,
                month=month_int,
                year=year,
                target=target
            )
            return Response({'message': 'Sales target inserted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        try:
            sales_person_id = request.GET.get('sales_person_id')
            
            # Check if sales_person_id is provided
            if not sales_person_id:
                return Response({'error': 'Missing SalePersonID'}, status=status.HTTP_400_BAD_REQUEST)

            # Filter and order results
            sales_targets = (
                SalesTarget.objects
                .filter(sales_person_id=sales_person_id)
                .values('month', 'year', 'target')
                .order_by('year', 'month')
            )

            # If no sales targets are found
            if not sales_targets.exists():
                return Response({'message': 'No sales targets found for the given SalePersonID'}, status=status.HTTP_404_NOT_FOUND)

            # Format the response
            return Response({
                'sales_person_id': sales_person_id,
                'sales_targets': list(sales_targets)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
#/get_salesperson_details_by_id/<int:sale_person_id>
class SalesPersonsFullDetails(APIView):
    def get(self, request):
        try:
            sales_person_id = request.GET.get("sales_person_id")

            # Step 1: Optimized SalesPerson Data
            salesperson = (
                SalePersons.objects
                .select_related('user')  # Efficient ForeignKey join
                .annotate(
                    active_clinics=Count('clinics', distinct=True),
                    total_users=Count('clinics__user_profiles__user', distinct=True)
                )
                .only(
                    'user__username', 'user__email', 'country', 'state',
                    'phone', 'commission_percent', 'subscription_count'
                )
                .get(sales_person_id=sales_person_id)
            )

            # Step 2: Optimized Revenue Calculation (Separate Query for Efficiency)
            total_revenue = (
                Payment.objects
                .filter(
                    user__user_profiles__clinic__sales_person_id=sales_person_id,
                    payment_status='Paid'
                )
                .aggregate(total_revenue=Coalesce(Sum('amount'), Value(0.0)))['total_revenue']
            )

            # Step 3: Optimized Clinics Fetch in Chunks (Using Chunking for Scalability)
            active_clinic_names = list(
                Clinics.objects
                .filter(sales_person_id=sales_person_id)
                .only('clinic_name')
                .values_list("clinic_name", flat=True)
            )

            # Step 4: Sales Per Clinic Calculation
            sales_per_clinic = (
                -(-salesperson.total_users // salesperson.active_clinics)
                if salesperson.active_clinics > 0 else 0
            )

            # Step 5: Final Data Preparation
            result = {
                'sales_person_id': sales_person_id,
                'name': salesperson.user.username,
                'email': salesperson.user.email,
                'country': salesperson.country,
                'state': salesperson.state,
                'phone': salesperson.phone,
                'commission_percent': salesperson.commission_percent,
                'subscription_count': salesperson.subscription_count,
                'active_clinics': salesperson.active_clinics,
                'active_clinic_names': active_clinic_names,
                'sales_per_clinic': sales_per_clinic,
                'revenue_generated': total_revenue
            }

            return Response(result, status=200)

        except SalePersons.DoesNotExist:
            return Response({'error': 'Salesperson not found'}, status=404)
        
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=500)

#/get_sales_commission,
#in middle
class SalesCommision(APIView):
    def get(self , request ):
        try:
            time_filter = request.GET.get('time_filter', None)

            date_filter =None
            if time_filter == 'last_month':
                date_filter = now() - timedelta(days=30)
            elif time_filter == 'annual':
                date_filter = now() - timedelta(days=365)
    
            # Fetch sales commission details
            sales_commission_details = SalePersons.objects.annotate(
                    revenue_generated=Coalesce(
                        Sum('clinics__user_profiles__user__payments__amount',
                            filter=Q(clinics__user_profiles__user__payments__payment_date__gte=date_filter) & Q(clinics__user_profiles__user__payments__payment_status='Paid')
                            ),
                        Value(0.0,output_field=FloatField())
                    ),
                    commission_per_salesperson=Round(
                        F('revenue_generated') * (F('commission_percent') / 100.0),
                        2
                    )
                ).values('sales_person_id', 'user__username', 'revenue_generated', 'commission_per_salesperson')
             # Convert to JSON response
             
            results = []
            for row in sales_commission_details:
                results.append({
                    'sales_person_id': row["sales_person_id"],
                    'name': row["user__username"],
                    'revenue_generated': row["revenue_generated"],
                    'commission_per_salesperson': row["commission_per_salesperson"]
                })
            return Response(results, status=200)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=500)


#/get_sales_revenue,/get_sales_revenue_by_id/<int:sale_person_id>
class GetSalesPersonsRevenue(APIView):
    def get(self , request ):
        try:
            sales_person_id = request.GET.get('sales_person_id', None)
            time_filter = request.GET.get('time_filter', None) 
            date_filter = None
            if time_filter == 'last_month':
                date_filter = now() - timedelta(days=30)
                print("last_month")
            elif time_filter == 'annual':
                date_filter = now() - timedelta(days=365)
            
            if(sales_person_id is not None):
                #fetch sales persons revenue
                salesperson = SalePersons.objects.filter(sales_person_id=sales_person_id).annotate(
                        total_revenue=Coalesce(
                            Sum("clinics__user_profiles__user__payments__amount",
                                        filter=Q(clinics__user_profiles__user__payments__payment_date__gte=date_filter) & Q(clinics__user_profiles__user__payments__payment_status="Paid")),
                                        Value(0.0, output_field=FloatField())),
                        ).values(
                            "sales_person_id", "country", "state", "total_revenue"
                        ).first()
                return Response(
                    {
                        'sales_person_id': salesperson['sales_person_id'],
                        'country': salesperson['country'],
                        'state': salesperson['state'],
                        'revenue_generated': salesperson['total_revenue']
                        }, status=status.HTTP_200_OK)
            salesperson = SalePersons.objects.annotate(
                total_revenue=Coalesce(
                    Sum("clinics__user_profiles__user__payments__amount",
                                filter=Q(clinics__user_profiles__user__payments__payment_date__gte=date_filter) & Q(clinics__user_profiles__user__payments__payment_status="Paid")),
                                Value(0.0, output_field=FloatField())),
                ).values(
                    "sales_person_id", "country", "state", "total_revenue"
                )
            return Response({"salespersonrevenue": salesperson}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AssignSalesPersonToDemoRequest(APIView):
    def put(self, request, demo_request_id):
        try:
            # Fetch the demo request object
            demo_request = DemoRequested.objects.filter(demo_request_id=demo_request_id).first()
            if not demo_request:
                return Response({'error': 'Demo Request not found'}, status=status.HTTP_404_NOT_FOUND)

            # Track if any updates were made
            updated = False

            # Loop through provided fields and update them
            demo_request.sales_person_id = 10
            demo_request.save()

            # Save only if any field is updated
            if updated:
                demo_request.save()
                return Response({'message': 'Demo Request updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No changes were made'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#/create_sales
class SalesView(APIView):
    def post(self,request):
        try:
            sales_person_id = request.data.get('sales_person_id')
            subscription_count = request.data.get('subscription_count')
            commission_percent = request.data.get('commission_percent')
            subscription_type = request.data.get('subscription_type')  # Replacing SubscriptionID with SubscriptionType
            clinic_id = request.data.get('clinic_id')  # Adding ClinicID
            payment_status = request.data.get('payment_status', 'Unpaid')

            Sales.objects.create(
                sales_person_id=sales_person_id,
                subscription_count=subscription_count,
                commission_percent=commission_percent,
                subscription_type=subscription_type,
                payment_status = payment_status,
                clinic_id=clinic_id
            )
            return Response({'message': 'Sales record created successfully.'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)