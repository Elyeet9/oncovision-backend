from django.urls import path

from .views.clinical_cases import ClinicalCaseListView, ClinicalCaseCreateView

urlpatterns = [
    path("clinical_case_list", ClinicalCaseListView.as_view(), name="clinical_case_list"),
    path("clinical_case", ClinicalCaseCreateView.as_view(), name="clinical_case_create"),
]