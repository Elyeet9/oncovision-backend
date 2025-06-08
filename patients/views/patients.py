from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from patients.models.patient import Patient


class PatientListView(APIView):
    """
    API view that returns a list of patients.
    """

    def get(self, request, *args, **kwargs):
        patients = Patient.objects.all()
        response_data = []

        # Check for name, id_number or clinical_history in query parameters
        name = request.query_params.get('name', None)
        id_number = request.query_params.get('id_number', None)
        clinical_history = request.query_params.get('clinical_history', None)

        if name:
            # Filter by name if provided
            patients = patients.filter(names__icontains=name) | patients.filter(last_names__icontains=name)
        
        if id_number:
            # Filter by id_number if provided
            patients = patients.filter(id_number__icontains=id_number)

        if clinical_history:
            # Filter by clinical_history if provided
            patients = patients.filter(clinical_history__icontains=clinical_history)

        try:
            for patient in patients:
                full_name = f'{patient.last_names}, {patient.names}'
                id_number = patient.id_number if patient.id_number else "-"
                clinical_history = patient.clinical_history if patient.clinical_history else "-"
                response_data.append({
                    'full_name': full_name,
                    'id_number': id_number,
                    'clinical_history': clinical_history,
                    'created_at': patient.created_at,
                    'updated_at': patient.updated_at
                })

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
