from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'email', 'is_staff', 'is_active')
    search_fields = ('user_id', 'name', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('user_id',)
