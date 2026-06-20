from django.db import models
from django.contrib.auth.models import User

class Mood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="moods")
    mood = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} ({self.timestamp})"
