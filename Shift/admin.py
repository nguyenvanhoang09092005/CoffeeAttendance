from django.contrib import admin
from django.utils.html import format_html
from .models import Shift, WeeklyShiftAssignment, ShiftException


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "qr_preview")
    search_fields = ("name",)
    readonly_fields = ("qr_preview", "qr_token")

    def qr_preview(self, obj):
        if obj.qr_token:
            url = obj.get_qr_url()
            return format_html(
                '<a href="{0}" target="_blank">Mở QR</a><br>'
                '<img src="https://api.qrserver.com/v1/create-qr-code/?size=100x100&data={0}" width="100" height="100"/>',
                url
            )
        return "-"
    qr_preview.short_description = "QR Code"


@admin.register(WeeklyShiftAssignment)
class WeeklyShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ("employee", "shift", "weekday")
    list_filter = ("weekday", "shift", "employee")
    search_fields = ("employee__first_name", "employee__last_name")


@admin.register(ShiftException)
class ShiftExceptionAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "exception_type", "date", "weekday",
        "start_time", "end_time", "is_added", "reason"
    )
    list_filter = ("exception_type", "date", "weekday", "is_added")
    search_fields = ("employee__first_name", "employee__last_name", "reason")
