from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from cases.models.clinical_case import ClinicalCase
from cases.models.medical_imaging import MedicalImaging
from cases.models.lung_nodule import LungNodule 


class ClinicalCaseListView(APIView):
    """
    API view that returns a summary of clinical cases, including counts
    of medical images and nodules for each case.
    """

    def get(self, request, *args, **kwargs):
        clinical_cases = ClinicalCase.objects.all()
        response_data = []

        try:
            for case in clinical_cases:
                # Ensure patient_id is set to an empty string if patient is None
                patient_id = case.patient.id if case.patient else ""

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
                    'patient_id': case.patient.id,
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