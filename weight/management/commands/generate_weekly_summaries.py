from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from weight.models import WeightLog, WeeklySummary, Profile

class Command(BaseCommand):
    help = "Generates weekly summaries for all users"

    def generate_highlights(self, logs):
        highlights = {}

        # logs count
        highlights['logs'] = f"You logged weight {len(logs)} times this week."

        # streak calculation
        streak = 0
        max_streak = 0
        last_date = None
        for log in logs.order_by('date'):
            if last_date and (log.date - last_date).days == 1:
                streak += 1
            else:
                streak = 1
            if streak > max_streak:
                max_streak = streak
            last_date = log.date
        highlights['streak'] = f"Your longest streak: {max_streak} days in a row."

        # gain/loss detection
        gains = []
        logs_list = list(logs.order_by('date'))
        for i in range(1, len(logs_list)):
            diff = logs_list[i].weight - logs_list[i-1].weight
            if diff > 0:
                gains.append(f"You gained {diff} kg on {logs_list[i].date.strftime('%A')}")

        highlights['gain'] = ', '.join(gains) if gains else "No gains this week!"

        return highlights, max_streak


    def handle(self, *args, **kwargs):
        try:
            today = timezone.now().date()
            end_date = today - timedelta(days=today.weekday() + 1)  # last Sunday
            start_date = end_date - timedelta(days=6)  # previous Monday
            
            self.stdout.write(f"Generating summaries for week: {start_date} → {end_date}")

            profiles = Profile.objects.all()
            for profile in profiles:
                logs = WeightLog.objects.filter(profile=profile, date__range=(start_date, end_date)).order_by('date')
                if not logs.exists():
                    self.stdout.write(f"⏭️ Skipped {profile.user.username} — no logs found.")
                    continue

                weights = [log.weight for log in logs if log.weight]
                if weights:
                    avg_weight = sum(weights) / len(weights)

                    # find previous week’s data (for change calculation)
                    prev_start = start_date - timedelta(days=7)
                    prev_end = end_date - timedelta(days=7)
                    prev_logs = WeightLog.objects.filter(profile=profile, date__range=(prev_start, prev_end))
                    prev_avg = sum([log.weight for log in prev_logs]) / len(prev_logs) if prev_logs.exists() else avg_weight

                    weight_change = round(avg_weight - prev_avg, 2)
                    bmi = logs.last().bmi if hasattr(logs.last(), 'bmi') else None  # optional if your model has BMI
                    bmi_status = None
                    if bmi:
                        if bmi < 18.5: bmi_status = "Underweight"
                        elif 18.5 <= bmi < 24.9: bmi_status = "Normal"
                        elif 25 <= bmi < 29.9: bmi_status = "Overweight"
                        else: bmi_status = "Obese"

                    # highlights
                    highlights, streak = self.generate_highlights(logs)

                    WeeklySummary.objects.update_or_create(
                        user=profile.user,
                        week_start=start_date,
                        week_end=end_date,
                        defaults={
                            "avg_weight": avg_weight,
                            "change_from_last_week": weight_change,
                            "bmi_status": bmi_status,
                            "highlights": highlights,
                            "streak": streak,
                            "has_checked": False
                        }
                    )

                    self.stdout.write(f"Summary generated for {profile.user.username}")
        except Exception as e:
            import traceback
            self.stdout.write(f"Error occured while generating summaries: {e}")
            traceback.print_exc()

        self.stdout.write(self.style.SUCCESS("Weekly summary generation complete!"))
