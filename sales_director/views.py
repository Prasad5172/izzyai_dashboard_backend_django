from django.shortcuts import render
from django.db.models import Count, Sum, F, Q,FloatField,Value,Case,When,ExpressionWrapper
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

def activeClinicsForSalesPerson(sale_person_id):
    return Clinics.objects.filter(sale_person_id=sale_person_id)

# Create your views here.
#/get_all_salespersons_overview
#query verified
class SalesPersonDetails(APIView):
    def get_all_salespersons_overview(request):
        """
        Fetches an overview of all salespersons, including clinic count, user count, sales per clinic, and revenue.
        """
        try:
            salespersons = SalePersons.objects.annotate(
                active_clinics_count=Count("clinics", distinct=True),
                total_revenue=Coalesce(Sum(
                        "clinics__user_profiles__user__payments__amount",
                        filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")
                    ),Value(0.0, output_field=FloatField())),
                total_users=Count("clinics__user_profiles", distinct=True),
                commission_amount=Coalesce(
                                    Sum(
                                        F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                                        (F('sales__commission_percent') / 100.0),
                                        distinct=True,
                                        output_field=FloatField()
                                    ),
                                    Value(0.0, output_field=FloatField())
                )
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
                    SalePersonId=F("sale_person_id"),
                    ActiveClinics=F("active_clinics_count"),
                    SalesPerClinic=F("sales_per_clinic"),
                    RevenueGenerated=F("total_revenue"),
                ).values(
                    "SalePersonId",
                    "country",
                    "name",
                    "ActiveClinics",
                    "SalesPerClinic",
                    "RevenueGenerated",
                    "total_users",
                    "commission_amount"
                )
            result = list(salespersons)
            return Response({result:result},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

#/get_sales_target,/insert_sales_target
class SalesTarget(APIView):
    def post(request):
        """
        Endpoint to insert a sales target for a salesperson.

        This endpoint allows inserting a sales target for a specific salesperson, 
        identified by SalePersonID, for a given month and year.
        """
        sale_person_id = request.data.get('SalePersonID')
        month = request.data.get('Month')
        year = request.data.get('Year')
        target = request.data.get('Target')

        month_mapping = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

        month_int = month_mapping.get(month)
        if month_int is None:
            return Response({'error': 'Invalid month provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            SalesTarget.objects.create(
                sale_person_id=sale_person_id,
                month=month_int,
                year=year,
                target=target
            )
            return Response({'message': 'Sales target inserted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self,request):
        try:
            sale_person_id = request.GET.get('SalePersonID')
            sales_target = SalesTarget.objects.filter(sale_person_id=sale_person_id).first()
            return Response({
                'SalePersonID': sale_person_id,
                'Month': sales_target.month,
                'Year': sales_target.year,
                'Target': sales_target.target
            },status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#/get_salesperson_details,/get_salesperson_details_by_id
class SalesPersonsFullDetails(APIView):
    def get(self , request , sale_person_id ):
        try:
            # Fetch SalesPerson details including subscription count
            salesperson = SalePersons.objects.filter(sale_person_id=sale_person_id).annotate(
                active_clinics=Count("clinics"),
                total_revenue=Sum("clinics__user_profiles__user__payments__amount", 
                                filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")),
                total_users=Count("clinics__user_profiles__user", distinct=True)  # Count unique users across clinics
                ).values(
                    "user__username", "country", "state", "subscription_count",
                    "commission_percent", "user__email", "phone", "user_id",
                    "active_clinics", "total_revenue", "total_users"
                ).first()

            if not salesperson:
                print({"error": "Salesperson not found"})
            else:
                clinics = Clinics.objects.filter(sale_person_id=sale_person_id).values_list("clinic_name", flat=True)
                active_clinic_names = list(clinics)

                # Avoid division by zero
                sales_per_clinic = -(-salesperson["total_users"] // salesperson["active_clinics"]) if salesperson["active_clinics"] > 0 else 0

                # Prepare the result
                result = {
                    'SalePersonID': sale_person_id,
                    'Name': salesperson['user__username'],
                    'Email': salesperson['user__email'],
                    'Country': salesperson['country'],
                    'State': salesperson['state'],
                    'Phone': salesperson['phone'],
                    'CommissionPercent': salesperson['commission_percent'],
                    'SubscriptionCount': salesperson['subscription_count'],
                    'ActiveClinics': salesperson['active_clinics'],
                    'ActiveClinicNames': active_clinic_names,
                    'SalesPerClinic': sales_per_clinic,
                    'RevenueGenerated': salesperson['total_revenue'] or 0
                }
            return Response(result, status=200)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=500)

#/get_sales_commission,
#in middle
class SalesCommision(APIView):
    def get(self , request , sale_person_id ):
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
                ).values('sale_person_id', 'user__username', 'revenue_generated', 'commission_per_salesperson')
             # Convert to JSON response
             
            results = []
            for row in sales_commission_details:
                results.append({
                    'SalePersonID': row["sale_person_id"],
                    'Name': row["user__username"],
                    'RevenueGenerated': row["revenue_generated"],
                    'CommissionPerSalePerson': row["commission_per_salesperson"]
                })
            return Response(list(results), safe=False)

        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'}, status=500)


#pass saleperson_id for salesperson revenue else it fetches all persons revenue.

class AssignSalesPersonToDemoRequest(APIView):
    def put(self, request, demo_request_id):
        try:
            # Fetch the demo request object
            demo_request = DemoRequested.objects.filter(demo_request_id=demo_request_id).first()
            if not demo_request:
                return Response({'error': 'Demo Request not found'}, status=status.HTTP_404_NOT_FOUND)

            # Fields to update
            updatable_fields = ["sale_person_id"]

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

#/get_sales_revenue,/get_sales_revenue_by_id/<int:sale_person_id>
class GetSalesPersonsRevenue(APIView):
    def get(self , request ):
        try:
            saleperson_id = int(request.GET.get('sales_person_id', None))
            time_filter = request.GET.get('time_filter', None) 
            date_filter = now()-timedelta(days=365)
            if time_filter == 'last_month':
                date_filter = now() - timedelta(days=30)
            elif time_filter == 'annual':
                date_filter = now() - timedelta(days=365)

            if(saleperson_id is not None):
                #fetch sales persons revenue
                salesperson = SalePersons.objects.filter(sale_person_id=saleperson_id).annotate(
                        total_revenue=Coalesce(Sum("clinics__user_profiles__user__payments__amount",
                                        filter=Q(clinics__user_profiles__user__payments__payment_date__gte=date_filter) & Q(clinics__user_profiles__user__payments__payment_status="Paid")),
                                        Value(0.0, output_field=FloatField())),
                        ).values(
                            "sale_person_id", "country", "state", "total_revenue"
                        ).first()
                return Response(
                    {
                        'SalePersonID': salesperson.sale_person_id,
                        'Country': salesperson.country,
                        'State': salesperson.state,
                        'RevenueGenerated': salesperson.total_revenue
                        }, status=status.HTTP_200_OK)
            salesperson = SalePersons.objects.annotate(
                total_revenue=Coalesce(Sum("clinics__user_profiles__user__payments__amount",
                                filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")),
                                Value(0.0, output_field=FloatField())),
                ).values(
                    "sale_person_id", "country", "state", "total_revenue"
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