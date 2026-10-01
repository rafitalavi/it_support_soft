from django.db import models
from django.conf import settings
from user_informations.models import Employee


class user_ip_phones_informations(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='ip_phones',
        verbose_name="Employee"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_ip_phones',
        verbose_name="System User"
    )
    section = models.CharField(max_length=100, verbose_name="Section")
    work_station = models.CharField(max_length=100, verbose_name="Work Station")
    ip_phone_no = models.CharField(max_length=100, verbose_name="IP Phone No / Extension")
    ip_phone_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="IP Phone Model")
    ip_phone_mac_address = models.CharField(max_length=100, blank=True, null=True, verbose_name="MAC Address")
    ip_phone_ip_address = models.CharField(max_length=100, blank=True, null=True, verbose_name="IP Address")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_ip_phones',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='updated_ip_phones',
        verbose_name="Updated By"
    )

    class Meta:
        verbose_name = "User IP Phone Information"
        verbose_name_plural = "User IP Phone Informations"
        ordering = ['-created_at']

    def __str__(self):
        emp_name = self.employee.name if self.employee else "Unassigned"
        return f"{emp_name} - {self.ip_phone_no}"