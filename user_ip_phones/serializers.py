from rest_framework import serializers
from .models import user_ip_phones_informations


class UserIPPhonesSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_id_val = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.name', read_only=True)

    class Meta:
        model = user_ip_phones_informations
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_id_val',
            'employee_department',
            'user',
            'user_name',
            'section',
            'work_station',
            'ip_phone_no',
            'ip_phone_model',
            'ip_phone_mac_address',
            'ip_phone_ip_address',
            'note',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
            'updated_by',
            'updated_by_name',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
