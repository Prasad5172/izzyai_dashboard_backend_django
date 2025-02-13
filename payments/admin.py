from django.contrib import admin

# Register your models here.
from .models import Payment, Invoice, Coupon

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'owner_name', 'plan', 'amount', 'status', 'payment_date')
    search_fields = ('payment_id', 'owner_name', 'owner_email')
    list_filter = ('status', 'payment_method')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'customer_name', 'paid_amount', 'due_date', 'invoice_status')
    search_fields = ('invoice_id', 'customer_name', 'customer_email')
    list_filter = ('invoice_status', 'subscription_type')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_id', 'code', 'discount', 'expiration_date', 'is_used')
    search_fields = ('code',)
    list_filter = ('is_used', 'user_type')
