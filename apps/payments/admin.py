from django.contrib import admin
from apps.payments.models import EmployeeOvertime, EmployeeSalary, EmployeeContract

# Register your models here.
admin.site.register(EmployeeOvertime)
admin.site.register(EmployeeSalary)
admin.site.register(EmployeeContract)
