from django.db import models

class SalePersons(models.Model):
    sale_person_id = models.BigAutoField(primary_key=True)
    phone = models.BigIntegerField()
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    user_id = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    subscription_id = models.ForeignKey('payment.Subscriptions', on_delete=models.CASCADE)
    subscription_count = models.BigIntegerField(default=0)
    commission_percent = models.BigIntegerField(default=0)

    def __str__(self):        
        return f"SalePerson {self.sale_person_id} - {self.status}"

class SalesTarget(models.Model):
    sales_target_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    target = models.BigIntegerField()

    def __str__(self):
        return f"Target for SalePerson {self.sale_person_id} ({self.month}/{self.year})"
class SalePersonActivityLog(models.Model):
    sale_person_activity_log_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    meetings = models.BigIntegerField()
    qualifying_calls = models.BigIntegerField()
    renewal_calls = models.BigIntegerField()
    proposals_sent = models.BigIntegerField()
    date = models.DateTimeField()

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