from django.db import models


class BaseModel(models.Model):
    """
    Base model that includes common fields for all models.
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        abstract = True
        ordering = ["-created_at", "-updated_at"]