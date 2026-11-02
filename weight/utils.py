from .models import Milestone, UserMilestone, Profile, WeightLog
from datetime import timedelta
import pandas as pd


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

    first_log = logs.only("weight").first()
    latest_log = logs.only("weight", "bmi").last()
    if not first_log or not latest_log:
        return

    weight_lost = first_log.weight - latest_log.weight
    for milestone in Milestone.objects.filter(category="weight_loss"):
        if weight_lost >= milestone.value:
            _assign_milestone(profile, milestone.title)

    if latest_log.bmi is not None:
        for milestone in Milestone.objects.filter(category="bmi_target"):
            if latest_log.bmi <= milestone.value:
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
    if weight is None or height is None or float(height) <= 0:
        return {}
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

    updated_count = 0
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
        logs = profile.weightlog_set.filter(check_in=True).exclude(
            weight__isnull=True
        ).exclude(check_in_at=None).order_by("-date").only("date", "check_in_at")
        prev_log = None
        streaks = 0
        streaks_from = None

        for log in logs:
            if prev_log:
                gap = (prev_log.date - log.date).days
                if gap > 2:
                    break
                streaks += 1
                streaks_from = log.check_in_at
            else:
                streaks = 1
                streaks_from = log.check_in_at

            prev_log = log

        profile.streaks = streaks
        if streaks_from:
            profile.streaks_from = streaks_from

        profile.save(update_fields=["streaks", "streaks_from"])

    return None


class Insights:
    def __init__(self, logs):
        self.logs = logs
        self.circle_circumference = 2 * 3.1416 * 54  # ≈ 339.292

    def get_progress(self, profile):
        result = {
            "percentage": None,
            "offset": self.circle_circumference,
            "status": "Add a target weight",
            "detail": "Set a target weight to track your goal.",
            "detail_amount": None,
            "detail_label": "",
            "has_detail_amount": False,
            "has_percentage": False,
            "is_maintaining": False,
        }
        target_weight = profile.target_weight
        latest_log = self.logs.last()
        if target_weight is None:
            return result
        if float(target_weight) <= 0:
            result.update(status="Check your target", detail="Target weight must be greater than zero.")
            return result
        if latest_log is None:
            result.update(status="Log a weight to begin", detail="Your progress will appear after your first weight log.")
            return result

        target_weight = float(target_weight)
        current_weight = float(latest_log.weight)
        settings = getattr(profile.user, "settings", None)
        goal_type = getattr(settings, "goal_type", "lose")

        if goal_type == "maintain":
            # Keep maintenance distinct from a directional completion percentage.
            tolerance = target_weight * 0.01
            difference = abs(current_weight - target_weight)
            in_range = difference <= tolerance
            result.update(
                is_maintaining=True,
                status="On target" if in_range else "Outside target range",
                detail="Your weight is within 1% of your target." if in_range else "Your weight is outside the 1% maintenance range.",
                detail_amount=None if in_range else round(difference, 1),
                detail_label="above target" if current_weight > target_weight else "below target",
                has_detail_amount=not in_range,
            )
            return result

        configured_start = getattr(settings, "starting_weight", None)
        first_log = self.logs.first()
        start_weight = float(configured_start) if configured_start is not None else (float(first_log.weight) if first_log else None)
        if start_weight is None:
            result.update(status="Add a starting weight", detail="A starting weight is needed to measure progress.")
            return result

        is_loss = goal_type == "lose"
        goal_distance = start_weight - target_weight if is_loss else target_weight - start_weight
        if goal_distance <= 0:
            result.update(
                status="Check your target",
                detail="For this goal, your target must be below your starting weight." if is_loss else "For this goal, your target must be above your starting weight.",
            )
            return result

        change_toward_goal = start_weight - current_weight if is_loss else current_weight - start_weight
        percentage = max(0, min(round((change_toward_goal / goal_distance) * 100), 100))
        result["percentage"] = percentage
        result["has_percentage"] = True
        result["offset"] = self.circle_circumference - (percentage / 100) * self.circle_circumference
        if change_toward_goal < 0:
            result.update(
                status="Moving away from goal",
                detail_amount=round(abs(current_weight - start_weight), 1),
                detail_label="above your starting weight" if is_loss else "below your starting weight",
                has_detail_amount=True,
            )
        elif change_toward_goal == 0:
            result.update(status="No change yet", detail="Your weight is still at its starting point.")
        elif percentage == 100:
            result.update(status="Goal reached", detail="You have reached your target weight.")
        else:
            result.update(
                status="On track",
                detail_amount=round(abs(current_weight - start_weight), 1),
                detail_label="down from your starting weight" if is_loss else "up from your starting weight",
                has_detail_amount=True,
            )
        return result

    def get_line_data(self, recent_len=None, date_range=None):
        if recent_len:
            # Recent-log charts should plot actual entries only. Reindexing these
            # dates to a daily range makes a five-entry chart show many empty days.
            recent_logs = list(self.logs.order_by('-date')[:recent_len])
            recent_logs.reverse()
            return {
                "labels": [log.date.strftime('%d-%m-%Y') for log in recent_logs],
                "weights": [log.weight for log in recent_logs],
            }
        elif date_range:
            start_date, end_date = date_range
            logs = self.logs.filter(date__range=(start_date, end_date))
        else: 
            logs = self.logs

        if not logs:
            return {"labels": [], "weights": []}

        # Convert to DataFrame
        data = {
            "date": [log.date for log in logs],
            "weight": [log.weight for log in logs]
        }
        df = pd.DataFrame(data)

        # Set date as index
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        # Determine full range
        if date_range:
            start_date, end_date = date_range
        else:
            start_date, end_date = df.index.min(), df.index.max()

        # Create full date range (inclusive)
        full_range = pd.date_range(start=start_date, end=end_date, freq='D')
        df = df.reindex(full_range)

        # Forward fill missing weights
        df["weight"] = df["weight"].ffill().bfill()

        # Format output
        line_data = {
            "labels": [d.strftime('%d-%m-%Y') for d in df.index],
            "weights": df["weight"].tolist()
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
