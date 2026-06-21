from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from apps.core.models import AbstractBaseModel
from datetime import datetime

# Create your models here.
MONTHS_LIST = (
    ("January", "January"),
    ("February", "February"),
    ("March", "March"),
    ("April", "April"),
    ("May", "May"),
    ("June", "June"),
    ("July", "July"),
    ("August", "August"),
    ("September", "September"),
    ("October", "October"),
    ("November", "November"),
    ("December", "December"),
)

PAY_BASIS_CHOICES = (
    ("Daily", "Daily work"),
    ("Monthly", "Monthly salary"),
)

DEDUCTION_VALUE_TYPES = (
    ("Percentage", "Percentage"),
    ("Amount", "Fixed amount"),
)

PERSONAL_DEDUCTION_STATUS = (
    ("Active", "Active"),
    ("Paused", "Paused"),
    ("Completed", "Completed"),
)

PAYROLL_RUN_STATUS = (
    ("Draft", "Draft"),
    ("Processed", "Processed"),
)

PAYROLL_ITEM_TYPES = (
    ("Earning", "Earning"),
    ("Deduction", "Deduction"),
    ("Tax", "Tax"),
)


def money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class EmployeeContract(AbstractBaseModel):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="contracts"
    )
    title = models.CharField(max_length=255, default="Employment Contract")
    pay_basis = models.CharField(max_length=20, choices=PAY_BASIS_CHOICES)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-is_active", "-start_date"]

    def __str__(self):
        return f"{self.employee} - {self.pay_basis}"

    def base_pay(self, days_worked=0):
        if self.pay_basis == "Monthly":
            return money(self.monthly_salary)
        return money(self.daily_rate * Decimal(days_worked or 0))


class CommonDeduction(AbstractBaseModel):
    name = models.CharField(max_length=255, unique=True)
    value_type = models.CharField(max_length=20, choices=DEDUCTION_VALUE_TYPES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def calculate(self, gross_pay):
        if self.value_type == "Percentage":
            return money(Decimal(gross_pay or 0) * self.value / Decimal("100"))
        return money(self.value)


class PAYEBand(AbstractBaseModel):
    name = models.CharField(max_length=255)
    lower_limit = models.DecimalField(max_digits=12, decimal_places=2)
    upper_limit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    relief_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["lower_limit"]

    def __str__(self):
        return self.name


class PersonalDeduction(AbstractBaseModel):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="personal_deductions"
    )
    name = models.CharField(max_length=255)
    value_type = models.CharField(max_length=20, choices=DEDUCTION_VALUE_TYPES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=PERSONAL_DEDUCTION_STATUS, default="Active"
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["employee", "name"]

    def __str__(self):
        return f"{self.employee} - {self.name}"

    def calculate(self, gross_pay):
        if self.value_type == "Percentage":
            amount = Decimal(gross_pay or 0) * self.value / Decimal("100")
        else:
            amount = self.value
        if self.balance is not None:
            amount = min(amount, self.balance)
        return money(amount)


class ContractAllowance(AbstractBaseModel):
    contract = models.ForeignKey(
        EmployeeContract, on_delete=models.CASCADE, related_name="allowances"
    )
    name = models.CharField(max_length=255)
    value_type = models.CharField(max_length=20, choices=DEDUCTION_VALUE_TYPES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.contract.employee} - {self.name}"

    def calculate(self, base_pay):
        if self.value_type == "Percentage":
            return money(Decimal(base_pay or 0) * self.value / Decimal("100"))
        return money(self.value)


class PayrollRun(AbstractBaseModel):
    month = models.CharField(max_length=255, choices=MONTHS_LIST)
    year = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=PAYROLL_RUN_STATUS, default="Draft")
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("month", "year")
        ordering = ["-year", "-created"]

    def __str__(self):
        return f"{self.month} {self.year}"


class PayrollLine(AbstractBaseModel):
    payroll_run = models.ForeignKey(
        PayrollRun, on_delete=models.CASCADE, related_name="lines"
    )
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    contract = models.ForeignKey(
        EmployeeContract, on_delete=models.SET_NULL, null=True, blank=True
    )
    pay_basis = models.CharField(max_length=20, choices=PAY_BASIS_CHOICES)
    days_worked = models.PositiveIntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    base_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    common_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    personal_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("payroll_run", "employee")
        ordering = ["employee__first_name", "employee__last_name"]

    def __str__(self):
        return f"{self.employee} - {self.payroll_run}"


class PayrollLineItem(AbstractBaseModel):
    payroll_line = models.ForeignKey(
        PayrollLine, on_delete=models.CASCADE, related_name="items"
    )
    item_type = models.CharField(max_length=20, choices=PAYROLL_ITEM_TYPES)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["item_type", "name"]

    def __str__(self):
        return f"{self.name}: {self.amount}"


class EmployeeSalary(AbstractBaseModel):
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MONTHS_LIST)
    year = models.CharField(max_length=10)
    days_worked = models.IntegerField(default=0)
    daily_rate = models.DecimalField(max_digits=100, decimal_places=2)
    overtime = models.DecimalField(max_digits=100, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=100, decimal_places=2)

    def __str__(self):
        return self.employee.first_name + " " + self.employee.last_name

    def daily_total(self):
        return self.total_amount - self.overtime

    def current_date(self):
        return datetime.now().date()


class EmployeeOvertime(AbstractBaseModel):
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MONTHS_LIST)
    year = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    overtime_date = models.DateField()

    def __str__(self):
        return self.year + "-" + self.month


class Payslip(AbstractBaseModel):
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MONTHS_LIST)
    year = models.CharField(max_length=10)
    days_worked = models.IntegerField(default=0)
    daily_rate = models.DecimalField(max_digits=100, decimal_places=2)
    overtime = models.DecimalField(max_digits=100, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=100, decimal_places=2)

    def __str__(self):
        return str(self.employee)

    def daily_total(self):
        return self.total_amount - self.overtime

    def current_date(self):
        return datetime.now().date()


class BankInformation(AbstractBaseModel):
    employee = models.OneToOneField(
        "employees.Employee", on_delete=models.CASCADE, related_name="bankingdetails"
    )
    bank_name = models.CharField(max_length=255, default="Equity Bank Kenya")
    branch_name = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=255, null=True)
    account_number = models.CharField(max_length=255)

    def __str__(self):
        return self.account_name
