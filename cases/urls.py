from django.urls import path

from .views.clinical_cases import ClinicalCaseListView, ClinicalCaseCreateView, ClinicalCaseViewSet, ClinicalCaseUploadImagesView
from .views.medical_imaging import MedicalImagingViewSet, MedicalImagingID

urlpatterns = [
    path("clinical_case_list", ClinicalCaseListView.as_view(), name="clinical_case_list"),
    path("clinical_case", ClinicalCaseCreateView.as_view(), name="clinical_case_create"),
    path("clinical_case_detail/<int:pk>", ClinicalCaseViewSet.as_view(), name="clinical_case_detail"),
    path("upload_images", ClinicalCaseUploadImagesView.as_view(), name="upload_images"),
    path("medical_imaging", MedicalImagingViewSet.as_view(), name="medical_imaging"),
    path("medical_imaging/<str:pk>", MedicalImagingID.as_view(), name="medical_imaging_id"),
]