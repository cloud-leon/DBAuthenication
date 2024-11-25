from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, unique=True)  # Unique identifier for the device
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    last_active_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.device_name} - {self.user.username}"
