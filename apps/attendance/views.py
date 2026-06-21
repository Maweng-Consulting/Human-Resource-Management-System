from datetime import datetime
import calendar
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from django.db.models import Q
from apps.attendance.models import Attendance
from apps.payments.models import EmployeeSalary, EmployeeOvertime
from apps.employees.models import Employee


date_today = datetime.now().date()

current_month = calendar.month_name[date_today.month]
current_year = str(date_today.year)


# Create your views here.
@login_required(login_url="/users/login")
def attendaces(request):
    atteandaces = Attendance.objects.all().order_by("-created")

    show_generate_attendance = False

    if request.method == "POST":
        search_text = request.POST.get("search_text")
        atteandaces = Attendance.objects.filter(
            Q(employee__first_name__icontains=search_text)
            | Q(employee__last_name__icontains=search_text)
            | Q(employee__id_number__icontains=search_text)
        )

    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])
    attendances_today = Attendance.objects.filter(date=date_today).count()

    if attendances_today < employees.count():
        show_generate_attendance = True

    paginator = Paginator(atteandaces, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "show_generate_attendance": show_generate_attendance,
    }
    return render(request, "attendances/attendances.html", context)


@login_required(login_url="/users/login")
def generate_attendance(request):
    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])
    attendances_today = Attendance.objects.filter(date=date_today).count()

    print(f"The Attendance Today is: {attendances_today}")

    if employees.count() > attendances_today:
        attendace_list = []

        for employee in employees:
            attendace_list.append(
                Attendance(employee=employee, date=date_today, marked=False)
            )

        Attendance.objects.bulk_create(attendace_list)

    return redirect("attendances")


@login_required(login_url="/users/login")
def reset_attendance(request, id):
    attendance = Attendance.objects.get(id=id)
    current_status = attendance.status
    attendance.marked = False
    attendance.status = "Present"
    attendance.save()

    ## Update Salary
    if current_status == "Present":
        salary = EmployeeSalary.objects.filter(employee=attendance.employee).first()

        if salary:
            salary.total_amount -= salary.employee.job_category.daily_rate
            salary.days_worked -= 1
            salary.save()

    return redirect("attendances")


@login_required(login_url="/users/login")
def mark_absent(request, id):
    user = request.user
    attendace = Attendance.objects.get(id=id)
    attendace.marked = True
    attendace.status = "Absent"
    attendace.checked_in_by = user
    attendace.checkin_time = datetime.now()
    attendace.save()
    return redirect("attendances")
