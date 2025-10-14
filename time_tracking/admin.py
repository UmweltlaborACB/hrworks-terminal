from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'chip_id', 'personnel_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'chip_id', 'personnel_number')
    readonly_fields = ('created_at', 'updated_at')
