from oncovision.utils.models import BaseModel
from oncovision.utils.options import IMAGING_STATE_CHOICES
from django.db import models


def full_image_upload_path(instance, filename):
    """
    Generate file path for full images, organizing them by clinical case ID.
    """
    # Use the clinical case ID if available, otherwise use 'unassigned'
    case_id = instance.clinical_case.id if instance.clinical_case else 'unassigned'
    return f"medical_imaging/full_images/{case_id}/{filename}"

def processed_image_upload_path(instance, filename):
    """
    Generate file path for processed images, organizing them by clinical case ID.
    """
    # Use the clinical case ID if available, otherwise use 'unassigned'
    case_id = instance.clinical_case.id if instance.clinical_case else 'unassigned'
    return f"medical_imaging/processed_images/{case_id}/{filename}"


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
        upload_to=full_image_upload_path,
        blank=True, null=True,
        verbose_name="Imagen completa"
    )
    processed_image = models.FileField(
        upload_to=processed_image_upload_path,
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
