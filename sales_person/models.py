from django.db import models

class SalePerson(models.Model):
    phone = models.BigIntegerField()
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)
    subscription_id = models.ForeignKey('subscription.Subscription', on_delete=models.CASCADE)
    subscription_count = models.BigIntegerField()
    commission_percent = models.BigIntegerField()

    def __str__(self):
        return f"SalePerson {self.name} - {self.email}"

class SalesTarget(models.Model):
    sale_person_id = models.ForeignKey(SalePerson, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    target = models.BigIntegerField()

    def __str__(self):
        return f"Target for SalePerson {self.sale_person_id} ({self.month}/{self.year})"
class SalePersonActivityLog(models.Model):
    sale_person_id = models.ForeignKey(SalePerson, on_delete=models.CASCADE)
    meetings = models.BigIntegerField()
    qualifying_calls = models.BigIntegerField()
    renewal_calls = models.BigIntegerField()
    proposals_sent = models.BigIntegerField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Activity Log - SalePerson {self.sale_person_id} ({self.date})"

class SalePersonPipeline(models.Model):
    sale_person_id = models.ForeignKey(SalePerson, on_delete=models.CASCADE)
    qualified_sales = models.BigIntegerField()
    renewals = models.BigIntegerField()
    prospective_sales = models.BigIntegerField()
    closed_sales = models.BigIntegerField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Pipeline - SalePerson {self.sale_person_id} ({self.date})"