import random
import string
from payment.models import Payment
from clinic.models import Clinics

from django.utils.timezone import now, timedelta,datetime
from authentication.models import CustomUser,UserProfile
from django.db.models import Sum, F,Value,CharField,Count,Func,Q,FloatField,OuterRef,Subquery
from django.utils.dateformat import DateFormat
from django.db.models.functions import ExtractYear, ExtractMonth,ExtractWeek,ExtractQuarter,Coalesce,Concat,Cast
from utils.MonthsShortHand import MONTH_ABBREVIATIONS

def printlist(list):
    for i in list:
        print(i)
def run():
    # clinic_details = get_sales_by_period_and_salesperson(1,"weekly")
    # print(clinic_details)
    year = datetime.now().year
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
            .filter(sale_person_id=1)
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
    printlist(clinics_queryset)
