from django.contrib import admin
from .models import ChipMapping

@admin.register(ChipMapping)
class ChipMappingAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'personnel_number', 'transponder_id']
    search_fields = ['last_name', 'personnel_number', 'transponder_id']
    list_filter = ['last_name']
