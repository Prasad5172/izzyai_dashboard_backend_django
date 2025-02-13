from django.db import models
class Sales(models.Model):
    sale_person_id = models.ForeignKey('sales_person.Salesperson', on_delete=models.CASCADE)
    sales_id = models.BigIntegerField(unique=True)
    subscription_count = models.BigIntegerField()
    commission_percent = models.BigIntegerField()
    clinic_id = models.ForeignKey('clinic.Clinic', on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=255)
    subscription_type = models.CharField(max_length=255)

    def __str__(self):
        return f"Sales ID {self.sales_id} - SalePerson {self.sale_person_id}"


class SalesDirector(models.Model):
    sales_director_id = models.BigIntegerField(unique=True)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE)
    department = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)

    def __str__(self):
        return f"Sales Director {self.sales_director_id} - {self.department}"
