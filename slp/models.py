from django.db import models
# Create your models here.
class Slps(models.Model):
    slp_id = models.BigIntegerField(unique=True)
    profile_image_path = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    slp_name = models.CharField(max_length=255)
    #user_id = models.BigIntegerField(unique=True)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE)
    #clinic_id = models.BigIntegerField(null=True, blank=True)
    clinic_id = models.ForeignKey('clinic.Clinics', on_delete=models.CASCADE)
    phone = models.BigIntegerField(unique=True)

    def __str__(self):  
        return self.slp_name

class SlpAppointments(models.Model):
    #disorder_id = models.BigIntegerField()
    disorder_id = models.ForeignKey('clinic.Disorders', on_delete=models.CASCADE)
    appointment_id = models.BigIntegerField(unique=True)
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp_id = models.ForeignKey(Slps, on_delete=models.CASCADE)
    #user_id = models.BigIntegerField(null=True, blank=True)
    user_id = models.ForeignKey('authentication.Users', on_delete=models.CASCADE)
    appointment_date = models.DateTimeField(null=False, blank=False)
    session_type = models.CharField(max_length=255)
    appointment_status = models.CharField(max_length=255)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)

    def __str__(self):
        return self.appointment_id