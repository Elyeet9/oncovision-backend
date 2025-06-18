from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.
from cases.models.clinical_case import ClinicalCase
from cases.models.medical_imaging import MedicalImaging
from cases.models.lung_nodule import LungNodule


class MedicalImagingInline(admin.TabularInline):
    model = MedicalImaging
    extra = 0

    readonly_fields = ('medical_imaging_link', 'created_at', 'updated_at')
    fields = ('medical_imaging_link', 'state', 'full_image', 'processed_image', 'created_at', 'updated_at')

    def medical_imaging_link(self, instance):
        if instance.pk:  # Only show link if object has been saved
            url = reverse('admin:cases_medicalimaging_change', args=[instance.pk])
            return format_html('<a href="{}">{}</a>', url, str(instance))
        return "Not saved yet"


class CustomClinicalCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "created_at", "updated_at")
    search_fields = ("id", "patient__names", "patient__last_names", "patient__id_number")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at", "-updated_at")
    inlines = (MedicalImagingInline,)


class LungNoduleInline(admin.TabularInline):
    model = LungNodule
    extra = 0

    readonly_fields = ('malignancy_type', 'x_position', 'y_position', 'width', 'height', 'confidence', 'created_at', 'updated_at')
    fields = ('malignancy_type', 'x_position', 'y_position', 'width', 'height', 'confidence', 'created_at', 'updated_at')


class CustomMedicalImagingAdmin(admin.ModelAdmin):
    list_display = ("id", "clinical_case", "state", "created_at", "updated_at")
    search_fields = ("id", "clinical_case__id", "clinical_case__patient__names", "clinical_case__patient__last_names")
    list_filter = ("state", "created_at", "updated_at")
    ordering = ("-created_at", "-updated_at")
    inlines = (LungNoduleInline,)


class CustomLungNoduleAdmin(admin.ModelAdmin):
    list_display = ("id", "medical_imaging__clinical_case", "medical_imaging", "malignancy_type", "x_position", "y_position", "width", "height", 'confidence', "created_at", "updated_at")
    search_fields = ("id", "medical_imaging__id", "medical_imaging__clinical_case__patient__names", "medical_imaging__clinical_case__patient__last_names")
    list_filter = ("malignancy_type", "created_at", "updated_at")
    ordering = ("-created_at", "-updated_at")


admin.site.register(ClinicalCase, CustomClinicalCaseAdmin)
admin.site.register(MedicalImaging, CustomMedicalImagingAdmin)
admin.site.register(LungNodule, CustomLungNoduleAdmin)