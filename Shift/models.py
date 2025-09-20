# models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from employee.models import Employee  

import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.db import models
from employee.models import Employee  

class Shift(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    qr_token = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = get_random_string(20)
        super().save(*args, **kwargs)

    def get_qr_url(self):
        base_url = settings.SITE_URL.strip().rstrip("/")
        return f"{base_url}{reverse('attendance:qr_checkin', args=[self.qr_token])}"

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class WeeklyShiftAssignment(models.Model):
    WEEKDAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAYS)

    class Meta:
        unique_together = ("employee", "shift", "weekday")  

    def __str__(self):
        return f"{self.employee} - {self.get_weekday_display()} - {self.shift}"

class ShiftException(models.Model):
    EXCEPTION_TYPES = [
        ("once", "Chỉ 1 ngày"),
        ("permanent", "Cố định"),
    ]

    WEEKDAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, null=True, blank=True)  
    date = models.DateField(null=True, blank=True)  # dùng cho loại "once"
    weekday = models.IntegerField(choices=WEEKDAYS, null=True, blank=True)  # dùng cho "permanent"
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=200, blank=True, null=True)
    exception_type = models.CharField(max_length=10, choices=EXCEPTION_TYPES, default="once")
    is_added = models.BooleanField(default=True)  # True = thêm, False = nghỉ

    class Meta:
        unique_together = ("employee", "date", "weekday", "exception_type")

    def __str__(self):
        if self.exception_type == "once":
            return f"{self.employee} - {self.date} ({self.get_exception_type_display()})"
        else:
            return f"{self.employee} - {self.get_weekday_display()} ({self.get_exception_type_display()})"
