from django.db import models
from django.utils import timezone
from django.urls import reverse
from employee.models import Employee
import uuid


class Attendance(models.Model):
    METHOD_CHOICES = [
        ("auto", "Tự động (FaceID + GPS)"),
        ("manual", "Thủ công (Admin nhập)"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendances"
    )

    shift = models.ForeignKey(
        "Shift.Shift", on_delete=models.CASCADE, null=True, blank=True
    )
    assignment = models.ForeignKey(
        "Shift.WeeklyShiftAssignment", on_delete=models.SET_NULL, null=True, blank=True
    )
    exception = models.ForeignKey(
        "Shift.ShiftException", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Thời gian check-in / check-out
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    unique_token = models.CharField(
        max_length=100,
        unique=True,
        default=uuid.uuid4,   # ✅ tự động sinh giá trị
        editable=False
    )

    # Định vị GPS
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_note = models.CharField(max_length=255, null=True, blank=True)

    # Xác thực khuôn mặt
    face_image = models.ImageField(upload_to="attendance_faces/", null=True, blank=True)
    face_verified = models.BooleanField(default=False)

    # Cách chấm công
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="auto")
    manual_by = models.ForeignKey(
        Employee, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="manual_attendances"
    )

    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chấm công"
        verbose_name_plural = "Danh sách chấm công"
        ordering = ["-created_at"]

 
    def __str__(self):
        return f"{self.employee} - {self.shift or 'No Shift'} - {self.created_at.strftime('%Y-%m-%d')}"

    # ======================
    #   Các helper function
    # ======================

    @property
    def is_late(self):
        """Nhân viên vào ca trễ"""
        if self.check_in_time and self.shift:
            return self.check_in_time.time() > self.shift.start_time
        return False

    @property
    def left_early(self):
        """Nhân viên ra ca sớm"""
        if self.check_out_time and self.shift:
            return self.check_out_time.time() < self.shift.end_time
        return False

    def get_toggle_url(self):
        """Trả về link duy nhất cho check-in/check-out"""
        return reverse("attendance:toggle", args=[self.unique_token])

    def get_qr_url(self):
        """Trả về link để sinh QR code"""
        return reverse("attendance:generate_qr", args=[self.unique_token])
