from django.contrib import admin
from .models import Users, UserProfile, UserFiles, UserExercises, UsersInsurance

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'verified', 'created_account')
    search_fields = ('username', 'email', 'user_type')
    list_filter = ('is_google_user', 'is_apple_user', 'verified', 'is_otp_verified')
    ordering = ('-created_account',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'clinic_id', 'status', 'contact_number')
    search_fields = ('full_name', 'user__username', 'clinic_id')
    list_filter = ('status', 'patient_status', 'gender')

@admin.register(UserFiles)
class UserFilesAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'role', 'user', 'upload_timestamp')
    search_fields = ('file_name', 'user__username', 'role')
    list_filter = ('role',)
    ordering = ('-upload_timestamp',)

@admin.register(UserExercises)
class UserExercisesAdmin(admin.ModelAdmin):
    list_display = ('user_exercise_id', 'user', 'level_name', 'world_id', 'completion_status', 'exercise_date')
    search_fields = ('user_exercise_id', 'user__username', 'level_name')
    list_filter = ('completion_status', 'world_id')
    ordering = ('-exercise_date',)

@admin.register(UsersInsurance)
class UsersInsuranceAdmin(admin.ModelAdmin):
    list_display = ('insurance_provider', 'user', 'insurance_status', 'policy_number', 'claim_date')
    search_fields = ('insurance_provider', 'user__username', 'policy_number')
    list_filter = ('insurance_status',)
    ordering = ('-claim_date',)
