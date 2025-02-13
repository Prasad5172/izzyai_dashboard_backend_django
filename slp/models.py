from django.db import models

# Create your models here.
class Slps(models.Model):
    slp_id = models.BigIntegerField(unique=True)
    profile_image_path = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    slp_name = models.CharField(max_length=255)
    #user_id = models.BigIntegerField(unique=True)
    user = models.ForeignKey('auth.Users', on_delete=models.CASCADE)
    #clinic_id = models.BigIntegerField(null=True, blank=True)
    clinic = models.ForeignKey('clinc.Clinics', on_delete=models.CASCADE)
    phone = models.BigIntegerField(unique=True)