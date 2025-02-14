from django.db import models

# Create your models here.
class Adminer(models.Model):
    user_id = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    department = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)

    def __str__(self):
        return self.user_id

    