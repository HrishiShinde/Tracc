from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height_cm = models.FloatField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    target_weight = models.FloatField(blank=True, null=True)
    
    def bmi(self, current_weight=None):
        weight = current_weight if current_weight else self.current_weight()
        height_m = self.height_cm / 100
        return round(weight / (height_m**2), 2)

    def current_weight(self):
        latest = self.weightlog_set.exclude(weight=None).order_by('-date').first()
        return latest.weight if latest and latest.weight else 0

class WeightLog(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    weight = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    check_in = models.BooleanField(default=False)
    check_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.profile.user.username} - {self.weight}kg on {self.date}"
