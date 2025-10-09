from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    ExpenseCategory, Expense, RevenueExpense, Revenue, 
    PayrollSummary, PayrollDetail
)
from .forms import (
    ExpenseForm, RevenueExpenseForm, RevenueForm, PayrollSummaryForm,
    ExpenseFilterForm, RevenueFilterForm, PayrollFilterForm, ExpenseCategoryForm
)
from employee.models import Employee



# ======= DASHBOARD =======
@login_required
def dashboard(request):
    """Trang tổng quan tài chính"""
    
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # ===== TỔNG CHI PHÍ (bao gồm 3 loại) =====
    
    # 1. Chi phí độc lập (đã duyệt)
    standalone_expense = Expense.objects.filter(
        status='approved'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # 2. Chi phí từ doanh thu
    revenue_expense = RevenueExpense.objects.all().aggregate(
        Sum('amount'))['amount__sum'] or Decimal(0)
    
    # 3. Tiền lương (đã thanh toán hoặc đã duyệt)
    payroll_expense = PayrollSummary.objects.filter(
        status__in=['paid', 'approved']
    ).aggregate(Sum('net_salary'))['net_salary__sum'] or Decimal(0)
    
    # Tổng chi phí = chi độc lập + chi doanh thu + lương
    total_expense = standalone_expense + revenue_expense + payroll_expense
    
    
    # ===== CHI PHÍ THÁNG NÀY =====
    
    # Chi phí độc lập tháng này
    standalone_expense_month = Expense.objects.filter(
        status='approved',
        expense_date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Chi phí từ doanh thu tháng này
    revenue_expense_month = RevenueExpense.objects.filter(
        expense_date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Tiền lương tháng này (theo ngày kết thúc kỳ lương)
    payroll_expense_month = PayrollSummary.objects.filter(
        status__in=['paid', 'approved'],
        end_date__gte=start_of_month
    ).aggregate(Sum('net_salary'))['net_salary__sum'] or Decimal(0)
    
    expense_this_month = standalone_expense_month + revenue_expense_month + payroll_expense_month
    
    
    # ===== DOANH THU =====
    
    # Tổng doanh thu
    total_revenue = Revenue.objects.aggregate(
        Sum('danh_thu_rong')
    )['danh_thu_rong__sum'] or Decimal(0)
    
    # Doanh thu tháng này
    revenue_this_month = Revenue.objects.filter(
        revenue_date__gte=start_of_month
    ).aggregate(Sum('danh_thu_rong'))['danh_thu_rong__sum'] or Decimal(0)
    
    
    # ===== LỢI NHUẬN =====
    
    # Lợi nhuận = Doanh thu - Tất cả chi phí (bao gồm lương)
    profit = total_revenue - total_expense
    profit_this_month = revenue_this_month - expense_this_month
    
    
    # ===== BẢNG LƯƠNG CHỜ DUYỆT =====
    pending_payrolls = PayrollSummary.objects.filter(
        status__in=['draft', 'pending']
    ).count()
    
    
    # ===== GỘP CHI PHÍ GẦN ĐÂY =====
    from itertools import chain
    from operator import attrgetter
    
    standalone_expenses = Expense.objects.select_related(
        'category', 'created_by'
    ).order_by('-expense_date', '-created_at')[:10]
    
    revenue_expenses = RevenueExpense.objects.select_related(
        'category', 'revenue', 'created_by'
    ).order_by('-expense_date', '-created_at')[:10]
    
    # Gộp và sắp xếp
    all_expenses = sorted(
        chain(standalone_expenses, revenue_expenses),
        key=attrgetter('expense_date', 'created_at'),
        reverse=True
    )[:5]
    
    
    # ===== DOANH THU & BẢNG LƯƠNG GẦN ĐÂY =====
    recent_revenues = Revenue.objects.select_related(
        'created_by'
    ).order_by('-revenue_date', '-created_at')[:5]
    
    recent_payrolls = PayrollSummary.objects.select_related(
        'employee'
    ).order_by('-created_at')[:5]
    
    
    # ===== CONTEXT =====
    context = {
        # Tổng chi phí
        "total_expense": total_expense,
        "standalone_expense": standalone_expense,
        "revenue_expense": revenue_expense,
        "payroll_expense": payroll_expense,  # MỚI
        "expense_this_month": expense_this_month,
        
        # Doanh thu
        "total_revenue": total_revenue,
        "revenue_this_month": revenue_this_month,
        
        # Lợi nhuận
        "profit": profit,
        "profit_this_month": profit_this_month,
        
        # Bảng lương
        "pending_payrolls": pending_payrolls,
        
        # Danh sách gần đây
        "recent_expenses": all_expenses,
        "recent_revenues": recent_revenues,
        "recent_payrolls": recent_payrolls,
    }
    
    return render(request, "finance/dashboard.html", context)
# ======= LOẠI CHI PHÍ =======

@login_required
def expense_category_list(request):
    """Danh sách danh mục chi phí"""
    categories = ExpenseCategory.objects.all().order_by('name')
    
    context = {
        "categories": categories,
    }
    return render(request, "finance/expense_category_list.html", context)


@login_required
def expense_category_create(request):
    """Tạo danh mục chi phí mới"""
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã tạo danh mục chi phí thành công!")
            return redirect("finance:expense_category_list")
    else:
        form = ExpenseCategoryForm()
    
    return render(request, "finance/expense_category_form.html", {"form": form})


@login_required
def expense_category_update(request, pk):
    """Cập nhật danh mục chi phí"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật danh mục chi phí!")
            return redirect("finance:expense_category_list")
    else:
        form = ExpenseCategoryForm(instance=category)
    
    return render(request, "finance/expense_category_form.html", {
        "form": form,
        "category": category
    })

@login_required
def expense_category_detail(request, pk):
    """Chi tiết danh mục chi phí"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    # Lấy tất cả chi phí của danh mục này
    expenses = category.expenses.select_related(
        'created_by', 'approved_by'
    ).order_by('-expense_date', '-created_at')
    
    # Thống kê theo trạng thái
    total_expenses = expenses.count()
    pending_expenses = expenses.filter(status='pending').count()
    approved_expenses = expenses.filter(status='approved').count()
    rejected_expenses = expenses.filter(status='rejected').count()
    
    # Tổng số tiền theo trạng thái
    total_pending_amount = expenses.filter(status='pending').aggregate(
        Sum('amount'))['amount__sum'] or Decimal(0)
    total_approved_amount = expenses.filter(status='approved').aggregate(
        Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Filter theo trạng thái (nếu có)
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        expenses = expenses.filter(status=status_filter)
    
    context = {
        "category": category,
        "expenses": expenses,
        "total_expenses": total_expenses,
        "pending_expenses": pending_expenses,
        "approved_expenses": approved_expenses,
        "rejected_expenses": rejected_expenses,
        "total_pending_amount": total_pending_amount,
        "total_approved_amount": total_approved_amount,
        "status_filter": status_filter,
    }
    return render(request, "finance/expense_category_detail.html", context)

@login_required
def expense_category_delete(request, pk):
    """Xóa danh mục chi phí"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    # Kiểm tra có chi phí nào đang dùng không
    if category.standalone_expenses.exists() or category.revenue_expenses.exists():
        messages.error(
            request, 
            f"Không thể xóa danh mục '{category.name}' vì đang có chi phí sử dụng!"
        )
        return redirect("finance:expense_category_list")
    
    if request.method == "POST":
        category.delete()
        messages.success(request, "Đã xóa danh mục chi phí!")
        return redirect("finance:expense_category_list")
    
    return render(request, "finance/expense_category_confirm_delete.html", {"category": category})


# ======= CHI PHÍ ĐỘC LẬP =======

@login_required
def expense_list(request):
    """Danh sách chi phí độc lập"""
    expenses = Expense.objects.select_related(
        'category', 'created_by', 'approved_by'
    ).order_by('-expense_date', '-created_at')
    
    # Áp dụng filter
    filter_form = ExpenseFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('category'):
            expenses = expenses.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data.get('status'):
            expenses = expenses.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data.get('start_date'):
            expenses = expenses.filter(expense_date__gte=filter_form.cleaned_data['start_date'])
        if filter_form.cleaned_data.get('end_date'):
            expenses = expenses.filter(expense_date__lte=filter_form.cleaned_data['end_date'])
    
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    context = {
        "expenses": expenses,
        "filter_form": filter_form,
        "total_amount": total_amount,
    }
    return render(request, "finance/expense_list.html", context)


@login_required
def expense_create(request):
    """Tạo chi phí độc lập mới"""
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, "Đã tạo chi phí thành công!")
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm()
    
    return render(request, "finance/expense_form.html", {"form": form})


@login_required
def expense_detail(request, pk):
    """Chi tiết chi phí độc lập"""
    expense = get_object_or_404(
        Expense.objects.select_related('category', 'created_by', 'approved_by'),
        pk=pk
    )
    return render(request, "finance/expense_detail.html", {"expense": expense})


@login_required
def expense_update(request, pk):
    """Cập nhật chi phí độc lập"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật chi phí!")
            return redirect("finance:expense_detail", pk=pk)
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, "finance/expense_form.html", {
        "form": form,
        "expense": expense
    })


@login_required
def expense_delete(request, pk):
    """Xóa chi phí độc lập"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Đã xóa chi phí!")
        return redirect("finance:expense_list")
    
    return render(request, "finance/expense_confirm_delete.html", {"expense": expense})


@login_required
def expense_approve(request, pk):
    """Phê duyệt chi phí"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if expense.status != 'pending':
        messages.error(request, "Chỉ có thể phê duyệt chi phí đang chờ duyệt!")
        return redirect("finance:expense_detail", pk=pk)
    
    if request.method == "POST":
        expense.status = 'approved'
        expense.approved_by = request.user
        expense.save()
        
        messages.success(request, "Đã phê duyệt chi phí!")
        return redirect("finance:expense_detail", pk=pk)
    
    return render(request, "finance/expense_confirm_approve.html", {"expense": expense})


@login_required
def expense_reject(request, pk):
    """Từ chối chi phí"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if expense.status != 'pending':
        messages.error(request, "Chỉ có thể từ chối chi phí đang chờ duyệt!")
        return redirect("finance:expense_detail", pk=pk)
    
    if request.method == "POST":
        expense.status = 'rejected'
        expense.approved_by = request.user
        expense.save()
        
        messages.warning(request, "Đã từ chối chi phí!")
        return redirect("finance:expense_detail", pk=pk)
    
    return render(request, "finance/expense_confirm_reject.html", {"expense": expense})


# ======= DOANH THU =======

@login_required
def revenue_list(request):
    """Danh sách doanh thu"""
    revenues = Revenue.objects.select_related(
        'created_by'
    ).prefetch_related('expenses').order_by('-revenue_date', '-created_at')
    
    # Áp dụng filter
    filter_form = RevenueFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('shift'):
            revenues = revenues.filter(shift=filter_form.cleaned_data['shift'])
        if filter_form.cleaned_data.get('start_date'):
            revenues = revenues.filter(revenue_date__gte=filter_form.cleaned_data['start_date'])
        if filter_form.cleaned_data.get('end_date'):
            revenues = revenues.filter(revenue_date__lte=filter_form.cleaned_data['end_date'])
    
    # Tổng số tiền
    total_tong = revenues.aggregate(Sum('tong'))['tong__sum'] or Decimal(0)
    total_chi = revenues.aggregate(Sum('chi'))['chi__sum'] or Decimal(0)
    total_danh_thu_rong = revenues.aggregate(Sum('danh_thu_rong'))['danh_thu_rong__sum'] or Decimal(0)
    
    context = {
        "revenues": revenues,
        "filter_form": filter_form,
        "total_tong": total_tong,
        "total_chi": total_chi,
        "total_danh_thu_rong": total_danh_thu_rong,
    }
    return render(request, "finance/revenue_list.html", context)


@login_required
def revenue_create(request):
    """Tạo doanh thu mới"""
    from .models import ExpenseCategory
    
    if request.method == "POST":
        form = RevenueForm(request.POST, request.FILES)
        if form.is_valid():
            revenue = form.save(commit=False)
            revenue.created_by = request.user
            revenue.save()
            
            # Xử lý chi phí inline
            expense_categories = request.POST.getlist('expense_category[]')
            expense_amounts = request.POST.getlist('expense_amount[]')
            expense_descriptions = request.POST.getlist('expense_description[]')
            expense_notes = request.POST.getlist('expense_note[]')
            
            # Tạo các chi phí
            for i in range(len(expense_amounts)):
                amount = expense_amounts[i]
                description = expense_descriptions[i]
                
                # Chỉ tạo nếu có số tiền và mô tả
                if amount and description:
                    category_id = expense_categories[i] if i < len(expense_categories) and expense_categories[i] else None
                    note = expense_notes[i] if i < len(expense_notes) else ''
                    
                    RevenueExpense.objects.create(
                        revenue=revenue,
                        category_id=category_id,
                        description=description,
                        amount=Decimal(amount),
                        note=note
                    )
            
            messages.success(request, "Đã ghi nhận doanh thu!")
            return redirect("finance:revenue_detail", pk=revenue.pk)
    else:
        form = RevenueForm()
    
    # Lấy danh sách loại chi phí cho template
    expense_categories = ExpenseCategory.objects.filter(is_active=True).order_by('name')
    
    return render(request, "finance/revenue_form.html", {
        "form": form,
        "expense_categories": expense_categories
    })


@login_required
def revenue_detail(request, pk):
    """Chi tiết doanh thu"""
    revenue = get_object_or_404(
        Revenue.objects.select_related('created_by').prefetch_related('expenses__category'),
        pk=pk
    )
    
    # Danh sách chi phí của phiếu doanh thu này
    expenses = revenue.expenses.all().order_by('-created_at')
    
    context = {
        "revenue": revenue,
        "expenses": expenses,
    }
    return render(request, "finance/revenue_detail.html", context)


@login_required
def revenue_update(request, pk):
    """Cập nhật doanh thu"""
    revenue = get_object_or_404(Revenue, pk=pk)
    
    if request.method == "POST":
        form = RevenueForm(request.POST, request.FILES, instance=revenue)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật doanh thu!")
            return redirect("finance:revenue_detail", pk=pk)
    else:
        form = RevenueForm(instance=revenue)
    
    return render(request, "finance/revenue_form.html", {
        "form": form,
        "revenue": revenue
    })


@login_required
def revenue_delete(request, pk):
    """Xóa doanh thu"""
    revenue = get_object_or_404(Revenue, pk=pk)
    
    if request.method == "POST":
        revenue.delete()
        messages.success(request, "Đã xóa doanh thu!")
        return redirect("finance:revenue_list")
    
    return render(request, "finance/revenue_confirm_delete.html", {"revenue": revenue})


# ======= CHI PHÍ LIÊN KẾT DOANH THU =======

@login_required
def revenue_expense_create(request, revenue_pk):
    """Thêm chi phí vào phiếu doanh thu"""
    revenue = get_object_or_404(Revenue, pk=revenue_pk)
    
    if request.method == "POST":
        form = RevenueExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.revenue = revenue
            expense.save()
            messages.success(request, "Đã thêm chi phí vào phiếu doanh thu!")
            return redirect("finance:revenue_detail", pk=revenue_pk)
    else:
        form = RevenueExpenseForm()
    
    return render(request, "finance/revenue_expense_form.html", {
        "form": form,
        "revenue": revenue
    })


@login_required
def revenue_expense_update(request, pk):
    """Cập nhật chi phí liên kết doanh thu"""
    expense = get_object_or_404(RevenueExpense, pk=pk)
    
    if request.method == "POST":
        form = RevenueExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật chi phí!")
            return redirect("finance:revenue_detail", pk=expense.revenue.pk)
    else:
        form = RevenueExpenseForm(instance=expense)
    
    return render(request, "finance/revenue_expense_form.html", {
        "form": form,
        "expense": expense,
        "revenue": expense.revenue
    })


@login_required
def revenue_expense_delete(request, pk):
    """Xóa chi phí liên kết doanh thu"""
    expense = get_object_or_404(RevenueExpense, pk=pk)
    revenue_pk = expense.revenue.pk
    
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Đã xóa chi phí!")
        return redirect("finance:revenue_detail", pk=revenue_pk)
    
    return render(request, "finance/revenue_expense_confirm_delete.html", {
        "expense": expense
    })


# ======= BẢNG LƯƠNG =======

@login_required
def payroll_list(request):
    """Danh sách bảng lương"""
    payrolls = PayrollSummary.objects.select_related(
        'employee', 'created_by', 'approved_by'
    ).order_by('-start_date', '-created_at')
    
    # Áp dụng filter
    filter_form = PayrollFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('employee'):
            payrolls = payrolls.filter(employee=filter_form.cleaned_data['employee'])
        if filter_form.cleaned_data.get('status'):
            payrolls = payrolls.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data.get('start_date'):
            payrolls = payrolls.filter(start_date__gte=filter_form.cleaned_data['start_date'])
        if filter_form.cleaned_data.get('end_date'):
            payrolls = payrolls.filter(end_date__lte=filter_form.cleaned_data['end_date'])
    
    context = {
        "payrolls": payrolls,
        "filter_form": filter_form,
    }
    return render(request, "finance/payroll_list.html", context)


@login_required
def payroll_create(request):
    employees = Employee.objects.all().order_by('first_name')

    if request.method == "POST":
        form = PayrollSummaryForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.created_by_id = request.user.id
            payroll.save()
            payroll.generate_details_from_attendance()
            messages.success(
                request, 
                f"Đã tạo bảng lương cho {payroll.employee.first_name} {payroll.employee.last_name}!"
            )
            return redirect("finance:payroll_detail", pk=payroll.pk)
    else:
        form = PayrollSummaryForm()

    return render(request, "finance/payroll_form.html", {
        "form": form,
        "employees": employees,
    })


@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(
        PayrollSummary.objects.select_related(
            'employee', 'created_by', 'approved_by'
        ).prefetch_related('payroll_details'),
        pk=pk
    )
    
    details = payroll.payroll_details.all().order_by('work_date')
    
    context = {
        "payroll": payroll,
        "details": details,
    }
    return render(request, "finance/payroll_detail.html", context)


@login_required
def payroll_update(request, pk):
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    employees = Employee.objects.all().order_by('first_name')
    
    if payroll.status in ['approved', 'paid']:
        messages.error(request, "Không thể cập nhật bảng lương đã duyệt hoặc đã thanh toán!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        form = PayrollSummaryForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            payroll.calculate_salary()
            messages.success(request, "Đã cập nhật bảng lương!")
            return redirect("finance:payroll_detail", pk=pk)
    else:
        form = PayrollSummaryForm(instance=payroll)
    
    return render(request, "finance/payroll_form.html", {
        "form": form,
        "payroll": payroll,
        "employees": employees,
    })


@login_required
def payroll_regenerate(request, pk):
    """Tạo lại chi tiết bảng lương từ chấm công"""
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    if payroll.status in ['approved', 'paid']:
        messages.error(request, "Không thể tạo lại chi tiết cho bảng lương đã duyệt!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        payroll.generate_details_from_attendance()
        messages.success(request, "Đã tạo lại chi tiết bảng lương từ dữ liệu chấm công!")
        return redirect("finance:payroll_detail", pk=pk)
    
    return render(request, "finance/payroll_confirm_regenerate.html", {"payroll": payroll})


@login_required
def payroll_approve(request, pk):
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    if payroll.status not in ['draft', 'pending']:
        messages.error(request, "Chỉ có thể phê duyệt bảng lương ở trạng thái Draft hoặc Pending!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        payroll.status = 'approved'
        payroll.approved_by = request.user
        payroll.approved_at = timezone.now()
        payroll.save()
        
        messages.success(request, "Đã phê duyệt bảng lương!")
        return redirect("finance:payroll_detail", pk=pk)
    
    return render(request, "finance/payroll_confirm_approve.html", {"payroll": payroll})


@login_required
def payroll_delete(request, pk):
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    if payroll.status in ['approved', 'paid']:
        messages.error(request, "Không thể xóa bảng lương đã duyệt hoặc đã thanh toán!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        payroll.delete()
        messages.success(request, "Đã xóa bảng lương!")
        return redirect("finance:payroll_list")
    
    return render(request, "finance/payroll_confirm_delete.html", {"payroll": payroll})


    # Nhân viên xem 
@login_required
def my_payroll_list(request):
    """Nhân viên xem bảng lương của chính mình"""
    try:
        # Lấy thông tin nhân viên từ user đang đăng nhập
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "Bạn chưa được liên kết với hồ sơ nhân viên nào!")
        return redirect("finance:dashboard")
    
    # Lấy tất cả bảng lương của nhân viên này
    payrolls = PayrollSummary.objects.filter(
        employee=employee
    ).select_related(
        'created_by', 'approved_by'
    ).order_by('-start_date', '-created_at')
    
    # Áp dụng filter theo thời gian
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', 'all')
    
    if start_date:
        payrolls = payrolls.filter(start_date__gte=start_date)
    if end_date:
        payrolls = payrolls.filter(end_date__lte=end_date)
    if status_filter != 'all':
        payrolls = payrolls.filter(status=status_filter)
    
    # Thống kê
    total_payrolls = payrolls.count()
    total_paid = payrolls.filter(status='paid').aggregate(
        Sum('net_salary'))['net_salary__sum'] or Decimal(0)
    total_pending = payrolls.filter(status__in=['draft', 'pending']).aggregate(
        Sum('net_salary'))['net_salary__sum'] or Decimal(0)
    total_approved = payrolls.filter(status='approved').aggregate(
        Sum('net_salary'))['net_salary__sum'] or Decimal(0)
    
    context = {
        "employee": employee,
        "payrolls": payrolls,
        "total_payrolls": total_payrolls,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "total_approved": total_approved,
        "start_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
    }
    return render(request, "staff/Finance/my_payroll_list.html", context)


@login_required
def my_payroll_detail(request, pk):
    """Nhân viên xem chi tiết bảng lương của chính mình"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "Bạn chưa được liên kết với hồ sơ nhân viên!")
        return redirect("finance:dashboard")
    
    # Chỉ cho phép xem bảng lương của chính mình
    payroll = get_object_or_404(
        PayrollSummary.objects.select_related(
            'employee', 'created_by', 'approved_by'
        ).prefetch_related('payroll_details'),
        pk=pk,
        employee=employee  # Quan trọng: chỉ lấy bảng lương của nhân viên này
    )
    
    details = payroll.payroll_details.all().order_by('work_date')
    
    context = {
        "payroll": payroll,
        "details": details,
        "employee": employee,
    }
    return render(request, "staff/Finance/my_payroll_detail.html", context)