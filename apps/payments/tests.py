from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.employees.models import Employee
from apps.payments.models import (
    CommonDeduction,
    ContractAllowance,
    EmployeeContract,
    EmployeeSalary,
    PAYEBand,
    PayrollRun,
    PersonalDeduction,
)
from apps.payments.services import build_payroll_line, generate_payroll_run


class PayrollCalculationTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            first_name="Jane",
            last_name="Guard",
            gender="Female",
            phone_number="0700000000",
            id_number="12345678",
            status="Available",
        )
        PAYEBand.objects.create(
            name="Standard PAYE",
            lower_limit=0,
            upper_limit=50000,
            rate=10,
        )

    def test_monthly_payroll_line_applies_global_personal_and_paye_deductions(self):
        EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=30000,
            daily_rate=1000,
            overtime_rate=250,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="SHIF",
            value_type="Percentage",
            value=Decimal("2.75"),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="NSSF Tier I",
            value_type="Amount",
            value=Decimal("500.00"),
            is_active=True,
        )
        PersonalDeduction.objects.create(
            employee=self.employee,
            name="Loan",
            value_type="Amount",
            value=Decimal("1000.00"),
            balance=Decimal("800.00"),
            start_date=date(2026, 1, 1),
            status="Active",
        )
        run = PayrollRun.objects.create(month="June", year="2026")

        line = build_payroll_line(run, self.employee, overtime_hours=2)

        self.assertEqual(line.base_pay, Decimal("30000.00"))
        self.assertEqual(line.overtime_pay, Decimal("500.00"))
        self.assertEqual(line.gross_pay, Decimal("30500.00"))
        self.assertEqual(line.common_deductions, Decimal("1338.75"))
        self.assertEqual(line.personal_deductions, Decimal("800.00"))
        self.assertEqual(line.paye, Decimal("2836.13"))
        self.assertEqual(line.total_deductions, Decimal("4974.88"))
        self.assertEqual(line.net_pay, Decimal("25525.12"))
        self.assertEqual(line.items.count(), 6)

    def test_daily_contract_uses_days_worked(self):
        EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Daily",
            monthly_salary=0,
            daily_rate=1200,
            overtime_rate=100,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        run = PayrollRun.objects.create(month="July", year="2026")

        line = build_payroll_line(run, self.employee, days_worked=12, overtime_hours=3)

        self.assertEqual(line.base_pay, Decimal("14400.00"))
        self.assertEqual(line.overtime_pay, Decimal("300.00"))
        self.assertEqual(line.gross_pay, Decimal("14700.00"))

    def test_daily_contract_uses_compiled_monthly_earnings_for_run_month(self):
        EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Daily",
            monthly_salary=0,
            daily_rate=1200,
            overtime_rate=100,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        EmployeeSalary.objects.create(
            employee=self.employee,
            month="July",
            year="2026",
            days_worked=9,
            daily_rate=Decimal("1200.00"),
            overtime=Decimal("650.00"),
            total_amount=Decimal("11450.00"),
        )
        EmployeeSalary.objects.create(
            employee=self.employee,
            month="August",
            year="2026",
            days_worked=20,
            daily_rate=Decimal("1200.00"),
            overtime=Decimal("0.00"),
            total_amount=Decimal("24000.00"),
        )
        run = PayrollRun.objects.create(month="July", year="2026")

        line = build_payroll_line(run, self.employee, days_worked=30, overtime_hours=10)

        self.assertEqual(line.days_worked, 9)
        self.assertEqual(line.base_pay, Decimal("10800.00"))
        self.assertEqual(line.overtime_pay, Decimal("650.00"))
        self.assertEqual(line.gross_pay, Decimal("11450.00"))

    def test_contract_allowances_increase_gross_pay(self):
        contract = EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=30000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        ContractAllowance.objects.create(
            contract=contract,
            name="Transport Allowance",
            value_type="Amount",
            value=Decimal("2500.00"),
            is_active=True,
        )
        run = PayrollRun.objects.create(month="December", year="2026")

        line = build_payroll_line(run, self.employee)

        self.assertEqual(line.base_pay, Decimal("30000.00"))
        self.assertEqual(line.gross_pay, Decimal("32500.00"))
        self.assertEqual(line.paye, Decimal("3250.00"))
        self.assertEqual(line.net_pay, Decimal("29250.00"))
        self.assertTrue(
            line.items.filter(
                item_type="Earning",
                name="Transport Allowance",
                amount=Decimal("2500.00"),
            ).exists()
        )

    def test_payroll_applies_allowances_deductions_paye_and_tax_relief(self):
        PAYEBand.objects.all().delete()
        contract = EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=50000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        ContractAllowance.objects.create(
            contract=contract,
            name="Housing Allowance",
            value_type="Amount",
            value=Decimal("5000.00"),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="SHIF",
            value_type="Percentage",
            value=Decimal("2.00"),
            is_active=True,
        )
        PersonalDeduction.objects.create(
            employee=self.employee,
            name="Loan",
            value_type="Amount",
            value=Decimal("1000.00"),
            balance=Decimal("600.00"),
            start_date=date(2026, 1, 1),
            status="Active",
        )
        PAYEBand.objects.create(
            name="First Band",
            lower_limit=0,
            upper_limit=24000,
            rate=10,
            relief_amount=Decimal("2400.00"),
        )
        PAYEBand.objects.create(
            name="Second Band",
            lower_limit=24000,
            upper_limit=40000,
            rate=25,
            relief_amount=Decimal("2400.00"),
        )
        PAYEBand.objects.create(
            name="Third Band",
            lower_limit=40000,
            upper_limit=None,
            rate=30,
            relief_amount=Decimal("2400.00"),
        )
        run = PayrollRun.objects.create(month="November", year="2026")

        line = build_payroll_line(run, self.employee)

        self.assertEqual(line.base_pay, Decimal("50000.00"))
        self.assertEqual(line.gross_pay, Decimal("55000.00"))
        self.assertEqual(line.common_deductions, Decimal("1100.00"))
        self.assertEqual(line.personal_deductions, Decimal("600.00"))
        self.assertEqual(line.paye, Decimal("15270.00"))
        self.assertEqual(line.total_deductions, Decimal("16970.00"))
        self.assertEqual(line.net_pay, Decimal("38030.00"))
        self.assertTrue(line.items.filter(name="Housing Allowance", amount=Decimal("5000.00")).exists())
        self.assertTrue(line.items.filter(name="SHIF", amount=Decimal("1100.00")).exists())
        self.assertTrue(line.items.filter(name="Loan", amount=Decimal("600.00")).exists())
        self.assertTrue(line.items.filter(name="PAYE", amount=Decimal("15270.00")).exists())

    def test_paye_is_calculated_after_common_deductions_and_tax_relief(self):
        PAYEBand.objects.all().delete()
        EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=50000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="Housing Levy",
            value_type="Percentage",
            value=Decimal("1.50"),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="NSSF 1",
            value_type="Amount",
            value=Decimal("6500.00"),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="NSSF 2",
            value_type="Amount",
            value=Decimal("500.00"),
            is_active=True,
        )
        CommonDeduction.objects.create(
            name="SHIF",
            value_type="Percentage",
            value=Decimal("2.50"),
            is_active=True,
        )
        PersonalDeduction.objects.create(
            employee=self.employee,
            name="Staff Loan",
            value_type="Amount",
            value=Decimal("7500.00"),
            balance=Decimal("75000.00"),
            start_date=date(2026, 1, 1),
            status="Active",
        )
        PAYEBand.objects.create(
            name="Zero Band",
            lower_limit=0,
            upper_limit=23999,
            rate=0,
            relief_amount=0,
        )
        PAYEBand.objects.create(
            name="First Band",
            lower_limit=24000,
            upper_limit=33000,
            rate=10,
            relief_amount=Decimal("2400.00"),
        )
        PAYEBand.objects.create(
            name="Second Band",
            lower_limit=34000,
            upper_limit=44000,
            rate=15,
            relief_amount=Decimal("2400.00"),
        )
        PAYEBand.objects.create(
            name="Third Band",
            lower_limit=45000,
            upper_limit=150000,
            rate=25,
            relief_amount=Decimal("2400.00"),
        )
        run = PayrollRun.objects.create(month="January", year="2026")

        line = build_payroll_line(run, self.employee)

        self.assertEqual(line.gross_pay, Decimal("50000.00"))
        self.assertEqual(line.common_deductions, Decimal("9000.00"))
        self.assertEqual(line.personal_deductions, Decimal("7500.00"))
        self.assertEqual(line.paye, Decimal("3110.00"))
        self.assertTrue(line.items.filter(name="PAYE", amount=Decimal("3110.00")).exists())

    def test_generate_payroll_skips_employees_without_active_contracts(self):
        other_employee = Employee.objects.create(
            first_name="No",
            last_name="Contract",
            gender="Male",
            phone_number="0711111111",
            status="Available",
        )
        EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=20000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )

        payroll_run, lines = generate_payroll_run("August", "2026")

        self.assertEqual(payroll_run.status, "Processed")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].employee, self.employee)
        self.assertFalse(payroll_run.lines.filter(employee=other_employee).exists())

    def test_generate_payroll_rerun_refreshes_existing_month(self):
        contract = EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=20000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )

        first_run, first_lines = generate_payroll_run("September", "2026")
        contract.monthly_salary = 26000
        contract.save()
        second_run, second_lines = generate_payroll_run("September", "2026")

        self.assertEqual(first_run.id, second_run.id)
        self.assertEqual(PayrollRun.objects.filter(month="September", year="2026").count(), 1)
        self.assertEqual(second_run.lines.count(), 1)
        self.assertEqual(len(first_lines), 1)
        self.assertEqual(len(second_lines), 1)
        self.assertEqual(second_lines[0].base_pay, Decimal("26000.00"))
        self.assertEqual(second_run.lines.first().items.filter(name="Base Pay").count(), 1)

    def test_generate_payroll_rerun_removes_stale_lines(self):
        contract = EmployeeContract.objects.create(
            employee=self.employee,
            pay_basis="Monthly",
            monthly_salary=20000,
            daily_rate=0,
            overtime_rate=0,
            start_date=date(2026, 1, 1),
            is_active=True,
        )

        payroll_run, lines = generate_payroll_run("October", "2026")
        contract.is_active = False
        contract.save()
        refreshed_run, refreshed_lines = generate_payroll_run("October", "2026")

        self.assertEqual(payroll_run.id, refreshed_run.id)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(refreshed_lines), 0)
        self.assertEqual(refreshed_run.lines.count(), 0)
