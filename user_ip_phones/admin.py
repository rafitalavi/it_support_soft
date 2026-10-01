from django.contrib import admin
from .models import user_ip_phones_informations


@admin.register(user_ip_phones_informations)
class UserIPPhonesAdmin(admin.ModelAdmin):
    list_display = (
        'ip_phone_no',
        'employee',
        'section',
        'work_station',
        'ip_phone_model',
        'ip_phone_ip_address',
        'created_at',
    )
    search_fields = (
        'ip_phone_no',
        'employee__name',
        'employee__employee_id',
        'section',
        'work_station',
        'ip_phone_mac_address',
        'ip_phone_ip_address',
    )
    list_filter = ('section', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('Allocation & User', {
            'fields': ('employee', 'user')
        }),
        ('Workstation Location', {
            'fields': ('section', 'work_station')
        }),
        ('Phone & Network Details', {
            'fields': ('ip_phone_no', 'ip_phone_model', 'ip_phone_ip_address', 'ip_phone_mac_address')
        }),
        ('Notes', {
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
