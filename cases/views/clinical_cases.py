from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from cases.models.clinical_case import ClinicalCase
from cases.models.medical_imaging import MedicalImaging
from cases.models.lung_nodule import LungNodule
from patients.models.patient import Patient 


class ClinicalCaseListView(APIView):
    """
    API view that returns a summary of clinical cases, including counts
    of medical images and nodules for each case.
    """

    def get(self, request, *args, **kwargs):
        clinical_cases = ClinicalCase.objects.all()
        response_data = []

        # Check for case_id or patient_id in query parameters
        case_id = request.query_params.get('case_id', None)
        patient_id = request.query_params.get('patient_id', None)

        if case_id:
            # Filter by case_id if provided
            clinical_cases = clinical_cases.filter(id=case_id)
        if patient_id:
            # Check for any cases with ids similar to the provided patient_id
            clinical_cases = clinical_cases.filter(patient__id_number=patient_id)

        try:
            for case in clinical_cases:
                # Ensure patient_id is set to an empty string if patient is None
                patient_id = case.patient.id_number if case.patient else "-"

                # Get counts of medical images and nodules for the case
                medical_images_count = 0
                medical_images = MedicalImaging.objects.filter(clinical_case=case)
                if medical_images.exists():
                    medical_images_count = medical_images.count()
                
                # Get count of lung nodules associated with the medical images of the case
                lung_nodules_count = 0
                lung_nodules = LungNodule.objects.filter(medical_imaging__clinical_case=case)
                if lung_nodules.exists():
                    lung_nodules_count = lung_nodules.count()

                response_data.append({
                    'id': case.id,
                    'patient_id': patient_id,
                    'medical_images_count': medical_images_count,
                    'nodules_count': lung_nodules_count,
                    'created_at': case.created_at,
                    'updated_at': case.updated_at
                })

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ClinicalCaseCreateView(APIView):
    """
    API view to create a new clinical case.
    """

    def post(self, request, *args, **kwargs):
        # This method should handle the creation of a clinical case
        data = request.data

        # Get patient_id
        patient_id = data.get('patient_id', None)
        print("patient_id", patient_id)
        patient = None
        if patient_id:
            patient = Patient.objects.filter(
                id_number=patient_id
            ).first()
            if not Patient.objects.filter(id_number=patient_id).exists():
                return Response(
                    {"error": "Patient with the provided ID does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Create the clinical case
            clinical_case = ClinicalCase.objects.create(
                description='New clinical case created via API',
            )
            if patient:
                clinical_case.patient = patient
                clinical_case.save()
            return Response(
                {"message": "Clinical case created successfully", "clinical_case_id": clinical_case.id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print(e)
            if clinical_case:
                clinical_case.delete()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
