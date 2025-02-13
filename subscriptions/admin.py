from django.contrib import admin
from .models import Subscriptions
# Register your models here.

@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = ('subscription_id', 'subscription_name', 'subscription_price')
    search_fields = ('subscription_id', 'subscription_name')
    list_filter = ('subscription_price', 'subscription_name')
