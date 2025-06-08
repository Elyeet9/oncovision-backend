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
        last_name = request.query_params.get('last_name', None)
        id_number = request.query_params.get('id_number', None)
        clinical_history = request.query_params.get('clinical_history', None)

        if name:
            # Filter by name if provided
            patients = patients.filter(names__icontains=name)
            
        if last_name:
            # Filter by last_name if provided
            patients = patients.filter(last_names__icontains=last_name)

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


class PatientCreateView(APIView):
    """
    API view to create a new patient.
    """

    def post(self, request, *args, **kwargs):
        try:
            patient_data = request.data
            
            # Get the name
            names = patient_data.get('names')
            last_names = patient_data.get('last_names')
            id_number = patient_data.get('id_number')

            # Validate required fields
            if not names or not last_names or not id_number:
                return Response(
                    {"error": "Names, last names, and ID number are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if a patient with the same ID number already exists
            if Patient.objects.filter(id_number=str(id_number).strip()).exists():
                return Response(
                    {"error": "A patient with this ID number already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get clinical_history and check if it's unique
            clinical_history = patient_data.get('clinical_history', "")
            if clinical_history and Patient.objects.filter(clinical_history=clinical_history).exists():
                return Response(
                    {"error": "A patient with this clinical history already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the patient
            patient = Patient.objects.create(
                names=str(names).strip(),
                last_names=str(last_names).strip(),
                id_number=str(id_number).strip(),
                clinical_history=str(clinical_history).strip() if clinical_history else None,
            )

            return Response(
                {"message": "Patient created successfully", "id": patient.id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )