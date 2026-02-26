from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height_cm = models.FloatField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    target_weight = models.FloatField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    streaks = models.IntegerField(default=0)
    streaks_from = models.DateTimeField(null=True, blank=True)
    
    def bmi(self, current_weight=None):
        weight = current_weight if current_weight else self.current_weight()
        height_m = self.height_cm / 100
        return round(weight / (height_m**2), 2)

    def current_weight(self):
        latest = self.weightlog_set.exclude(weight=None).order_by('-date').first()
        return latest.weight if latest and latest.weight else 0


class Settings(models.Model):
    GOAL_CHOICES = [
        ("lose", "Lose Weight"),
        ("gain", "Gain Weight"),
        ("maintain", "Maintain"),
    ]
    HT_UNIT_CHOICES = [
        ("cm", "Centimeters"),
        ("ft", "Feet"),
    ]
    WT_UNIT_CHOICES = [
        ("kg", "Kilograms"),
        ("lbs", "Pounds"),
    ]
    THEME_CHOICES = [
        ("light", "Light"), 
        ("dark", "Dark")
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # ---- Goal Strategy ----
    goal_type = models.CharField(max_length=10, choices=GOAL_CHOICES, default="lose")
    weekly_goal_rate = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)  # Target weight change per week (kg or lbs depending on unit).
    starting_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Captured automatically on first weight log.

    # ---- Units ----
    height_unit = models.CharField(max_length=5, choices=HT_UNIT_CHOICES, default="cm")
    weight_unit = models.CharField(max_length=5, choices=WT_UNIT_CHOICES, default="kg")

    # ---- Notifications ----
    daily_log = models.BooleanField(default=False)
    reminder_time = models.TimeField(null=True, blank=True)  # Default: 8 AM.
    weekly_summary = models.BooleanField(default=False)

    # ---- Appearance ----
    theme_family = models.CharField(max_length=50, default="classic")
    theme_mode = models.CharField(max_length=10, choices=THEME_CHOICES, default="dark")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Settings"


class WeightLog(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    weight = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    check_in = models.BooleanField(default=False)
    check_in_at = models.DateTimeField(null=True, blank=True)
    bmi = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.profile.user.username} - {self.weight}kg on {self.date}"


class Milestone(models.Model):
    CATEGORY_CHOICES = [
        ("weight_loss", "Weight Loss"),
        ("bmi", "BMI"),
        ("streak", "Streak"),
        ("target", "Target"),
        ("consistency", "Consistency"),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    value = models.IntegerField()

    def __str__(self):
        return self.title


class UserMilestone(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    achieved_on = models.DateField(auto_now_add=True)
    displayed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("profile", "milestone")

    def __str__(self):
        return f"{self.profile.user.username} - {self.milestone.title}"


class WeeklySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_summaries")
    week_start = models.DateField()
    week_end = models.DateField()

    avg_weight = models.FloatField()
    change_from_last_week = models.FloatField(default=0.0)
    bmi_status = models.CharField(max_length=20)

    streak = models.IntegerField(default=0)
    highlights = models.JSONField(default=dict, blank=True)

    has_checked = models.BooleanField(default=False)
    checked_on = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "week_start", "week_end")
        ordering = ["-week_start"]

    def __str__(self):
        return f"{self.user.username} - {self.week_start} to {self.week_end}"
