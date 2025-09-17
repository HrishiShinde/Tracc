from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection

from .models import Profile, WeightLog, UserMilestone
from .utils import Insights, calculate_bmi
import csv
import io
from datetime import datetime

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
    recent_logs = logs.order_by('-date')[:5]
    latest_weight = logs.last().weight

    # Call Insights class.
    insights = Insights(logs)

    # BMI and Progress.
    progress, progress_offset = insights.get_progress(profile)
    bmi_data = calculate_bmi(latest_weight, profile.height_cm)

    # Graphs processing.
    line_data = insights.get_line_data()
    daily_changes = insights.get_daily_change()

    context = {
        'profile': profile,
        'recent_logs': recent_logs, 
        'bmi_data': bmi_data,
        'progress': progress,
        'progress_offset': progress_offset,
        'clock_in_time': today_log.check_in_at.isoformat() if today_log and today_log.check_in_at else None,
        'line_data': line_data,
        'daily_changes': daily_changes
    }
    return render(request, 'pages/dashboard.html', context)


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
        check_in = request.POST.get('check_in') == 'true'  # button sends 'true' if clicked

        if pk:
            # Editing existing log
            log = get_object_or_404(profile.weightlog_set, pk=pk)
        else:
            # Add new log OR get today's log if check_in
            log, created = WeightLog.objects.get_or_create(profile=profile, date=today)

        # Update fields
        if weight:
            log.weight = weight
        log.notes = notes

        if check_in:
            log.check_in = True
            log.check_in_at = timezone.now()

        log.save()
        if not weight:
            return redirect('dashboard')
        return redirect('weightlog_list')  # ya dashboard, jahan se call ho raha hai


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
                date_obj = datetime.strptime(row["Date"], "%d/%m/%y").date()

                weight = float(row["Weight (kg)"]) if row["Weight (kg)"] else None
                notes = row.get("Notes/Mood", "")

                # Avoid duplicates
                log, created = WeightLog.objects.get_or_create(
                    profile=profile,
                    date=date_obj,
                    defaults={"weight": weight, "notes": notes}
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

        messages.success(request, f"{imported_count} logs imported successfully!")
        return redirect("settings")

    messages.error(request, "No file uploaded.")
    return redirect("settings")


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
    milestones = UserMilestone.objects.filter(profile=profile).last().milestone

    context = {
        "profile": profile,
        "line_data": line_data,
        "daily_changes": daily_changes,
        "monthly_avg": monthly_avg,
        "weight_zones": weight_zones,
        "streaks": streaks,
        "milestones": milestones,
        "fastest_drop": fastest_drop,
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
