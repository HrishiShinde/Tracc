from django.core.management.base import BaseCommand
from weight.models import Milestone, UserMilestone, Profile 
from django.utils.timezone import now

MILESTONES = [
    # 📉 Weight Loss
    {
        "title": "First Step",
        "description": "Logged your first weight entry 🎉",
        "category": "weight_loss",
        "value": 0,
    },
    {
        "title": "First 2 Kg Down",
        "description": "Lost your first 2 kilograms 🎉",
        "category": "weight_loss",
        "value": 2,
    },
    {
        "title": "5Kg Down",
        "description": "Lost 5 kilograms 🏆",
        "category": "weight_loss",
        "value": 5,
    },
    {
        "title": "10Kg Warrior",
        "description": "Lost 10 kilograms 🔥",
        "category": "weight_loss",
        "value": 10,
    },
    {
        "title": "20Kg Beast Mode",
        "description": "Lost 20 kilograms 💪",
        "category": "weight_loss",
        "value": 20,
    },

    # ⚖️ BMI Based
    {
        "title": "Normal BMI Ninja",
        "description": "Entered the normal BMI range (18.5-24.9) ✨",
        "category": "bmi",
        "value": 24.9,
    },
    {
        "title": "Obese Crusher",
        "description": "Moved from Obese to Overweight category 👏",
        "category": "bmi_transition",
        "value": 0,
    },
    {
        "title": "Overweight Slayer",
        "description": "Moved from Overweight to Normal BMI category 🥳",
        "category": "bmi_transition",
        "value": 0,
    },

    # 🎯 Target
    {
        "title": "Bullseye!",
        "description": "Reached your target weight 🎯",
        "category": "target_weight",
        "value": 1,
    },
    {
        "title": "Target Maintainer",
        "description": "Maintained your target weight for 30 days ✅",
        "category": "target_maintain",
        "value": 30,
    },

    # 🔥 Streaks
    {
        "title": "7-Day Hustler",
        "description": "Logged weight for 7 days in a row 🔥",
        "category": "streak",
        "value": 7,
    },
    {
        "title": "30-Day Champ",
        "description": "Logged weight for 30 days in a row 🐉",
        "category": "streak",
        "value": 30,
    },
    {
        "title": "100-Day Legend",
        "description": "Logged weight for 100 days in a row 💯",
        "category": "streak",
        "value": 100,
    },

    # 📊 Consistency
    {
        "title": "Deca Logger",
        "description": "Logged your weight 10 times 📊",
        "category": "log_count",
        "value": 10,
    },
    {
        "title": "50 Logs Hero",
        "description": "Logged your weight 50 times 📈",
        "category": "log_count",
        "value": 50,
    },
    {
        "title": "Consistency King/Queen",
        "description": "Logged your weight 100 times 🏅",
        "category": "log_count",
        "value": 100,
    },
]

class Command(BaseCommand):
    help = "Seed milestones and assign already achieved ones to users"

    def handle(self, *args, **options):
        # Seed milestones
        for milestone_data in MILESTONES:
            milestone, created = Milestone.objects.get_or_create(
                title=milestone_data["title"],
                defaults=milestone_data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created milestone: {milestone.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Milestone already exists: {milestone.title}"))

        # Assign milestones to users
        for profile in Profile.objects.all():
            logs = profile.weightlog_set.exclude(weight__isnull=True).order_by("date")
            if not logs.exists():
                continue

            starting_weight = logs.first().weight
            latest_weight = logs.last().weight
            latest_bmi = logs.last().bmi

            # First Step
            self._assign_milestone(profile, "First Step")

            # Weight Loss Milestones
            weight_lost = starting_weight - latest_weight
            for milestone in Milestone.objects.filter(category="weight_loss"):
                if weight_lost >= milestone.value:
                    self._assign_milestone(profile, milestone.title)

            # BMI Target
            for milestone in Milestone.objects.filter(category="bmi_target"):
                if latest_bmi <= milestone.value:
                    self._assign_milestone(profile, milestone.title)

            # Streak (simplest: just check longest streak length)
            # streak_length = self._calculate_streak(logs)
            # for milestone in Milestone.objects.filter(category="streak"):
            #     if streak_length >= milestone.value:
            #         self._assign_milestone(profile, milestone.title)

    def _assign_milestone(self, profile, milestone_title):
        milestone = Milestone.objects.get(title=milestone_title)
        obj, created = UserMilestone.objects.get_or_create(profile=profile, milestone=milestone)
        if created:
            print(f"✅ {profile.user.username} achieved: {milestone.title}")

    # def _calculate_streak(self, logs):
    #     streak = longest = 1
    #     prev_date = logs.first().date

    #     for log in logs[1:]:
    #         if (log.date - prev_date).days == 1:
    #             streak += 1
    #             longest = max(longest, streak)
    #         else:
    #             streak = 1
    #         prev_date = log.date
    #     return longest