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
    ExpenseFilterForm, RevenueFilterForm, PayrollFilterForm
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
        status='pending'
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
            # Gán người tạo
            try:
                expense.created_by = request.user.employee_profile
            except:
                expense.created_by = None
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
            # Gán người tạo
            try:
                revenue.created_by = request.user.employee_profile
            except:
                revenue.created_by = None
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
    """Tạo bảng lương mới"""
    if request.method == "POST":
        form = PayrollSummaryForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            # Gán người tạo
            try:
                payroll.created_by = request.user.employee_profile
            except:
                payroll.created_by = None
            payroll.save()
            
            # Tự động tạo chi tiết từ chấm công
            payroll.generate_details_from_attendance()
            
            messages.success(
                request, 
                f"Đã tạo bảng lương cho {payroll.employee.first_name} {payroll.employee.last_name}!"
            )
            return redirect("finance:payroll_detail", pk=payroll.pk)
    else:
        form = PayrollSummaryForm()
    
    return render(request, "finance/payroll_form.html", {"form": form})


@login_required
def payroll_detail(request, pk):
    """Chi tiết bảng lương"""
    payroll = get_object_or_404(
        PayrollSummary.objects.select_related(
            'employee', 'created_by', 'approved_by'
        ).prefetch_related('payroll_details'),
        pk=pk
    )
    
    # Lấy chi tiết
    details = payroll.payroll_details.all().order_by('work_date')
    
    context = {
        "payroll": payroll,
        "details": details,
    }
    return render(request, "finance/payroll_detail.html", context)


@login_required
def payroll_update(request, pk):
    """Cập nhật bảng lương"""
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    # Không cho phép cập nhật nếu đã duyệt hoặc đã thanh toán
    if payroll.status in ['approved', 'paid']:
        messages.error(request, "Không thể cập nhật bảng lương đã duyệt hoặc đã thanh toán!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        form = PayrollSummaryForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            # Tính lại lương
            payroll.calculate_salary()
            messages.success(request, "Đã cập nhật bảng lương!")
            return redirect("finance:payroll_detail", pk=pk)
    else:
        form = PayrollSummaryForm(instance=payroll)
    
    return render(request, "finance/payroll_form.html", {
        "form": form,
        "payroll": payroll
    })


@login_required
def payroll_regenerate(request, pk):
    """Tạo lại chi tiết bảng lương từ chấm công"""
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    # Không cho phép nếu đã duyệt
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
    """Phê duyệt bảng lương"""
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    if request.method == "POST":
        payroll.status = 'approved'
        try:
            payroll.approved_by = request.user.employee_profile
        except:
            payroll.approved_by = None
        payroll.approved_at = timezone.now()
        payroll.save()
        
        messages.success(request, "Đã phê duyệt bảng lương!")
        return redirect("finance:payroll_detail", pk=pk)
    
    return render(request, "finance/payroll_confirm_approve.html", {"payroll": payroll})


@login_required
def payroll_delete(request, pk):
    """Xóa bảng lương"""
    payroll = get_object_or_404(PayrollSummary, pk=pk)
    
    # Không cho phép xóa nếu đã duyệt hoặc đã thanh toán
    if payroll.status in ['approved', 'paid']:
        messages.error(request, "Không thể xóa bảng lương đã duyệt hoặc đã thanh toán!")
        return redirect("finance:payroll_detail", pk=pk)
    
    if request.method == "POST":
        payroll.delete()
        messages.success(request, "Đã xóa bảng lương!")
        return redirect("finance:payroll_list")
    
    return render(request, "finance/payroll_confirm_delete.html", {"payroll": payroll})