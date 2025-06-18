from django.urls import path

from .views.patients import PatientListView, PatientCreateView, PatientViewSet

urlpatterns = [
    path("patient_list", PatientListView.as_view(), name="patient_list"),
    path("patient_create", PatientCreateView.as_view(), name="patient_create"),
    path("patient_detail/<str:pk>", PatientViewSet.as_view(), name="patient_detail"),
]