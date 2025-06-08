from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.
from patients.models.patient import Patient
from cases.models.clinical_case import ClinicalCase


class ClinicalCaseInline(admin.TabularInline):
    model = ClinicalCase
    extra = 0
    
    readonly_fields = ('case_link', 'created_at', 'updated_at')
    fields = ('case_link', 'created_at', 'updated_at')  # Add other fields you want to display
    
    def case_link(self, instance):
        if instance.pk:  # Only show link if object has been saved
            url = reverse('admin:cases_clinicalcase_change', args=[instance.pk])
            return format_html('<a href="{}">{}</a>', url, str(instance))
        return "Not saved yet"
    case_link.short_description = 'Caso Clínico'



class CustomPatientAdmin(admin.ModelAdmin):
    list_display = ("id_number", "id_type", "names", "last_names", "birth_date", "created_at", "updated_at")
    search_fields = ("names", "last_names", "id_number")
    list_filter = ("id_type", "birth_date")
    ordering = ("-created_at", "-updated_at")
    inlines = (ClinicalCaseInline,)


admin.site.register(Patient, CustomPatientAdmin)