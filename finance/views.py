from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    ExpenseCategory, Expense, Revenue, 
    PayrollSummary, PayrollDetail
)
from .forms import (
    ExpenseForm, RevenueForm, PayrollSummaryForm,
    ExpenseFilterForm, RevenueFilterForm, PayrollFilterForm, ExpenseCategoryForm
)
from employee.models import Employee


# ======= DASHBOARD =======
@login_required
def dashboard(request):
    """Trang tổng quan tài chính"""
    
    # Lấy tháng hiện tại
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Tổng chi phí
    total_expense = Expense.objects.filter(
        status='approved'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    expense_this_month = Expense.objects.filter(
        status='approved',
        expense_date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Tổng doanh thu
    total_revenue = Revenue.objects.aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal(0)
    
    revenue_this_month = Revenue.objects.filter(
        revenue_date__gte=start_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Lợi nhuận
    profit = total_revenue - total_expense
    profit_this_month = revenue_this_month - expense_this_month
    
    # Bảng lương chờ duyệt
    pending_payrolls = PayrollSummary.objects.filter(
        status='draft'
    ).count()
    
    # Dữ liệu gần đây
    recent_expenses = Expense.objects.select_related(
        'category', 'created_by'
    ).order_by('-expense_date', '-created_at')[:5]
    
    recent_revenues = Revenue.objects.select_related(
        'created_by'
    ).order_by('-revenue_date', '-created_at')[:5]
    
    recent_payrolls = PayrollSummary.objects.select_related(
        'employee'
    ).order_by('-created_at')[:5]
    
    context = {
        "total_expense": total_expense,
        "expense_this_month": expense_this_month,
        "total_revenue": total_revenue,
        "revenue_this_month": revenue_this_month,
        "profit": profit,
        "profit_this_month": profit_this_month,
        "pending_payrolls": pending_payrolls,
        "recent_expenses": recent_expenses,
        "recent_revenues": recent_revenues,
        "recent_payrolls": recent_payrolls,
    }
    
    return render(request, "finance/dashboard.html", context)


# ======= CHI PHÍ =======

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
        
        # Redirect về category detail nếu có
        category_id = request.GET.get('from_category')
        if category_id:
            return redirect("finance:expense_category_detail", pk=category_id)
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
        
        # Redirect về category detail nếu có
        category_id = request.GET.get('from_category')
        if category_id:
            return redirect("finance:expense_category_detail", pk=category_id)
        return redirect("finance:expense_detail", pk=pk)
    
    return render(request, "finance/expense_confirm_reject.html", {"expense": expense})


@login_required
def expense_category_delete(request, pk):
    """Xóa danh mục chi phí"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    # Kiểm tra xem có chi phí nào đang sử dụng danh mục này không
    if category.expenses.exists():
        messages.error(
            request, 
            f"Không thể xóa danh mục '{category.name}' vì đang có {category.expenses.count()} chi phí sử dụng!"
        )
        return redirect("finance:expense_category_list")
    
    if request.method == "POST":
        category.delete()
        messages.success(request, "Đã xóa danh mục chi phí!")
        return redirect("finance:expense_category_list")
    
    return render(request, "finance/expense_category_confirm_delete.html", {"category": category})


@login_required
def expense_list(request):
    """Danh sách chi phí"""
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
    
    # Tổng số tiền
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    context = {
        "expenses": expenses,
        "filter_form": filter_form,
        "total_amount": total_amount,
    }
    return render(request, "finance/expense_list.html", context)


@login_required
def expense_create(request):
    """Tạo chi phí mới"""
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
    """Chi tiết chi phí"""
    expense = get_object_or_404(
        Expense.objects.select_related('category', 'created_by', 'approved_by'),
        pk=pk
    )
    return render(request, "finance/expense_detail.html", {"expense": expense})


@login_required
def expense_update(request, pk):
    """Cập nhật chi phí"""
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
    """Xóa chi phí"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Đã xóa chi phí!")
        return redirect("finance:expense_list")
    
    return render(request, "finance/expense_confirm_delete.html", {"expense": expense})


# ======= DOANH THU =======
@login_required
def revenue_list(request):
    """Danh sách doanh thu"""
    revenues = Revenue.objects.select_related(
        'created_by'
    ).order_by('-revenue_date', '-created_at')
    
    # Áp dụng filter
    filter_form = RevenueFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('category'):
            revenues = revenues.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data.get('start_date'):
            revenues = revenues.filter(revenue_date__gte=filter_form.cleaned_data['start_date'])
        if filter_form.cleaned_data.get('end_date'):
            revenues = revenues.filter(revenue_date__lte=filter_form.cleaned_data['end_date'])
    
    # Tổng số tiền
    total_amount = revenues.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    context = {
        "revenues": revenues,
        "filter_form": filter_form,
        "total_amount": total_amount,
    }
    return render(request, "finance/revenue_list.html", context)


@login_required
def revenue_create(request):
    """Tạo doanh thu mới"""
    if request.method == "POST":
        form = RevenueForm(request.POST)
        if form.is_valid():
            revenue = form.save(commit=False)
            revenue.created_by = request.user
            revenue.save()
            messages.success(request, "Đã ghi nhận doanh thu!")
            return redirect("finance:revenue_list")
    else:
        form = RevenueForm()
    
    return render(request, "finance/revenue_form.html", {"form": form})


@login_required
def revenue_detail(request, pk):
    """Chi tiết doanh thu"""
    revenue = get_object_or_404(
        Revenue.objects.select_related('created_by'),
        pk=pk
    )
    return render(request, "finance/revenue_detail.html", {"revenue": revenue})


@login_required
def revenue_update(request, pk):
    """Cập nhật doanh thu"""
    revenue = get_object_or_404(Revenue, pk=pk)
    
    if request.method == "POST":
        form = RevenueForm(request.POST, instance=revenue)
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