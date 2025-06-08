from oncovision.utils.models import BaseModel
from oncovision.utils.options import MALIGNANCY_TYPES
from django.db import models


class LungNodule(BaseModel):
    """
    Model representing a lung nodule.
    """

    malignancy_type = models.CharField(choices=MALIGNANCY_TYPES, default=MALIGNANCY_TYPES[0][0], max_length=50, verbose_name="Tipo de malignidad")
    x_position = models.FloatField(blank=True, null=True, verbose_name="Posición X")
    y_position = models.FloatField(blank=True, null=True, verbose_name="Posición Y")
    width = models.FloatField(blank=True, null=True, verbose_name="Ancho")
    height = models.FloatField(blank=True, null=True, verbose_name="Altura")
    medical_imaging = models.ForeignKey(
        "cases.MedicalImaging",
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="lung_nodules",
        verbose_name="Caso clínico"
    )

    class Meta:
        verbose_name = "Nódulo pulmonar"
        verbose_name_plural = "Nódulos pulmonares"
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"Nódulo pulmonar {self.id} - Caso: {self.medical_imaging.clinical_case.id}"
