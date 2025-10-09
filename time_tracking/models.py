from django.db import models
from django.utils import timezone


class ChipMapping(models.Model):
    
    #Lokale Zuordnung von Chip-IDs zu HRworks-Personalnummern
    #für schnelleres Caching (optional)
    
    chip_id = models.CharField(max_length=100, unique=True, verbose_name="Chip-ID")
    personnel_number = models.CharField(max_length=50, verbose_name="Personalnummer")
    employee_name = models.CharField(max_length=200, verbose_name="Mitarbeitername")
    last_synced = models.DateTimeField(auto_now=True, verbose_name="Zuletzt synchronisiert")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    class Meta:
        verbose_name = "Chip-Zuordnung"
        verbose_name_plural = "Chip-Zuordnungen"

    def __str__(self):
        return f"{self.employee_name} ({self.chip_id})"


class BookingLog(models.Model):
    
    #Lokales Log aller Stempelungen für Debugging/Monitoring
    
    BOOKING_TYPES = [
        ('come', 'Kommen'),
        ('go', 'Gehen'),
        ('business_trip', 'Dienstgang'),
    ]

    chip_id = models.CharField(max_length=100, verbose_name="Chip-ID")
    personnel_number = models.CharField(max_length=50, verbose_name="Personalnummer")
    employee_name = models.CharField(max_length=200, verbose_name="Mitarbeitername")
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES, verbose_name="Buchungstyp")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zeitstempel")
    success = models.BooleanField(default=False, verbose_name="Erfolgreich")
    error_message = models.TextField(blank=True, null=True, verbose_name="Fehlermeldung")

    class Meta:
        verbose_name = "Buchungslog"
        verbose_name_plural = "Buchungslogs"
        ordering = ['-timestamp']

    def __str__(self):
        status = "?" if self.success else "?"
        return f"{status} {self.employee_name} - {self.get_booking_type_display()} ({self.timestamp})"
