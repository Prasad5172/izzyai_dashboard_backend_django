from django.db import models
# Create your models here.
class Notification(models.Model):
    notification_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)
    notification_type = models.CharField(max_length=255)
    sections = models.CharField(max_length=255)

    def __str__(self):
        return f"Notification {self.notification_id} - User {self.user_id}"