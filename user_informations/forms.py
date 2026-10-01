from django import forms
# pyrefly: ignore [missing-import]
from .models import Employee, ITAsset


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'name',
            'designation',
            'department',
            'floor',
            'email_address',
            'mail_display_name',
            'ip_extension',
            'note',
            'is_active',
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. EMP001'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}),
            'designation': forms.Select(attrs={'class': 'form-select', 'id': 'id_designation'}),
            'department': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Department'}),
            'floor': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Floor / Location'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@squaregroup.com'}),
            'mail_display_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. John Doe (IT)'}),
            'ip_extension': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 4231'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional remarks...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'designation' in self.fields:
            self.fields['designation'].empty_label = "-- Select Designation (Optional) --"


class ITAssetForm(forms.ModelForm):
    class Meta:
        model = ITAsset
        fields = [
            'asset_no',
            'device_name',
            'device_type',
            'ip_address',
            'po_no',
            'status',
            'current_employee',
            'note',
        ]
        widgets = {
            'asset_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. AST-2024-001'}),
            'device_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. SQ-LAP-102'}),
            'device_type': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Laptop, Desktop, Printer'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 192.168.10.45'}),
            'po_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. PO-8921'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'current_employee': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Hardware specs or notes...'}),
        }


class ReassignAssetForm(forms.Form):
    asset = forms.ModelChoiceField(
        queryset=ITAsset.objects.all().order_by('asset_no'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'reassign-asset-select'}),
        label="Select IT Asset"
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'reassign-employee-select'}),
        label="New Employee Assignment",
        help_text="Select employee to assign, or leave EMPTY to return device back to stock."
    )
    returned_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        label="Handover / Return Date",
        help_text="Leave empty to use current time."
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Reason for transfer, device condition, or return notes...'}),
        label="Transfer / Return Remarks"
    )


class ReturnAssetForm(forms.Form):
    """
    Dedicated form for returning an asset from an employee back to IT inventory.
    """
    returned_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        label="Return Date & Time",
        help_text="Leave blank to use current time."
    )
    status = forms.ChoiceField(
        choices=[
            ('AVAILABLE', 'Available / In Stock'),
            ('MAINTENANCE', 'Under Maintenance (Needs Servicing)'),
            ('RETIRED', 'Retired / Disposed'),
        ],
        initial='AVAILABLE',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Status After Return"
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Device condition, accessories included, reason for return, etc.'}),
        label="Return Condition & Remarks"
    )
