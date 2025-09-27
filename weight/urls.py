from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('post-login/', views.redirect_after_login, name='redirect_after_login'),

    # Profile
    path('complete-profile/', views.get_more_data, name='get_more_data'),
    path('update-profile/', views.get_more_data, name='update_profile'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Logs
    path('logs/', views.weightlog_list, name='weightlog_list'),
    path('logs/add/', views.add_or_edit_weight_log, name='add_weight_log'),
    path('logs/<int:pk>/edit/', views.add_or_edit_weight_log, name='edit_weight_log'),
    path('logs/<int:pk>/delete/', views.delete_weight_log, name='delete_weight_log'),
    path('clock_in/', views.add_or_edit_weight_log, name='clock_in'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path("import-logs/", views.import_logs, name="import_logs"),
    path("export-logs/", views.export_logs, name="export_logs"),

    # Analytics
    path('analytics/', views.analytics, name='analytics'),

    # Catch-all empty path redirect
    path('', lambda request: redirect('dashboard'), name='home_redirect'),

    # Health.
    path("health/", views.health_view, name="health_page"),
    path("healthz/", views.health_json, name="health_json"),
]
