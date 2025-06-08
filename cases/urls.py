from django.urls import path

from .views.clinical_cases import ClinicalCaseListView

urlpatterns = [
    path("clinical_case_list", ClinicalCaseListView.as_view(), name="clinical_case_list"),
]