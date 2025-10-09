from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.utils import timezone
from .models import (
    ExpenseCategory, Expense, RevenueExpense, Revenue, 
    PayrollSummary, PayrollDetail
)


# ======= 1. LOẠI CHI PHÍ =======
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_active", "total_standalone_expenses", "total_revenue_expenses")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("name",)
    
    def total_standalone_expenses(self, obj):
        """Tổng chi phí độc lập"""
        total = obj.standalone_expenses.filter(status='approved').aggregate(
            Sum('amount'))['amount__sum'] or 0
        return format_html('<strong style="color: #dc3545;">{:,.0f} VND</strong>', total)
    total_standalone_expenses.short_description = "Chi phí độc lập (đã duyệt)"
    
    def total_revenue_expenses(self, obj):
        """Tổng chi phí liên kết doanh thu"""
        total = obj.revenue_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        return format_html('<strong style="color: #fd7e14;">{:,.0f} VND</strong>', total)
    total_revenue_expenses.short_description = "Chi từ doanh thu"


# ======= 2A. CHI PHÍ ĐỘC LẬP =======
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
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Mô tả"
    
    def amount_display(self, obj):
        return format_html('<strong style="color: #dc3545;">{:,.0f} VND</strong>', obj.amount)
    amount_display.short_description = "Số tiền"
    
    def status_badge(self, obj):
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
        updated = queryset.update(status='approved', approved_by=request.user)
        self.message_user(request, f"Đã phê duyệt {updated} chi phí")
    approve_expenses.short_description = "✅ Phê duyệt các chi phí đã chọn"
    
    def reject_expenses(self, request, queryset):
        updated = queryset.update(status='rejected', approved_by=request.user)
        self.message_user(request, f"Đã từ chối {updated} chi phí")
    reject_expenses.short_description = "❌ Từ chối các chi phí đã chọn"


# ======= 2B. CHI PHÍ LIÊN KẾT DOANH THU =======
class RevenueExpenseInline(admin.TabularInline):
    model = RevenueExpense
    extra = 1
    fields = ("category", "description", "amount", "note")
    readonly_fields = ("expense_date", "created_by")
    can_delete = True


@admin.register(RevenueExpense)
class RevenueExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_date",
        "revenue_info",
        "category",
        "description_short",
        "amount_display",
        "created_by"
    )
    list_filter = ("category", "expense_date", "created_at")
    search_fields = ("description", "note", "revenue__shift")
    date_hierarchy = "expense_date"
    ordering = ("-expense_date", "-created_at")
    
    readonly_fields = ("expense_date", "receipt_image", "created_by", "created_at", "updated_at")
    
    fieldsets = (
        ("Liên kết", {
            "fields": ("revenue",)
        }),
        ("Thông tin chi phí", {
            "fields": ("category", "description", "amount")
        }),
        ("Tự động từ Revenue", {
            "fields": ("expense_date", "receipt_image", "created_by"),
            "classes": ("collapse",)
        }),
        ("Ghi chú", {
            "fields": ("note",)
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def revenue_info(self, obj):
        return format_html(
            '<strong>{}</strong> - {}',
            obj.revenue.get_shift_display(),
            obj.revenue.revenue_date.strftime('%d/%m/%Y')
        )
    revenue_info.short_description = "Phiếu doanh thu"
    
    def description_short(self, obj):
        return obj.description[:40] + "..." if len(obj.description) > 40 else obj.description
    description_short.short_description = "Mô tả"
    
    def amount_display(self, obj):
        return format_html('<strong style="color: #fd7e14;">{:,.0f} VND</strong>', obj.amount)
    amount_display.short_description = "Số tiền"


# ======= 3. DOANH THU =======
@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = (
        "revenue_date",
        "shift_display",
        "tien_mat_display",
        "chuyen_khoan_display",
        "vnpay_display",
        "no_display",
        "chi_display",
        "tong_display",
        "danh_thu_rong_display",
        "created_by"
    )
    list_filter = ("shift", "revenue_date", "created_at")
    search_fields = ("note", "created_by__username")
    date_hierarchy = "revenue_date"
    ordering = ("-revenue_date", "-created_at")
    
    readonly_fields = ("tong", "danh_thu_rong", "chi", "created_at", "updated_at", "receipt_preview")
    
    fieldsets = (
        ("Thông tin ca", {
            "fields": ("revenue_date", "shift", "created_by")
        }),
        ("Doanh thu", {
            "fields": ("tien_mat", "chuyen_khoan", "vnpay", "no")
        }),
        ("Tổng hợp (tự động)", {
            "fields": ("chi", "tong", "danh_thu_rong"),
            "classes": ("collapse",)
        }),
        ("Chứng từ & Ghi chú", {
            "fields": ("receipt_image", "receipt_preview", "note")
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [RevenueExpenseInline]
    
    def shift_display(self, obj):
        colors = {
            'sang': '#17a2b8',
            'chieu': '#ffc107',
            'toi': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.shift, '#6c757d'),
            obj.get_shift_display()
        )
    shift_display.short_description = "Ca"
    
    def tien_mat_display(self, obj):
        color = "#dc3545" if obj.tien_mat < 0 else "#28a745"
        return format_html('<span style="color: {};">{:,.0f}</span>', color, obj.tien_mat)
    tien_mat_display.short_description = "Tiền mặt"
    
    def chuyen_khoan_display(self, obj):
        return format_html('{:,.0f}', obj.chuyen_khoan)
    chuyen_khoan_display.short_description = "CK"
    
    def vnpay_display(self, obj):
        return format_html('{:,.0f}', obj.vnpay)
    vnpay_display.short_description = "VNPay"
    
    def no_display(self, obj):
        return format_html('{:,.0f}', obj.no)
    no_display.short_description = "Nợ"
    
    def chi_display(self, obj):
        return format_html('<strong style="color: #dc3545;">{:,.0f}</strong>', obj.chi)
    chi_display.short_description = "Chi"
    
    def tong_display(self, obj):
        return format_html('<strong>{:,.0f}</strong>', obj.tong)
    tong_display.short_description = "Tổng"
    
    def danh_thu_rong_display(self, obj):
        color = "#28a745" if obj.danh_thu_rong >= 0 else "#dc3545"
        return format_html(
            '<strong style="color: {}; font-size: 14px;">{:,.0f} VND</strong>', 
            color, 
            obj.danh_thu_rong
        )
    danh_thu_rong_display.short_description = "Danh thu ròng"
    
    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px;" /></a>',
                obj.receipt_image.url,
                obj.receipt_image.url
            )
        return "Chưa có hình ảnh"
    receipt_preview.short_description = "Xem trước chứng từ"


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
        return format_html('<code>{}</code>', str(obj.payroll_id)[:8])
    payroll_id_short.short_description = "Mã BL"
    
    def employee_info(self, obj):
        url = reverse("admin:employee_employee_change", args=[obj.employee.pk])
        return format_html(
            '<a href="{}" target="_blank"><strong>{}</strong></a><br/><small style="color: #6c757d;">{}</small>',
            url,
            f"{obj.employee.first_name} {obj.employee.last_name}",
            obj.employee.employee_id
        )
    employee_info.short_description = "Nhân viên"
    
    def period_display(self, obj):
        return format_html(
            '{}<br/><small style="color: #6c757d;">đến</small><br/>{}',
            obj.start_date.strftime('%d/%m/%Y'),
            obj.end_date.strftime('%d/%m/%Y')
        )
    period_display.short_description = "Kỳ lương"
    
    def total_hours_display(self, obj):
        details_count = obj.payroll_details.count()
        return format_html(
            '<strong>{} giờ</strong> <small style="color: #6c757d;">({} ngày)</small>',
            obj.total_hours,
            details_count
        )
    total_hours_display.short_description = "Chi tiết giờ"
    
    def net_salary_display(self, obj):
        return format_html('<strong style="color: #28a745; font-size: 14px;">{:,.0f} VND</strong>', obj.net_salary)
    net_salary_display.short_description = "Lương thực nhận"
    
    def status_badge(self, obj):
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
        count = 0
        for payroll in queryset:
            payroll.generate_details_from_attendance()
            count += 1
        self.message_user(request, f"Đã tạo chi tiết cho {count} bảng lương từ dữ liệu chấm công")
    generate_payroll_details.short_description = "🔄 Tạo chi tiết từ chấm công"
    
    def calculate_salaries(self, request, queryset):
        count = 0
        for payroll in queryset:
            payroll.calculate_salary()
            count += 1
        self.message_user(request, f"Đã tính toán lương cho {count} bảng lương")
    calculate_salaries.short_description = "🧮 Tính toán lương"
    
    def approve_payrolls(self, request, queryset):
        for payroll in queryset:
            payroll.status = 'approved'
            payroll.approved_by = request.user
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
        return f"{obj.payroll_summary.employee.first_name} {obj.payroll_summary.employee.last_name}"
    employee_name.short_description = "Nhân viên"
    
    def status_display(self, obj):
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