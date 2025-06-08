from django.urls import path

from .views.patients import PatientListView

urlpatterns = [
    path("patient_list", PatientListView.as_view(), name="patient_list"),
]