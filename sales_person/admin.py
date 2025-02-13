from django.contrib import admin
from .models import (
    SalePersonActivityLog, SalePersonPipeline, SalePersons,  SalesTarget
)
# Register your models here.
@admin.register(SalePersonActivityLog)
class SalePersonActivityLogAdmin(admin.ModelAdmin):
    list_display = ('sale_person_id', 'meetings', 'qualifying_calls', 'renewal_calls', 'proposals_sent', 'date')
    search_fields = ('sale_person_id',)
    list_filter = ('date',)


@admin.register(SalePersonPipeline)
class SalePersonPipelineAdmin(admin.ModelAdmin):
    list_display = ('sale_person_id', 'qualified_sales', 'renewals', 'prospective_sales', 'closed_sales', 'date')
    search_fields = ('sale_person_id',)
    list_filter = ('date',)


@admin.register(SalePersons)
class SalePersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'state', 'country', 'status', 'subscription_count', 'commission_percent')
    search_fields = ('name', 'email')
    list_filter = ('state', 'country', 'status')

@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    list_display = ('sale_person_id', 'month', 'year', 'target')
    search_fields = ('sale_person_id',)
    list_filter = ('month', 'year')