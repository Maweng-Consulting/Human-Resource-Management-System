from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.employees.models import Employee
from apps.payments.models import (
    CommonDeduction,
    ContractAllowance,
    EmployeeContract,
    EmployeeSalary,
    PAYEBand,
    PayrollLine,
    PayrollLineItem,
    PayrollRun,
    PersonalDeduction,
    money,
)


def get_active_contract(employee):
    return (
        EmployeeContract.objects.filter(employee=employee, is_active=True)
        .order_by("-start_date")
        .first()
    )


def calculate_paye(taxable_pay):
    taxable_pay = money(taxable_pay)
    tax_relief = Decimal("0.00")
    active_bands = list(PAYEBand.objects.filter(is_active=True).order_by("lower_limit"))

    for band in active_bands:
        tax_relief = max(tax_relief, money(band.relief_amount))

    taxable_pay = max(money(taxable_pay - tax_relief), Decimal("0.00"))
    selected_band = None
    for band in active_bands:
        lower = money(band.lower_limit)
        upper = money(band.upper_limit) if band.upper_limit is not None else None

        if taxable_pay >= lower and (upper is None or taxable_pay <= upper):
            selected_band = band
            break
        if taxable_pay >= lower:
            selected_band = band

    if not selected_band:
        return Decimal("0.00")
    return max(money(taxable_pay * selected_band.rate / Decimal("100")), Decimal("0.00"))


def build_payroll_line(payroll_run, employee, days_worked=0, overtime_hours=0):
    contract = get_active_contract(employee)
    if not contract:
        return None

    days_worked = int(days_worked or 0)
    overtime_hours = Decimal(overtime_hours or 0)
    if contract.pay_basis == "Daily":
        salary = (
            EmployeeSalary.objects.filter(
                employee=employee,
                month=payroll_run.month,
                year=payroll_run.year,
            )
            .order_by("-created", "-id")
            .first()
        )
        if salary:
            days_worked = int(salary.days_worked or 0)
            base_pay = money(salary.daily_total())
            overtime_pay = money(salary.overtime)
            overtime_hours = Decimal("0.00")
        else:
            base_pay = contract.base_pay(days_worked)
            overtime_pay = money(contract.overtime_rate * overtime_hours)
    else:
        base_pay = contract.base_pay(days_worked)
        overtime_pay = money(contract.overtime_rate * overtime_hours)

    allowance_items = []
    allowance_total = Decimal("0.00")
    for allowance in ContractAllowance.objects.filter(contract=contract, is_active=True):
        amount = allowance.calculate(base_pay)
        if amount > 0:
            allowance_total += amount
            allowance_items.append(("Earning", allowance.name, amount))

    gross_pay = money(base_pay + overtime_pay + allowance_total)

    common_items = []
    common_total = Decimal("0.00")
    for deduction in CommonDeduction.objects.filter(is_active=True):
        amount = deduction.calculate(gross_pay)
        if amount > 0:
            common_total += amount
            common_items.append(("Deduction", deduction.name, amount))

    personal_items = []
    personal_total = Decimal("0.00")
    for deduction in PersonalDeduction.objects.filter(employee=employee, status="Active"):
        amount = deduction.calculate(gross_pay)
        if amount > 0:
            personal_total += amount
            personal_items.append(("Deduction", deduction.name, amount))

    taxable_pay = gross_pay - common_total - personal_total
    paye = calculate_paye(taxable_pay)
    total_deductions = money(common_total + personal_total + paye)
    net_pay = max(money(gross_pay - total_deductions), Decimal("0.00"))

    line, _ = PayrollLine.objects.update_or_create(
        payroll_run=payroll_run,
        employee=employee,
        defaults={
            "contract": contract,
            "pay_basis": contract.pay_basis,
            "days_worked": days_worked,
            "overtime_hours": overtime_hours,
            "base_pay": base_pay,
            "overtime_pay": overtime_pay,
            "gross_pay": gross_pay,
            "common_deductions": money(common_total),
            "personal_deductions": money(personal_total),
            "paye": paye,
            "total_deductions": total_deductions,
            "net_pay": net_pay,
        },
    )

    line.items.all().delete()
    items = [
        PayrollLineItem(payroll_line=line, item_type="Earning", name="Base Pay", amount=base_pay),
    ]
    if overtime_pay > 0:
        items.append(
            PayrollLineItem(
                payroll_line=line,
                item_type="Earning",
                name="Overtime",
                amount=overtime_pay,
            )
        )
    for item_type, name, amount in allowance_items + common_items + personal_items:
        items.append(
            PayrollLineItem(
                payroll_line=line,
                item_type=item_type,
                name=name,
                amount=amount,
            )
        )
    if paye > 0:
        items.append(
            PayrollLineItem(payroll_line=line, item_type="Tax", name="PAYE", amount=paye)
        )
    PayrollLineItem.objects.bulk_create(items)
    return line


@transaction.atomic
def generate_payroll_run(month, year, defaults=None, user=None):
    defaults = defaults or {}
    year = str(year)
    existing_runs = PayrollRun.objects.select_for_update().filter(month=month, year=year)
    payroll_run = existing_runs.order_by("-processed_at", "-created", "-id").first()

    if payroll_run:
        existing_runs.exclude(id=payroll_run.id).delete()
    else:
        payroll_run = PayrollRun.objects.create(month=month, year=year)

    payroll_run.status = "Processed"
    payroll_run.processed_at = timezone.now()
    if user and user.is_authenticated:
        payroll_run.processed_by = user
    payroll_run.save()

    payroll_run.lines.all().delete()
    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"]).filter(
        contracts__is_active=True
    ).distinct()
    generated = []
    for employee in employees:
        employee_defaults = defaults.get(str(employee.id), {})
        line = build_payroll_line(
            payroll_run,
            employee,
            days_worked=employee_defaults.get("days_worked", 0),
            overtime_hours=employee_defaults.get("overtime_hours", 0),
        )
        if line:
            generated.append(line)
    return payroll_run, generated
