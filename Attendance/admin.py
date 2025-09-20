from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "shift",
        "check_in_time",
        "check_out_time",
        "method",
        "face_verified",
        "created_at",
    )
    list_filter = ("method", "face_verified", "created_at", "shift")
    search_fields = (
        "employee__first_name",
        "employee__last_name",
        "employee__employee_id",
    )
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Thông tin nhân viên & ca", {
            "fields": ("employee", "shift", "assignment", "exception"),
        }),
        ("Thời gian", {
            "fields": ("check_in_time", "check_out_time"),
        }),
        ("Xác thực", {
            "fields": ("face_image", "face_verified"),
        }),
        ("Định vị GPS", {
            "fields": ("latitude", "longitude", "location_note"),
        }),
        ("Khác", {
            "fields": ("method", "manual_by", "note", "created_at"),
        }),
    )
