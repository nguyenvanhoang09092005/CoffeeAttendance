from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser, PasswordResetRequest
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string


# ==============================
# ĐĂNG KÝ TÀI KHOẢN
# ==============================
def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST.get('role')  

        # Tạo người dùng mới
        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        # Gán vai trò
        if role == 'employee':
            user.is_employee = True
        elif role == 'manager':
            user.is_manager = True
        elif role == 'admin':
            user.is_admin = True

        user.save()
        login(request, user)
        messages.success(request, 'Đăng ký tài khoản thành công!')
        return redirect('index')

    return render(request, 'authentication/register.html')


# ==============================
# ĐĂNG NHẬP
# ==============================
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Đăng nhập thành công!')

            # Điều hướng theo vai trò
            if user.is_admin or user.is_manager:  # admin + manager cùng dashboard
                return redirect('admin_dashboard')
            elif user.is_employee:
                return redirect('staff_dashboard')
            else:
                messages.error(request, 'Không xác định được vai trò của người dùng.')
                return redirect('index')
        else:
            messages.error(request, 'Email hoặc mật khẩu không đúng. Vui lòng thử lại.')

    return render(request, 'authentication/login.html')


# ==============================
# QUÊN MẬT KHẨU
# ==============================
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = CustomUser.objects.filter(email=email).first()

        if user:
            token = get_random_string(32)
            reset_request = PasswordResetRequest.objects.create(user=user, email=email, token=token)
            reset_request.send_reset_email()
            messages.success(request, 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.')
        else:
            messages.error(request, 'Không tìm thấy tài khoản với email này.')

    return render(request, 'authentication/forgot-password.html')


# ==============================
# ĐẶT LẠI MẬT KHẨU
# ==============================
def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).first()

    if not reset_request or not reset_request.is_valid():
        messages.error(request, 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.')
        return redirect('index')

    if request.method == 'POST':
        new_password = request.POST['new_password']
        reset_request.user.set_password(new_password)
        reset_request.user.save()
        messages.success(request, 'Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay bây giờ.')
        return redirect('login')

    return render(request, 'authentication/reset_password.html', {'token': token})


# ==============================
# ĐĂNG XUẤT
# ==============================
def logout_view(request):
    logout(request)
    messages.success(request, 'Bạn đã đăng xuất khỏi hệ thống.')
    return redirect('index')
