from oncovision.utils.models import BaseModel
from django.db import models


class ClinicalCase(BaseModel):
    """
    Model representing a clinical case.
    """

    description = models.TextField(default="", blank=True, null=True, verbose_name="Descripción del caso")
    patient = models.ForeignKey(
        "patients.Patient", 
        blank=True, null=True, 
        on_delete=models.SET_NULL, 
        related_name="clinical_cases", 
        verbose_name="Paciente"
    )

    class Meta:
        verbose_name = "Caso clínico"
        verbose_name_plural = "Casos clínicos"
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"Caso clínico {self.id} - Paciente: {self.patient.names} {self.patient.last_names}" if self.patient else f"Caso clínico {self.id}"
