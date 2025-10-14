from django.db import models

class Employee(models.Model):
    """Verknüpfung zwischen Chip-ID und HRworks Personalnummer"""
    chip_id = models.CharField(max_length=50, unique=True, verbose_name="Chip-ID")
    personnel_number = models.CharField(max_length=20, verbose_name="Personalnummer")
    name = models.CharField(max_length=100, verbose_name="Name")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mitarbeiter"
        verbose_name_plural = "Mitarbeiter"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (PN: {self.personnel_number})"


class ChipMapping(models.Model):
    """Mapping zwischen Transponder-ID und Personalnummer"""
    
    transponder_id = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        verbose_name="Transponder-ID"
    )
    personnel_number = models.CharField(
        max_length=50,
        verbose_name="Personalnummer"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Nachname"
    )
    
    class Meta:
        verbose_name = "Chip-Zuordnung"
        verbose_name_plural = "Chip-Zuordnungen"
        ordering = ['last_name']
    
    def __str__(self):
        return f"{self.last_name} ({self.personnel_number})"
