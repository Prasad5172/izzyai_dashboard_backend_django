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
    email = models.EmailField(unique=True)
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    warning_count = models.IntegerField(default=0)
    is_apple_user = models.BooleanField(default=False)
    is_google_user = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
    is_otp_verified = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    source = models.CharField(max_length=255, null=True, blank=True)
    otp_for_signup = models.CharField(max_length=255, null=True, blank=True)
    is_setup_profile = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    user_type = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255)
    created_account = models.DateTimeField(auto_now_add=True)

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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    clinic_id = models.BigIntegerField(null=True, blank=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    checkbox_values = models.TextField(null=True, blank=True)
    initial_question_logic = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=255)
    patient_status = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    profile_id = models.IntegerField(unique=True)
    slp_id = models.ForeignKey('slp.Slps', on_delete=models.CASCADE)
    avatar_id = models.IntegerField(null=True, blank=True)
    face_authentication_state = models.BooleanField(default=False)
    contact_number = models.BigIntegerField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    age = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.full_name


# User Files Model
class UserFiles(models.Model):
    file_id = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=255)
    file_path = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)

    def __str__(self):
        return self.file_name


# User Exercises Model
class UserExercises(models.Model):
    total_questions = models.IntegerField()
    user_exercise_id = models.IntegerField(unique=True)
    level_name = models.CharField(max_length=255)
    world_id = models.IntegerField()
    sound_id = models.IntegerField()
    session_id = models.ForeignKey('clinic.Sessions', on_delete=models.CASCADE)
    sound_id_list = models.CharField(max_length=255)
    disorder_id = models.ForeignKey('clinic.Disorders', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    completion_status = models.CharField(max_length=255)
    exercise_date = models.DateTimeField()
    score = models.FloatField()
    emotion = models.CharField(max_length=255)
    completed_questions = models.IntegerField()
    sentence_id = models.IntegerField()
    game_name = models.CharField(max_length=255)
    world_id_list = models.CharField(max_length=255)

    def __str__(self):
        return f"Exercise {self.user_exercise_id} - {self.user.email}"


# Users Insurance Model
class UsersInsurance(models.Model):
    cpt_number = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    insurance_provider = models.CharField(max_length=255)
    insurance_status = models.CharField(max_length=255)
    policy_number = models.BigIntegerField()
    insurance_id = models.BigIntegerField(unique=True)
    claim_date = models.DateField()

    def __str__(self):
        return f"Insurance {self.insurance_provider} - {self.user.email}"
