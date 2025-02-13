from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from ..slp.models import Slps
from ..authentication.models import Users

# Create your models here.
class Clinics(models.Model):
    clinic_id = models.BigIntegerField(unique=True)
    izzyai_patients = models.BigIntegerField(null=True, blank=True)
    state = models.CharField(max_length=255)
    total_patients = models.BigIntegerField(default=0)
    slp_count = models.BigIntegerField(default=0)
    #sale_person_id = models.BigIntegerField(null=True, blank=True) # need to add mapping to sales person
    sale_person_id = models.ForeignKey('sales_person.Salesperson', on_delete=models.CASCADE)
    country = models.CharField(max_length=255)
    #UserId = models.BigIntegerField(null=True, blank=True)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE) 
    email = models.EmailField(unique=True)
    ein_number = models.BigIntegerField(unique=True)
    phone = models.BigIntegerField(unique=True)
    clinic_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.clinic_name
    

class Disorders(models.Model):
    disorder_id = models.BigIntegerField(unique=True)
    disorder_name = models.CharField(max_length=255)

    def __str__(self):
        return self.disorder_name

class SessionType(models.Model):
    session_type_id = models.BigIntegerField(unique=True)
    type_name = models.CharField(max_length=255)

    def __str__(self):
        return self.type_name

class ClinicAppointments(models.Model):
    appointment_id= models.BigIntegerField(unique=True)
    #SlpID = models.BigIntegerField(null=True, blank=True)
    slp_id = models.ForeignKey(Slps, on_delete=models.CASCADE)
    #ClinicID = models.BigIntegerField(null=True, blank=True)
    clinic_id = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=255)
    appointment_status = models.CharField(max_length=255)
    appointment_date = models.DateTimeField(null=False, blank=False)
    appointment_start = models.DateTimeField(null=False, blank=False)
    appointment_end = models.DateTimeField(null=False, blank=False)
    #disorder_id =  models.BigIntegerField(null=True, blank=True)
    disorder_id = models.ForeignKey(Disorders, on_delete=models.CASCADE)
    #UserID = models.BigIntegerField(null=True, blank=True)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)

    def __str__(self):
        return self.appointment_id

class ClinicUserReminders(models.Model):
    reminder_id= models.BigIntegerField(unique=True)
    reminder_to= models.CharField(max_length=255)
    date=models.DateTimeField(null=False, blank=False)
    is_sent= models.BooleanField(default=False)
    #clinic_id= models.BigIntegerField(null=True, blank=True)
    clinic_id = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    time=models.DateTimeField(null=False, blank=False)
    #reminder_appointment_id=models.BigIntegerField(null=True, blank=True)
    reminder_appointment_id = models.ForeignKey(ClinicAppointments, on_delete=models.CASCADE)
    reminder_description=models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Remainder{self.reminder_id}-{self.reminder_description}"


class Tasks(models.Model):
    task_id = models.BigIntegerField(unique=True)
    #clinic_id = models.BigIntegerField(null=True, blank=True)
    clinic_id = models.ForeignKey(Clinics, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    task_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp_id = models.ForeignKey(Slps, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.task_name

class Sessions(models.Model):
    session_status = models.CharField(max_length=255)
    session_id = models.BigIntegerField(unique=True)
    #user_id = models.BigIntegerField(unique=True)
    user_id = models.ForeignKey('auth.Users',on_delete=models.CASCADE)
    #session_type_id = models.BigIntegerField(null=True, blank=True)
    session_type_id = models.ForeignKey(SessionType, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    #disorder_id = models.BigIntegerField(null=True, blank=True)
    disorder_id = models.ForeignKey(Disorders, on_delete=models.CASCADE)

    def __str__(self):
        return f"Session{self.session_id} - {self.disorder} "




class DemoRequested(models.Model):
    demo_request_id = models.BigIntegerField(unique=True)
    clinic_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    comments = models.CharField(max_length=255)
    contact_number = models.BigIntegerField(unique=True)
    #sales_person_id = models.BigIntegerField(null=True, blank=True) #need add mapping to sales person
    sales_person_id = models.ForeignKey('sales_person.Salesperson', on_delete=models.CASCADE)
    email = models.EmailField(unique=True) # check is it necessary if sales person has email field
    patients_count = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name

class PatientFiles(models.Model):
    file_id = models.BigIntegerField(unique=True)
    file_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=255)
    diagnosis_name = models.CharField(max_length=255)
    upload_timestamp = models.DateTimeField(null=False, blank=False)
    #user_id = models.BigIntegerField(null=False,blank=False)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)
    file_path = models.TextField(max_length=255)
    role = models.CharField(max_length=255)

    def __str__(self):
        return self.file_name


class TherapyData(models.Model):
    therapy_data_id = models.BigIntegerField(unique=True)
    objective = models.CharField(max_length=255,null=False,blank=False)
    patient_name = models.CharField(max_length=255,null=False,blank=False)
    submit_date = models.DateTimeField(null=False, blank=False)
    slp_name = models.CharField(max_length=255,null=False,blank=False)
    resources = models.CharField(max_length=255,null=False,blank=False)
    observations = models.CharField(max_length=255,null=False,blank=False)
    response_one = models.CharField(max_length=255)
    response_two = models.CharField(max_length=255)
    response_three = models.CharField(max_length=255)
    response_four = models.CharField(max_length=255)
    response_five = models.CharField(max_length=255)
    performance = models.CharField(max_length=255)
    condition = models.CharField(max_length=255)
    criterion = models.CharField(max_length=255)
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp_id = models.ForeignKey(Slps, on_delete=models.CASCADE)
    #user_id = models.BigIntegerField(null=True, blank=True)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.patient_name}-objective-{self.objective}"


class TreatmentData(models.Model):
    treatment_data_id = models.BigIntegerField(unique=True)
    interventions = models.CharField(max_length=255)
    diagnosis_name = models.CharField(max_length=255)
    therapist_name = models.CharField(max_length=255)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    date = models.DateTimeField(null=False, blank=False)
    #user_id = models.BigIntegerField(null=True, blank=True)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)
    #slp_id = models.IntegerField(null=True, blank=True)
    slp_id = models.ForeignKey('auth.slps', on_delete=models.CASCADE)
    goal = models.CharField(max_length=255)
    patient_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.patient_name}-{self.interventions}"
    

class AssessmentResults(models.Model):
    assessment_id = models.BigIntegerField(unique=True)
    #user_id = models.BigIntegerField(unique=True)
    user_id = models.ForeignKey('auth.Users', on_delete=models.CASCADE)
    #session_id = models.BigIntegerField()
    session_id = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    score = models.FloatField()
    #disorder_id = models.BigIntegerField()
    disorder_id = models.ForeignKey(Disorders, on_delete=models.CASCADE)
    sound_id_list = models.CharField(max_length=255) # need to map
    word_id_list = models.CharField(max_length=255) # need to map
    emotion = models.CharField(max_length=15000)
    assessment_date = models.DateTimeField(null=False, blank=False)
    quick_assessment = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.assessment_id}-{self.score}"














