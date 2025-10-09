from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
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


# ======= 2. DOANH THU (CẤU TRÚC MỚI) =======
class Revenue(models.Model):
    # Thông tin chính từ form
    revenue_date = models.DateField("Ngày", default=timezone.now)
    shift = models.CharField("Ca", max_length=20, choices=[
        ('sang', 'Sáng'),
        ('chieu', 'Chiều'),
        ('toi', 'Tối'),
    ])
    
    # Các khoản doanh thu
    tien_mat = models.DecimalField("Tiền mặt", max_digits=12, decimal_places=2, default=0)
    chuyen_khoan = models.DecimalField("Chuyển khoản", max_digits=12, decimal_places=2, default=0)
    vnpay = models.DecimalField("VNPay", max_digits=12, decimal_places=2, default=0)
    no = models.DecimalField("Nợ", max_digits=12, decimal_places=2, default=0)
    chi = models.DecimalField("Chi", max_digits=12, decimal_places=2, default=0)
    
    # Tổng cộng (tự động tính)
    tong = models.DecimalField("Tổng", max_digits=12, decimal_places=2, default=0)
    danh_thu_rong = models.DecimalField("Danh thu ròng", max_digits=12, decimal_places=2, default=0)
    
    # Thông tin người nhập và hình ảnh
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_revenues",
        verbose_name="Người nhập"
    )
    receipt_image = models.ImageField("Hình ảnh chứng từ", upload_to="revenues/receipts/", null=True, blank=True)
    
    # Ghi chú và thời gian
    note = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    class Meta:
        verbose_name = "Doanh thu"
        verbose_name_plural = "Danh sách doanh thu"
        ordering = ["-revenue_date", "-created_at"]

    def __str__(self):
        return f"{self.get_shift_display()} - {self.revenue_date.strftime('%d/%m/%Y')} - {self.created_by or 'N/A'}"

    def save(self, *args, **kwargs):
        """
        Tự động tính Tổng và Danh thu ròng trước khi lưu
        Validation: Đảm bảo các giá trị không âm (trừ tiền mặt có thể âm)
        """
        # Validation: Kiểm tra các giá trị không âm (tiền mặt có thể âm)
        if any(val < 0 for val in [self.chuyen_khoan, self.vnpay, self.no, self.chi]):
            raise ValidationError("Các giá trị chuyển khoản, VNPay, nợ, chi không được âm")
        
        # Tổng = Tiền mặt + Chuyển khoản + VNPay + Nợ
        self.tong = self.tien_mat + self.chuyen_khoan + self.vnpay + self.no
        
        # Danh thu ròng = Tổng - Chi
        self.danh_thu_rong = self.tong - self.chi
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Validation bổ sung
        """
        # Kiểm tra ngày hợp lệ
        if self.revenue_date > timezone.now().date():
            raise ValidationError({'revenue_date': 'Ngày doanh thu không được là ngày tương lai'})
        
        # Kiểm tra chi không vượt quá tổng thu
        if self.chi > self.tong:
            raise ValidationError({'chi': 'Chi phí không được lớn hơn tổng doanh thu'})


# ======= 3A. CHI PHÍ LIÊN KẾT VỚI DOANH THU (RevenueExpense) =======
class RevenueExpense(models.Model):
    """
    Chi phí gắn với phiếu doanh thu (nhập từ form doanh thu)
    """
    # Liên kết với doanh thu
    revenue = models.ForeignKey(
        Revenue,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="Phiếu doanh thu"
    )
    
    # Thông tin chi phí từ form
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Loại chi phí",
        related_name="revenue_expenses"
    )
    description = models.CharField("Mô tả", max_length=255)
    amount = models.DecimalField("Số tiền", max_digits=12, decimal_places=2)
    
    # Các thông tin tự động từ Revenue
    expense_date = models.DateField("Ngày chi", editable=False)
    receipt_image = models.ImageField("Hóa đơn/Chứng từ", upload_to="expenses/receipts/", editable=False, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_revenue_expenses",
        verbose_name="Người nhập",
        editable=False
    )
    
    # Ghi chú
    note = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    @property
    def is_standalone(self):
        """Kiểm tra đây có phải chi phí độc lập không"""
        return False

    class Meta:
        verbose_name = "Chi phí (liên kết doanh thu)"
        verbose_name_plural = "Chi phí liên kết doanh thu"
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.category or 'Khác'} - {self.amount:,.0f} VND - {self.expense_date.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        """
        Tự động lấy thông tin từ Revenue khi lưu
        """
        if self.revenue:
            self.expense_date = self.revenue.revenue_date
            self.receipt_image = self.revenue.receipt_image
            self.created_by = self.revenue.created_by
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Validation cho RevenueExpense
        """
        if self.amount <= 0:
            raise ValidationError({'amount': 'Số tiền chi phí phải lớn hơn 0'})
        
        if not self.category and not self.description:
            raise ValidationError('Phải có loại chi phí hoặc mô tả chi tiết')
        
        # Kiểm tra tổng chi phí không vượt quá doanh thu
        if self.revenue:
            total_expenses = self.revenue.expenses.exclude(pk=self.pk).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal(0)
            
            if total_expenses + self.amount > self.revenue.tong:
                raise ValidationError({
                    'amount': f'Tổng chi phí ({total_expenses + self.amount:,.0f} VND) sẽ vượt quá tổng doanh thu ({self.revenue.tong:,.0f} VND)'
                })


# ======= 3B. CHI PHÍ ĐỘC LẬP (Expense) =======
class Expense(models.Model):
    """
    Chi phí độc lập, có form nhập riêng (không liên kết Revenue)
    """
    # Thông tin chi phí - NHẬP ĐẦY ĐỦ từ form
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
    
    # Người tạo và phê duyệt
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_standalone_expenses",
        verbose_name="Người tạo"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_standalone_expenses",
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
    receipt_image = models.ImageField("Hóa đơn/Chứng từ", upload_to="expenses/standalone/", null=True, blank=True)
    note = models.TextField("Ghi chú", blank=True, null=True)
    
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lần cuối", auto_now=True)

    @property
    def is_standalone(self):
        return True

    class Meta:
        verbose_name = "Chi phí (độc lập)"
        verbose_name_plural = "Chi phí độc lập"
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.category or 'Khác'} - {self.amount:,.0f} VND - {self.expense_date.strftime('%d/%m/%Y')}"

    def clean(self):
        """
        Validation cho Expense độc lập
        """
        if self.amount <= 0:
            raise ValidationError({'amount': 'Số tiền chi phí phải lớn hơn 0'})
        
        if not self.category and not self.description:
            raise ValidationError('Phải có loại chi phí hoặc mô tả chi tiết')
        
        # Kiểm tra ngày chi không phải tương lai
        if self.expense_date > timezone.now().date():
            raise ValidationError({'expense_date': 'Ngày chi không được là ngày tương lai'})


# ======= SIGNALS: Tự động cập nhật chi phí trong Revenue =======

@receiver(post_save, sender=RevenueExpense)
@receiver(post_delete, sender=RevenueExpense)
def update_revenue_on_expense_change(sender, instance, **kwargs):
    """
    Signal: Tự động cập nhật tổng chi phí trong Revenue khi RevenueExpense thay đổi
    """
    if instance.revenue:
        # Tính tổng chi phí từ tất cả các expense liên quan
        total_chi = instance.revenue.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal(0)
        
        # Cập nhật trường 'chi' trong Revenue (tránh vòng lặp vô hạn)
        Revenue.objects.filter(pk=instance.revenue.pk).update(
            chi=total_chi,
            danh_thu_rong=models.F('tong') - total_chi
        )


# ======= 4. BẢNG LƯƠNG TỔNG (PayrollSummary) =======
class PayrollSummary(models.Model):
    payroll_id = models.UUIDField("Mã bảng lương", default=uuid.uuid4, unique=True, editable=False)
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="payroll_summaries",
        verbose_name="Nhân viên"
    )
    start_date = models.DateField("Ngày bắt đầu kỳ lương")
    end_date = models.DateField("Ngày kết thúc kỳ lương")
    
    total_hours = models.DecimalField("Tổng số giờ làm", max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField("Lương theo giờ (VND)", max_digits=10, decimal_places=2, default=0)
    base_salary = models.DecimalField("Tiền công (total_hours × hourly_rate)", max_digits=12, decimal_places=2, default=0)
    
    bonus = models.DecimalField("Tiền thưởng", max_digits=12, decimal_places=2, default=0)
    advance = models.DecimalField("Tiền ứng trước", max_digits=12, decimal_places=2, default=0)
    deduction = models.DecimalField("Khấu trừ/phạt", max_digits=12, decimal_places=2, default=0)
    
    net_salary = models.DecimalField("Lương thực nhận", max_digits=12, decimal_places=2, default=0)
    
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã hủy'),
    ]
    status = models.CharField("Trạng thái", max_length=10, choices=STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payrolls",
        verbose_name="Người lập"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls",
        verbose_name="Người duyệt"
    )
    approved_at = models.DateTimeField("Ngày duyệt", null=True, blank=True)
    
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
        details = self.payroll_details.all()
        self.total_hours = sum(detail.hours_worked or Decimal(0) for detail in details)
        self.base_salary = self.total_hours * self.hourly_rate
        self.net_salary = self.base_salary + self.bonus - self.advance - self.deduction
        self.save()
        return self.net_salary

    def generate_details_from_attendance(self):
        self.payroll_details.all().delete()
        
        attendances = Attendance.objects.filter(
            employee=self.employee,
            check_in_time__date__gte=self.start_date,
            check_in_time__date__lte=self.end_date
        ).order_by('check_in_time')
        
        for att in attendances:
            hours_worked = Decimal(0)
            if att.check_in_time and att.check_out_time:
                delta = att.check_out_time - att.check_in_time
                hours_worked = Decimal(delta.total_seconds() / 3600)
            
            status = ''
            if att.is_late:
                status = 'T'
            if att.left_early:
                status += 'S' if status else 'S'
            
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
        
        self.calculate_salary()


# ======= 5. CHI TIẾT BẢNG LƯƠNG (PayrollDetail) =======
class PayrollDetail(models.Model):
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
    
    work_date = models.DateField("Ngày làm việc")
    check_in_time = models.DateTimeField("Giờ vào", null=True, blank=True)
    check_out_time = models.DateTimeField("Giờ ra", null=True, blank=True)
    hours_worked = models.DecimalField("Số giờ làm", max_digits=5, decimal_places=2, default=0)
    
    STATUS_CHOICES = [
        ('', 'Bình thường'),
        ('T', 'Trễ'),
        ('S', 'Ra sớm'),
        ('V', 'Vắng'),
        ('TS', 'Trễ + Ra sớm'),
    ]
    status = models.CharField("Trạng thái", max_length=10, choices=STATUS_CHOICES, blank=True, default='')
    
    note = models.TextField("Ghi chú", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Chi tiết bảng lương"
        verbose_name_plural = "Chi tiết bảng lương"
        ordering = ["work_date"]

    def __str__(self):
        return f"{self.payroll_summary.employee.first_name} - {self.work_date.strftime('%d/%m/%Y')} - {self.hours_worked}h"

    def save(self, *args, **kwargs):
        if self.check_in_time and self.check_out_time and not self.hours_worked:
            delta = self.check_out_time - self.check_in_time
            self.hours_worked = round(Decimal(delta.total_seconds() / 3600), 2)
        
        super().save(*args, **kwargs)