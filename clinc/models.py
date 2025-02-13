from django.db import models

# Create your models here.
class Clinics(models.Model):
    clinic_id = models.BigIntegerField(unique=True)
    izzyai_patients = models.BigIntegerField(null=True, blank=True)
    state = models.CharField(max_length=255)
    total_patients = models.BigIntegerField(default=0)
    slpCount = models.BigIntegerField(default=0)
    sale_person_id = models.BigIntegerField(null=True, blank=True)
    country = models.CharField(max_length=255)
    #UserId = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey('auth.Users', on_delete=models.CASCADE) 
    email = models.EmailField(unique=True)
    ein_number = models.BigIntegerField(unique=True)
    phone = models.BigIntegerField(unique=True)
    clinic_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.clinic_name

class ClinicAppointments(models.Model):
    appointment_id= models.BigIntegerField(unique=True)
    #SlpID = models.BigIntegerField(null=True, blank=True)
    slp = models.ForeignKey('auth.slps', on_delete=models.CASCADE)
    #ClinicID = models.BigIntegerField(null=True, blank=True)
    clinic = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=255)
    appointment_status = models.CharField(max_length=255)
    appointment_date = models.DateTimeField(null=False, blank=False)
    appointment_start = models.DateTimeField(null=False, blank=False)
    appointment_end = models.DateTimeField(null=False, blank=False)
    #disorder_id =  models.BigIntegerField(null=True, blank=True)
    disorder = models.ForeignKey('Disorders', on_delete=models.CASCADE)
    #UserID = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey('auth.Users', on_delete=models.CASCADE)

    def __str__(self):
        return self.appointment_id

class ClinicUserReminders(models.Model):
    reminder_id= models.BigIntegerField(unique=True)
    reminder_to= models.CharField(max_length=255)
    date=models.DateTimeField(null=False, blank=False)
    is_sent= models.BooleanField(default=False)
    #clinic_id= models.BigIntegerField(null=True, blank=True)
    clinic = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    time=models.DateTimeField(null=False, blank=False)
    #reminder_appointment_id=models.BigIntegerField(null=True, blank=True)
    reminder_appointment = models.ForeignKey(ClinicAppointments, on_delete=models.CASCADE)
    reminder_description=models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Remainder{self.reminder_id}-{self.reminder_description}"


class Disorders(models.Model):
    disorder_id = models.BigIntegerField(unique=True)
    disorder_name = models.CharField(max_length=255)

    def __str__(self):
        return self.disorder_name

class Tasks(models.Model):
    task_id = models.BigIntegerField(unique=True)
    #clinic_id = models.BigIntegerField(null=True, blank=True)
    clinic = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    task_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp = models.ForeignKey('auth.slps', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.task_name


    