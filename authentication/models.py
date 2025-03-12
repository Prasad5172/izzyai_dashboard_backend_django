from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import uuid 
# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


# Custom User Model
class CustomUser(AbstractUser):
    user_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    warning_count = models.IntegerField(default=0)
    is_apple_user = models.BooleanField(default=False)
    is_google_user = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
    is_otp_verified = models.BooleanField(default=False)  # remove(redundant)
    verified = models.BooleanField(default=False)
    source = models.CharField(max_length=255, null=True, blank=True)
    otp_for_signup = models.CharField(max_length=255, null=True, blank=True)  #remove(redundant)
    is_setup_profile = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    user_type = models.CharField(max_length=255)
    created_account = models.DateTimeField(auto_now_add=True)
    username = models.CharField(unique=True,max_length=255)
    expiration_date = models.DateTimeField(null=True, blank=True), # this is for demo request users
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",
        blank=True
    )
    objects = CustomUserManager()
    def __str__(self):
        return self.username


# User Profile Model
class UserProfile(models.Model):
    profile_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="user_profiles")
    clinic = models.ForeignKey('clinic.Clinics', on_delete=models.SET_NULL, null=True, blank=True, related_name="user_profiles")
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    checkbox_values = models.TextField(null=True, blank=True)
    initial_question_logic = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=255)
    patient_status = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    status = models.CharField(max_length=255) #this is redundant for patient_status
    slp = models.ForeignKey('slp.Slps', on_delete=models.SET_NULL,null=True, blank=True, related_name="user_profiles")
    avatar_id = models.IntegerField(null=True, blank=True)
    face_authentication_state = models.BooleanField(default=False)
    contact_number = models.BigIntegerField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    profilephoto = models.TextField(null=True, blank=True)
    age = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.full_name


# User Files Model
class UserFiles(models.Model):
    file_id = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=255)
    file_path = models.TextField(null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)

    def __str__(self):
        return self.file_name


# User Exercises Model
class UserExercises(models.Model):
    user_exercise_id = models.BigAutoField(primary_key=True)
    total_questions = models.IntegerField(default=0)
    level_name = models.CharField(max_length=255)
    world_id = models.IntegerField(null=True, blank=True)
    sound_id = models.IntegerField(null=True, blank=True)
    session = models.ForeignKey('clinic.Sessions', on_delete=models.CASCADE,null=True, blank=True)
    sound_id_list = models.CharField(max_length=255)
    disorder = models.ForeignKey('clinic.Disorders', on_delete=models.CASCADE,null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    completion_status = models.CharField(max_length=255)
    exercise_date = models.DateTimeField(null=True,blank=True)
    score = models.FloatField(default=0)
    emotion = models.CharField(max_length=15000)
    completed_questions = models.IntegerField(default=0)
    sentence_id = models.IntegerField(null=True, blank=True)
    game_name = models.CharField(max_length=255)
    world_id_list = models.CharField(max_length=255)

    def __str__(self):
        return f"Exercise {self.user_exercise_id} - {self.user.email}"


# Users Insurance Model
class UsersInsurance(models.Model):
    insurance_id = models.BigAutoField(primary_key=True)
    cpt_number = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    insurance_provider = models.CharField(max_length=255)
    insurance_status = models.CharField(max_length=255)
    policy_number = models.BigIntegerField(null=True, blank=True)
    claim_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Insurance {self.insurance_provider} - {self.user.email}"
