# attendance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import math
import numpy as np
import cv2

import uuid
from django.contrib.auth.decorators import login_required


from .models import Attendance
from employee.models import Employee, EmployeeFace
from Shift.models import Shift, WeeklyShiftAssignment  
from employee.services.face_utils import compare_face  


ORIGIN_LAT = 16.095325 
ORIGIN_LON = 108.244254  
MAX_DISTANCE_METERS = 2.0  


# ---------- Helpers ----------
def haversine_distance(lat1, lon1, lat2, lon2):
    """Trả về khoảng cách giữa 2 toạ độ (mét) theo Haversine."""
    R = 6371000  # bán kính Trái Đất (m)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ======== Danh sách tổng hợp =========
def attendance_list(request):
    """
    Trang quản lý chấm công:
    - Bộ lọc tìm kiếm
    - Danh sách chi tiết
    - Trạng thái (đúng giờ, trễ, về sớm, nghỉ...)
    """

    today = timezone.now().date()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    employee_keyword = request.GET.get("employee")  # tên hoặc mã nhân viên
    shift_id = request.GET.get("shift")
    status = request.GET.get("status")

    # Nếu không chọn ngày -> mặc định trong tháng
    if not start_date or not end_date:
        first_day = today.replace(day=1)
        start_date = first_day
        end_date = today
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            start_date = today.replace(day=1)
            end_date = today

    # Lấy dữ liệu chấm công theo khoảng thời gian
    attendances = Attendance.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related("employee", "shift").order_by("-created_at")

    # Bộ lọc nhân viên
    if employee_keyword:
        attendances = attendances.filter(
            Q(employee__first_name__icontains=employee_keyword) |
            Q(employee__last_name__icontains=employee_keyword) |
            Q(employee__employee_id__icontains=employee_keyword)
        )

    # Bộ lọc ca
    if shift_id:
        attendances = attendances.filter(shift_id=shift_id)

    # Bộ lọc trạng thái
    if status:
        if status == "checked_in":
            attendances = attendances.filter(check_in_time__isnull=False)
        elif status == "checked_out":
            attendances = attendances.filter(check_out_time__isnull=False)
        elif status == "late":
            attendances = [a for a in attendances if a.is_late]
        elif status == "early":
            attendances = [a for a in attendances if a.left_early]
        elif status == "not_checked":
            attendances = attendances.filter(check_in_time__isnull=True, check_out_time__isnull=True)

    # Chuẩn hóa dữ liệu cho template
    data = []
    for idx, att in enumerate(attendances, start=1):
        # Xác định trạng thái
        if not att.check_in_time and not att.check_out_time:
            status_text = "Chưa check-in/out"
        elif att.is_late:
            status_text = "Đi trễ"
        elif att.left_early:
            status_text = "Về sớm"
        else:
            status_text = "Đúng giờ"

        # Tính số giờ làm
        work_hours = "-"
        if att.check_in_time and att.check_out_time:
            delta = att.check_out_time - att.check_in_time
            work_hours = round(delta.total_seconds() / 3600, 2)

        data.append({
            "stt": idx,
            "id": att.id,
            "employee_name": f"{att.employee.first_name} {att.employee.last_name}",
            "employee_id": att.employee.employee_id,
            "shift": att.shift.name if att.shift else "Không có",
            "date": att.created_at.strftime("%d/%m/%Y"),
            "check_in": att.check_in_time.strftime("%H:%M") if att.check_in_time else "-",
            "check_out": att.check_out_time.strftime("%H:%M") if att.check_out_time else "-",
            "hours": work_hours,
            "status": status_text,
            "location": att.location_note or "-",
            "gps": f"{att.latitude}, {att.longitude}" if att.latitude and att.longitude else "-",
            "face_image": att.face_image.url if att.face_image else None,
            "method": att.get_method_display(),
            "note": att.note or "",
        })

    # Lấy danh sách ca để filter
    shifts = Shift.objects.all()

    context = {
        "today": today,
        "start_date": start_date,
        "end_date": end_date,
        "data": data,
        "shifts": shifts,
    }
    return render(request, "attendance/attendance_list.html", context)

# ======== Lịch sử theo nhân viên =========
def attendance_history(request, emp_id):
    emp = get_object_or_404(Employee, pk=emp_id)

    # Lấy toàn bộ lịch sử chấm công theo nhân viên, mới nhất trước
    records = Attendance.objects.filter(employee=emp).order_by("-created_at")

    data = []
    for r in records:
        data.append({
            "employee_id": emp.id,
            "employee_name": emp.full_name if hasattr(emp, "full_name") else str(emp),
            "shift": str(r.shift) if r.shift else "--",
            "check_in_time": r.check_in_time.strftime("%H:%M:%S %d/%m/%Y") if r.check_in_time else None,
            "check_out_time": r.check_out_time.strftime("%H:%M:%S %d/%m/%Y") if r.check_out_time else None,
            "location_note": r.location_note if r.location_note else "--",
            "distance": f"{r.distance:.1f} m" if r.distance else "--",
            "status": r.status if hasattr(r, "status") else "--",   # nếu có trạng thái (đúng giờ, đi muộn…)
            "note": r.note if hasattr(r, "note") else None,         # nếu có ghi chú
            "created_at": r.created_at.strftime("%H:%M:%S %d/%m/%Y"),
        })

    return JsonResponse(data, safe=False)

def get_current_shift():
    now = timezone.localtime().time()
    shifts = Shift.objects.all()
    for shift in shifts:
        # giả sử shift.start_time và end_time là time objects
        if shift.start_time <= now <= shift.end_time:
            return shift
    return None


def qr_checkin(request, qr_token):
    """Khi quét QR → tìm shift rồi chuyển tới trang chấm công"""
    shift = get_object_or_404(Shift, qr_token=qr_token)
    return redirect("attendance:toggle", shift_id=shift.id)

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


@login_required
def my_attendance_history(request):
    
    # 1️⃣ Kiểm tra xem tài khoản có liên kết với employee không
    if not hasattr(request.user, "employee_profile"):
        messages.error(request, "Tài khoản của bạn chưa được liên kết với nhân viên trong hệ thống.")
        return redirect("home")

    employee = request.user.employee_profile  # chỉ dùng employee của chính user

    # 2️⃣ Lấy ngày hiện tại và thông tin lọc
    today = timezone.now().date()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status_filter = request.GET.get("status")

    try:
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            start_date = today.replace(day=1)
            end_date = today
    except ValueError:
        start_date = today.replace(day=1)
        end_date = today

    # 3️⃣ Truy vấn dữ liệu chấm công CHỈ của nhân viên này
    attendances = (
        Attendance.objects.filter(
            employee=employee,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        .select_related("shift", "matched_face")
        .order_by("-created_at")
    )

    # 4️⃣ Lọc theo trạng thái nếu có
    if status_filter:
        if status_filter == "checked_in":
            attendances = attendances.filter(check_in_time__isnull=False, check_out_time__isnull=True)
        elif status_filter == "checked_out":
            attendances = attendances.filter(check_out_time__isnull=False)
        elif status_filter == "complete":
            attendances = attendances.filter(check_in_time__isnull=False, check_out_time__isnull=False)
        elif status_filter == "late":
            attendances = [a for a in attendances if getattr(a, "is_late", False)]
        elif status_filter == "early":
            attendances = [a for a in attendances if getattr(a, "left_early", False)]

    # 5️⃣ Xử lý dữ liệu hiển thị & thống kê
    data = []
    total_work_hours = total_late_count = total_early_count = total_complete_days = 0

    for att in attendances:
        # Xác định trạng thái
        if not att.check_in_time and not att.check_out_time:
            status_text = "Chưa chấm công"
        elif not att.check_out_time:
            status_text = "Chưa check-out"
        elif getattr(att, "is_late", False) and getattr(att, "left_early", False):
            status_text = "Đi trễ & về sớm"
            total_late_count += 1
            total_early_count += 1
        elif getattr(att, "is_late", False):
            status_text = "Đi trễ"
            total_late_count += 1
        elif getattr(att, "left_early", False):
            status_text = "Về sớm"
            total_early_count += 1
        else:
            status_text = "Đúng giờ"

        # Tính giờ làm việc
        hours = None
        if att.check_in_time and att.check_out_time:
            delta = att.check_out_time - att.check_in_time
            hours = round(delta.total_seconds() / 3600, 2)
            total_work_hours += hours
            total_complete_days += 1

        # Kiểm tra vị trí
        location_status = "Đúng vị trí"
        if att.distance_meters and att.distance_meters > 50:
            location_status = "Sai vị trí"

        # Ngày trong tuần
        day_of_week = [
            "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"
        ][att.created_at.weekday()]

        data.append({
            "id": att.id,
            "date": att.created_at.strftime("%d/%m/%Y"),
            "day_of_week": day_of_week,
            "shift": att.shift.name if att.shift else "Không có ca",
            "check_in": att.check_in_time.strftime("%H:%M:%S") if att.check_in_time else "-",
            "check_out": att.check_out_time.strftime("%H:%M:%S") if att.check_out_time else "-",
            "hours": hours,
            "status": status_text,
            "location_status": location_status,
            "face_image": att.face_image.url if att.face_image else None,
            "distance": f"{att.distance_meters}m" if att.distance_meters else "-",
        })

    total_days = len(attendances)
    avg_work_hours = round(total_work_hours / total_complete_days, 2) if total_complete_days > 0 else 0

    context = {
        "employee": employee,
        "data": data,
        "start_date": start_date,
        "end_date": end_date,
        "stats": {
            "total_days": total_days,
            "total_work_hours": round(total_work_hours, 2),
            "avg_work_hours": avg_work_hours,
            "total_late_count": total_late_count,
            "total_early_count": total_early_count,
        },
    }

    return render(request, "staff/Attendance/my_history.html", context)


# --------- Check-in / Check-out ----------
def attendance_toggle(request, shift_id=None):
    if not request.user.is_authenticated:
        messages.error(request, "Vui lòng đăng nhập để tiếp tục.")
        return redirect("login")

    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn với nhân viên.")
        return redirect("attendance:attendance_list")

    # Lấy ca làm (nếu không có id thì tự tìm ca theo giờ hiện tại)
    shift = get_object_or_404(Shift, id=shift_id) if shift_id else get_current_shift()
    if not shift:
        messages.error(request, "Không có ca làm phù hợp ở thời điểm hiện tại.")
        return redirect("attendance:attendance_list")

    today = timezone.localdate()
    attendance, _ = Attendance.objects.get_or_create(
        employee=employee,
        shift=shift,
        created_at__date=today,
    )

    if request.method == "POST":
        action = request.POST.get("action") 
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        location_note = request.POST.get("location_note")
        face_image = request.FILES.get("face_image")

        # ================== KIỂM TRA DỮ LIỆU ==================
        if not latitude or not longitude:
            messages.error(request, "❌ Thiếu dữ liệu GPS.")
            return redirect(request.path)
        if not face_image:
            messages.error(request, "❌ Vui lòng chụp ảnh khuôn mặt.")
            return redirect(request.path)

        try:
            lat = float(latitude)
            lon = float(longitude)
        except ValueError:
            messages.error(request, "⚠️ Tọa độ GPS không hợp lệ.")
            return redirect(request.path)

        # ================== XÁC THỰC KHUÔN MẶT ==================
        known_encodings = [f.face_encoding for f in employee.faces.all() if f.face_encoding]
        if not known_encodings:
            messages.error(request, "⚠️ Bạn chưa đăng ký dữ liệu khuôn mặt.")
            return redirect(request.path)

        file_bytes = np.frombuffer(face_image.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        face_image.seek(0)

        matched = compare_face(frame, known_encodings)

        matched_face_obj = None
        if isinstance(matched, bool) and matched:
            matched_face_obj = employee.faces.first()
        elif isinstance(matched, int):
            matched_face_obj = employee.faces.all()[matched]
        elif isinstance(matched, tuple) and matched[0]:
            matched_face_obj = employee.faces.all()[matched[1]]

        if not matched_face_obj:
            messages.error(request, "❌ Khuôn mặt không trùng khớp. Vui lòng xác thực lại.")
            return redirect(request.path)

        # ================== LƯU DỮ LIỆU ==================
        now_dt = timezone.localtime()
        note_status = []

        # --- Trường hợp CHECK-IN ---
        if action == "checkin":
            if attendance.check_in_time:
                messages.warning(request, "⚠️ Bạn đã check-in trước đó rồi.")
                return redirect(request.path)

            attendance.check_in_time = now_dt
            if shift.start_time and now_dt.time() > shift.start_time:
                note_status.append("Đi muộn")

            messages.success(request, "✅ Check-in thành công!")

        elif action == "checkout":
            if not attendance.check_in_time:
                messages.error(request, "⚠️ Bạn chưa check-in, không thể check-out.")
                return redirect(request.path)
            if attendance.check_out_time:
                messages.warning(request, "⚠️ Bạn đã check-out rồi.")
                return redirect(request.path)

            attendance.check_out_time = now_dt
            if shift.end_time and now_dt.time() < shift.end_time:
                note_status.append("Về sớm")

            messages.success(request, "✅ Check-out thành công!")

        # --- Kiểm tra khoảng cách ---
        dist_m = haversine_distance(lat, lon, ORIGIN_LAT, ORIGIN_LON)
        if dist_m > MAX_DISTANCE_METERS:
            note_status.append(f"Sai vị trí ({dist_m:.1f} m)")

        # --- Nếu không có lỗi gì ---
        if not note_status:
            note_status.append("Đúng giờ, đúng vị trí")

        # --- Ghi dữ liệu vào model ---
        attendance.latitude = Decimal(f"{lat:.6f}")
        attendance.longitude = Decimal(f"{lon:.6f}")
        attendance.location_note = location_note or attendance.location_note
        attendance.face_image = face_image
        attendance.face_verified = True
        attendance.matched_face = matched_face_obj
        attendance.method = "auto"
        attendance.distance_meters = Decimal(f"{dist_m:.2f}")

        # --- Ghi chú tình trạng (nối thêm nếu đã có) ---
        old_note = attendance.note or ""
        if old_note:
            attendance.note = old_note + " | " + ", ".join(note_status)
        else:
            attendance.note = ", ".join(note_status)

        attendance.save()

        messages.success(request, "✅ Khuôn mặt trùng khớp, chấm công thành công!")
        return render(request, "staff/Attendance/checkin_success.html", {"attendance": attendance})

    # ================== GET REQUEST ==================
    return render(request, "staff/Attendance/checkin.html", {
        "shift": shift,
        "attendance": attendance
    })
