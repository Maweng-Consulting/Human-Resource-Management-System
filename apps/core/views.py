from django.shortcuts import render, redirect
from apps.core.models import Workstation, Client, PaymentConfig, TaxBand, JobRole
from apps.employees.models import Employee, DeploymentAssignment
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

# Create your views here.
SP_CATEGORIES_CHOICES = ["Staff", "Service Provider"]
SP_GROUP_CHOICES = [
    "Security Manager",
    "Supervisor" "Finance Officer",
    "HR Admin",
    "Security Guard",
    "CCTV Installer",
]


@login_required(login_url="/users/login")
def home(request):
    active_statuses = ["Available", "Approved"]
    active_guards = Employee.objects.filter(status__in=active_statuses)
    workstations = Workstation.objects.select_related("client").all().order_by("client__name", "name")
    posted_counts = dict(
        active_guards.filter(workstation__isnull=False)
        .values_list("workstation_id")
        .annotate(total=Count("id"))
    )

    coverage_rows = []
    total_required = 0
    total_posted = 0
    for workstation in workstations:
        required = workstation.guards_needed or 0
        posted = posted_counts.get(workstation.id, 0)
        shortage = max(required - posted, 0)
        total_required += required
        total_posted += posted
        if shortage:
            coverage_rows.append(
                {
                    "workstation": workstation,
                    "client": workstation.client,
                    "required": required,
                    "posted": posted,
                    "shortage": shortage,
                }
            )

    recent_deployments = DeploymentAssignment.objects.select_related(
        "employee", "client", "workstation", "assigned_by"
    ).order_by("-assigned_at", "-created")[:6]

    context = {
        "employees_count": Employee.objects.count(),
        "active_guards_count": active_guards.count(),
        "available_count": Employee.objects.filter(status="Available").count(),
        "on_leave_count": Employee.objects.filter(status="On Leave").count(),
        "pending_count": Employee.objects.filter(status="Pending Approval").count(),
        "clients_count": Client.objects.count(),
        "workstations_count": workstations.count(),
        "total_required": total_required,
        "total_posted": total_posted,
        "open_posts": max(total_required - total_posted, 0),
        "coverage_rows": coverage_rows[:8],
        "recent_deployments": recent_deployments,
    }
    return render(request, "home.html", context)

@login_required(login_url="/users/login")
def clients(request):
    work_stations = Client.objects.all().order_by("-created")

    if request.method == "POST":
        search_text = request.POST.get("search_text")
        work_stations = Client.objects.filter(Q(name__icontains=search_text))

    paginator = Paginator(work_stations, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "clients/clients.html", context)


@login_required(login_url="/users/login")
def new_client(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        contract_start_date = request.POST.get("contract_start_date")
        guards_posted = request.POST.get("guards_posted")
        guards_needed = request.POST.get("guards_needed")
        work_shift = request.POST.get("work_shift")
        location_description = request.POST.get("location_description")

        address = request.POST.get("address")
        town = request.POST.get("town")
        county = request.POST.get("county")
        country = request.POST.get("country")

        Client.objects.create(
            name=name,
            phone_number=phone_number,
            email=email,
            contract_start_date=contract_start_date,
            guards_needed=guards_needed,
            guards_posted=guards_posted,
            work_shift=work_shift,
            location_description=location_description,
            postal_address=address,
            town=town,
            county=county,
            country=country,
        )

        return redirect("clients")
    return render(request, "clients/new_client.html")


@login_required(login_url="/users/login")
def edit_client(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        name = request.POST.get("name")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        contract_start_date = request.POST.get("contract_start_date")
        guards_posted = request.POST.get("guards_posted")
        guards_needed = request.POST.get("guards_needed")
        work_shift = request.POST.get("work_shift")
        location_description = request.POST.get("location_description")

        address = request.POST.get("address")
        town = request.POST.get("town")
        county = request.POST.get("county")
        country = request.POST.get("country")

        client = Client.objects.get(id=client_id)
        client.name = name
        client.phone_number = phone_number
        client.email = email
        client.contract_start_date = contract_start_date
        client.guards_needed = guards_needed
        client.guards_posted = guards_posted
        client.work_shift = work_shift
        client.location_description = location_description
        client.postal_address = address
        client.town = town
        client.county = county
        client.country = country
        client.save()

        return redirect("clients")
    return render(request, "clients/edit_client.html")


@login_required(login_url="/users/login")
def delete_client(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        client = Client.objects.get(id=client_id)
        client.delete()
        return redirect("clients")
    return render(request, "clients/delete_client.html")


@login_required(login_url="/users/login")
def client_detail(request, client_id):
    client = Client.objects.get(id=client_id)

    guards = client.clientsguards.select_related("position", "workstation").order_by(
        "first_name", "last_name", "id"
    )
    workstations = client.workstations.all()
    workstation_count = workstations.count()
    total_required = sum(workstation.guards_needed or 0 for workstation in workstations)
    total_posted = guards.count()
    open_posts = max(total_required - total_posted, 0)
    over_posted = max(total_posted - total_required, 0)
    coverage_percent = int((total_posted / total_required) * 100) if total_required else 0
    coverage_bar_percent = min(coverage_percent, 100)
    paginator = Paginator(guards, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "client": client,
        "page_obj": page_obj,
        "workstations": workstations,
        "workstation_count": workstation_count,
        "total_required": total_required,
        "total_posted": total_posted,
        "open_posts": open_posts,
        "over_posted": over_posted,
        "coverage_percent": coverage_percent,
        "coverage_bar_percent": coverage_bar_percent,
    }
    return render(request, "clients/client_detail.html", context)


## Work stations
@login_required(login_url="/users/login")
def new_workstation(request):
    if request.method == "POST":
        name = request.POST.get("name")
        client_id = request.POST.get("client_id")
        guards_needed = request.POST.get("guards_needed")
        guards_posted = request.POST.get("guards_posted")
        work_shift = request.POST.get("work_shift")

        Workstation.objects.create(
            name=name,
            client_id=client_id,
            guards_needed=guards_needed,
            guards_posted=guards_posted,
            work_shift=work_shift,
        )

        return redirect(f"/clients/{client_id}")
    return render(request, "workstations/new_workstation.html")


@login_required(login_url="/users/login")
def edit_workstation(request):
    if request.method == "POST":
        name = request.POST.get("name")
        client_id = request.POST.get("client_id")
        workstation_id = request.POST.get("workstation_id")
        guards_needed = request.POST.get("guards_needed")
        guards_posted = request.POST.get("guards_posted")
        work_shift = request.POST.get("work_shift")

        workstation = Workstation.objects.get(id=workstation_id)
        workstation.name = name
        workstation.guards_needed = guards_needed
        workstation.work_shift = work_shift
        workstation.guards_posted = guards_posted
        workstation.save()

        return redirect(f"/clients/{client_id}")
    return render(request, "workstations/edit_workstation.html")


@login_required(login_url="/users/login")
def delete_workstation(request):
    if request.method == "POST":
        workstation_id = request.POST.get("workstation_id")
        client_id = request.POST.get("client_id")
        workstation = Workstation.objects.get(id=workstation_id)
        workstation.delete()
        return redirect(f"/clients/{client_id}")
    return render(request, "workstations/delete_workstation.html")


@login_required(login_url="/users/login")
def job_roles(request):
    job_roles = JobRole.objects.all()
    context = {
        "job_roles": job_roles,
        "job_groups": SP_GROUP_CHOICES,
        "job_categories": SP_CATEGORIES_CHOICES,
    }
    return render(request, "job_roles/job_roles.html", context)


@login_required(login_url="/users/login")
def new_job_role(request):
    if request.method == "POST":
        category = request.POST.get("category")
        group = request.POST.get("group")

        JobRole.objects.create(category=category, group=group)
        return redirect("job-roles")
    return render(request, "job_roles/new_job_role.html")


@login_required(login_url="/users/login")
def edit_job_role(request):
    if request.method == "POST":
        category = request.POST.get("category")
        group = request.POST.get("group")
        role_id = request.POST.get("job_role_id")

        job_role = JobRole.objects.get(id=role_id)
        job_role.category = category
        job_role.group = group
        job_role.save()

        return redirect("job-roles")
    return render(request, "job_roles/edit_job_role.html")


@login_required(login_url="/users/login")
def delete_job_role(request):
    if request.method == "POST":
        role_id = request.POST.get("job_role_id")
        job_role = JobRole.objects.get(id=role_id)
        job_role.delete()

        return redirect("job-roles")
    return render(request, "job_roles/delete_job_role.html")


@login_required(login_url="/users/login")
def payments(request):
    payments = PaymentConfig.objects.all()
    job_roles = JobRole.objects.all()
    context = {"payments": payments, "job_roles": job_roles}

    return render(request, "salaries/payments.html", context)


@login_required(login_url="/users/login")
def new_payment_config(request):
    if request.method == "POST":
        job_group = request.POST.get("job_group")
        overtime = request.POST.get("overtime")
        daily_rate = request.POST.get("daily_rate")
        monthly_rate = request.POST.get("monthly_rate")

        job_role = JobRole.objects.get(id=job_group)

        PaymentConfig.objects.create(
            job_group=job_role,
            overtime=overtime,
            daily_rate=daily_rate,
            monthly_rate=monthly_rate,
        )

        return redirect("payment-configs")
    return render(request, "salaries/new_payment_config.html")


@login_required(login_url="/users/login")
def edit_payment_config(request):
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        job_group = request.POST.get("job_group")
        overtime = request.POST.get("overtime")
        daily_rate = request.POST.get("daily_rate")
        monthly_rate = request.POST.get("monthly_rate")
        job_role = JobRole.objects.get(id=job_group)

        payment_config = PaymentConfig.objects.get(id=payment_id)
        payment_config.job_group = job_role
        payment_config.overtime = overtime
        payment_config.daily_rate = daily_rate
        payment_config.monthly_rate = monthly_rate
        payment_config.save()

        return redirect("payment-configs")
    return render(request, "salaries/edit_payment_config.html")


@login_required(login_url="/users/login")
def delete_payment_config(request):
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        payment_config = PaymentConfig.objects.get(id=payment_id)
        payment_config.delete()

        return redirect("payment-configs")
    return render(request, "salaries/delete_payment_config.html")


### Tax Configurations
def tax_configurations(request):
    tax_configurations = TaxBand.objects.all()
    context = {"tax_configurations": tax_configurations}
    return render(request, "taxes/tax_configs.html", context)


def new_tax_config(request):
    if request.method == "POST":
        category = request.POST.get("category")
        lower_end = request.POST.get("lower_end")
        upper_end = request.POST.get("upper_end")
        nhif = request.POST.get("nhif")
        shif = request.POST.get("shif")
        nssf_tier_one = request.POST.get("nssf_tier_one")
        nssf_tier_two = request.POST.get("nssf_tier_two")
        housing_levy = request.POST.get("housing_levy")
        tax_relief = request.POST.get("tax_relief")
        allowable_deductions = request.POST.get("allowable_deductions")
        insurance_relief = request.POST.get("insurance_relief")

        band = TaxBand.objects.create(
            category=category,
            lower_end=lower_end,
            upper_end=upper_end,
            nhif=nhif,
            shif=shif,
            nssf_tier_one=nssf_tier_one,
            nssf_tier_two=nssf_tier_two,
            housing_levy=housing_levy,
            tax_relief=tax_relief,
            allowable_deductions=allowable_deductions,
            insurance_relief=insurance_relief,
        )

        return redirect("tax-configurations")
    return render(request, "taxes/new_tax_config.html")


def edit_tax_config(request):
    if request.method == "POST":
        tax_config_id = request.POST.get("tax_config_id")
        category = request.POST.get("category")
        lower_end = request.POST.get("lower_end")
        upper_end = request.POST.get("upper_end")
        nhif = request.POST.get("nhif")
        shif = request.POST.get("shif")
        nssf_tier_one = request.POST.get("nssf_tier_one")
        nssf_tier_two = request.POST.get("nssf_tier_two")
        housing_levy = request.POST.get("housing_levy")
        tax_relief = request.POST.get("tax_relief")
        allowable_deductions = request.POST.get("allowable_deductions")
        insurance_relief = request.POST.get("insurance_relief")

        tax_band = TaxBand.objects.get(id=tax_config_id)
        tax_band.category = category
        tax_band.lower_end = lower_end
        tax_band.upper_end = upper_end
        tax_band.nhif = nhif
        tax_band.shif = shif
        tax_band.nssf_tier_one = nssf_tier_one
        tax_band.nssf_tier_two = nssf_tier_two
        tax_band.housing_levy = housing_levy
        tax_band.tax_relief = tax_relief
        tax_band.allowable_deductions = allowable_deductions
        tax_band.insurance_relief = insurance_relief
        tax_band.save()

        return redirect("tax-configurations")
    return render(request, "taxes/edit_tax_config.html")


def delete_tax_config(request):
    if request.method == "POST":
        tax_config_id = request.POST.get("tax_config_id")
        band = TaxBand.objects.get(id=tax_config_id)
        band.delete()

        return redirect("tax-configurations")
    return render(request, "taxes/delete_tax_config.html")
