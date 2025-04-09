from django.db import models
from django.contrib.auth.models import User

class AdminPreference(models.Model):
    """Model for storing admin-specific preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_preferences')
    show_completed_jobs = models.BooleanField(default=False)
    items_per_page = models.IntegerField(default=10)
    default_view = models.CharField(max_length=20, default='pending')
    
    def __str__(self):
        return f"Preferences for {self.user.username}"