from django.db import models

class SalePersons(models.Model):
    sale_person_id = models.BigIntegerField(unique=True)
    phone = models.BigIntegerField()
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE)
    subscription_id = models.ForeignKey('payments.Subscriptions', on_delete=models.CASCADE)
    subscription_count = models.BigIntegerField()
    commission_percent = models.BigIntegerField()

    def __str__(self):        
        return f"SalePerson {self.name} - {self.email}"

class SalesTarget(models.Model):
    id = models.BigIntegerField(primary_key=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    target = models.BigIntegerField()

    def __str__(self):
        return f"Target for SalePerson {self.sale_person_id} ({self.month}/{self.year})"
class SalePersonActivityLog(models.Model):
    sale_person_activity_log_id = models.BigIntegerField(unique=True)
    sale_person_id = models.ForeignKey('SalePersons', on_delete=models.CASCADE)
    meetings = models.BigIntegerField()
    qualifying_calls = models.BigIntegerField()
    renewal_calls = models.BigIntegerField()
    proposals_sent = models.BigIntegerField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Activity Log - SalePerson {self.sale_person_id} ({self.date})"

class SalePersonPipeline(models.Model):
    sale_person_pipeline_id = models.BigIntegerField(unique=True)
    sale_person_id = models.ForeignKey(SalePersons, on_delete=models.CASCADE)
    qualified_sales = models.BigIntegerField()
    renewals = models.BigIntegerField()
    prospective_sales = models.BigIntegerField()
    closed_sales = models.BigIntegerField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Pipeline - SalePerson {self.sale_person_id} ({self.date})"