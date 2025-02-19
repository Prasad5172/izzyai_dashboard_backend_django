import random
import string
from payment.models import Payment
from clinic.models import Clinics

from django.utils.timezone import now, timedelta,datetime
from authentication.models import CustomUser,UserProfile
from django.db.models import Sum, F,Value,CharField,Count,Func,Q,FloatField,OuterRef,Subquery,Case,When,ExpressionWrapper
from django.utils.dateformat import DateFormat
from django.db.models.functions import ExtractYear, ExtractMonth,ExtractWeek,ExtractQuarter,Coalesce,Concat,Cast
from utils.MonthsShortHand import MONTH_ABBREVIATIONS
from sales_person.models import SalePersons
def printlist(list):
    for i in list:
        print(i)
def run():

    salespersons_ = SalePersons.objects.annotate(
        active_clinics_count=Count("clinics", distinct=True),
        total_revenue=Sum(
                "clinics__user_profiles__user__payments__amount",
                filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")
            ),
        total_users=Count("clinics__user_profiles", distinct=True),
        commission_amount=Coalesce(
                            Sum(
                                F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                                (F('sales__commission_percent') / 100.0),
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
    result = list(salespersons_)
    printlist(result)
    