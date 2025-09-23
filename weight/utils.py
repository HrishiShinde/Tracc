from .models import Profile

def update_streaks(profile=None):
    profiles = Profile.objects.all()
    if profile:
        profiles = [profile]

    for profile in profiles:
        logs = profile.weightlog_set.filter(check_in=True).exclude(weight__isnull=True).order_by("check_in_at")
        prev_log = None
        streaks = 0
        streaks_from = None

        for log in logs:
            if prev_log:
                gap = (log.check_in_at.date() - prev_log.check_in_at.date()).days

                if gap == 1:
                    streaks += 1
                elif gap == 2 and prev_log.check_in_at.isoweekday() == 6:
                    streaks += 1
                else:
                    streaks = 1
                    streaks_from = log.check_in_at
            else:
                streaks = 1
                streaks_from = log.check_in_at

            prev_log = log

        profile.streaks = streaks
        if streaks_from:
            profile.streaks_from = streaks_from

        profile.save()

    return None


def calculate_bmi(weight, height):
    height_m = height / 100
    bmi = round(float(weight) / (height_m ** 2), 2)

    # BMI Styles and details.
    if bmi < 18.5:
        bmi_class = "Underweight"
        style = "bmi-underweight"
    elif bmi < 25:
        bmi_class = "Normal"
        style = "bmi-normal"
    elif bmi < 30:
        bmi_class = "Overweight"
        style = "bmi-overweight"
    else:
        bmi_class = "Obese"
        style = "bmi-obese"

    bmi_data = {
        "value": bmi,
        "class": bmi_class,
        "style": style
    }
    return bmi_data

class Insights:
    def __init__(self, logs):
        self.logs = logs
        self.circle_circumference = 2 * 3.1416 * 54  # ≈ 339.292

    def get_progress(self, profile):
        progress = None
        progress_offset = self.circle_circumference  # default if no progress
        latest_weight_log = self.logs.order_by('-date').first()
        latest_weight = latest_weight_log.weight if latest_weight_log else 0
        
        if profile.target_weight and latest_weight_log:
            start_weight = self.logs.first().weight if self.logs else latest_weight
            weight_diff = start_weight - profile.target_weight
            if weight_diff != 0:
                progress = round(((start_weight - latest_weight) / weight_diff) * 100)
                progress = max(0, min(progress, 100))  # Clamp between 0–100
                progress_offset = self.circle_circumference - (progress / 100) * self.circle_circumference

        return progress, progress_offset

    def get_line_data(self, recent_len=None):
        line_data = {}
        logs = self.logs[:recent_len] if recent_len else self.logs
        if self.logs:
            line_data = {
                "labels": [log.date.strftime('%d-%m-%Y') for log in logs],
                "weights": [log.weight for log in logs]
            }
        return line_data

    def get_daily_change(self):
        daily_changes = []
        previous_weight = None

        for log in self.logs:
            if log.weight is None:
                break
            date_str = log.date.strftime('%d-%m-%Y')
            if previous_weight is not None:
                change = round(log.weight - previous_weight, 1)
                daily_changes.append({
                    'date': date_str,
                    'change': change
                })
            previous_weight = log.weight
        return daily_changes

    def get_monthly_avg(self):
        """Returns dict with monthly average weight and bmi."""
        from collections import defaultdict
        import calendar

        monthly_data = defaultdict(list)
        for log in self.logs:
            if log.weight:
                month_key = log.date.strftime('%Y-%m')
                monthly_data[month_key].append((log.weight, log.bmi))

        monthly_avg = []
        for month, values in monthly_data.items():
            weights = [v[0] for v in values]
            bmis = [v[1] for v in values if v[1] is not None]
            avg_weight = round(sum(weights) / len(weights), 1)
            avg_bmi = round(sum(bmis) / len(bmis), 1) if bmis else None
            month_label = f"{calendar.month_abbr[int(month.split('-')[1])]} {month.split('-')[0]}"
            monthly_avg.append({
                "month": month_label,
                "avg_weight": avg_weight,
                "avg_bmi": avg_bmi
            })
        return monthly_avg

    def get_weight_zones(self):
        """Categorize logs into BMI zones."""
        zones = {
            "Underweight": 0,
            "Normal": 0,
            "Overweight": 0,
            "Obese": 0,
        }
        for log in self.logs:
            if log.bmi is None:
                continue
            if log.bmi < 18.5:
                zones["Underweight"] += 1
            elif 18.5 <= log.bmi < 25:
                zones["Normal"] += 1
            elif 25 <= log.bmi < 30:
                zones["Overweight"] += 1
            else:
                zones["Obese"] += 1

        weight_zones = [
            {
                "label": zone,
                "count": count,
                "color": f"--bmi-{zone.lower()}"
            }
            for zone, count in zones.items() 
        ]

        return weight_zones

    def get_fastest_drop(self):
        fastest = None
        previous_weight = None
        for log in self.logs:
            if log.weight is None:
                continue
            if previous_weight is not None:
                drop = round(log.weight - previous_weight, 1)
                if drop < 0:  # drop means negative change
                    if (fastest is None) or (drop < fastest["drop"]):
                        fastest = {
                            "date": log.date.strftime('%d-%m-%Y'),
                            "drop": drop
                        }
            previous_weight = log.weight
        return fastest
