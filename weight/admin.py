from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Profile)
admin.site.register(WeightLog)
admin.site.register(Milestone)
admin.site.register(UserMilestone)