from oncovision.utils.models import BaseModel
from oncovision.utils.options import IMAGING_STATE_CHOICES
from django.db import models


class MedicalImaging(BaseModel):
    """
    Model representing an uploaded MedicalImaging.
    """

    description = models.TextField(default="", blank=True, null=True, verbose_name="Descripción de la imagen")
    state = models.CharField(
        max_length=50,
        choices=IMAGING_STATE_CHOICES, 
        default=IMAGING_STATE_CHOICES[0][0],
        blank=True, null=True,
        verbose_name="Estado de la imagen"
    )
    full_image = models.FileField(
        upload_to="medical_imaging/full_images",
        blank=True, null=True,
        verbose_name="Imagen completa"
    )
    processed_image = models.FileField(
        upload_to="medical_imaging/processed_images",
        blank=True, null=True,
        verbose_name="Imagen procesada"
    )
    clinical_case = models.ForeignKey(
        "cases.ClinicalCase",
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name="medical_imaging",
        verbose_name="Caso clínico"
    )

    class Meta:
        verbose_name = "Imagen médica"
        verbose_name_plural = "Imágenes médicas"
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"Imagen médica {self.id}"
