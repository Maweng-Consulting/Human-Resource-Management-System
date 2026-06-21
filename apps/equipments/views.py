from django.shortcuts import render, redirect
from apps.equipments.models import (
    Equipment,
    EquipmentIssue,
    Vehicle,
    VehicleFuelHistory,
    VehicleServiceHistory,
)
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from apps.employees.models import Employee
from django.db.models import Q


# Create your views here.
@login_required(login_url="/users/login")
def equipments(request):
    equipments = Equipment.objects.all().order_by("-created")

    if request.method == "POST":
        search_text = request.POST.get("search_text")

        equipments = Equipment.objects.filter(Q(name__icontains=search_text))

    paginator = Paginator(equipments, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }

    return render(request, "equipments/equipments.html", context)


@login_required(login_url="/users/login")
def new_equipment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")
        category = request.POST.get("category")

        Equipment.objects.create(
            name=name, price=price, quantity=quantity, category=category
        )

        return redirect("equipments")
    return render(request, "equipments/new_equipment.html")


@login_required(login_url="/users/login")
def edit_equipment(request):
    if request.method == "POST":
        equipment_id = request.POST.get("equipment_id")
        equipment = Equipment.objects.get(id=equipment_id)

        name = request.POST.get("name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")
        category = request.POST.get("category")

        equipment.quantity = quantity
        equipment.category = category
        equipment.price = price
        equipment.name = name
        equipment.save()

        print(equipments)

        return redirect("equipments")
    return render(request, "equipments/edit_equipment.html")


@login_required(login_url="/users/login")
def delete_equipment(request):
    if request.method == "POST":
        equipment_id = request.POST.get("equipment")
        equipment = Equipment.objects.get(id=equipment_id)
        equipment.delete()

        return redirect("equipments")

    return render(request, "equipments/delete_equipment.html")


@login_required(login_url="/users/login")
def issued_equipment(request):
    issued_equipment = EquipmentIssue.objects.all().order_by("-created")

    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])
    equipments = Equipment.objects.all()

    if request.method == "POST":
        search_text = request.POST.get("search_text")
        issued_equipment = EquipmentIssue.objects.filter(
            Q(employee__first_name__icontains=search_text)
            | Q(employee__last_name__icontains=search_text)
            | Q(employee__id_number__icontains=search_text)
        )

    paginator = Paginator(issued_equipment, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "employees": employees, "equipments": equipments}

    return render(request, "equipments/issued_equipment.html", context)


@login_required(login_url="/users/login")
def issue_equipment(request):
    user = request.user
    if request.method == "POST":
        employee = request.POST.get("employee")
        date_issued = request.POST.get("date_issued")

        head_cap_issued = request.POST.get("head_cap_issued")
        shirt_issued = request.POST.get("shirt_issued")
        belt_issued = request.POST.get("belt_issued")
        chest_guard_issued = request.POST.get("chest_guard_issued")
        shoes_issued = request.POST.get("shoes_issued")
        boots_issued = request.POST.get("boots_issued")
        sweater_issued = request.POST.get("sweater_issued")
        baton_issued = request.POST.get("baton_issued")
        trouser_issued = request.POST.get("trouser_issued")

        EquipmentIssue.objects.create(
            employee_id=employee,
            date_issued=date_issued,
            issued_by=user,
            baton_issued=True if baton_issued else False,
            sweater_issued=True if sweater_issued else False,
            boots_issued=True if boots_issued else False,
            shoes_issued=True if shoes_issued else False,
            chest_guard_issued=True if chest_guard_issued else False,
            belt_issued=True if belt_issued else False,
            shirt_issued=True if shirt_issued else False,
            head_cap_issued=True if head_cap_issued else False,
            trouser_issued=True if trouser_issued else False,
        )

        return redirect("issued-equipments")
    return render(request, "equipments/issue_equipment.html")


@login_required(login_url="/users/login")
def mark_issued_equipment(request):
    if request.method == "POST":
        equipment_issue_id = request.POST.get("issue_id")
        action_type = request.POST.get("action_type")

        issued_equipment = EquipmentIssue.objects.get(id=equipment_issue_id)
        issued_equipment.status = action_type
        issued_equipment.save()

        return redirect("issued-equipments")
    return render(request, "equipments/mark.html")


@login_required(login_url="/users/login")
def delete_issued_equipment(request):
    if request.method == "POST":
        equipment_issue_id = request.POST.get("issue_id")

        issued_equipment = EquipmentIssue.objects.get(id=equipment_issue_id)
        issued_equipment.delete()

        return redirect("issued-equipments")
    return render(request, "equipments/delete_issue.html")


## Vehicles Management
@login_required(login_url="/users/login")
def vehicles(request):
    vehicles = Vehicle.objects.all().order_by("-created")
    if request.method == "POST":
        search_text = request.POST.get("search_text")
        vehicles = Vehicle.objects.filter(
            Q(plate_number__icontains=search_text)
            | Q(vehicle_model__icontains=search_text)
            | Q(vehicle_type__icontains=search_text)
        )

    paginator = Paginator(vehicles, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}
    return render(request, "vehicles/vehicles.html", context)


@login_required(login_url="/users/login")
def new_vehicle(request):
    if request.method == "POST":
        vehicle_model = request.POST.get("vehicle_model")
        plate_number = request.POST.get("plate_number")
        vehicle_type = request.POST.get("vehicle_type")

        Vehicle.objects.create(
            vehicle_model=vehicle_model,
            plate_number=plate_number,
            vehicle_type=vehicle_type,
        )
        return redirect("vehicles")
    return render(request, "vehicles/new_vehicle.html")


@login_required(login_url="/users/login")
def edit_vehicle(request):
    if request.method == "POST":
        vehicle_id = request.POST.get("vehicle_id")
        vehicle_model = request.POST.get("vehicle_model")
        plate_number = request.POST.get("plate_number")
        vehicle_type = request.POST.get("vehicle_type")

        vehicle = Vehicle.objects.get(id=vehicle_id)
        vehicle.vehicle_model = vehicle_model
        vehicle.plate_number = plate_number
        vehicle.vehicle_type = vehicle_type
        vehicle.save()

        return redirect("vehicles")
    return render(request, "vehicles/edit_vehicle.html")


@login_required(login_url="/users/login")
def delete_vehicle(request):
    if request.method == "POST":
        vehicle_id = request.POST.get("vehicle_id")
        vehicle = Vehicle.objects.get(id=vehicle_id)
        vehicle.delete()
        return redirect("vehicles")
    return render(request, "vehicles/delete_vehicle.html")


@login_required(login_url="/users/login")
def vehicle_fueling_history(request, id):
    fueling_history = VehicleFuelHistory.objects.filter(vehicle_id=id).order_by("-created")
    paginator = Paginator(fueling_history, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}
    return render(request, "vehicles/fuel_history.html", context)


@login_required(login_url="/users/login")
def vehicle_service_history(request, id):
    service_history = VehicleServiceHistory.objects.filter(vehicle_id=id).order_by("-created")
    paginator = Paginator(service_history, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}
    return render(request, "vehicles/service_history.html", context)