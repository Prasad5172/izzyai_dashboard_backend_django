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
from sales_person.models import SalePersons

def printlist(list):
    for i in list:
        print(i)
def run():
    # clinic_details = get_sales_by_period_and_salesperson(1,"weekly")
    # print(clinic_details)
    salespersons = (
        SalePersons.objects
        .annotate(
            total_revenue=Coalesce(
                Sum(
                    'clinics__user_profiles__user__payments__amount',
                    filter=Q(clinics__user_profiles__user__payments__payment_status='Paid'),
                    output_field=FloatField()
                ),
                Value(0.0, output_field=FloatField())
            )
        )
        .values(
            'sales_person_id',
            'user__username',  # Salesperson's username
            'total_revenue'
        )
    )
    printlist(salespersons)
