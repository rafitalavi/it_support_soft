from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import Employee, ITAsset, AssetAssignmentHistory, Designation


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)


class AssetAssignmentHistoryInline(admin.TabularInline):
    model = AssetAssignmentHistory
    extra = 0
    fields = ('employee', 'assigned_date', 'returned_date', 'is_current', 'assigned_by', 'remarks')
    readonly_fields = ('assigned_date', 'returned_date', 'is_current', 'assigned_by')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # We prefer reassignment via ITAsset form save or action
        return False


class EmployeeAssetHistoryInline(admin.TabularInline):
    model = AssetAssignmentHistory
    fk_name = 'employee'
    extra = 0
    fields = ('asset', 'assigned_date', 'returned_date', 'is_current', 'assigned_by', 'remarks')
    readonly_fields = ('asset', 'assigned_date', 'returned_date', 'is_current', 'assigned_by', 'remarks')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'name',
        'designation',
        'department',
        'floor',
        'email_address',
        'ip_extension',
        'is_active',
    )
    search_fields = ('employee_id', 'name', 'designation__name', 'email_address', 'department', 'mail_display_name')
    list_filter = ('designation', 'department', 'floor', 'is_active')
    inlines = [EmployeeAssetHistoryInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'name', 'designation', 'email_address', 'mail_display_name', 'department', 'floor', 'ip_extension', 'is_active')
        }),
        ('Additional Notes', {
            'fields': ('note',)
        }),
        ('Audit Metadata', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ITAsset)
class ITAssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_no',
        'device_name',
        'device_type',
        'status',
        'current_employee',
        'ip_address',
        'po_no',
    )
    list_filter = ('status', 'device_type')
    search_fields = (
        'asset_no',
        'device_name',
        'device_type',
        'po_no',
        'ip_address',
        'current_employee__name',
        'current_employee__employee_id',
    )
    inlines = [AssetAssignmentHistoryInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('Asset Details', {
            'fields': ('asset_no', 'device_name', 'device_type', 'po_no', 'ip_address', 'status')
        }),
        ('Assignment', {
            'description': 'Assign or reassign this asset to an employee. History will automatically be recorded.',
            'fields': ('current_employee', 'note')
        }),
        ('Audit Metadata', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        is_new = not change
        old_employee = None

        if change:
            orig = ITAsset.objects.filter(pk=obj.pk).first()
            if orig:
                old_employee = orig.current_employee

        if is_new:
            obj.created_by = request.user
        obj.updated_by = request.user

        super().save_model(request, obj, form, change)

        # Detect assignment change or initial assignment
        new_employee = obj.current_employee
        if is_new and new_employee:
            obj.reassign_to(
                new_employee=new_employee,
                assigned_by=request.user,
                remarks=f"Initial assignment to {new_employee.name}"
            )
        elif change and (old_employee != new_employee):
            if new_employee:
                remarks = f"Reassigned from {old_employee.name if old_employee else 'Inventory'} to {new_employee.name}"
                obj.reassign_to(
                    new_employee=new_employee,
                    assigned_by=request.user,
                    remarks=remarks
                )
            else:
                remarks = f"Returned to inventory from {old_employee.name if old_employee else 'Unknown'}"
                obj.return_to_inventory(
                    returned_by=request.user,
                    remarks=remarks
                )


@admin.register(AssetAssignmentHistory)
class AssetAssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'employee',
        'assigned_date',
        'returned_date',
        'is_current',
        'assigned_by',
        'returned_by',
    )
    list_filter = ('is_current', 'assigned_date', 'returned_date')
    search_fields = (
        'asset__asset_no',
        'asset__device_name',
        'employee__name',
        'employee__employee_id',
        'remarks',
    )
    readonly_fields = (
        'asset',
        'employee',
        'assigned_date',
        'returned_date',
        'is_current',
        'assigned_by',
        'returned_by',
    )
    ordering = ('-assigned_date',)

    def has_add_permission(self, request):
        return False
