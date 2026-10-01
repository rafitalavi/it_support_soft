from rest_framework import serializers
# pyrefly: ignore [missing-import]
from .models import Employee, ITAsset, AssetAssignmentHistory


class EmployeeSerializer(serializers.ModelSerializer):
    active_assets_count = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_id',
            'name',
            'department',
            'floor',
            'email_address',
            'mail_display_name',
            'ip_extension',
            'note',
            'is_active',
            'active_assets_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_active_assets_count(self, obj):
        return obj.assigned_assets.count()


class AssetAssignmentHistorySerializer(serializers.ModelSerializer):
    asset_no = serializers.CharField(source='asset.asset_no', read_only=True)
    device_name = serializers.CharField(source='asset.device_name', read_only=True)
    employee_id_val = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    returned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AssetAssignmentHistory
        fields = [
            'id',
            'asset',
            'asset_no',
            'device_name',
            'employee',
            'employee_id_val',
            'employee_name',
            'assigned_date',
            'returned_date',
            'is_current',
            'assigned_by',
            'assigned_by_name',
            'returned_by',
            'returned_by_name',
            'remarks',
        ]
        read_only_fields = ['assigned_date', 'returned_date', 'is_current', 'assigned_by', 'returned_by']

    def get_assigned_by_name(self, obj):
        return str(obj.assigned_by) if obj.assigned_by else None

    def get_returned_by_name(self, obj):
        return str(obj.returned_by) if obj.returned_by else None


class ITAssetSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_employee_name = serializers.CharField(source='current_employee.name', read_only=True)
    current_employee_id = serializers.CharField(source='current_employee.employee_id', read_only=True)

    class Meta:
        model = ITAsset
        fields = [
            'id',
            'asset_no',
            'device_name',
            'device_type',
            'ip_address',
            'po_no',
            'status',
            'status_display',
            'current_employee',
            'current_employee_id',
            'current_employee_name',
            'note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ITAssetDetailSerializer(ITAssetSerializer):
    assignment_history = AssetAssignmentHistorySerializer(many=True, read_only=True)

    class Meta(ITAssetSerializer.Meta):
        fields = ITAssetSerializer.Meta.fields + ['assignment_history']


class EmployeeDetailSerializer(EmployeeSerializer):
    assigned_assets = ITAssetSerializer(many=True, read_only=True)
    asset_history = AssetAssignmentHistorySerializer(many=True, read_only=True)

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ['assigned_assets', 'asset_history']


class AssetReassignSerializer(serializers.Serializer):
    employee_id = serializers.CharField(
        required=True,
        help_text="Employee PK (id) or employee_id string (e.g. 'EMP001')"
    )
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Reason or notes for this reassignment"
    )
