from django import forms
from .models import (
    ExpenseCategory, Expense, RevenueExpense, Revenue, 
    PayrollSummary, PayrollDetail
)
from employee.models import Employee


# ======= 1. FORM LOẠI CHI PHÍ =======
class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nhập tên loại chi phí"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Mô tả loại chi phí"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }


# ======= 2A. FORM CHI PHÍ ĐỘC LẬP =======
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "category", 
            "description", 
            "amount", 
            "expense_date",
            "receipt_image",
            "note"
        ]
        widgets = {
            "category": forms.Select(attrs={
                "class": "form-select"
            }),
            "description": forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhập mô tả chi tiết...',
                'style': 'resize: vertical; font-size: 15px;'
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "expense_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "receipt_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ghi chú thêm"
            })
        }
        labels = {
            "category": "Loại chi phí",
            "description": "Mô tả",
            "amount": "Số tiền (VND)",
            "expense_date": "Ngày chi",
            "receipt_image": "Hóa đơn/Chứng từ",
            "note": "Ghi chú"
        }


# ======= 2B. FORM CHI PHÍ LIÊN KẾT DOANH THU =======
class RevenueExpenseForm(forms.ModelForm):
    """Form nhập chi phí từ phiếu doanh thu (chỉ 3 trường)"""
    class Meta:
        model = RevenueExpense
        fields = ["category", "description", "amount", "note"]
        widgets = {
            "category": forms.Select(attrs={
                "class": "form-select"
            }),
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Mô tả chi phí"
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ghi chú (nếu có)"
            })
        }
        labels = {
            "category": "Loại chi phí",
            "description": "Mô tả",
            "amount": "Số tiền (VND)",
            "note": "Ghi chú"
        }


# ======= 3. FORM DOANH THU =======
class RevenueForm(forms.ModelForm):
    class Meta:
        model = Revenue
        fields = [
            "revenue_date",
            "shift",
            "tien_mat",
            "chuyen_khoan",
            "vnpay",
            "no",
            "receipt_image",
            "note"
        ]
        widgets = {
            "revenue_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "shift": forms.Select(attrs={
                "class": "form-select"
            }),
            "tien_mat": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "chuyen_khoan": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "vnpay": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "no": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "receipt_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ghi chú thêm"
            })
        }
        labels = {
            "revenue_date": "Ngày",
            "shift": "Ca",
            "tien_mat": "Tiền mặt (VND)",
            "chuyen_khoan": "Chuyển khoản (VND)",
            "vnpay": "VNPay (VND)",
            "no": "Nợ (VND)",
            "receipt_image": "Hình ảnh chứng từ",
            "note": "Ghi chú"
        }


# ======= 4. FORM BẢNG LƯƠNG TỔNG =======
class PayrollSummaryForm(forms.ModelForm):
    class Meta:
        model = PayrollSummary
        fields = [
            "employee",
            "start_date",
            "end_date",
            "hourly_rate",
            "bonus",
            "advance",
            "deduction",
            "notes"
        ]
        widgets = {
            "employee": forms.Select(attrs={
                "class": "form-select"
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "hourly_rate": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "bonus": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "advance": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "deduction": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0",
                "step": "0.01"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ghi chú về bảng lương"
            })
        }
        labels = {
            "employee": "Nhân viên",
            "start_date": "Ngày bắt đầu kỳ lương",
            "end_date": "Ngày kết thúc kỳ lương",
            "hourly_rate": "Lương theo giờ (VND)",
            "bonus": "Tiền thưởng (VND)",
            "advance": "Tiền ứng trước (VND)",
            "deduction": "Khấu trừ/Phạt (VND)",
            "notes": "Ghi chú"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ hiển thị nhân viên đang làm việc
        self.fields['employee'].queryset = Employee.objects.filter(
            employment_status='Active'
        ).order_by('first_name', 'last_name')


# ======= 5. FORM CHI TIẾT BẢNG LƯƠNG =======
class PayrollDetailForm(forms.ModelForm):
    class Meta:
        model = PayrollDetail
        fields = [
            "work_date",
            "check_in_time",
            "check_out_time",
            "hours_worked",
            "status",
            "note"
        ]
        widgets = {
            "work_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "check_in_time": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
            "check_out_time": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
            "hours_worked": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "readonly": True
            }),
            "status": forms.Select(attrs={
                "class": "form-select"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ghi chú"
            })
        }
        labels = {
            "work_date": "Ngày làm việc",
            "check_in_time": "Giờ vào",
            "check_out_time": "Giờ ra",
            "hours_worked": "Số giờ làm",
            "status": "Trạng thái",
            "note": "Ghi chú"
        }


# ======= 6. FORM TÌM KIẾM/LỌC CHI PHÍ =======
class ExpenseFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        empty_label="Tất cả loại chi phí",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    status = forms.ChoiceField(
        choices=[("", "Tất cả trạng thái")] + Expense.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Từ ngày"
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Đến ngày"
        })
    )


# ======= 7. FORM TÌM KIẾM/LỌC DOANH THU =======
class RevenueFilterForm(forms.Form):
    shift = forms.ChoiceField(
        choices=[("", "Tất cả ca")] + Revenue._meta.get_field('shift').choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Từ ngày"
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Đến ngày"
        })
    )


# ======= 8. FORM TÌM KIẾM/LỌC BẢNG LƯƠNG =======
class PayrollFilterForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all().order_by('first_name', 'last_name'),
        required=False,
        empty_label="Tất cả nhân viên",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    status = forms.ChoiceField(
        choices=[("", "Tất cả trạng thái")] + PayrollSummary.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Từ ngày"
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Đến ngày"
        })
    )