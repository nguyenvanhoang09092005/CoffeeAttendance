from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib import messages
from .utils import create_notification

from django.contrib.auth import get_user_model

User = get_user_model()

# ==============================
# Thêm nhân viên
# ==============================
def add_employee(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        employee_id = request.POST.get('employee_id')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        position = request.POST.get('position')
        joining_date = request.POST.get('joining_date')
        mobile_number = request.POST.get('mobile_number')
        address = request.POST.get('address')
        employee_image = request.FILES.get('employee_image')
        bank_account_number = request.POST.get('bank_account_number')
        bank_name = request.POST.get('bank_name')
        employment_status = request.POST.get('employment_status', 'Active')
        resignation_date = request.POST.get('resignation_date')

        # Lưu nhân viên
        employee = Employee.objects.create(
            first_name=first_name,
            last_name=last_name,
            email = email,
            employee_id=employee_id,
            gender=gender,
            date_of_birth=date_of_birth,
            position=position,
            joining_date=joining_date,
            mobile_number=mobile_number,
            address = address,
            employee_image=employee_image,
            bank_account_number = bank_account_number,
            bank_name = bank_name,
            employment_status = employment_status,
            resignation_date = resignation_date,

        )
        # 👉 Tạo User (username = email hoặc employee_id)
        username = email if email else f"user_{mobile_number}"
        default_password = "12345678"  # mật khẩu mặc định

        user = User.objects.create_user(
            username=username,
            email=email,
            password=default_password,
            first_name=first_name,
            last_name=last_name
        )

        # 👉 Tạo Employee và liên kết User
        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            gender=gender,
            date_of_birth=date_of_birth,
            position=position,
            joining_date=joining_date,
            mobile_number=mobile_number,
            address=address,
            employee_image=employee_image,
            bank_account_number=bank_account_number,
            bank_name=bank_name,
            employment_status=employment_status,
            resignation_date=resignation_date,
        )

        create_notification(request.user, f"Đã thêm nhân viên: {employee.first_name} {employee.last_name}")
        messages.success(request, f"Nhân viên {employee.first_name} {employee.last_name} được thêm thành công. Tài khoản đăng nhập: {username}, mật khẩu mặc định: {default_password}")

        return redirect("employee_list")

    return render(request, "employees/add-employee.html")


# ==============================
# Danh sách nhân viên
# ==============================
def employee_list(request):
    employee_list = Employee.objects.all()
    unread_notification = request.user.notification_set.filter(is_read=False)
    context = {
        'employee_list': employee_list,
        'unread_notification': unread_notification
    }
    return render(request, "employees/employees.html", context)


# ==============================
# Sửa thông tin nhân viên
# ==============================
def edit_employee(request, slug):
    employee = get_object_or_404(Employee, slug=slug)
    if request.method == "POST":
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.employee_id = request.POST.get('employee_id')
        employee.gender = request.POST.get('gender')
        employee.date_of_birth = request.POST.get('date_of_birth')
        employee.position = request.POST.get('position')
        employee.joining_date = request.POST.get('joining_date')
        employee.mobile_number = request.POST.get('mobile_number')
        employee.address = request.POST.get('address')
        if request.FILES.get('employee_image'):
            employee.employee_image = request.FILES.get('employee_image')
        employee.bank_account_number = request.POST.get('bank_account_number')
        employee.bank_name = request.POST.get('bank_name')
        employee.employment_status = request.POST.get('employment_status', 'Active')
        resignation_date = request.POST.get('resignation_date')
        employee.resignation_date = resignation_date if resignation_date else None

        employee.save()
        create_notification(request.user, f"Updated Employee: {employee.first_name} {employee.last_name}")
        return redirect("employee_list")

    return render(request, "employees/edit-employee.html", {'employee': employee})


# ==============================
# Xem chi tiết nhân viên
# ==============================
def view_employee(request, slug):
    employee = get_object_or_404(Employee, slug=slug)
    context = {
        'employee': employee
    }
    return render(request, "employees/employee-details.html", context)


# ==============================
# Xóa nhân viên
# ==============================
def delete_employee(request, slug):
    if request.method == "POST":
        employee = get_object_or_404(Employee, slug=slug)
        employee_name = f"{employee.first_name} {employee.last_name}"
        employee.delete()
        create_notification(request.user, f"Deleted Employee: {employee_name}")
        return redirect('employee_list')
    return HttpResponseForbidden()
