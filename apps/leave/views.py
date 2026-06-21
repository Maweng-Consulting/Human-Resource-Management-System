from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from apps.employees.models import Employee
from apps.leave.models import EmployeeLeave


# Create your views here.
@login_required(login_url="/users/login")
def leave_applications(request):
    leave_applications = EmployeeLeave.objects.all().order_by("-created")

    if request.method == "POST":
        search_text = request.POST.get("search_text")

        leave_applications = EmployeeLeave.objects.filter(
            Q(employee__first_name__icontains=search_text)
            | Q(employee__last_name__icontains=search_text)
        )

    paginator = Paginator(leave_applications, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])

    context = {"page_obj": page_obj, "employees": employees}

    return render(request, "leaves/leaves.html", context)


@login_required(login_url="/users/login")
def apply_leave(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee")
        days_applied = request.POST.get("days_applied")
        leave_type = request.POST.get("leave_type")
        leave_from = request.POST.get("leave_from")
        leave_to = request.POST.get("leave_to")

        EmployeeLeave.objects.create(
            employee_id=employee_id,
            days_applied=days_applied,
            leave_type=leave_type,
            leave_from=leave_from,
            leave_to=leave_to,
        )

        return redirect("leave-applications")

    return render(request, "leaves/apply_leave.html")


@login_required(login_url="/users/login")
def mark_leave_application(request):
    if request.method == "POST":
        leave_id = request.POST.get("leave_id")
        action_type = request.POST.get("action_type")

        leave = EmployeeLeave.objects.get(id=leave_id)
        leave.status = action_type
        leave.save()

        if action_type == "Approved":
            leave.employee.status = "On Leave"
            leave.employee.save()
        else:
            pass

        return redirect("leave-applications")
    return render(request, "leaves/mark_leave.html")


def complete_leave(request):
    if request.method == "POST":
        leave_id = request.POST.get("leave_id")
        leave = EmployeeLeave.objects.get(id=leave_id)
        leave.status = "Complete"
        leave.save()

        leave.employee.status = "Available"
        leave.employee.save()
        return redirect("leave-applications")

    return render(request, "leaves/mark_leave_complete.html")


@login_required(login_url="/users/login")
def delete_leave_application(request):
    if request.method == "POST":
        leave_id = request.POST.get("leave_id")
        leave = EmployeeLeave.objects.get(id=leave_id)
        leave.delete()
        return redirect("leave-applications")
    return render(request, "leaves/delete_leave.html")
