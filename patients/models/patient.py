from oncovision.utils.models import BaseModel
from oncovision.utils.options import ID_TYPES
from django.db import models


class Patient(BaseModel):
    """
    Model representing a patient.
    """

    names = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombres")
    last_names = models.CharField(max_length=100, blank=True, null=True, verbose_name="Apellidos")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    id_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de identificación")
    id_type = models.CharField(max_length=50, choices=ID_TYPES, default=ID_TYPES[0][0], verbose_name="Tipo de identificación")
    clinical_history = models.CharField(max_length=20, blank=True, null=True, verbose_name="Historia clínica")

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["-created_at", "-updated_at"]
        unique_together = (("id_number", "id_type"),)

    def __str__(self):
        return f"{self.names} {self.last_names} ({self.id_number})" if self.id_number else f"{self.names} {self.last_names}"
    