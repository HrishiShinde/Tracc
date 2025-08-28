from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('post-login/', views.redirect_after_login, name='redirect_after_login'),
    path('complete-profile/', views.get_more_data, name='get_more_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logs/', views.weightlog_list, name='weightlog_list'),
    path('logs/add/', views.add_or_edit_weight_log, name='add_weight_log'),
    path('logs/<int:pk>/edit/', views.add_or_edit_weight_log, name='edit_weight_log'),
    path('logs/<int:pk>/delete/', views.delete_weight_log, name='delete_weight_log'),
    path('clock_in/', views.add_or_edit_weight_log, name='clock_in'),
]
