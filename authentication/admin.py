from django.contrib import admin
from .models import CustomUser, UserProfile, UserFiles, UserExercises, UsersInsurance
from django.contrib.auth.admin import UserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('user_id', 'email', 'verified', 'created_account')
    search_fields = ('email',)
    list_filter = ('verified', 'is_google_user', 'is_apple_user')
    ordering = ('-created_account',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('warning_count', 'user_type', 'verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'created_account')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gender', 'patient_status', 'state', 'status')
    search_fields = ('full_name', 'patient_status', 'state')
    list_filter = ('gender', 'patient_status', 'status')

@admin.register(UserFiles)
class UserFilesAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_name', 'role', 'user', 'upload_timestamp')
    search_fields = ('file_name', 'role', 'user__email')
    list_filter = ('upload_timestamp',)
    ordering = ('-upload_timestamp',)

@admin.register(UserExercises)
class UserExercisesAdmin(admin.ModelAdmin):
    list_display = ('user_exercise_id', 'user', 'level_name', 'completion_status', 'exercise_date', 'score')
    search_fields = ('user__email', 'level_name', 'game_name')
    list_filter = ('completion_status', 'exercise_date')
    ordering = ('-exercise_date',)

@admin.register(UsersInsurance)
class UsersInsuranceAdmin(admin.ModelAdmin):
    list_display = ('insurance_id', 'user', 'insurance_provider', 'insurance_status', 'policy_number', 'claim_date')
    search_fields = ('user__email', 'insurance_provider', 'policy_number')
    list_filter = ('insurance_status', 'claim_date')
    ordering = ('-claim_date',)
