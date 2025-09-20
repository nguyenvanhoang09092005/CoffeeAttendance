from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages

from .models import Attendance
from employee.models import Employee
from Shift.models import Shift

import uuid

def attendance_list(request):
    """
    Bảng tổng hợp chấm công theo nhân viên trong tháng hiện tại.
    """
    today = timezone.now().date()
    first_day = today.replace(day=1)

    employees = Employee.objects.all()
    data = []

    for emp in employees:
        latest = emp.latest_attendance
        if not latest or latest.created_at.date() != today:
            Attendance.objects.create(employee=emp)

        attendances = Attendance.objects.filter(
            employee=emp,
             unique_token=str(uuid.uuid4()),
            created_at__date__gte=first_day,
            created_at__date__lte=today
        )

        late_count = sum(1 for a in attendances if a.is_late)
        early_count = sum(1 for a in attendances if a.left_early)
        ontime_count = sum(
            1 for a in attendances
            if a.check_in_time and not a.is_late and not a.left_early
        )
        total = attendances.count()

        data.append({
            "id": emp.id,
            "employee_id": emp.employee_id,
            "name": f"{emp.first_name} {emp.last_name}",
            "employee_image": emp.employee_image.url if emp.employee_image else None,
            "late": late_count,
            "early": early_count,
            "ontime": ontime_count,
            "total": total,
            "position": emp.position,
        })

    context = {
        "today": today,
        "month": today.strftime("%m/%Y"),
        "data": data,
    }
    return render(request, "attendance/attendance_list.html", context)


def get_current_shift():
    """Xác định ca hiện tại dựa trên giờ hệ thống"""
    now = timezone.localtime().time()
    shifts = Shift.objects.all()
    for shift in shifts:
        if shift.start_time <= now <= shift.end_time:
            return shift
    return None



def attendance_manual(request):
    employees = Employee.objects.all()
    shifts = Shift.objects.all()

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        shift_id = request.POST.get("shift_id")
        note = request.POST.get("note")

        attendance = Attendance.objects.create(
            employee_id=employee_id,
            shift_id=shift_id,
            check_in_time=timezone.now(),
            method="manual",
            note=note,
            manual_by=request.user.employee if hasattr(request.user, "employee") else None,
        )
        messages.success(request, f"Đã thêm chấm công thủ công cho {attendance.employee}")
        return redirect("attendance:attendance_list")

    return render(request, "attendance/manual.html", {
        "employees": employees,
        "shifts": shifts
    })


#staff


def attendance_toggle(request, shift_id):
    """Nhân viên thực hiện check-in/check-out"""
    if not request.user.is_authenticated:
        messages.error(request, "Vui lòng đăng nhập để tiếp tục.")
        return redirect("login")

    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Tài khoản không gắn với nhân viên.")
        return redirect("attendance:attendance_list")

    shift = get_object_or_404(Shift, id=shift_id)

    # Kiểm tra xem đã có record chưa
    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        shift=shift,
        created_at__date=timezone.now().date()
    )

    # Nếu chưa check-in
    if not attendance.check_in_time:
        if request.method == "POST":
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            face_image = request.FILES.get("face_image")

            if not face_image:
                messages.error(request, "Vui lòng chụp ảnh khuôn mặt để xác thực!")
                return redirect(request.path)

            attendance.check_in_time = timezone.now()
            attendance.latitude = latitude
            attendance.longitude = longitude
            attendance.face_image = face_image
            attendance.face_verified = True  # TODO: gọi AI để xác thực khuôn mặt
            attendance.save()

            messages.success(request, f"✅ {employee} đã check-in thành công vào {shift}")
       
            return render(request, "staff/Attendance/checkin.html", {"attendance": attendance, "shift": shift})

        return render(request, "staff/Attendance/checkin.html", {"attendance": attendance, "shift": shift})

    elif not attendance.check_out_time:
        if request.method == "POST":
            attendance.check_out_time = timezone.now()
            attendance.save()
            messages.success(request, f"✅ {employee} đã check-out thành công khỏi {shift}")
            return render(request, "staff/Attendance/checkin.html", {"attendance": attendance, "shift": shift})

        return render(request, "staff/Attendance/checkin.html", {"attendance": attendance, "shift": shift})

    # Nếu đã check-out rồi
    else:
        messages.warning(request, "Bạn đã hoàn tất ca làm hôm nay.")
        return render(request, "staff/Attendance/checkin.html", {"attendance": attendance, "shift": shift})



def qr_checkin(request, qr_token):
    """Khi quét QR → tìm shift rồi chuyển tới trang chấm công"""
    shift = get_object_or_404(Shift, qr_token=qr_token)
    return redirect("attendance:toggle", shift_id=shift.id)