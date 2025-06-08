from django.urls import path

from .views.patients import PatientListView, PatientCreateView

urlpatterns = [
    path("patient_list", PatientListView.as_view(), name="patient_list"),
    path("patient_create", PatientCreateView.as_view(), name="patient_create"),
]