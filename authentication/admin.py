from django.contrib import admin
from .models import Users, UserProfile, UserFiles, UserExercises, UsersInsurance

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'verified', 'created_account')
    search_fields = ('username', 'email')
    list_filter = ('verified', 'is_google_user', 'is_apple_user')
    ordering = ('-created_account',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'gender', 'patient_status', 'state', 'status')
    search_fields = ('full_name', 'patient_status', 'state')
    list_filter = ('gender', 'patient_status', 'status')

@admin.register(UserFiles)
class UserFilesAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_name', 'role', 'user_id', 'upload_timestamp')
    search_fields = ('file_name', 'role', 'user_id__username')
    list_filter = ('upload_timestamp',)
    ordering = ('-upload_timestamp',)

@admin.register(UserExercises)
class UserExercisesAdmin(admin.ModelAdmin):
    list_display = ('user_exercise_id', 'user_id', 'level_name', 'completion_status', 'exercise_date', 'score')
    search_fields = ('user_id__username', 'level_name', 'game_name')
    list_filter = ('completion_status', 'exercise_date')
    ordering = ('-exercise_date',)

@admin.register(UsersInsurance)
class UsersInsuranceAdmin(admin.ModelAdmin):
    list_display = ('insurance_id', 'user_id', 'insurance_provider', 'insurance_status', 'policy_number', 'claim_date')
    search_fields = ('user_id__username', 'insurance_provider', 'policy_number')
    list_filter = ('insurance_status', 'claim_date')
    ordering = ('-claim_date',)
