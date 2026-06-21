from django.shortcuts import render, redirect
from apps.payments.models import (
    CommonDeduction,
    ContractAllowance,
    EmployeeContract,
    EmployeeSalary,
    EmployeeOvertime,
    MONTHS_LIST,
    PAYEBand,
    Payslip,
    BankInformation,
    PayrollLine,
    PayrollRun,
    PersonalDeduction,
)
from apps.payments.services import generate_payroll_run
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from apps.employees.models import Employee
import calendar


date_today = datetime.now().date()
current_month = calendar.month_name[date_today.month]
current_year = str(date_today.year)


def parse_money(value):
    return value or 0


def payroll_base_context(active_tab="overview"):
    contracts = EmployeeContract.objects.select_related("employee").all()
    common_deductions = CommonDeduction.objects.all()
    paye_bands = PAYEBand.objects.all()
    personal_deductions = PersonalDeduction.objects.select_related("employee").all()
    payroll_runs = PayrollRun.objects.all()
    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])
    active_contracts = contracts.filter(is_active=True)

    return {
        "active_tab": active_tab,
        "contracts": contracts,
        "common_deductions": common_deductions,
        "paye_bands": paye_bands,
        "personal_deductions": personal_deductions,
        "payroll_runs": payroll_runs,
        "employees": employees,
        "months": MONTHS_LIST,
        "current_year": current_year,
        "active_contracts_count": active_contracts.count(),
        "employees_without_contract": employees.exclude(contracts__is_active=True).count(),
        "common_deductions_count": common_deductions.filter(is_active=True).count(),
        "latest_run": payroll_runs.first(),
    }


@login_required(login_url="/users/login")
def payroll_dashboard(request):
    return render(request, "payroll/dashboard.html", payroll_base_context("overview"))


@login_required(login_url="/users/login")
def payroll_contracts(request):
    return render(request, "payroll/contracts.html", payroll_base_context("contracts"))


@login_required(login_url="/users/login")
def payroll_contract_detail(request, contract_id):
    contract = EmployeeContract.objects.select_related("employee").get(id=contract_id)
    context = payroll_base_context("contracts")
    context.update(
        {
            "contract": contract,
            "allowances": contract.allowances.all(),
            "employee_deductions": PersonalDeduction.objects.filter(
                employee=contract.employee
            ),
        }
    )
    return render(request, "payroll/contract_detail.html", context)


@login_required(login_url="/users/login")
def payroll_paye(request):
    return render(request, "payroll/paye.html", payroll_base_context("paye"))


@login_required(login_url="/users/login")
def payroll_deductions(request):
    return render(request, "payroll/deductions.html", payroll_base_context("deductions"))


@login_required(login_url="/users/login")
def payroll_configurations(request):
    return redirect("payroll-deductions")


@login_required(login_url="/users/login")
def payroll_personal_deductions(request):
    return render(
        request,
        "payroll/personal_deductions.html",
        payroll_base_context("personal-deductions"),
    )


@login_required(login_url="/users/login")
def payroll_runs(request):
    return render(request, "payroll/runs.html", payroll_base_context("runs"))


@login_required(login_url="/users/login")
def create_contract(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        is_active = request.POST.get("is_active") == "on"
        if is_active:
            EmployeeContract.objects.filter(employee_id=employee_id, is_active=True).update(
                is_active=False
            )
        EmployeeContract.objects.create(
            employee_id=employee_id,
            title=request.POST.get("title") or "Employment Contract",
            pay_basis=request.POST.get("pay_basis"),
            monthly_salary=parse_money(request.POST.get("monthly_salary")),
            daily_rate=parse_money(request.POST.get("daily_rate")),
            overtime_rate=parse_money(request.POST.get("overtime_rate")),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date") or None,
            is_active=is_active,
            notes=request.POST.get("notes"),
        )
    return redirect("payroll-contracts")


@login_required(login_url="/users/login")
def edit_contract(request):
    if request.method == "POST":
        contract = EmployeeContract.objects.get(id=request.POST.get("contract_id"))
        status = request.POST.get("status")
        is_active = status == "Active" if status else request.POST.get("is_active") == "on"
        if is_active:
            EmployeeContract.objects.filter(
                employee=contract.employee, is_active=True
            ).exclude(id=contract.id).update(is_active=False)

        contract.title = request.POST.get("title") or "Employment Contract"
        contract.pay_basis = request.POST.get("pay_basis")
        contract.monthly_salary = parse_money(request.POST.get("monthly_salary"))
        contract.daily_rate = parse_money(request.POST.get("daily_rate"))
        contract.overtime_rate = parse_money(request.POST.get("overtime_rate"))
        contract.start_date = request.POST.get("start_date")
        contract.end_date = request.POST.get("end_date") or None
        contract.is_active = is_active
        contract.notes = request.POST.get("notes")
        contract.save()
    return redirect("payroll-contracts")


@login_required(login_url="/users/login")
def create_common_deduction(request):
    if request.method == "POST":
        CommonDeduction.objects.create(
            name=request.POST.get("name"),
            value_type=request.POST.get("value_type"),
            value=parse_money(request.POST.get("value")),
            is_active=request.POST.get("is_active") == "on",
            description=request.POST.get("description"),
        )
    return redirect("payroll-deductions")


@login_required(login_url="/users/login")
def edit_common_deduction(request):
    if request.method == "POST":
        deduction = CommonDeduction.objects.get(id=request.POST.get("deduction_id"))
        deduction.name = request.POST.get("name")
        deduction.value_type = request.POST.get("value_type")
        deduction.value = parse_money(request.POST.get("value"))
        deduction.is_active = request.POST.get("is_active") == "on"
        deduction.description = request.POST.get("description")
        deduction.save()
    return redirect("payroll-deductions")


@login_required(login_url="/users/login")
def create_paye_band(request):
    if request.method == "POST":
        PAYEBand.objects.create(
            name=request.POST.get("name"),
            lower_limit=parse_money(request.POST.get("lower_limit")),
            upper_limit=request.POST.get("upper_limit") or None,
            rate=parse_money(request.POST.get("rate")),
            relief_amount=parse_money(request.POST.get("relief_amount")),
            is_active=request.POST.get("is_active") == "on",
        )
    return redirect("payroll-paye")


@login_required(login_url="/users/login")
def edit_paye_band(request):
    if request.method == "POST":
        band = PAYEBand.objects.get(id=request.POST.get("paye_band_id"))
        band.name = request.POST.get("name")
        band.lower_limit = parse_money(request.POST.get("lower_limit"))
        band.upper_limit = request.POST.get("upper_limit") or None
        band.rate = parse_money(request.POST.get("rate"))
        band.relief_amount = parse_money(request.POST.get("relief_amount"))
        band.is_active = request.POST.get("is_active") == "on"
        band.save()
    return redirect("payroll-paye")


@login_required(login_url="/users/login")
def create_personal_deduction(request):
    if request.method == "POST":
        contract_id = request.POST.get("contract_id")
        PersonalDeduction.objects.create(
            employee_id=request.POST.get("employee_id"),
            name=request.POST.get("name"),
            value_type=request.POST.get("value_type"),
            value=parse_money(request.POST.get("value")),
            balance=request.POST.get("balance") or None,
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date") or None,
            status=request.POST.get("status") or "Active",
            notes=request.POST.get("notes"),
        )
        if contract_id:
            return redirect("payroll-contract-detail", contract_id=contract_id)
    return redirect("payroll-personal-deductions")


@login_required(login_url="/users/login")
def edit_personal_deduction(request):
    if request.method == "POST":
        contract_id = request.POST.get("contract_id")
        deduction = PersonalDeduction.objects.get(
            id=request.POST.get("personal_deduction_id")
        )
        deduction.employee_id = request.POST.get("employee_id")
        deduction.name = request.POST.get("name")
        deduction.value_type = request.POST.get("value_type")
        deduction.value = parse_money(request.POST.get("value"))
        deduction.balance = request.POST.get("balance") or None
        deduction.start_date = request.POST.get("start_date")
        deduction.end_date = request.POST.get("end_date") or None
        deduction.status = request.POST.get("status") or "Active"
        deduction.notes = request.POST.get("notes")
        deduction.save()
        if contract_id:
            return redirect("payroll-contract-detail", contract_id=contract_id)
    return redirect("payroll-personal-deductions")


@login_required(login_url="/users/login")
def create_contract_allowance(request):
    if request.method == "POST":
        contract_id = request.POST.get("contract_id")
        ContractAllowance.objects.create(
            contract_id=contract_id,
            name=request.POST.get("name"),
            value_type=request.POST.get("value_type"),
            value=parse_money(request.POST.get("value")),
            is_active=request.POST.get("is_active") == "on",
            notes=request.POST.get("notes"),
        )
        return redirect("payroll-contract-detail", contract_id=contract_id)
    return redirect("payroll-contracts")


@login_required(login_url="/users/login")
def edit_contract_allowance(request):
    if request.method == "POST":
        allowance = ContractAllowance.objects.get(
            id=request.POST.get("contract_allowance_id")
        )
        allowance.name = request.POST.get("name")
        allowance.value_type = request.POST.get("value_type")
        allowance.value = parse_money(request.POST.get("value"))
        allowance.is_active = request.POST.get("is_active") == "on"
        allowance.notes = request.POST.get("notes")
        allowance.save()
        return redirect("payroll-contract-detail", contract_id=allowance.contract_id)
    return redirect("payroll-contracts")


@login_required(login_url="/users/login")
def payroll_run_detail(request, run_id):
    payroll_run = PayrollRun.objects.get(id=run_id)
    lines = payroll_run.lines.select_related("employee", "contract").prefetch_related("items")
    context = payroll_base_context("runs")
    context.update(
        {
            "payroll_run": payroll_run,
            "lines": lines,
        }
    )
    return render(
        request,
        "payroll/run_detail.html",
        context,
    )


@login_required(login_url="/users/login")
def generate_payroll(request):
    if request.method == "POST":
        payroll_run, _ = generate_payroll_run(
            request.POST.get("month"),
            request.POST.get("year"),
            user=request.user,
        )
        return redirect("payroll-run-detail", run_id=payroll_run.id)
    return redirect("payroll-runs")


@login_required(login_url="/users/login")
def payroll_payslip(request, line_id):
    line = PayrollLine.objects.select_related("payroll_run", "employee", "contract").prefetch_related("items").get(id=line_id)
    return render(request, "payroll/payslip.html", {"line": line})


# Create your views here.
@login_required(login_url="/users/login")
def employee_salaries(request):
    salaries = EmployeeSalary.objects.all().order_by("-created")

    paginator = Paginator(salaries, 13)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "salaries/salaries.html", context)


def overtimes(request):
    overtimes = EmployeeOvertime.objects.all()
    employees = Employee.objects.exclude(status__in=["Pending Approval", "Declined"])

    paginator = Paginator(overtimes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "employees": employees}
    return render(request, "salaries/overtimes.html", context)


def record_overtime(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        date_str = request.POST.get("overtime_date")

        employee = Employee.objects.get(id=employee_id)

        overtime_date = datetime.strptime(date_str, "%Y-%m-%d")
        month_name = calendar.month_name[overtime_date.month]

        EmployeeOvertime.objects.create(
            employee=employee,
            overtime_date=date_str,
            month=month_name,
            year=str(overtime_date.year),
            amount=employee.job_category.overtime,
        )

        # Update Salary
        salary = EmployeeSalary.objects.filter(
            employee=employee, year=current_year, month=current_month
        ).first()

        if salary:
            salary.total_amount += employee.job_category.overtime
            salary.overtime += employee.job_category.overtime
            salary.save()
        else:
            salary = EmployeeSalary.objects.create(
                employee=employee,
                month=current_month,
                year=current_year,
                days_worked=1,
                daily_rate=employee.job_category.daily_rate,
                total_amount=employee.job_category.daily_rate,
                overtime=employee.job_category.overtime,
            )

        return redirect("overtimes")

    return render(request, "salaries/record_overtime.html")


def payslips(request):
    payslips = Payslip.objects.all()

    paginator = Paginator(payslips, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}

    return render(request, "salaries/payslips.html", context)


def delete_payslip(request):
    if request.method == "POST":
        payslip_id = request.POST.get("payslip_id")
        payslip = Payslip.objects.get(id=payslip_id)
        payslip.delete()

        return redirect("payslips")
    return redirect(request, "salaries/delete_payslip.html")


def generate_payslips(request):
    if request.method == "POST":
        month_name = request.POST.get("month")
        year = request.POST.get("year")
        action_type = request.POST.get("action_type")

        if action_type.lower() == "delete":
            payslips = Payslip.objects.filter(month=month_name, year=year)
            print(payslips)
        elif action_type.lower() == "generate":
            salaries = EmployeeSalary.objects.filter(month=month_name, year=year)
            salaries_list = []
            for salary in salaries:
                salaries_list.append(
                    Payslip(
                        employee=salary.employee,
                        month=salary.month,
                        year=salary.year,
                        days_worked=salary.days_worked,
                        daily_rate=salary.daily_rate,
                        overtime=salary.overtime,
                        total_amount=salary.total_amount,
                    )
                )

            Payslip.objects.bulk_create(salaries_list)
            # print(salaries_list)

        return redirect("payslips")
    return render(request, "salaries/generate_payslips.html")


def payslip_receipt(request, id):
    payslip = Payslip.objects.get(id=id)

    return render(request, "salaries/payslip_receipt.html", {"payslip": payslip})


# Service Provider Payment Details


def new_bank_details(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        bank_name = request.POST.get("bank_name")
        branch_name = request.POST.get("branch_name")
        account_name = request.POST.get("account_name")
        account_type = request.POST.get("account_type")
        account_number = request.POST.get("account_number")

        BankInformation.objects.create(
            employee_id=employee_id,
            bank_name=bank_name,
            branch_name=branch_name,
            account_name=account_name,
            account_type=account_type,
            account_number=account_number,
        )

        return redirect(f"/employees/{employee_id}")
    return render(request, "bank/new_bank_details.html")


def edit_bank_details(request):
    if request.method == "POST":
        banking_info_id = request.POST.get("banking_info_id")
        employee_id = request.POST.get("employee_id")
        bank_name = request.POST.get("bank_name")
        branch_name = request.POST.get("branch_name")
        account_name = request.POST.get("account_name")
        account_type = request.POST.get("account_type")
        account_number = request.POST.get("account_number")

        banking_info = BankInformation.objects.get(id=banking_info_id)
        banking_info.account_number = account_number
        banking_info.account_type = account_type
        banking_info.account_name = account_name
        banking_info.bank_name = bank_name
        banking_info.branch_name = branch_name
        banking_info.save()

        return redirect(f"/employees/{employee_id}")
    return render(request, "bank/edit_bank_details.html")
