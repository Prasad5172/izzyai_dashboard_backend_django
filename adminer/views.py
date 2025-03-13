from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.utils.timezone import now
from authentication.models import CustomUser
from django.db.models import Sum, Q, FloatField, Value,Count
from django.db.models.functions import Coalesce,TruncMonth,TruncYear
from datetime import date
from payment.models import Payment

def get_date_filter(time_filter):
    date_filter =None
    if time_filter == 'last_month':
        date_filter = now() - timedelta(days=30)
    elif time_filter == 'annual':
        date_filter = now() - timedelta(days=365)
    return date_filter

# Create your views here.
#/get_users_overview
class TotalUsersWithRevenue(APIView):
    def get(self, request):
        try:
            time_filter = request.GET.get('time_filter')
            date_filter = None
            
            if time_filter == 'last_month':
                date_filter = now() - timedelta(days=30)
            elif time_filter == 'annual':
                date_filter = now() - timedelta(days=365)

            # Define payment filter condition
            payment_filter = Q(payments__payment_status='Paid')
            if date_filter:
                payment_filter &= Q(payments__payment_date__gte=date_filter)
                user_filter = Q(created_account__gte=date_filter)

            # Query result
            query_result = CustomUser.objects.filter(user_type="patient").aggregate(
                total_revenue=Coalesce(
                    Sum('payments__amount', filter=payment_filter),
                    Value(0.0, output_field=FloatField())
                ),
                total_users=Count('user_id',filter=user_filter, distinct=True)
            )

            return Response(query_result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": f'Error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


#/get_registration_percentage
class RegistrationPercentage(APIView):
    def get(self,request):
        try:
            time_filter = request.GET.get('time_filter')  # Get time filter from request
            date_filter =get_date_filter(time_filter)

            query_result = CustomUser.objects.filter(
                created_account__gte=date_filter, user_type="patient"
            ).aggregate(
                todays_registrations=Count('user_id', distinct=True, filter=Q(created_account__date=date.today())),
                total_users=Count('user_id', distinct=True,filter=Q(created_account__gte=date_filter))
            )
            today_registrations = query_result['todays_registrations']
            total_registrations = query_result['total_users']
            if total_registrations > 0:
                registration_percentage = round((today_registrations * 100.0) / total_registrations,2)
            else:
                registration_percentage = 0.0

            
            return Response({"registration_percentage":registration_percentage,"total_users":total_registrations,"today_registrations":today_registrations},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#/get_revenue_percentage #users_types = ['patient']
#/get_total_income
class RevenuePercentage(APIView):
    def get(self,request):
        try:
            users_types = request.data.get('user_types')  #['patient', 'clinic'] list of user_types
            time_filter = request.GET.get('time_filter')  # Get time filter from request
            date_filter =get_date_filter(time_filter)

            query_result = CustomUser.objects.filter(
                created_account__gte=date_filter, user_type__in=users_types
            ).aggregate(
                todays_revenue=Coalesce(
                    Sum('payments__amount', filter=Q(payments__payment_date__date=date.today()) & Q(payments__payment_status='Paid')),
                    Value(0.0, output_field=FloatField())
                ),
                total_revenue=Coalesce(
                    Sum('payments__amount', filter=Q(payments__payment_status='Paid') & Q(payments__payment_date__gte=date_filter)),
                    Value(0.0, output_field=FloatField())
                )
            )
            todays_revenue = query_result['todays_revenue']
            total_revenue = query_result['total_revenue']
            if total_revenue > 0:
                revenue_percentage = round((todays_revenue * 100.0) / total_revenue,2)
            else:
                revenue_percentage = 0.0
            
            return Response({"todays_revenue":todays_revenue,"revenue_percentage":revenue_percentage,"total_revenue":total_revenue},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#/get_revenue_breakdown
class GetRevenueBreakdown(APIView):
    def get(self,request):
        try:
            view_type = request.GET.get('view_type', 'yearly')
            year = request.GET.get('year', None)
            quarter = request.GET.get('quarter', None)
            # Validate parameters
            if view_type in ['quarterly', 'monthly'] and not year:
             return Response({'error': 'Year is a required parameter for quarterly and monthly views.'}, status=status.HTTP_400_BAD_REQUEST)
           
            payments = Payment.objects.filter(payment_status='Paid')
            # Apply filtering based on view_type
            if view_type == 'quarterly':
                if not quarter or quarter not in {'1', '2', '3', '4'}:
                    return Response({'error': 'Invalid or missing quarter. Quarter should be 1, 2, 3, or 4.'}, status=400)
                
                # Map quarter to corresponding months
                quarter_to_months = {
                    '1': [1, 2, 3],
                    '2': [4, 5, 6],
                    '3': [7, 8, 9],
                    '4': [10, 11, 12]
                }

                payments = payments.filter(payment_date__year=year, payment_date__month__in=quarter_to_months[quarter])

                # Group by month and user type
                revenue_data = payments.annotate(
                    period=TruncMonth('payment_date')  # Groups by month
                ).values('period', 'user__user_type') \
                .annotate(total_revenue=Coalesce(Sum('amount', output_field=FloatField()), 0.0)) \
                .order_by('period', 'user__user_type')

            elif view_type == 'monthly':
                payments = payments.filter(payment_date__year=year)

                # Group by month and user type
                revenue_data = payments.annotate(
                    period=TruncMonth('payment_date')
                ).values('period', 'user__user_type') \
                .annotate(total_revenue=Coalesce(Sum('amount', output_field=FloatField()), 0.0)) \
                .order_by('period', 'user__user_type')

            else:  # Yearly breakdown
                # Group by year and user type
                revenue_data = payments.annotate(
                    period=TruncYear('payment_date')
                ).values('period', 'user__user_type') \
                .annotate(total_revenue=Coalesce(Sum('amount', output_field=FloatField()), 0.0)) \
                .order_by('period', 'user__user_type')

            # Format the response
            revenue_breakdown = [
                {
                    'Period': row['period'].strftime('%Y-%m' if view_type in ['monthly', 'quarterly'] else '%Y'),
                    'UserType': row['user__user_type'],
                    'TotalRevenue': float(row['total_revenue'])
                }
                for row in revenue_data
            ]

            return Response({'revenue_breakdown': revenue_breakdown}, status=200)

        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)