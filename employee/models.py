from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.conf import settings


class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
        null=True, blank=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=8, unique=True, editable=False)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Nam'), ('Female', 'Nữ'), ('Others', 'Khác')]
    )
    date_of_birth = models.DateField()
    position = models.CharField(
        max_length=50,
        choices=[
            ('Manager', 'quin lý'),
            ('Cashier', 'Thu ngân'),
            ('Barista', 'Pha chế'),
            ('Waiter', 'Phục vụ'),
        ]
    )
    joining_date = models.DateField()
    mobile_number = models.CharField(max_length=10)
    address = models.CharField(max_length=200, blank=True, null=True)
    employee_image = models.ImageField(upload_to='employees/', blank=True)

    # Thông tin bổ sung
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    employment_status = models.CharField(
        max_length=20,
        choices=[
            ('Active', 'Đang làm'),
            ('Inactive', 'Nghỉ việc'),
            ('On Hold', 'Tạm nghỉ')
        ],
        default='Active'
    )
    resignation_date = models.DateField(blank=True, null=True)

    # Slug
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Sinh employee_id nếu chưa có
        if not self.employee_id:
            self.employee_id = "DC" + get_random_string(length=6, allowed_chars="0123456789")

        # Sinh slug
        if not self.slug:
            self.slug = slugify(f"{self.first_name}-{self.last_name}-{self.employee_id}")

        super().save(*args, **kwargs)

    @property
    def latest_attendance(self):
        """
        Lấy bản ghi chấm công mới nhất của nhân viên
        """
        return self.attendances.order_by("-created_at").first()

    # def get_toggle_url(self):
       
    #     if self.latest_attendance:
    #         return self.latest_attendance.get_toggle_url()
    #     return "#"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"


class EmployeeFace(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="faces")
    face_image = models.ImageField(upload_to="employee_faces/")
    face_encoding = models.JSONField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Khuôn mặt của {self.employee}"