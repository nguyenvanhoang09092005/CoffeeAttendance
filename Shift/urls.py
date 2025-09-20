from django.urls import path
from . import views

urlpatterns = [
    # Quản lý tổng hợp
    path("manage/", views.shift_manage, name="shift_manage"),
    path("schedule/", views.shift_schedule, name="shift_schedule"),
    path("assignments/", views.all_manage, name="all_manage"),
    path("assignment/update_all/", views.assignment_update_all, name="assignment_update_all"),

    # --- Shift (Loại ca) ---
    path("shifts/<int:pk>/edit/", views.shift_edit, name="shift_edit"),
    path("shifts/<int:pk>/delete/", views.shift_delete, name="shift_delete"),

    # --- WeeklyShiftAssignment (Phân công ca) ---
  
    path("assignments/<int:pk>/edit/", views.assignment_edit, name="assignment_edit"),
    path("assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),

    # --- ShiftException (Ca ngoại lệ) ---
    path("exceptions/<int:pk>/edit/", views.exception_edit, name="exception_edit"),
    path("exceptions/<int:pk>/delete/", views.exception_delete, name="exception_delete"),

    #staff
     path("shows/", views.show_shift, name="show_shift"),
]
