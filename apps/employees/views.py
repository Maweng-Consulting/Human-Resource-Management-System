from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from apps.users.models import User
from datetime import datetime
import calendar
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.payments.models import EmployeeSalary
from apps.employees.models import (
    NextOfKin,
    EducationInformation,
    Employee,
    EmployeeDocument,
    DeploymentAssignment,
)
from apps.payments.models import EmployeeSalary, BankInformation
from apps.core.models import Workstation, PaymentConfig, JobRole

date_today = datetime.now().date()

current_month = calendar.month_name[date_today.month]
current_year = str(date_today.year)

# Employee Management

SHIFT_CHOICES = ["Day Shift", "Night Shift", "24 Hours Shift"]

def record_deployment_assignment(employee, workstation, work_shift, assigned_by=None):
    DeploymentAssignment.objects.filter(
        employee=employee, status="Active", released_at__isnull=True
    ).update(status="Reassigned", released_at=timezone.now())

    DeploymentAssignment.objects.create(
        employee=employee,
        client=workstation.client,
        workstation=workstation,
        work_shift=work_shift,
        assigned_by=assigned_by if assigned_by and assigned_by.is_authenticated else None,
        assigned_at=timezone.now(),
    )


@login_required(login_url="/users/login/")
def employees(request):
    employees = Employee.objects.all().order_by("-created")
    workstations = Workstation.objects.all()
    payment_configs = PaymentConfig.objects.all()

    if request.method == "POST":
        search_text = request.POST.get("search_text")
        employees = Employee.objects.filter(
            Q(first_name__icontains=search_text)
            | Q(first_name__icontains=search_text)
            | Q(phone_number__icontains=search_text)
            | Q(id_number__icontains=search_text)
        ).order_by("-created")

    paginator = Paginator(employees, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "workstations": workstations,
        "payment_configs": payment_configs,
        "work_shifts": SHIFT_CHOICES,
    }
    return render(request, "employees/employees.html", context)


@login_required(login_url="/users/login/")
def new_employee(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        id_number = request.POST.get("id_number")
        phone_number = request.POST.get("phone_number")
        physical_address = request.POST.get("address")
        postal_address = request.POST.get("address")
        city = request.POST.get("city")
        country = request.POST.get("country")
        county = request.POST.get("county")
        nhif_number = request.POST.get("nhif_number")
        nssf_number = request.POST.get("nssf_number")
        residence = request.POST.get("place_of_residence")

        job_category = request.POST.get("job_category")
        payment_config = PaymentConfig.objects.get(id=job_category)
        kra_pin = request.POST.get("kra_pin")

        Employee.objects.create(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            id_number=id_number,
            kra_pin=kra_pin,
            phone_number=phone_number,
            physical_address=physical_address,
            postal_address=postal_address,
            town=city,
            county=county,
            country=country,
            residence=residence,
            position=payment_config.job_group,
            nhif_number=nhif_number,
            nssf_number=nssf_number,
            job_category=payment_config,
            status="Pending Approval",
        )

        return redirect("employees")
    return render(request, "employees/new_employees.html")


def upload_documents(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")

        employee = Employee.objects.get(id=employee_id)
        documents = EmployeeDocument.objects.filter(employee=employee).first()

        chief_letter = request.FILES.get("chief_letter")
        police_clearance = request.FILES.get("police_clearance")
        referee_letter = request.FILES.get("referee_letter")
        scanned_id = request.FILES.get("scanned_id")
        kra_certificate = request.FILES.get("kra_certificate")
        kcpe_certificate = request.FILES.get("kcpe_certificate")
        kcse_certificate = request.FILES.get("kcse_certificate")
        college_certificate = request.FILES.get("college_certificate")

        if documents:
            documents.kra_certificate = (
                kra_certificate if kra_certificate else documents.kra_certificate
            )
            documents.chief_letter = (
                chief_letter if chief_letter else documents.chief_letter
            )
            documents.police_clearance = (
                police_clearance if police_clearance else documents.police_clearance
            )
            documents.referee_letter = (
                referee_letter if referee_letter else documents.referee_letter
            )
            documents.scanned_id = scanned_id if scanned_id else documents.scanned_id
            documents.kcpe_certificate = (
                kcpe_certificate if kcpe_certificate else documents.kcpe_certificate
            )
            documents.kcse_certificate = (
                kcse_certificate if kcse_certificate else documents.kcse_certificate
            )
            documents.college_certificate = (
                college_certificate
                if college_certificate
                else documents.college_certificate
            )
            documents.save()
        else:
            documents = EmployeeDocument()
            documents.employee = employee
            documents.kra_certificate = kra_certificate if kra_certificate else None
            documents.chief_letter = chief_letter if chief_letter else None
            documents.police_clearance = police_clearance if police_clearance else None
            documents.referee_letter = referee_letter if referee_letter else None
            documents.scanned_id = scanned_id if scanned_id else None
            documents.kcpe_certificate = kcpe_certificate if kcpe_certificate else None
            documents.kcse_certificate = kcse_certificate if kcse_certificate else None
            documents.college_certificate = (
                college_certificate if college_certificate else None
            )
            documents.save()

        return redirect(f"/users/{employee_id}")
    return redirect(request, "employees/upload_documents.html")


def approval_all(request):
    Employee.objects.update(status="Available")
    return redirect("users")


@login_required(login_url="/users/login/")
def edit_employee(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        id_number = request.POST.get("id_number")
        phone_number = request.POST.get("phone_number")
        address = request.POST.get("address")
        city = request.POST.get("city")
        county = request.POST.get("county")
        country = request.POST.get("country")
        nhif_number = request.POST.get("nhif_number")
        nssf_number = request.POST.get("nssf_number")
        kra_pin = request.POST.get("kra_pin")
        residence = request.POST.get("place_of_residence")
        job_category = request.POST.get("job_category")
        payment_config = PaymentConfig.objects.get(id=job_category)

        employee = Employee.objects.get(id=employee_id)
        employee.first_name = first_name
        employee.last_name = last_name
        employee.gender = gender
        employee.id_number = id_number
        employee.phone_number = phone_number
        employee.physical_address = address
        employee.postal_address = address
        employee.town = city
        employee.position = payment_config.job_group
        employee.county = county
        employee.country = country
        employee.nhif_number = nhif_number
        employee.nssf_number = nssf_number
        employee.job_category = payment_config
        employee.kra_pin = kra_pin
        employee.residence = residence
        employee.save()

        return redirect("employees")

    return render(request, "employees/edit_employee.html")


@login_required(login_url="/users/login/")
def delete_employee(request):
    if request.method == "POST":

        employee_id = request.POST.get("employee_id")
        employee = Employee.objects.get(id=employee_id)
        employee.delete()

        return redirect("employees")

    return render(request, "employees/delete_employee.html")


@login_required(login_url="/users/login/")
def employee_details(request, employee_id=None):
    employee = Employee.objects.get(id=employee_id)
    family_members = employee.nextofkins.all()
    education_details = employee.educationdetails.all()
    documents = EmployeeDocument.objects.filter(employee=employee).first()

    bank_details_found = False
    banking_details = BankInformation.objects.filter(employee=employee).first()

    workstations = Workstation.objects.all()
    payment_configs = PaymentConfig.objects.select_related("job_group").all()
    deployment_history = employee.deployment_history.select_related(
        "client", "workstation", "assigned_by"
    ).all()[:5]

    if banking_details:
        bank_details_found = True

    context = {
        "employee": employee,
        "family_members": family_members,
        "education_details": education_details,
        "documents": documents,
        "banking_details_found": bank_details_found,
        "banking_info": banking_details,
        "workstations": workstations,
        "payment_configs": payment_configs,
        "deployment_history": deployment_history,
        "work_shifts": SHIFT_CHOICES,
    }

    return render(request, "employees/employee_details.html", context)


def approve_employee(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        workstation_id = request.POST.get("workstation_id")
        work_shift = request.POST.get("work_shift")

        employee = Employee.objects.get(id=employee_id)
        workstation = Workstation.objects.get(id=workstation_id)

        employee.client = workstation.client
        employee.workstation = workstation
        employee.status = "Approved"
        employee.workshift = work_shift
        employee.save()
        record_deployment_assignment(employee, workstation, work_shift, request.user)

        return redirect(f"/employees/{employee_id}")
    return render(request, "employees/approve_employee.html")


def disapprove_employee(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        employee = Employee.objects.get(id=employee_id)

        employee.status = "Declined"
        employee.save()

        return redirect(f"/employees/{employee_id}")
    return render(request, "employees/decline_employee.html")


# Employee Relatives
def new_relative(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        relationship = request.POST.get("relationship")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")

        relative = NextOfKin.objects.create(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            relation=relationship,
            email=email,
            phone_number=phone_number,
        )

        return redirect(f"/employees/{employee_id}")
    return render(request, "family/new_family_member.html")


def edit_relative(request):
    if request.method == "POST":
        family_member_id = request.POST.get("family_member_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = request.POST.get("gender")
        relationship = request.POST.get("relationship")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")

        relative = NextOfKin.objects.get(id=family_member_id)
        relative.first_name = first_name
        relative.last_name = last_name
        relative.gender = gender
        relative.relation = relationship
        relative.email = email
        relative.phone_number = phone_number
        relative.save()

        return redirect(f"/employees/{relative.employee.id}")
    return render(request, "family/edit_relative.html")


def delete_relative(request):
    if request.method == "POST":
        relative_id = request.POST.get("relative_id")
        relative = NextOfKin.objects.get(id=relative_id)
        employee_id = relative.employee.id
        relative.delete()
        return redirect(f"/users/{employee_id}")

    return render(request, "family/delete_relative.html")


## EDUCATION RECORDS MANAGEMENT


def new_education_record(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        school_name = request.POST.get("school_name")
        level = request.POST.get("level")
        start_year = request.POST.get("start_year")
        graduation_year = request.POST.get("graduation_year")

        EducationInformation.objects.create(
            employee_id=employee_id,
            school_name=school_name,
            level=level,
            start_year=start_year,
            graduation_year=graduation_year,
        )

        return redirect(f"/users/{employee_id}")
    return render(request, "education/new_education.html")


def edit_education_record(request):
    if request.method == "POST":
        education_id = request.POST.get("education_id")
        school_name = request.POST.get("school_name")
        level = request.POST.get("level")
        start_year = request.POST.get("start_year")
        graduation_year = request.POST.get("graduation_year")

        education = EducationInformation.objects.get(id=education_id)
        education.school_name = school_name
        education.level = level
        education.start_year = start_year
        education.graduation_year = graduation_year
        education.save()

        return redirect(f"/users/{education.employee.id}")
    return render(request, "education/edit_education.html")


def delete_education_record(request):
    if request.method == "POST":
        education_id = request.POST.get("education_id")
        employee_id = request.POST.get("employee_id")
        education = EducationInformation.objects.get(id=education_id)
        education.delete()

        return redirect(f"/users/{employee_id}")
    return render(request, "education/delete_education.html")


## Employees Assignments
def employee_assignments(request):
    assignable_employees = Employee.objects.exclude(
        status__in=["Pending Approval", "Declined"]
    ).order_by("-created")
    employees = assignable_employees

    if request.method == "POST":
        search_text = request.POST.get("search_text")
        employees = assignable_employees.filter(
            Q(first_name__icontains=search_text)
            | Q(last_name__icontains=search_text)
            | Q(phone_number__icontains=search_text)
            | Q(id_number__icontains=search_text)
        ).order_by("-created")

    paginator = Paginator(employees, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    workstations = Workstation.objects.select_related("client").all()
    context = {
        "page_obj": page_obj,
        "work_shifts": SHIFT_CHOICES,
        "workstations": workstations,
        "assigned_count": assignable_employees.filter(workstation__isnull=False).count(),
        "unassigned_count": assignable_employees.filter(workstation__isnull=True).count(),
        "workstation_count": workstations.count(),
    }
    return render(request, "assignments/assignments.html", context)


def reassign_employee(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        workstation_id = request.POST.get("workstation")
        work_shift = request.POST.get("work_shift")

        workstation = Workstation.objects.get(id=workstation_id)

        employee = Employee.objects.get(id=employee_id)
        employee.workstation = workstation
        employee.client = workstation.client
        employee.workshift = work_shift
        employee.save()
        record_deployment_assignment(employee, workstation, work_shift, request.user)

        return redirect("assignments")
    return render(request, "assignments/reassign.html")
