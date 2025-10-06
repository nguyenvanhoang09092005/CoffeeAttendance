# attendance/urls.py
from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("toggle/<int:shift_id>/", views.attendance_toggle, name="toggle"),
    path("qr/<str:qr_token>/", views.qr_checkin, name="qr_checkin"), 
    path("manual/", views.attendance_manual, name="manual"),
    path("", views.attendance_list, name="attendance_list"),
    path('history/<int:emp_id>/', views.attendance_history, name='attendance_history'),
]
