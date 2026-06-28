from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    INTEREST_CHOICES = [
        ('SPIRITUAL', 'Spiritual Growth & Ministry'),
        ('CAREER', 'Career & Professional Development'),
        ('LEADERSHIP', 'Leadership & Governance'),
        ('RELATIONSHIP', 'Family & Relationship'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    interests = models.CharField(max_length=20, choices=INTEREST_CHOICES)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
