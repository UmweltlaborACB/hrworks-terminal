from django.contrib import admin
from .models import Employee, ChipMapping

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'chip_id', 'personnel_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'chip_id', 'personnel_number')
    readonly_fields = ('created_at', 'updated_at')



@admin.register(ChipMapping)
class ChipMappingAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'personnel_number', 'transponder_id']
    search_fields = ['last_name', 'personnel_number', 'transponder_id']
    list_filter = ['last_name']
