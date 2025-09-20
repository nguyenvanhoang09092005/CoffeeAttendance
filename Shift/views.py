from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Shift, WeeklyShiftAssignment, ShiftException
from .forms import ShiftForm, WeeklyShiftAssignmentForm, ShiftExceptionForm
from employee.models import Employee
import datetime

def shift_manage(request):
    employees = Employee.objects.all()
    shifts = Shift.objects.all()

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "shift":  # Form tạo ca
            form = ShiftForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Thêm ca thành công!")
                return redirect("shift_manage")

        elif form_type == "assignment":  # Form phân công ca
            form = WeeklyShiftAssignmentForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Phân công ca thành công!")
                return redirect("shift_manage")

        elif form_type == "exception":  # Form ngoại lệ
            form = ShiftExceptionForm(request.POST)
            if form.is_valid():
                # Convert is_added về Boolean
                exception = form.save(commit=False)
                is_added_value = request.POST.get("is_added")
                exception.is_added = True if is_added_value == "true" else False
                exception.save()

                messages.success(request, "Thêm ngoại lệ thành công!")
                return redirect("shift_manage")

    context = {
        "employees": employees,
        "shifts": shifts,
    }
    return render(request, "shifts/shift_manage.html", context)

def shift_schedule(request):
    shifts = Shift.objects.all().order_by("start_time")
    weekdays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday())  
    end_week = start_week + datetime.timedelta(days=6) 
    week_dates = [(start_week + datetime.timedelta(days=i)) for i in range(7)]
    weekdays_with_dates = list(zip(weekdays, week_dates))

    table = {shift: [""] * 7 for shift in shifts}

    # Phân công cố định
    assignments = WeeklyShiftAssignment.objects.select_related("employee", "shift").all()
    for a in assignments:
        shift = a.shift
        weekday_index = a.weekday  
        name = f"{a.employee.first_name}"
        table[shift][weekday_index] += (", " if table[shift][weekday_index] else "") + name

    # Ngoại lệ
    exceptions_once = ShiftException.objects.filter(
        exception_type="once",
        date__range=[start_week, end_week]
    )
    exceptions_perm = ShiftException.objects.filter(exception_type="permanent")

    for e in list(exceptions_once) + list(exceptions_perm):
        # --- Tìm ca có overlap dài nhất ---
        best_shift = None
        best_overlap = datetime.timedelta(0)

        for shift in shifts:
            shift_start = shift.start_time
            shift_end = shift.end_time
            exc_start = e.start_time
            exc_end = e.end_time

            overlap_start = max(shift_start, exc_start)
            overlap_end = min(shift_end, exc_end)

            if overlap_start < overlap_end:
                overlap = datetime.datetime.combine(datetime.date.today(), overlap_end) - datetime.datetime.combine(datetime.date.today(), overlap_start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_shift = shift

        if not best_shift:
            continue

        if e.exception_type == "once" and e.date:
            weekday_index = e.date.weekday()
        elif e.exception_type == "permanent" and e.weekday is not None:
            weekday_index = e.weekday
        else:
            continue

        if e.is_added:
            # Nếu giờ ngoại lệ khác ca chuẩn thì thêm ghi chú
            if e.start_time != best_shift.start_time or e.end_time != best_shift.end_time:
                text = f"{e.employee.first_name} ({e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')})"
            else:
                text = f"{e.employee.first_name} "
            table[best_shift][weekday_index] += (", " if table[best_shift][weekday_index] else "") + text
        else:
            if table[best_shift][weekday_index]:
                names = [n.strip() for n in table[best_shift][weekday_index].split(",")]
                names = [n for n in names if not n.startswith(f"{e.employee.first_name} ")]
                table[best_shift][weekday_index] = ", ".join(names)

    context = {
        "table": table,
        "weekdays_with_dates": weekdays_with_dates,
        "today": today,
    }
    return render(request, "shifts/shift_schedule.html", context)


def all_manage(request):
    # Lấy dữ liệu
    shifts = Shift.objects.all()
    assignments = WeeklyShiftAssignment.objects.select_related("employee", "shift")
    exceptions = ShiftException.objects.select_related("employee", "shift")

    context = {
        "shifts": shifts,
        "assignments": assignments,
        "exceptions": exceptions,
    }
    return render(request, "shifts/all_manage.html", context)

def assignment_update_all(request):
    employees = Employee.objects.all()
    shifts = Shift.objects.all()
    weekdays = [
        ("Mon", "Thứ 2"),
        ("Tue", "Thứ 3"),
        ("Wed", "Thứ 4"),
        ("Thu", "Thứ 5"),
        ("Fri", "Thứ 6"),
        ("Sat", "Thứ 7"),
        ("Sun", "Chủ nhật"),
    ]

    if request.method == "POST":
        try:
            with transaction.atomic():
                # giả sử model có field "week" để phân biệt tuần
                current_week = timezone.now().isocalendar().week  
                WeeklyShiftAssignment.objects.filter(week=current_week).delete()

                for i in range(1, 21):  # ví dụ cho nhập tối đa 20 dòng
                    emp_id = request.POST.get(f"employee_{i}")
                    shift_id = request.POST.get(f"shift_{i}")
                    weekday = request.POST.get(f"weekday_{i}")
                    if emp_id and shift_id and weekday:
                        WeeklyShiftAssignment.objects.create(
                            employee_id=emp_id,
                            shift_id=shift_id,
                            weekday=weekday,
                            week=current_week
                        )

            messages.success(request, "Đã cập nhật toàn bộ phân công tuần mới!")
            return redirect("all_manage")

        except Exception as e:
            messages.error(request, f"Lỗi khi cập nhật: {e}")

    return render(
        request,
        "shifts/assignment_update_all.html",
        {"employees": employees, "shifts": shifts, "weekdays": weekdays},
    )

# ==========================
# QUẢN LÝ LOẠI CA LÀM VIỆC
# ==========================

def shift_edit(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == "POST":
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật ca thành công!")
            return redirect("all_manage")
    else:
        form = ShiftForm(instance=shift)
    return render(request, "shifts/shift_edit.html", {"form": form, "shift": shift})

def shift_delete(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == "POST":
        shift.delete()
        messages.success(request, "Xóa ca thành công!")
        return redirect("all_manage")
    return render(request, "shifts/shift_delete.html", {"shift": shift})


# ==========================
# 2. QUẢN LÝ PHÂN CÔNG CA CỐ ĐỊNH
# ==========================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import WeeklyShiftAssignment, Employee, Shift
from .forms import WeeklyShiftAssignmentForm

def assignment_edit(request, pk):
    assignment = get_object_or_404(WeeklyShiftAssignment, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update":
            form = WeeklyShiftAssignmentForm(request.POST, instance=assignment)
            if form.is_valid():
                form.save()
                messages.success(request, "Cập nhật phân công thành công!")
                return redirect("all_manage")

        elif action == "replace":
            new_emp_id = request.POST.get("new_employee")
            if new_emp_id:
                assignment.employee_id = new_emp_id
                assignment.save()
                messages.success(request, "Thay thế nhân viên thành công!")
            return redirect("all_manage")

        elif action == "swap":
            other_id = request.POST.get("other_assignment")
            if other_id:
                try:
                    with transaction.atomic():
                        other = WeeklyShiftAssignment.objects.get(id=other_id)
                        assignment.employee, other.employee = other.employee, assignment.employee
                        assignment.save()
                        other.save()
                        messages.success(request, "Hoán đổi ca thành công!")
                except WeeklyShiftAssignment.DoesNotExist:
                    messages.error(request, "Không tìm thấy ca để hoán đổi.")
            return redirect("all_manage")

    else:
        form = WeeklyShiftAssignmentForm(instance=assignment)

    employees = Employee.objects.all()
    shifts = Shift.objects.all()
    assignments = WeeklyShiftAssignment.objects.exclude(id=assignment.id)

    weekdays = [
        ("0", "Thứ 2"), ("1", "Thứ 3"), ("2", "Thứ 4"),
        ("3", "Thứ 5"), ("4", "Thứ 6"), ("5", "Thứ 7"), ("6", "Chủ nhật")
    ]

    return render(
        request,
        "shifts/assignment_edit.html",
        {
            "form": form,
            "assignment": assignment,
            "employees": employees,
            "shifts": shifts,
            "assignments": assignments,
            "weekdays": weekdays,
        },
    )

def assignment_delete(request, pk):
    assignment = get_object_or_404(WeeklyShiftAssignment, pk=pk)
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Xóa phân công thành công!")
        return redirect("all_manage")
    return render(request, "shifts/assignment_delete.html", {"assignment": assignment})


# ==========================
# 3. QUẢN LÝ NGOẠI LỆ CA
# ==========================

def exception_edit(request, pk):
    exception = get_object_or_404(ShiftException, pk=pk)

    if request.method == "POST":
        form = ShiftExceptionForm(request.POST, instance=exception)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật ngoại lệ thành công!")
            return redirect("all_manage")
    else:
        form = ShiftExceptionForm(instance=exception)

    # Bổ sung dữ liệu cho form hiển thị đầy đủ
    employees = Employee.objects.all()
    shifts = Shift.objects.all()
    weekdays = [
        (0, "Thứ 2"),
        (1, "Thứ 3"),
        (2, "Thứ 4"),
        (3, "Thứ 5"),
        (4, "Thứ 6"),
        (5, "Thứ 7"),
        (6, "Chủ nhật"),
    ]
    exception_types = [
        ("once", "Một lần"),
        ("permanent", "Lặp lại hàng tuần"),
    ]

    context = {
        "form": form,
        "exception": exception,
        "employees": employees,
        "shifts": shifts,
        "weekdays": weekdays,
        "exception_types": exception_types,
    }
    return render(request, "shifts/exception_edit.html", context)

def exception_delete(request, pk):

    exception = get_object_or_404(ShiftException, pk=pk)
    if request.method == "POST":
        exception.delete()
        messages.success(request, "Xóa ngoại lệ thành công!")
        return redirect("all_manage")
    return render(request, "shifts/exception_delete.html", {"exception": exception})


#staff

def show_shift(request):
    shifts = Shift.objects.all().order_by("start_time")
    weekdays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday())  
    end_week = start_week + datetime.timedelta(days=6) 
    week_dates = [(start_week + datetime.timedelta(days=i)) for i in range(7)]
    weekdays_with_dates = list(zip(weekdays, week_dates))

    table = {shift: [""] * 7 for shift in shifts}

    # Phân công cố định
    assignments = WeeklyShiftAssignment.objects.select_related("employee", "shift").all()
    for a in assignments:
        shift = a.shift
        weekday_index = a.weekday  
        name = f"{a.employee.first_name}"
        table[shift][weekday_index] += (", " if table[shift][weekday_index] else "") + name

    # Ngoại lệ
    exceptions_once = ShiftException.objects.filter(
        exception_type="once",
        date__range=[start_week, end_week]
    )
    exceptions_perm = ShiftException.objects.filter(exception_type="permanent")

    for e in list(exceptions_once) + list(exceptions_perm):
        # --- Tìm ca có overlap dài nhất ---
        best_shift = None
        best_overlap = datetime.timedelta(0)

        for shift in shifts:
            shift_start = shift.start_time
            shift_end = shift.end_time
            exc_start = e.start_time
            exc_end = e.end_time

            overlap_start = max(shift_start, exc_start)
            overlap_end = min(shift_end, exc_end)

            if overlap_start < overlap_end:
                overlap = datetime.datetime.combine(datetime.date.today(), overlap_end) - datetime.datetime.combine(datetime.date.today(), overlap_start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_shift = shift

        if not best_shift:
            continue

        if e.exception_type == "once" and e.date:
            weekday_index = e.date.weekday()
        elif e.exception_type == "permanent" and e.weekday is not None:
            weekday_index = e.weekday
        else:
            continue

        if e.is_added:
            # Nếu giờ ngoại lệ khác ca chuẩn thì thêm ghi chú
            if e.start_time != best_shift.start_time or e.end_time != best_shift.end_time:
                text = f"{e.employee.first_name} ({e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')})"
            else:
                text = f"{e.employee.first_name} "
            table[best_shift][weekday_index] += (", " if table[best_shift][weekday_index] else "") + text
        else:
            if table[best_shift][weekday_index]:
                names = [n.strip() for n in table[best_shift][weekday_index].split(",")]
                names = [n for n in names if not n.startswith(f"{e.employee.first_name} ")]
                table[best_shift][weekday_index] = ", ".join(names)

    context = {
        "table": table,
        "weekdays_with_dates": weekdays_with_dates,
        "today": today,
    }
    return render(request, "staff/Shift/Show_shift.html", context)

