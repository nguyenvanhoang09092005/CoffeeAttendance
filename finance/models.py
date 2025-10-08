from django.db import models
from django.utils import timezone
from decimal import Decimal
from employee.models import Employee
from Attendance.models import Attendance
from home_auth.models import CustomUser 
import uuid


# ======= 1. LOẠI CHI PHÍ =======
class ExpenseCategory(models.Model):
    name = models.CharField("Tên loại chi phí", max_length=100, unique=True)
    description = models.TextField("Mô tả", blank=True, null=True)
    is_active = models.BooleanField("Đang sử dụng", default=True)

    class Meta:
        verbose_name = "Loại chi phí"
        verbose_name_plural = "Các loại chi phí"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ======= 2. CHI PHÍ =======
class Expense(models.Model):
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Loại chi phí",
        related_name="expenses"
    )
    description = models.CharField("Mô tả", max_length=255)
    amount = models.DecimalField("Số tiền", max_digits=12, decimal_places=2)
    expense_date = models.DateField("Ngày chi", default=timezone.now)
    
    # Người tạo và phê duyệt - Đổi từ Employee sang CustomUser
    created_by = models.ForeignKey(
        CustomUser,  # Changed from Employee to CustomUser
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_expenses",
        verbose_name="Người tạo"
    )
    approved_by = models.ForeignKey(
        CustomUser,  # Changed from Employee to CustomUser
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
        verbose_name="Người phê duyệt"
    )
    
    # Trạng thái
    STATUS_CHOICES = [
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ]
    status = models.CharField("Trạng thái", max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Chứng từ đính kèm
    receipt_image = models.ImageField("Hóa đơn/Chứng từ", upload_to="expenses/receipts/", null=True, blank=True)
    note = models.TextField("Ghi chú", blank=True, null=True)
    
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    class Meta:
        verbose_name = "Chi phí"
        verbose_name_plural = "Danh sách chi phí"
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.category or 'Khác'} - {self.amount:,.0f} VND - {self.expense_date.strftime('%d/%m/%Y')}"


# ======= 3. DOANH THU =======
class Revenue(models.Model):
    source = models.CharField("Nguồn thu", max_length=255)
    description = models.TextField("Mô tả", blank=True, null=True)
    amount = models.DecimalField("Số tiền", max_digits=12, decimal_places=2)
    revenue_date = models.DateField("Ngày thu", default=timezone.now)
    
    # Người ghi nhận - Đổi từ Employee sang CustomUser
    created_by = models.ForeignKey(
        CustomUser,  # Changed from Employee to CustomUser
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_revenues",
        verbose_name="Người ghi nhận"
    )
    
    # Phân loại
    CATEGORY_CHOICES = [
        ('sales', 'Doanh thu bán hàng'),
        ('service', 'Dịch vụ'),
        ('other', 'Khác'),
    ]
    category = models.CharField("Loại doanh thu", max_length=20, choices=CATEGORY_CHOICES, default='sales')
    
    note = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    class Meta:
        verbose_name = "Doanh thu"
        verbose_name_plural = "Danh sách doanh thu"
        ordering = ["-revenue_date", "-created_at"]

    def __str__(self):
        return f"{self.source} - {self.amount:,.0f} VND - {self.revenue_date.strftime('%d/%m/%Y')}"


# ======= 4. BẢNG LƯƠNG TỔNG (PayrollSummary) =======
class PayrollSummary(models.Model):
    # Mã định danh
    payroll_id = models.UUIDField("Mã bảng lương", default=uuid.uuid4, unique=True, editable=False)
    
    # Nhân viên và kỳ lương
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="payroll_summaries",
        verbose_name="Nhân viên"
    )
    start_date = models.DateField("Ngày bắt đầu kỳ lương")
    end_date = models.DateField("Ngày kết thúc kỳ lương")
    
    # Tính toán lương
    total_hours = models.DecimalField("Tổng số giờ làm", max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField("Lương theo giờ (VND)", max_digits=10, decimal_places=2, default=0)
    base_salary = models.DecimalField("Tiền công (total_hours × hourly_rate)", max_digits=12, decimal_places=2, default=0)
    
    # Các khoản phụ
    bonus = models.DecimalField("Tiền thưởng", max_digits=12, decimal_places=2, default=0)
    advance = models.DecimalField("Tiền ứng trước", max_digits=12, decimal_places=2, default=0)
    deduction = models.DecimalField("Khấu trừ/phạt", max_digits=12, decimal_places=2, default=0)
    
    # Lương thực nhận
    net_salary = models.DecimalField("Lương thực nhận", max_digits=12, decimal_places=2, default=0)
    
    # Trạng thái
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy'),
    ]
    status = models.CharField("Trạng thái", max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Người tạo và phê duyệt - Đổi từ Employee sang CustomUser
    created_by = models.ForeignKey(
        CustomUser,  # Changed from Employee to CustomUser
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payrolls",
        verbose_name="Người lập"
    )
    approved_by = models.ForeignKey(
        CustomUser,  # Changed from Employee to CustomUser
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls",
        verbose_name="Người duyệt"
    )
    approved_at = models.DateTimeField("Ngày duyệt", null=True, blank=True)
    
    # Ghi chú và thời gian
    notes = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày lập bảng lương", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    class Meta:
        verbose_name = "Bảng lương tổng"
        verbose_name_plural = "Danh sách bảng lương"
        ordering = ["-start_date", "-created_at"]
        unique_together = ("employee", "start_date", "end_date")

    def __str__(self):
        return f"Lương {self.employee.first_name} {self.employee.last_name} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"

    def calculate_salary(self):
        """
        Tính toán lương dựa trên chi tiết chấm công
        """
        # Lấy tất cả chi tiết bảng lương
        details = self.payroll_details.all()
        
        # Tính tổng giờ làm
        self.total_hours = sum(detail.hours_worked or Decimal(0) for detail in details)
        
        # Tính tiền công = tổng giờ × lương/giờ
        self.base_salary = self.total_hours * self.hourly_rate
        
        # Tính lương thực nhận
        self.net_salary = self.base_salary + self.bonus - self.advance - self.deduction
        
        self.save()
        return self.net_salary

    def generate_details_from_attendance(self):
        """
        Tự động tạo chi tiết bảng lương từ dữ liệu chấm công
        """
        # Xóa chi tiết cũ (nếu có)
        self.payroll_details.all().delete()
        
        # Lấy tất cả bản ghi chấm công trong kỳ
        attendances = Attendance.objects.filter(
            employee=self.employee,
            check_in_time__date__gte=self.start_date,
            check_in_time__date__lte=self.end_date
        ).order_by('check_in_time')
        
        # Tạo chi tiết cho từng ngày
        for att in attendances:
            # Tính số giờ làm
            hours_worked = Decimal(0)
            if att.check_in_time and att.check_out_time:
                delta = att.check_out_time - att.check_in_time
                hours_worked = Decimal(delta.total_seconds() / 3600)
            
            # Xác định trạng thái
            status = ''
            if att.is_late:
                status = 'T'  # Trễ
            if att.left_early:
                status += 'S' if status else 'S'  # Ra sớm
            
            # Tạo chi tiết
            PayrollDetail.objects.create(
                payroll_summary=self,
                attendance=att,
                work_date=att.check_in_time.date(),
                check_in_time=att.check_in_time,
                check_out_time=att.check_out_time,
                hours_worked=round(hours_worked, 2),
                status=status,
                note=att.note or ''
            )
        
        # Tính lại tổng lương
        self.calculate_salary()


# ======= 5. CHI TIẾT BẢNG LƯƠNG (PayrollDetail) =======
class PayrollDetail(models.Model):
    # Liên kết
    payroll_summary = models.ForeignKey(
        PayrollSummary,
        on_delete=models.CASCADE,
        related_name="payroll_details",
        verbose_name="Bảng lương tổng"
    )
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_details",
        verbose_name="Bản ghi chấm công"
    )
    
    # Thông tin ngày làm việc
    work_date = models.DateField("Ngày làm việc")
    check_in_time = models.DateTimeField("Giờ vào", null=True, blank=True)
    check_out_time = models.DateTimeField("Giờ ra", null=True, blank=True)
    hours_worked = models.DecimalField("Số giờ làm", max_digits=5, decimal_places=2, default=0)
    
    # Trạng thái
    STATUS_CHOICES = [
        ('', 'Bình thường'),
        ('T', 'Trễ'),
        ('S', 'Ra sớm'),
        ('V', 'Vắng'),
        ('TS', 'Trễ + Ra sớm'),
    ]
    status = models.CharField("Trạng thái", max_length=10, choices=STATUS_CHOICES, blank=True, default='')
    
    # Ghi chú chi tiết
    note = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Chi tiết bảng lương"
        verbose_name_plural = "Chi tiết bảng lương"
        ordering = ["work_date"]

    def __str__(self):
        return f"{self.payroll_summary.employee.first_name} - {self.work_date.strftime('%d/%m/%Y')} - {self.hours_worked}h"

    def save(self, *args, **kwargs):
        """
        Tự động tính số giờ làm nếu có check_in và check_out
        """
        if self.check_in_time and self.check_out_time and not self.hours_worked:
            delta = self.check_out_time - self.check_in_time
            self.hours_worked = round(Decimal(delta.total_seconds() / 3600), 2)
        
        super().save(*args, **kwargs)