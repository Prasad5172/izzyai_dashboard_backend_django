from django.db import models
# Create your models here.

class Subscriptions(models.Model) : 
    subscription_id = models.BigIntegerField(primary_key=True)
    subscription_price = models.FloatField()
    subscription_name = models.CharField(max_length=255)


    def __str__(self):
        return f"Subscription {self.subscription_id} - User {self.user_id}"
class Payment(models.Model):
    plan = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=255)
    owner_email = models.EmailField(max_length=255)
    payment_method_id = models.CharField(max_length=255 , unique=True)
    invoice_id = models.CharField(max_length=255 , unique=True)
    subscription_id = models.ForeignKey('payments.Subscriptions', on_delete=models.CASCADE)  # This should be a ForeignKey to Subscription model
    status = models.CharField(max_length=255)
    payment_date = models.DateTimeField()
    amount = models.FloatField()
    #user_id = models.IntegerField(unique=True)
    customer_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE, related_name="customer_payments")
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE, related_name="user_payments")
    user_payment_id = models.IntegerField(unique=True)
    subscription_start_date = models.DateTimeField()
    subscription_end_date = models.DateTimeField()
    payment_failures = models.IntegerField()
    has_used_trial = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.owner_name}"


class Invoice(models.Model):
    paid_amount = models.BigIntegerField(default=0)
    due_date = models.DateTimeField()
    subscription_count = models.BigIntegerField(default=0)
    invoice_id = models.IntegerField(unique=True)
    subscription_type = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(max_length=255)
    invoice_status = models.CharField(max_length=50)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE) #ask jayanth, not present in the pdf
    subscription_id = models.ForeignKey('payments.Subscriptions', on_delete=models.CASCADE) # This should be a ForeignKey to Subscription model
    clinic_id = models.ForeignKey('clinic.Clinics', on_delete=models.CASCADE) # This should be a ForeignKey to Clinic model
    issue_date = models.DateTimeField()
    amount = models.BigIntegerField()

    def __str__(self):
        
        return f"Invoice {self.invoice_id} - {self.customer_name}"


class Coupon(models.Model):
    free_trial = models.IntegerField()
    is_used = models.BooleanField(default=False)
    code = models.CharField(max_length=50, unique=True)
    user_type = models.CharField(max_length=255) # This should be a ForeignKey to User model
    coupon_id = models.BigIntegerField(unique=True)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE) # This should be a ForeignKey to User model
    discount = models.IntegerField()
    expiration_date = models.DateField()
    redemption_count = models.IntegerField()

    def __str__(self):
        return f"Coupon {self.code} - Discount {self.discount}%"

