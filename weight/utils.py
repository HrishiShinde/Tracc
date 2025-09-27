from .models import Milestone, UserMilestone, Profile, WeightLog


def _assign_milestone(profile, milestone_title):
    milestone = Milestone.objects.get(title=milestone_title)
    obj, created = UserMilestone.objects.get_or_create(profile=profile, milestone=milestone)
    if created:
        print(f"🏅 {profile.user.username} achieved: {milestone.title}")

def check_for_achievements(profile):
    logs = profile.weightlog_set.exclude(weight__isnull=True).order_by("date")
    streaks = profile.streaks
    
    # Streak milestones
    for milestone in Milestone.objects.filter(category="streak"):
        if streaks == milestone.value:
            _assign_milestone(profile, milestone.title)

    for log in logs:
        current_weight = log.weight
        current_bmi = log.bmi

        # Weight loss milestones
        starting_weight = logs.first().weight
        weight_lost = starting_weight - current_weight
        for milestone in Milestone.objects.filter(category="weight_loss"):
            if weight_lost >= milestone.value:
                _assign_milestone(profile, milestone.title)

        # BMI milestones
        for milestone in Milestone.objects.filter(category="bmi_target"):
            if current_bmi <= milestone.value:
                _assign_milestone(profile, milestone.title)

        # TODO: Add other milestone types here.


def seed_milestones():
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
            "category": "bmi",
            "value": 0,
        },
        {
            "title": "Overweight Slayer",
            "description": "Moved from Overweight to Normal BMI category 🥳",
            "category": "bmi",
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
            "category": "target_weight",
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

    # Seed milestones
    for milestone_data in MILESTONES:
        milestone, created = Milestone.objects.get_or_create(
            title=milestone_data["title"],
            defaults=milestone_data,
        )
        if created:
            print(f"🌱 Created milestone: {milestone.title}")
        else:
            print(f"⚠️ Already exists: {milestone.title}")

    # Assign milestones to users
    for profile in Profile.objects.all():
        check_for_achievements(profile)


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


def update_all_bmis():
    # Inform when the process starts
    print("🚀 Starting BMI update of all weight logs...")
    
    # Fetch all WeightLog records where weight is not null
    logs = WeightLog.objects.exclude(weight__isnull=True)
    total_logs = logs.count()
    print(f"ℹ️  Found {total_logs} weight logs to update.")

    for log in logs:
        height = log.profile.height_cm
        weight = log.weight

        # Print current processing log
        print(f"🔧 Processing log ID: {log.id}, Weight: {weight} kg, Height: {height} cm")

        # Calculate BMI using utility function
        bmi_data = calculate_bmi(weight, height)
        log.bmi = bmi_data.get("value")

        print(f"✅ Updated BMI for log ID {log.id}: {bmi_data}")

        updated_count += 1

    # Perform bulk update for performance
    WeightLog.objects.bulk_update(logs, ['bmi'], batch_size=100)

    # Final message after update is complete
    print(f"🎯 Successfully updated BMI for {updated_count} logs.")


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
