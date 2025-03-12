from django.db import models
# Create your models here.

class Subscriptions(models.Model) : 
    subscription_id = models.BigAutoField(primary_key=True)
    subscription_price = models.FloatField(default=0)
    subscription_name = models.CharField(max_length=255)

    def __str__(self):
        return f"Subscription {self.subscription_id}"
class Payment(models.Model):
    payment_id = models.BigAutoField(primary_key=True)
    plan = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=255)
    owner_email = models.EmailField(max_length=255)
    payment_method_id = models.CharField(max_length=255 , unique=True)
    invoice_id = models.CharField(max_length=255 , unique=True)
    subscription = models.ForeignKey('payment.Subscriptions', on_delete=models.CASCADE)
    status = models.CharField(max_length=255)#dont know why
    payment_date = models.DateTimeField(null=True, blank=True)
    amount = models.FloatField(default=0)
    #user_id = models.IntegerField(unique=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name="payments")
    user_payment_id = models.IntegerField(unique=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    payment_failures = models.IntegerField(default=0)
    has_used_trial = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=255)# this is paid or not

    def __str__(self):
        return f"Payment {self.payment_id} - {self.owner_name}"


class Invoice(models.Model):
    invoice_id = models.BigAutoField(primary_key=True)
    paid_amount = models.BigIntegerField(default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    subscription_count = models.BigIntegerField(default=0)
    subscription_type = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(max_length=255)
    invoice_status = models.CharField(max_length=50)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE) #ask jayanth, not present in the pdf
    subscription = models.ForeignKey('payment.Subscriptions', on_delete=models.CASCADE) # This should be a ForeignKey to Subscription model
    clinic = models.ForeignKey('clinic.Clinics', on_delete=models.CASCADE) # This should be a ForeignKey to Clinic model
    issue_date = models.DateTimeField(null=True, blank=True)
    amount = models.BigIntegerField(default=0)

    def __str__(self):
        return f"Invoice {self.invoice_id} - {self.customer_name}"


class Coupon(models.Model):
    coupon_id = models.BigAutoField(primary_key=True)
    free_trial = models.IntegerField()
    is_used = models.BooleanField(default=False)
    code = models.CharField(max_length=50, unique=True)
    user_type = models.CharField(max_length=255) # This should be a ForeignKey to User model
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE) # This should be a ForeignKey to User model
    discount = models.IntegerField()
    expiration_date = models.DateField()
    redemption_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Coupon {self.code} - Discount {self.discount}%"

