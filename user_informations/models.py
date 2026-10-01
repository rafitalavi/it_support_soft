from django.db import models
from django.conf import settings
from django.utils import timezone

class Designation(models.Model):
    name = models.CharField(max_length=150, verbose_name="Designation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Designation"
        verbose_name_plural = "Designations"
        ordering = ['name']

    def __str__(self):
        return self.name

class Employee(models.Model):
    """
    Stores employee / user personal and workstation information.
    """
    employee_id = models.CharField(max_length=50, unique=True, verbose_name="Employee ID")
    name = models.CharField(max_length=150, verbose_name="Name")
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Designation")
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Department")
    floor = models.CharField(max_length=50, blank=True, null=True, verbose_name="Floor")
    email_address = models.EmailField(blank=True, null=True, verbose_name="Email Address")
    mail_display_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Mail Display Name")
    ip_extension = models.CharField(max_length=20, blank=True, null=True, verbose_name="IP Extension")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    is_active = models.BooleanField(default=True, verbose_name="Active Employee")

    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_employees'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_employees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class ITAsset(models.Model):
    """
    Stores physical IT hardware assets (laptops, desktops, printers, etc.).
    """
    class AssetStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available / In Stock'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        RETIRED = 'RETIRED', 'Retired'

    asset_no = models.CharField(max_length=100, unique=True, verbose_name="Asset No")
    device_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Device Name")
    device_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Device Type")  # e.g. Laptop, Desktop, Printer
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=False, blank=True, null=True, verbose_name="IP Address")
    po_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="PO No")
    status = models.CharField(
        max_length=20,
        choices=AssetStatus.choices,
        default=AssetStatus.AVAILABLE,
        verbose_name="Status"
    )

    # Current owner/user
    current_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        verbose_name="Currently Assigned To"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Asset Note")

    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assets'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_assets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "IT Asset"
        verbose_name_plural = "IT Assets"
        ordering = ['asset_no']

    def __str__(self):
        return f"{self.asset_no} - {self.device_name or self.device_type or 'Asset'} ({self.get_status_display()})"

    def reassign_to(self, new_employee, assigned_by=None, remarks=""):
        """
        Reassign this asset to a new employee. Closes the previous assignment history
        record (or creates one if missing) and logs a new active assignment record.
        """
        now = timezone.now()
        old_employee = self.current_employee

        # If previously assigned to someone else, ensure their history record is archived
        if old_employee and old_employee != new_employee:
            active_hists = self.assignment_history.filter(employee=old_employee, is_current=True)
            if active_hists.exists():
                active_hists.update(
                    returned_date=now,
                    returned_by=assigned_by,
                    is_current=False
                )
            else:
                # Ensure the previous holder is NEVER omitted from history
                self.assignment_history.create(
                    employee=old_employee,
                    assigned_date=self.created_at or now,
                    returned_date=now,
                    is_current=False,
                    assigned_by=self.created_by or assigned_by,
                    returned_by=assigned_by,
                    remarks=f"Device returned and reassigned to {new_employee.name if new_employee else 'Inventory'}."
                )

        self.current_employee = new_employee
        self.status = self.AssetStatus.ASSIGNED if new_employee else self.AssetStatus.AVAILABLE
        self.updated_by = assigned_by
        self.save()

        # Create new history entry if an employee is assigned
        if new_employee:
            AssetAssignmentHistory.objects.create(
                asset=self,
                employee=new_employee,
                assigned_date=now,
                is_current=True,
                assigned_by=assigned_by,
                remarks=remarks or f"Assigned to {new_employee.name}"
            )

    def return_to_inventory(self, returned_by=None, remarks="", returned_date=None, new_status=None):
        """
        Return the asset back to IT inventory/stock. Marks asset Available (or chosen status)
        and logs the returned_date and return notes in history.
        """
        now = returned_date or timezone.now()
        active_hists = self.assignment_history.filter(is_current=True)
        if active_hists.exists():
            active_hists.update(
                returned_date=now,
                returned_by=returned_by,
                is_current=False,
                remarks=remarks if remarks else models.F('remarks')
            )
        elif self.current_employee:
            self.assignment_history.create(
                employee=self.current_employee,
                assigned_date=self.created_at or now,
                returned_date=now,
                is_current=False,
                returned_by=returned_by,
                remarks=remarks or f"Returned to inventory from {self.current_employee.name}"
            )

        self.current_employee = None
        self.status = new_status or self.AssetStatus.AVAILABLE
        self.updated_by = returned_by
        self.save()


class AssetAssignmentHistory(models.Model):
    """
    Maintains a full audit trail of every employee who previously used or currently uses an IT asset.
    """
    asset = models.ForeignKey(
        ITAsset,
        on_delete=models.CASCADE,
        related_name='assignment_history',
        verbose_name="IT Asset"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='asset_history',
        verbose_name="Employee"
    )
    assigned_date = models.DateTimeField(default=timezone.now, verbose_name="Assigned Date")
    returned_date = models.DateTimeField(blank=True, null=True, verbose_name="Returned Date")
    is_current = models.BooleanField(default=True, verbose_name="Currently Active")
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments_made',
        verbose_name="Assigned By (IT)"
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_returns_processed',
        verbose_name="Returned By (IT)"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="Assignment / Transfer Notes")

    class Meta:
        verbose_name = "Asset Assignment History"
        verbose_name_plural = "Asset Assignment Histories"
        ordering = ['-assigned_date']

    def __str__(self):
        status_text = "Current" if self.is_current else f"Returned {self.returned_date.strftime('%Y-%m-%d') if self.returned_date else ''}"
        return f"{self.asset.asset_no} -> {self.employee.name} ({status_text})"

    @property
    def duration_display(self):
        end_time = self.returned_date or timezone.now()
        delta = end_time - self.assigned_date
        days = delta.days
        hours = delta.seconds // 3600
        if days > 0:
            return f"{days} day{'s' if days != 1 else ''}"
        elif hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            minutes = max(1, delta.seconds // 60)
            return f"{minutes} min{'s' if minutes != 1 else ''}"