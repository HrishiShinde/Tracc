from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db import connection
from django.db import transaction
from django.db.models import Exists, OuterRef, F, Value, Min
from django.db.models.functions import Replace
from django.core.management import call_command
from django.core.management.base import CommandError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import csv
import io
import random
import json
import secrets
from dateutil.parser import parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import Profile, Settings, WeightLog, UserMilestone, WeeklySummary, Milestone, PushSubscription
from .utils import Insights, calculate_bmi, update_streaks, check_for_achievements


def profile_localdate(profile):
    try:
        return timezone.localtime(timezone=ZoneInfo(profile.time_zone or "UTC")).date()
    except ZoneInfoNotFoundError:
        return timezone.localdate()


# ---------- Register ----------
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')
        
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)
        Settings.objects.create(user=user)
        messages.success(request, "Account created! Login now!")
        return redirect('login')
    
    return render(request, 'auth/register.html')


# ---------- Login ----------
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back.")
            return redirect('redirect_after_login')
        else:
            messages.error(request, "Invalid credentials!")
            return redirect('login')
    
    return render(request, 'auth/login.html')


# ---------- Logout ----------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Redirect ----------
def redirect_after_login(request):
    profile = request.user.profile
    if not profile.height_cm or not profile.target_weight:
        return redirect('get_more_data')
    return redirect('dashboard')


# ---------- Complete your Profile ----------
@login_required
def get_more_data(request):
    profile = request.user.profile
    settings = request.user.settings
    is_update = request.path.endswith('update-profile/')

    if request.method == 'POST':
        gender = request.POST.get('gender')
        height = request.POST.get('height_cm')
        current_weight = request.POST.get('current_weight')
        target_weight = request.POST.get('target_weight')
        dob = request.POST.get('dob')

        profile.gender = gender
        profile.height_cm = height
        profile.target_weight = target_weight
        profile.dob = dob if dob else None
        profile.save()

        # Save first weight log
        if current_weight and not is_update:
            WeightLog.objects.create(profile=profile, weight=current_weight)

            # Update starting weight in settings.
            settings.starting_weight = current_weight
            settings.save()

        if is_update:
            messages.success(request, "Profile details saved.")
            return redirect('settings')
        else:
            messages.success(request, "Profile completed.")
            return redirect('dashboard')

    return render(request, 'profile/get_more_data.html', {
        'profile': profile,
        'settings': settings,
        'is_update': is_update,
    })


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    profile = request.user.profile
    today = profile_localdate(profile)
    
    # Today's log for Clock In.
    today_log = profile.weightlog_set.filter(date=today).first()

    # Fetch logs.
    logs = profile.weightlog_set.exclude(weight__isnull=True).order_by('date')

    # Recent and Latest.
    recent_len = 5
    recent_logs = logs.order_by('-date')[:recent_len]
    latest_log = logs.last()
    latest_weight = latest_log.weight if latest_log else None

    # Call Insights class.
    insights = Insights(logs)

    # BMI and Progress.
    progress_data = insights.get_progress(profile)
    bmi_data = calculate_bmi(latest_weight, profile.height_cm) if latest_weight and profile.height_cm else {}

    # Graphs processing.
    line_data = insights.get_line_data(recent_len=recent_len)
    
    # latest summary for the logged-in user
    sum_line_data = {}
    summary = WeeklySummary.objects.filter(user=request.user, has_checked=False).order_by('-week_start').first()
    if summary:
        sum_line_data = insights.get_line_data(date_range=(summary.week_start, summary.week_end))

    context = {
        'profile': profile,
        'current_weight': latest_weight,
        'recent_logs': recent_logs, 
        'bmi_data': bmi_data,
        'progress_data': progress_data,
        'clock_in_time': today_log.check_in_at.isoformat() if today_log and today_log.check_in_at else None,
        'line_data': line_data,
        'summary': summary,
        'sum_line_data': sum_line_data
    }
    return render(request, 'pages/dashboard.html', context)

@login_required
def mark_summary_checked(request, pk):
    if request.method == "POST":
        summary = get_object_or_404(WeeklySummary, pk=pk, user=request.user)
        summary.has_checked = True
        summary.save(update_fields=["has_checked"])
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# ---------- Logs ----------
@login_required
def weightlog_list(request):
    logs = request.user.profile.weightlog_set.all()
    return render(request, 'logs/weightlog_list.html', {'logs': logs})


# ---------- Add or Edit Logs ----------
@login_required
def add_or_edit_weight_log(request, pk=None):
    profile = request.user.profile
    today = profile_localdate(profile)

    # POST check
    if request.method == 'POST':
        weight = request.POST.get('weight')
        notes = request.POST.get('notes', '')
        check_in = request.POST.get('check_in') == 'true'

        if pk:
            # Editing existing log
            log = get_object_or_404(profile.weightlog_set, pk=pk)
        else:
            # Add new log OR get today's log if check_in
            log, created = WeightLog.objects.get_or_create(profile=profile, date=today)

        # Update fields
        if weight:
            log.weight = weight
            log.bmi = calculate_bmi(weight, profile.height_cm).get("value")
        log.notes = notes

        # Today's clock in.
        if check_in:
            log.check_in = True
            log.check_in_at = timezone.now()

        # Save logs.
        log.save()

        # Update Streaks and check achievements.
        if log.check_in and log.weight:
            update_streaks(profile)
            check_for_achievements(profile)

        if check_in:
            messages.success(request, "You are checked in for today.")
        elif pk:
            messages.success(request, "Weight log updated.")
        else:
            messages.success(request, "Weight log saved.")
    
        if not weight:
            return redirect('dashboard')
        # The modal is a quick-add flow; return directly to the dashboard so a
        # successful save doesn't force another full logs-table render.
        return redirect('dashboard' if not pk else 'weightlog_list')


# ---------- Delete Logs ----------
@login_required
def delete_weight_log(request, pk):
    log = get_object_or_404(request.user.profile.weightlog_set, pk=pk)
    
    if request.method == 'POST':
        log.delete()
        messages.success(request, "Weight log deleted.")
        return redirect('weightlog_list')


# ---------- Settings ----------
@login_required
def settings_views(request):
    if request.method == "GET":
        profile = request.user.profile
        settings = request.user.settings if hasattr(request.user, 'settings') else None
        if not settings:
            settings = Settings.objects.create(user=request.user)

            logs = profile.weightlog_set.exclude(weight=None).order_by('date')
            settings.starting_weight = logs.first().weight if logs.exists() else None

            settings.save()

        return render(request, 'pages/settings.html', {
            'profile': profile,
            'settings': settings,
            'goal_choices': Settings.GOAL_CHOICES,
        })

    if request.method == "PUT":
        allowed_fields = [
            "height_unit",
            "weight_unit",
            "daily_log",
            "reminder_time",
            "weekly_summary",
            "goal_type",
            "weekly_goal_rate",
            "theme_family",
            "theme_mode",
        ]
        settings = request.user.settings

        try:
            data = json.loads(request.body)
        except (TypeError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        if not isinstance(data, dict) or not data:
            return JsonResponse({"error": "Provide settings to update."}, status=400)

        bool_fields = {"daily_log", "weekly_summary"}
        choices = {"height_unit": {"cm", "ft"}, "weight_unit": {"kg", "lbs"},
                   "goal_type": {value for value, _ in Settings.GOAL_CHOICES},
                   "theme_family": {"classic", "serene", "dusky", "midnight", "onyx-glow", "charcoal-canary", "gold-ember", "sunset-noir"},
                   "theme_mode": {value for value, _ in Settings.THEME_CHOICES}}

        for field, value in data.items():
            if field not in allowed_fields:
                return JsonResponse({"error": f"Invalid field: {field}"}, status=400)
            if field in bool_fields and not isinstance(value, bool):
                return JsonResponse({"error": f"{field} must be true or false."}, status=400)
            if field in choices and value not in choices[field]:
                return JsonResponse({"error": f"Invalid value for {field}."}, status=400)
            if field == "reminder_time" and value:
                try:
                    datetime.strptime(value, "%H:%M")
                except (TypeError, ValueError):
                    return JsonResponse({"error": "Reminder time must use HH:MM."}, status=400)
            if field == "weekly_goal_rate":
                if value in (None, ""):
                    value = None
                    if data.get("goal_type", settings.goal_type) == "maintain":
                        data[field] = None
                        continue
                    return JsonResponse({"error": "Enter a weekly target for gain or loss goals."}, status=400)
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    return JsonResponse({"error": "Weekly target must be a number."}, status=400)
                if not 0 < value <= 2:
                    return JsonResponse({"error": "Weekly target must be greater than 0 and at most 2."}, status=400)
                data[field] = value

        fields_to_save = set(data)
        for field, value in data.items():
            if field == "goal_type" and value == "maintain":
                settings.weekly_goal_rate = None
                fields_to_save.add("weekly_goal_rate")
            setattr(settings, field, value)
        settings.save(update_fields=[*fields_to_save, "updated_at"])

        return JsonResponse({"success": True})


@login_required
@require_POST
@transaction.atomic
def reset_user_data(request):
    """Delete a user's logs and derived progress while keeping their account/profile/settings."""
    profile = request.user.profile
    profile.weightlog_set.all().delete()
    UserMilestone.objects.filter(profile=profile).delete()
    WeeklySummary.objects.filter(user=request.user).delete()
    profile.streaks = 0
    profile.streaks_from = None
    profile.save(update_fields=["streaks", "streaks_from"])
    user_settings = getattr(request.user, "settings", None)
    if user_settings:
        user_settings.starting_weight = None
        user_settings.save(update_fields=["starting_weight", "updated_at"])
    return JsonResponse({"success": True})


@login_required
@require_POST
@transaction.atomic
def delete_account(request):
    """Delete the authenticated user's account and cascading app data."""
    user = request.user
    logout(request)
    user.delete()
    return JsonResponse({"success": True})


# ---------- Import Logs ----------
def generate_logs(profile, weight, start_date, end_date):
    log_count = (end_date - start_date).days - 1
    for i in range(log_count):
        date = start_date - timedelta(days=i+1)
        weight_variation = random.uniform(-0.8, 0.8)
        new_weight = round(weight + weight_variation, 1)
        bmi = calculate_bmi(new_weight, profile.height_cm).get("value")
        
        log, created = WeightLog.objects.get_or_create(
            profile=profile,
            date=date,
            defaults={"weight": weight, "notes": "Auto generated log.", "bmi": bmi}
        )
        weight = new_weight

    return created

@login_required
def import_logs(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]

        # Ensure it's CSV
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("settings")

        # Decode file
        data = csv_file.read().decode("utf-8")
        io_string = io.StringIO(data)
        reader = csv.DictReader(io_string)

        profile = request.user.profile
        imported_count = 0

        for row in reader:
            try:
                # Parse date
                prev_date, prev_weight = None
                date_obj = parse(row["Date"]).date()

                weight = float(row["Weight (kg)"]) if row["Weight (kg)"] else None
                notes = row.get("Notes/Mood", "")
                bmi = calculate_bmi(weight, profile.height_cm).get("value") if weight else None

                if prev_date and (prev_date - date_obj).days > 1:
                    generate_logs(profile, prev_weight, prev_date, date_obj)

                prev_date = date_obj
                prev_weight = weight

                # Avoid duplicates
                log, created = WeightLog.objects.get_or_create(
                    profile=profile,
                    date=date_obj,
                    defaults={"weight": weight, "notes": notes, "bmi": bmi}
                )

                if not created:
                    # If already exists, update
                    log.weight = weight
                    log.notes = notes
                    log.save()

                imported_count += 1

            except Exception as e:
                print(f"Row skipped due to error: {e}")
                continue

        # Update Streaks and check achievements.
        update_streaks(profile)
        check_for_achievements(profile)

        messages.success(request, f"{imported_count} logs imported successfully!")
        return redirect("settings")

    messages.error(request, "No file uploaded.")
    return redirect("settings")


# ---------- Export Logs ----------
@login_required
def export_logs(request):
    profile = request.user.profile
    logs = profile.weightlog_set.all().order_by("date")

    # Create the HttpResponse with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="weight_logs.csv"'

    writer = csv.writer(response)
    # Write header row (same as import)
    writer.writerow(["Date", "Weight (kg)", "Notes/Mood"])

    # Write logs
    for log in logs:
        writer.writerow([
            log.date.strftime("%d/%m/%y"),  # same format as import
            log.weight if log.weight is not None else "",
            log.notes or ""
        ])

    return response


# ---------- Analytics ----------
@login_required
def analytics(request):
    profile = request.user.profile
    logs = profile.weightlog_set.exclude(weight__isnull=True).order_by('date')

    insights = Insights(logs)

    # Graphs processing
    line_data = insights.get_line_data()
    daily_changes = insights.get_daily_change()
    monthly_avg = insights.get_monthly_avg()
    weight_zones = insights.get_weight_zones()

    # Compact cards use only values already stored in weight logs and settings.
    streaks = profile.streaks
    first_weight_log = logs.first()
    latest_weight_log = logs.last()
    user_settings = getattr(request.user, "settings", None)
    configured_start = getattr(user_settings, "starting_weight", None)
    starting_weight = configured_start if configured_start is not None else (first_weight_log.weight if first_weight_log else None)
    net_weight_change = round(float(latest_weight_log.weight) - float(starting_weight), 1) if latest_weight_log and starting_weight is not None else None
    net_weight_change_amount = round(abs(net_weight_change), 1) if net_weight_change is not None else None
    net_weight_change_direction = "gained" if net_weight_change and net_weight_change > 0 else ("lost" if net_weight_change and net_weight_change < 0 else "no change")
    lowest_weight = logs.aggregate(value=Min("weight"))["value"]
    checkin_count = profile.weightlog_set.filter(check_in=True).count()
    progress_data = insights.get_progress(profile)
    usermilestones = UserMilestone.objects.filter(profile=profile).last()

    milestones = None
    if usermilestones:
        milestones = usermilestones.milestone

    # Fetch all milestones and annotate if unlocked for this user
    all_milestones = Milestone.objects.annotate(
        is_unlocked=Exists(
            UserMilestone.objects.filter(
                milestone=OuterRef('pk'), 
                profile=profile
            )
        ),
        clean_category=Replace(F('category'), Value('_'), Value(' ')),
    ).order_by('category')

    # Calendar events.
    streak_events = []
    streak_dates = set()
    logs_by_date = {
        log.date.strftime("%Y-%m-%d"): log
        for log in logs
    }
    if profile.streaks and profile.streaks > 1 and profile.streaks_from:
        buffer = 0
        for i in range(profile.streaks):
            streak_day = profile.streaks_from + timedelta(days=i+buffer)

            log = logs_by_date.get(streak_day.strftime("%Y-%m-%d"))
            if not log or not log.weight or not log.check_in:
                buffer += 1

            streak_day = profile.streaks_from + timedelta(days=i+buffer)

            formatted_date = streak_day.strftime("%Y-%m-%d")
            streak_dates.add(formatted_date)
            streak_events.append({
                "type": "streak",
                "date": formatted_date
            })

    checkin_logs = logs.filter(check_in=True)
    checkins = [
        {
            "type": "checkin",
            "date": log.date.strftime("%Y-%m-%d")
        }
        for log in checkin_logs
        if log.date.strftime("%Y-%m-%d") not in streak_dates
    ]

    calendar_events = checkins + streak_events

    # latest summary for the logged-in user
    summary = WeeklySummary.objects.filter(user=request.user).order_by('-week_start').first()
    sum_line_data = {}
    if summary:
        sum_line_data = insights.get_line_data(date_range=(summary.week_start, summary.week_end))

    context = {
        "profile": profile,
        "line_data": line_data,
        "daily_changes": daily_changes,
        "monthly_avg": monthly_avg,
        "weight_zones": weight_zones,
        "streaks": streaks,
        "milestones": milestones,
        "all_milestones": all_milestones,
        "starting_weight": starting_weight,
        "net_weight_change": net_weight_change,
        "net_weight_change_amount": net_weight_change_amount,
        "net_weight_change_direction": net_weight_change_direction,
        "has_net_weight_change": net_weight_change is not None,
        "lowest_weight": lowest_weight,
        "has_lowest_weight": lowest_weight is not None,
        "checkin_count": checkin_count,
        "progress_data": progress_data,
        "calendar_events": calendar_events,
        'summary': summary,
        'sum_line_data': sum_line_data
    }
    return render(request, "pages/analytics.html", context)


# ---------- Health ----------
def health_view(request):
    db_status = False
    try:
        # Just test if DB responds
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        db_status = True
    except Exception:
        db_status = False

    context = {
        "db_status": db_status,
        "checked_at": timezone.now(),
    }
    return render(request, "pages/health.html", context)

def health_json(request):
    db_status = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        db_status = True
    except Exception:
        db_status = False

    return JsonResponse({
        "status": "ok" if db_status else "error",
        "database": db_status,
        "checked_at": timezone.now().isoformat(),
    })


def service_worker(request):
    """Serve the worker at the site root so it can control the installed PWA."""
    worker_path = settings.BASE_DIR / "static" / "js" / "service-worker.js"
    response = HttpResponse(worker_path.read_text(encoding="utf-8"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@login_required
def push_config(request):
    public_key = getattr(settings, "VAPID_PUBLIC_KEY", "")
    if not public_key:
        return JsonResponse({"error": "Push reminders are not configured on the server."}, status=503)
    return JsonResponse({"publicKey": public_key})


@login_required
@require_POST
def push_subscription(request):
    try:
        data = json.loads(request.body)
        subscription = data["subscription"]
        endpoint = subscription["endpoint"]
        keys = subscription["keys"]
        time_zone = data.get("timeZone", "UTC")
        ZoneInfo(time_zone)
        if (not isinstance(endpoint, str) or not endpoint.startswith("https://")
                or not isinstance(keys, dict) or not keys.get("p256dh") or not keys.get("auth")):
            raise ValueError
    except (TypeError, KeyError, ValueError, AttributeError, json.JSONDecodeError, ZoneInfoNotFoundError):
        return JsonResponse({"error": "Invalid push subscription."}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": request.user, "p256dh": keys["p256dh"], "auth": keys["auth"]},
    )
    profile = request.user.profile
    profile.time_zone = time_zone
    profile.save(update_fields=["time_zone"])
    return JsonResponse({"success": True})


@login_required
@require_POST
def push_unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (TypeError, KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid subscription endpoint."}, status=400)
    request.user.push_subscriptions.filter(endpoint=endpoint).delete()
    return JsonResponse({"success": True})


# ---------- Weekly summary ----------
@csrf_exempt
def run_weekly_summary(request):
    # simple token-based protection
    token = request.GET.get("token")
    if token != settings.CRON_SECRET:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    call_command("generate_weekly_summaries")
    return JsonResponse({"status": "success"})


@csrf_exempt
@require_GET
def run_daily_push_reminders(request):
    """HTTP entry point for an external cron service to send due reminders."""
    token = request.GET.get("token", "")
    cron_secret = settings.CRON_SECRET
    if not cron_secret or cron_secret == "dev-secret-key":
        return JsonResponse({"error": "Cron secret is not configured."}, status=503)
    if not secrets.compare_digest(token, cron_secret):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        call_command("send_daily_push_reminders")
    except CommandError:
        return JsonResponse({"error": "Reminder job is not configured."}, status=503)
    return JsonResponse({"status": "success"})
