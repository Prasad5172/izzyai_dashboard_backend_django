from django.contrib import admin
from .models import Notification
# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id', 'user_id', 'message', 'is_read', 'time')
    search_fields = ('user_id', 'message')
    list_filter = ('is_read', 'notification_type')
    
