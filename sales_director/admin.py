from django.contrib import admin
from .models import (
    Sales, SalesDirector
)

@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ('sales_id', 'sales_person_id', 'subscription_count', 'commission_percent', 'clinic_id', 'payment_status', 'subscription_type')
    search_fields = ('sales_id', 'sales_person_id')
    list_filter = ('payment_status', 'subscription_type')


@admin.register(SalesDirector)
class SalesDirectorAdmin(admin.ModelAdmin):
    list_display = ('sales_director_id', 'user_id', 'department', 'designation')
    search_fields = ('sales_director_id', 'department')
    list_filter = ('department',)



