from django.db import models

class Users(models.Model):
    username = models.CharField(max_length=255, unique=True)
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
    email = models.EmailField(unique=True)
    user_id = models.BigIntegerField(unique=True)
    created_account = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user_id = models.OneToOneField(Users, on_delete=models.CASCADE)
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
    #slp_id = models.BigIntegerField(null=True, blank=True)
    slp_id = models.ForeignKey('slp.Slps', on_delete=models.CASCADE)
    avatar_id = models.IntegerField(null=True, blank=True)
    face_authentication_state = models.BooleanField(default=False)
    contact_number = models.BigIntegerField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    age = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.full_name


class UserFiles(models.Model):
    file_id = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=255)
    file_path = models.TextField()
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)

    def __str__(self):
        return self.file_name


class UserExercises(models.Model):
    total_questions = models.IntegerField()
    user_exercise_id = models.IntegerField(unique=True)
    level_name = models.CharField(max_length=255)
    world_id = models.IntegerField()
    sound_id = models.IntegerField()
    #session_id = models.IntegerField()
    session_id = models.ForeignKey('clinc.Session', on_delete=models.CASCADE)
    sound_id_list = models.CharField(max_length=255)
    #disorder_id = models.IntegerField()
    disorder_id = models.ForeignKey('clinc.Disorders', on_delete=models.CASCADE)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    completion_status = models.CharField(max_length=255)
    exercise_date = models.DateTimeField()
    score = models.FloatField()
    emotion = models.CharField(max_length=255)
    completed_questions = models.IntegerField()
    sentence_id = models.IntegerField()
    game_name = models.CharField(max_length=255)
    world_id_list = models.CharField(max_length=255)

    def __str__(self):
        return f"Exercise {self.user_exercise_id} - {self.user.username}"


class UsersInsurance(models.Model):
    cpt_number = models.CharField(max_length=255)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE)
    insurance_provider = models.CharField(max_length=255)
    insurance_status = models.CharField(max_length=255)
    policy_number = models.BigIntegerField()
    insurance_id = models.BigIntegerField(unique=True)
    claim_date = models.DateField()

    def __str__(self):
        return f"Insurance {self.insurance_provider} - {self.user.username}"
