from django import forms
from .models import user_ip_phones_informations
from user_informations.models import Employee
from users.models import CustomUser


class UserIPPhonesForm(forms.ModelForm):
    class Meta:
        model = user_ip_phones_informations
        fields = [
            'employee',
            'user',
            'section',
            'work_station',
            'ip_phone_no',
            'ip_phone_model',
            'ip_phone_mac_address',
            'ip_phone_ip_address',
            'note',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. IT Operations, HR, Sales'}),
            'work_station': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. WS-302, Floor-4 Desk-12'}),
            'ip_phone_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 4021 or 88029876543'}),
            'ip_phone_model': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Cisco 7821, Yealink T46U, Grandstream'}),
            'ip_phone_mac_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 00:08:E2:09:A1:B2'}),
            'ip_phone_ip_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 192.168.20.105'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Configuration details, port allocation, or special notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).order_by('name')
        self.fields['employee'].empty_label = "-- Select Assigned Employee *"
        self.fields['user'].queryset = CustomUser.objects.filter(is_active=True).order_by('name')
        self.fields['user'].empty_label = "-- Select System User (Optional) --"
