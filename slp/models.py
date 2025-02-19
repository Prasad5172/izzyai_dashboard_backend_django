from django.db import models
# Create your models here.
class Slps(models.Model):
    slp_id = models.BigAutoField(primary_key=True)
    profile_image_path = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50)#redundant
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    slp_name = models.CharField(max_length=255)
    #user_id = models.BigIntegerField(unique=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    #clinic_id = models.BigIntegerField(null=True, blank=True)
    clinic = models.ForeignKey('clinic.Clinics', on_delete=models.CASCADE)
    phone = models.BigIntegerField(unique=True)

    def __str__(self):  
        return self.slp_name

class SlpAppointments(models.Model):
    #disorder_id = models.BigIntegerField()
    appointment_id = models.BigAutoField(primary_key=True)
    disorder = models.ForeignKey('clinic.Disorders', on_delete=models.CASCADE)
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp = models.ForeignKey('slp.Slps', on_delete=models.CASCADE)
    #user_id = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    appointment_date = models.DateTimeField(null=False, blank=False)
    session_type = models.CharField(max_length=255)
    appointment_status = models.CharField(max_length=255)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)

    def __str__(self):
        return str(self.appointment_id)
    