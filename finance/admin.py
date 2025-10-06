from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.utils import timezone
from .models import ExpenseCategory, Expense, Revenue, PayrollSummary, PayrollDetail


# ======= 1. LOẠI CHI PHÍ =======
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_active", "total_expenses")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("name",)
    
    def total_expenses(self, obj):
        """Hiển thị tổng số chi phí thuộc loại này"""
        total = obj.expenses.filter(status='approved').aggregate(Sum('amount'))['amount__sum'] or 0
        return format_html('<strong>{:,.0f} VND</strong>', total)
    total_expenses.short_description = "Tổng chi (đã duyệt)"


# ======= 2. CHI PHÍ =======
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_date", 
        "category", 
        "description_short", 
        "amount_display", 
        "status_badge",
        "created_by", 
        "approved_by"
    )
    list_filter = ("status", "category", "expense_date", "created_at")
    search_fields = ("description", "note")
    date_hierarchy = "expense_date"
    ordering = ("-expense_date", "-created_at")
    
    readonly_fields = ("created_at", "updated_at", "receipt_preview")
    
    fieldsets = (
        ("Thông tin chi phí", {
            "fields": ("category", "description", "amount", "expense_date")
        }),
        ("Trạng thái & Phê duyệt", {
            "fields": ("status", "created_by", "approved_by")
        }),
        ("Chứng từ & Ghi chú", {
            "fields": ("receipt_image", "receipt_preview", "note")
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def description_short(self, obj):
        """Hiển thị mô tả ngắn gọn"""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Mô tả"
    
    def amount_display(self, obj):
        """Hiển thị số tiền với định dạng"""
        return format_html('<strong style="color: #dc3545;">{:,.0f} VND</strong>', obj.amount)
    amount_display.short_description = "Số tiền"
    
    def status_badge(self, obj):
        """Hiển thị trạng thái với màu sắc"""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        labels = {
            'pending': 'Chờ duyệt',
            'approved': 'Đã duyệt',
            'rejected': 'Từ chối',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            labels.get(obj.status, obj.status)
        )
    status_badge.short_description = "Trạng thái"
    
    def receipt_preview(self, obj):
        """Hiển thị preview hình ảnh hóa đơn"""
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px;" /></a>',
                obj.receipt_image.url,
                obj.receipt_image.url
            )
        return "Chưa có hóa đơn"
    receipt_preview.short_description = "Xem trước hóa đơn"
    
    actions = ['approve_expenses', 'reject_expenses']
    
    def approve_expenses(self, request, queryset):
        """Action phê duyệt nhiều chi phí"""
        # Kiểm tra xem user có employee_profile không
        try:
            approved_by = request.user.employee_profile
        except:
            approved_by = None
        
        updated = queryset.update(status='approved', approved_by=approved_by)
        self.message_user(request, f"Đã phê duyệt {updated} chi phí")
    approve_expenses.short_description = "✅ Phê duyệt các chi phí đã chọn"
    
    def reject_expenses(self, request, queryset):
        """Action từ chối nhiều chi phí"""
        try:
            approved_by = request.user.employee_profile
        except:
            approved_by = None
            
        updated = queryset.update(status='rejected', approved_by=approved_by)
        self.message_user(request, f"Đã từ chối {updated} chi phí")
    reject_expenses.short_description = "❌ Từ chối các chi phí đã chọn"


# ======= 3. DOANH THU =======
@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = (
        "revenue_date",
        "source",
        "category_display",
        "amount_display",
        "created_by"
    )
    list_filter = ("category", "revenue_date", "created_at")
    search_fields = ("source", "description", "note")
    date_hierarchy = "revenue_date"
    ordering = ("-revenue_date", "-created_at")
    
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Thông tin doanh thu", {
            "fields": ("source", "category", "amount", "revenue_date")
        }),
        ("Mô tả & Ghi chú", {
            "fields": ("description", "note")
        }),
        ("Người ghi nhận", {
            "fields": ("created_by",)
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def category_display(self, obj):
        """Hiển thị loại doanh thu"""
        colors = {
            'sales': '#007bff',
            'service': '#17a2b8',
            'other': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.category, '#6c757d'),
            obj.get_category_display()
        )
    category_display.short_description = "Loại"
    
    def amount_display(self, obj):
        """Hiển thị số tiền với định dạng"""
        return format_html('<strong style="color: #28a745;">{:,.0f} VND</strong>', obj.amount)
    amount_display.short_description = "Số tiền"


# ======= 4. CHI TIẾT BẢNG LƯƠNG (Inline) =======
class PayrollDetailInline(admin.TabularInline):
    model = PayrollDetail
    extra = 0
    readonly_fields = ("attendance", "work_date", "check_in_time", "check_out_time", "hours_worked", "status")
    fields = ("work_date", "check_in_time", "check_out_time", "hours_worked", "status", "note")
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ======= 5. BẢNG LƯƠNG TỔNG =======
@admin.register(PayrollSummary)
class PayrollSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "payroll_id_short",
        "employee_info",
        "period_display",
        "total_hours",
        "net_salary_display",
        "status_badge",
        "created_at"
    )
    list_filter = ("status", "start_date", "created_at")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_id", "payroll_id")
    date_hierarchy = "start_date"
    ordering = ("-start_date", "-created_at")
    
    readonly_fields = (
        "payroll_id", 
        "base_salary", 
        "net_salary", 
        "created_at", 
        "updated_at",
        "approved_at",
        "total_hours_display"
    )
    
    fieldsets = (
        ("Thông tin nhân viên & Kỳ lương", {
            "fields": ("payroll_id", "employee", "start_date", "end_date")
        }),
        ("Tính toán lương", {
            "fields": (
                ("total_hours", "total_hours_display"),
                ("hourly_rate", "base_salary"),
            )
        }),
        ("Các khoản phụ", {
            "fields": ("bonus", "advance", "deduction", "net_salary")
        }),
        ("Trạng thái & Phê duyệt", {
            "fields": ("status", "created_by", "approved_by", "approved_at")
        }),
        ("Ghi chú", {
            "fields": ("notes",)
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [PayrollDetailInline]
    
    actions = ['generate_payroll_details', 'calculate_salaries', 'approve_payrolls']
    
    def payroll_id_short(self, obj):
        """Hiển thị mã bảng lương ngắn gọn"""
        return format_html('<code>{}</code>', str(obj.payroll_id)[:8])
    payroll_id_short.short_description = "Mã BL"
    
    def employee_info(self, obj):
        """Hiển thị thông tin nhân viên"""
        url = reverse("admin:employee_employee_change", args=[obj.employee.pk])
        return format_html(
            '<a href="{}" target="_blank"><strong>{}</strong></a><br/><small style="color: #6c757d;">{}</small>',
            url,
            f"{obj.employee.first_name} {obj.employee.last_name}",
            obj.employee.employee_id
        )
    employee_info.short_description = "Nhân viên"
    
    def period_display(self, obj):
        """Hiển thị kỳ lương"""
        return format_html(
            '{}<br/><small style="color: #6c757d;">đến</small><br/>{}',
            obj.start_date.strftime('%d/%m/%Y'),
            obj.end_date.strftime('%d/%m/%Y')
        )
    period_display.short_description = "Kỳ lương"
    
    def total_hours_display(self, obj):
        """Hiển thị tổng giờ với chi tiết"""
        details_count = obj.payroll_details.count()
        return format_html(
            '<strong>{} giờ</strong> <small style="color: #6c757d;">({} ngày)</small>',
            obj.total_hours,
            details_count
        )
    total_hours_display.short_description = "Chi tiết giờ"
    
    def net_salary_display(self, obj):
        """Hiển thị lương thực nhận"""
        return format_html('<strong style="color: #28a745; font-size: 14px;">{:,.0f} VND</strong>', obj.net_salary)
    net_salary_display.short_description = "Lương thực nhận"
    
    def status_badge(self, obj):
        """Hiển thị trạng thái với màu sắc"""
        colors = {
            'draft': '#6c757d',
            'pending': '#ffc107',
            'approved': '#17a2b8',
            'paid': '#28a745',
            'cancelled': '#dc3545',
        }
        labels = {
            'draft': 'Nháp',
            'pending': 'Chờ duyệt',
            'approved': 'Đã duyệt',
            'paid': 'Đã thanh toán',
            'cancelled': 'Đã hủy',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            labels.get(obj.status, obj.status)
        )
    status_badge.short_description = "Trạng thái"
    
    def generate_payroll_details(self, request, queryset):
        """Action tự động sinh chi tiết từ chấm công"""
        count = 0
        for payroll in queryset:
            payroll.generate_details_from_attendance()
            count += 1
        self.message_user(request, f"Đã tạo chi tiết cho {count} bảng lương từ dữ liệu chấm công")
    generate_payroll_details.short_description = "🔄 Tạo chi tiết từ chấm công"
    
    def calculate_salaries(self, request, queryset):
        """Action tính toán lương"""
        count = 0
        for payroll in queryset:
            payroll.calculate_salary()
            count += 1
        self.message_user(request, f"Đã tính toán lương cho {count} bảng lương")
    calculate_salaries.short_description = "🧮 Tính toán lương"
    
    def approve_payrolls(self, request, queryset):
        """Action phê duyệt bảng lương"""
        try:
            approved_by = request.user.employee_profile
        except:
            approved_by = None
        
        for payroll in queryset:
            payroll.status = 'approved'
            payroll.approved_by = approved_by
            payroll.approved_at = timezone.now()
            payroll.save()
        
        self.message_user(request, f"Đã phê duyệt {queryset.count()} bảng lương")
    approve_payrolls.short_description = "✅ Phê duyệt bảng lương"


# ======= 6. CHI TIẾT BẢNG LƯƠNG (Riêng lẻ) =======
@admin.register(PayrollDetail)
class PayrollDetailAdmin(admin.ModelAdmin):
    list_display = (
        "work_date",
        "employee_name",
        "check_in_time",
        "check_out_time",
        "hours_worked",
        "status_display"
    )
    list_filter = ("status", "work_date", "payroll_summary__employee")
    search_fields = ("payroll_summary__employee__first_name", "payroll_summary__employee__last_name", "note")
    date_hierarchy = "work_date"
    ordering = ("-work_date",)
    
    readonly_fields = ("attendance", "created_at")
    
    fieldsets = (
        ("Liên kết", {
            "fields": ("payroll_summary", "attendance")
        }),
        ("Thông tin ca làm", {
            "fields": ("work_date", "check_in_time", "check_out_time", "hours_worked")
        }),
        ("Trạng thái & Ghi chú", {
            "fields": ("status", "note")
        }),
        ("Thời gian", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    
    def employee_name(self, obj):
        """Hiển thị tên nhân viên"""
        return f"{obj.payroll_summary.employee.first_name} {obj.payroll_summary.employee.last_name}"
    employee_name.short_description = "Nhân viên"
    
    def status_display(self, obj):
        """Hiển thị trạng thái chi tiết"""
        if obj.status == 'V':
            return format_html('<span style="color: #dc3545;">❌ Vắng</span>')
        elif obj.status == 'T':
            return format_html('<span style="color: #ffc107;">⚠️ Trễ</span>')
        elif obj.status == 'S':
            return format_html('<span style="color: #17a2b8;">⏰ Ra sớm</span>')
        elif obj.status == 'TS':
            return format_html('<span style="color: #fd7e14;">⚠️ Trễ + Ra sớm</span>')
        return format_html('<span style="color: #28a745;">✅ Bình thường</span>')
    status_display.short_description = "Trạng thái"