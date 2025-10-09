from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import connection
from django.db.models import Exists, OuterRef
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import csv
import io
from datetime import datetime, timedelta
import random

from .models import Profile, WeightLog, UserMilestone, WeeklySummary, Milestone
from .utils import Insights, calculate_bmi, update_streaks, check_for_achievements


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

        if is_update:
            return redirect('settings')
        else:
            return redirect('dashboard')

    return render(request, 'profile/get_more_data.html', {'profile': profile, 'is_update':is_update})


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    profile = request.user.profile
    today = timezone.localdate()
    
    # Today's log for Clock In.
    today_log = profile.weightlog_set.filter(date=today).first()

    # Fetch logs.
    logs = profile.weightlog_set.exclude(weight__isnull=True).order_by('date')

    # Recent and Latest.
    recent_len = 5
    recent_logs = logs.order_by('-date')[:recent_len]
    latest_weight = logs.last().weight

    # Call Insights class.
    insights = Insights(logs)

    # BMI and Progress.
    progress, progress_offset = insights.get_progress(profile)
    bmi_data = calculate_bmi(latest_weight, profile.height_cm)

    # Graphs processing.
    line_data = insights.get_line_data(recent_len)
    
    # latest summary for the logged-in user
    summary = WeeklySummary.objects.filter(user=request.user, has_checked=False).order_by('-week_start').first()
    sum_line_data = {}
    if summary:
        sum_line_data = insights.get_line_data(date_range=(summary.week_start, summary.week_end))

    context = {
        'profile': profile,
        'recent_logs': recent_logs, 
        'bmi_data': bmi_data,
        'progress': progress,
        'progress_offset': progress_offset,
        'clock_in_time': today_log.check_in_at.isoformat() if today_log and today_log.check_in_at else None,
        'line_data': line_data,
        'summary': summary,
        'sum_line_data': sum_line_data
    }
    return render(request, 'pages/dashboard.html', context)


def mark_summary_checked(request, pk):
    if request.method == "POST":
        try:
            summary = WeeklySummary.objects.get(pk=pk)
            summary.has_checked = True
            summary.save()
            return JsonResponse({"status": "success"})
        except WeeklySummary.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)
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
    today = timezone.localdate()

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
    
        if not weight:
            return redirect('dashboard')
        return redirect('weightlog_list')


# ---------- Delete Logs ----------
@login_required
def delete_weight_log(request, pk):
    log = get_object_or_404(request.user.profile.weightlog_set, pk=pk)
    
    if request.method == 'POST':
        log.delete()
        return redirect('weightlog_list')


# ---------- Settings ----------
@login_required
def settings(request):
    return render(request, 'pages/settings.html')


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
                date_obj = datetime.strptime(row["Date"], "%d/%m/%y").date()

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

    # Cards.
    streaks = profile.streaks
    fastest_drop = insights.get_fastest_drop()
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
        )
    ).order_by('category')

    # Calendar events.
    streak_events = []
    streak_dates = set()
    if profile.streaks and profile.streaks > 1 and profile.streaks_from:
        for i in range(profile.streaks):
            streak_day = profile.streaks_from + timedelta(days=i)
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
        "fastest_drop": fastest_drop,
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


# ---------- Weekly summary ----------
@csrf_exempt
def run_weekly_summary(request):
    # simple token-based protection
    token = request.GET.get("token")
    if token != settings.CRON_SECRET:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    call_command("generate_weekly_summaries")
    return JsonResponse({"status": "success"})
