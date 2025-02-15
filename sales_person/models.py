from django.db import models

class SalePersons(models.Model):
    sale_person_id = models.BigAutoField(primary_key=True)
    phone = models.BigIntegerField(default=0)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    status = models.CharField(max_length=255)#redundant
    user_id = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    subscription_id = models.ForeignKey('payment.Subscriptions', on_delete=models.CASCADE)
    subscription_count = models.BigIntegerField(default=0)
    commission_percent = models.BigIntegerField(default=0)

    def __str__(self):        
        return f"SalePerson {self.sale_person_id} - {self.status}"

class SalesTarget(models.Model):
    sales_target_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    month = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    target = models.BigIntegerField(default=0)

    def __str__(self):
        return f"Target for SalePerson {self.sale_person_id} ({self.month}/{self.year})"
class SalePersonActivityLog(models.Model):
    sale_person_activity_log_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    meetings = models.BigIntegerField(default=0)
    qualifying_calls = models.BigIntegerField(default=0)
    renewal_calls = models.BigIntegerField(default=0)
    proposals_sent = models.BigIntegerField(default=0)
    date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Activity Log - SalePerson {self.sale_person_id} ({self.date})"

class SalePersonPipeline(models.Model):
    sale_person_pipeline_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey(SalePersons, on_delete=models.CASCADE)
    qualified_sales = models.BigIntegerField()
    renewals = models.BigIntegerField()
    prospective_sales = models.BigIntegerField()
    closed_sales = models.BigIntegerField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Pipeline - SalePerson {self.sale_person_id} ({self.date})"