from django.db import models

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
    first_name = models.CharField(
        max_length=100,
        verbose_name="Vorname"
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
