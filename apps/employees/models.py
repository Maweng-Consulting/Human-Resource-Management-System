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
)

GENDER_CHOICES = (
    ("Male", "Male"),
    ("Female", "Female"),
)


EMPLOYEE_STATUS = (
    ("Pending Approval", "Pending Approval"),
    ("Declined", "Declined"),
    ("Available", "Available"),
    ("On Leave", "On Leave"),
    ("Suspended", "Suspended"),
)


class Employee(AbstractBaseModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=255)
    id_number = models.CharField(max_length=255, null=True)
    nhif_number = models.CharField(max_length=255, null=True)
    nssf_number = models.CharField(max_length=255, null=True)
    kra_pin = models.CharField(max_length=255, null=True)
    position = models.ForeignKey("core.JobRole", on_delete=models.SET_NULL, null=True)
    postal_address = models.CharField(max_length=255, null=True)
    physical_address = models.CharField(max_length=255, null=True)
    town = models.CharField(max_length=255, null=True)
    county = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    basic_salary = models.DecimalField(max_digits=100, decimal_places=2, default=0)
    daily_rate = models.DecimalField(max_digits=100, decimal_places=2, default=350)
    residence = models.TextField(null=True)
    workshift = models.CharField(max_length=255, null=True)
    client = models.ForeignKey(
        "core.Client",
        on_delete=models.SET_NULL,
        null=True,
        related_name="clientsguards",
    )
    workstation = models.ForeignKey(
        "core.Workstation", on_delete=models.SET_NULL, null=True
    )
    job_category = models.ForeignKey(
        "core.PaymentConfig", on_delete=models.SET_NULL, null=True
    )
    passport_photo = models.ImageField(upload_to="passport_photos/", null=True)
    status = models.CharField(
        max_length=255, choices=EMPLOYEE_STATUS, default="Pending Approval"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



DEPLOYMENT_STATUS_CHOICES = (
    ("Active", "Active"),
    ("Reassigned", "Reassigned"),
    ("Ended", "Ended"),
)


class DeploymentAssignment(AbstractBaseModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="deployment_history"
    )
    client = models.ForeignKey(
        "core.Client", on_delete=models.SET_NULL, null=True, related_name="deployments"
    )
    workstation = models.ForeignKey(
        "core.Workstation",
        on_delete=models.SET_NULL,
        null=True,
        related_name="deployments",
    )
    work_shift = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=255, choices=DEPLOYMENT_STATUS_CHOICES, default="Active"
    )
    assigned_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        workstation = self.workstation.name if self.workstation else "Unassigned"
        return f"{self.employee} - {workstation}"

class EmployeeDocument(AbstractBaseModel):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="employeedocuments"
    )
    police_clearance = models.FileField(
        upload_to="police_clearances/", null=True, blank=True
    )
    chief_letter = models.FileField(upload_to="chief_letters/", null=True, blank=True)
    referee_letter = models.FileField(
        upload_to="recommended_letters/", null=True, blank=True
    )
    scanned_id = models.FileField(upload_to="scanned_ids/", null=True, blank=True)
    kcse_certificate = models.FileField(upload_to="kcse_certificates/", null=True)
    kcpe_certificate = models.FileField(upload_to="kcpe_certificates/", null=True)
    college_certificate = models.FileField(upload_to="college_certificates/", null=True)
    kra_certificate = models.FileField(upload_to="kra_certificates", null=True)

    def __str__(self):
        return self.employee.username


class EducationInformation(AbstractBaseModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="educationdetails"
    )
    level = models.CharField(max_length=255)
    school_name = models.CharField(max_length=255)
    start_year = models.CharField(max_length=255, null=True)
    graduation_year = models.CharField(max_length=255)

    def __str__(self):
        return self.school_name


class NextOfKin(AbstractBaseModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="nextofkins"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    email = models.EmailField(null=True)
    relation = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.first_name + " " + self.last_name
