from django.contrib import admin
from .models import ChipMapping, BookingLog


@admin.register(ChipMapping)
class ChipMappingAdmin(admin.ModelAdmin):
    list_display = ('chip_id', 'personnel_number', 'employee_name', 'is_active', 'last_synced')
    list_filter = ('is_active', 'last_synced')
    search_fields = ('chip_id', 'personnel_number', 'employee_name')
    readonly_fields = ('last_synced',)


@admin.register(BookingLog)
class BookingLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'employee_name', 'booking_type', 'success', 'chip_id')
    list_filter = ('success', 'booking_type', 'timestamp')
    search_fields = ('chip_id', 'personnel_number', 'employee_name')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        # Logs sollen nur lesbar sein
        return False
