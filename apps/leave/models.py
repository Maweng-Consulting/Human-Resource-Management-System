from django.db import models
from apps.core.models import AbstractBaseModel

# Create your models here.
STATUS_CHOICES = (
    ("Absent", "Absent"),
    ("Present", "Present"),
)

LEAVE_TYPES = (
    ("Sick Leave", "Sick Leave"),
    ("Emergency Leave", "Emergency Leave"),
    ("Normal Leave", "Normal Leave"),
)

LEAVE_STATUS_CHOICES = (
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
    ("Pending Review", "Pending Review"),
    ("Complete", "Complete"),
)


class EmployeeLeave(AbstractBaseModel):
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE)
    days_applied = models.IntegerField(default=1)
    leave_type = models.CharField(max_length=255, choices=LEAVE_TYPES)
    status = models.CharField(
        max_length=255, choices=LEAVE_STATUS_CHOICES, default="Pending Review"
    )
    leave_from = models.DateField(null=True, blank=True)
    leave_to = models.DateField(null=True)
    approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="leaveapprovers",
    )

    def __str__(self):
        return f"{self.employee.first_name}"
