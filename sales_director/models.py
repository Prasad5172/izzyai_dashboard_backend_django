from django.db import models
class Sales(models.Model):
    sales_id = models.BigAutoField(primary_key=True)
    sale_person_id = models.ForeignKey('sales_person.SalePersons', on_delete=models.CASCADE)
    subscription_count = models.BigIntegerField()
    commission_percent = models.BigIntegerField()
    clinic_id = models.ForeignKey('clinic.Clinics', on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=255)
    subscription_type = models.CharField(max_length=255)

    def __str__(self):
        return f"Sales ID {self.sales_id} - SalePerson {self.sale_person_id}"


class SalesDirector(models.Model):
    sales_director_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    department = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)

    def __str__(self):
        return f"Sales Director {self.sales_director_id} - {self.department}"
