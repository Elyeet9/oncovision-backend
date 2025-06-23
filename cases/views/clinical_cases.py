from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.files.base import ContentFile

from pydicom import dcmread
import numpy as np
import tempfile
import cv2
import os

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

        if clinical_cases:
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


class ClinicalCaseViewSet(APIView):
    """
    API view to retrieve details of a specific clinical case by its ID.
    """
    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        if not pk:
            return Response(
                {"error": "Clinical case ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            clinical_case = ClinicalCase.objects.get(id=pk)
            response_data = {
                'id': clinical_case.id,
                'description': clinical_case.description,
                'patient_id': clinical_case.patient.id_number if clinical_case.patient else '-',
                'clinical_history': clinical_case.patient.clinical_history if clinical_case.patient and clinical_case.patient.clinical_history else '-',
            }
            # Get medical images associated with the clinical case
            medical_images = MedicalImaging.objects.filter(clinical_case=clinical_case)
            medical_images_data = []
            for medical_image in medical_images:
                # Check for lung nodules if they exists
                lung_nodules = LungNodule.objects.filter(medical_imaging=medical_image)
                nodule_data = []
                for lung_nodule in lung_nodules:
                    nodule_data.append({
                        'id': lung_nodule.id,
                        'medical_imaging_id': lung_nodule.medical_imaging.id,
                        'malignancy_type': lung_nodule.get_malignancy_type_display(),
                        'x_position': lung_nodule.x_position,
                        'y_position': lung_nodule.y_position,
                        'width': lung_nodule.width,
                        'height': lung_nodule.height,
                        'confidence': lung_nodule.confidence,
                    })
                medical_images_data.append({
                    'id': medical_image.id,
                    'state': medical_image.state,
                    'full_image': medical_image.full_image.url if medical_image.full_image else None,
                    'processed_image': medical_image.processed_image.url if medical_image.processed_image else None,
                    'lung_nodules': nodule_data
                })
                
                # Add the medical image data to the response
            response_data['medical_images'] = medical_images_data

            return Response(response_data, status=status.HTTP_200_OK)
        # Handle case where clinical case does not exist
        except ClinicalCase.DoesNotExist:
            return Response(
                {"error": "Clinical case not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ClinicalCaseUploadImagesView(APIView):
    """
    API view to upload images for a clinical case.
    """

    def post(self, request, *args, **kwargs):
        # This method should handle the upload of images for a clinical case
        data = request.data

        # Get clinical_case_id
        clinical_case_id = data.get('case_id', None)
        if not clinical_case_id:
            return Response(
                {"error": "Clinical case ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            clinical_case = ClinicalCase.objects.get(id=clinical_case_id)
            # Process the uploaded images and associate them with the clinical case
            images = data.getlist('files', [])
            if not images:
                return Response(
                    {"error": "No images provided."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for image in images:
                # Check if it's in a correct format
                if not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.dcm')):
                    return Response(
                        {"error": "Invalid file type. Only PNG, JPG, JPEG, and DICOM files are allowed."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Handling DICOMS
                if image.name.lower().endswith('.dcm'):
                    try:
                        # Create a temporary file to store the uploaded DICOM
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            for chunk in image.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name
                        
                        # Read DICOM file
                        dicom_data = dcmread(temp_file_path)
                        
                        # Convert DICOM to image array
                        pixel_array = dicom_data.pixel_array
                        
                        # Normalize the pixel values
                        if pixel_array.dtype != np.uint8:
                            # Scale to 8-bit (0-255)
                            pixel_min = pixel_array.min()
                            pixel_max = pixel_array.max()
                            if pixel_max != pixel_min:  # Avoid division by zero
                                pixel_array = ((pixel_array - pixel_min) * 255.0 / (pixel_max - pixel_min))
                            pixel_array = pixel_array.astype(np.uint8)

                        # Encode as PNG
                        success, encoded_image = cv2.imencode('.png', pixel_array)
                        if not success:
                            return Response(
                                {"error": f"Failed to convert DICOM image {image.name} to PNG format."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )
                        
                        # Create a PNG file from the encoded image
                        png_file = ContentFile(encoded_image.tobytes())
                        
                        # Create MedicalImaging instance
                        medical_image = MedicalImaging(
                            clinical_case=clinical_case,
                            state='preview'
                        )
                        
                        # Use original filename but change extension to .png
                        base_filename = os.path.splitext(image.name)[0]
                        medical_image.full_image.save(f"{base_filename}.png", png_file, save=True)
                        
                        # Clean up the temp file
                        os.unlink(temp_file_path)
                        
                    except Exception as e:
                        return Response(
                            {"error": f"Error processing DICOM file {image.name}: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    # Handle regular image files (PNG, JPG, JPEG)
                    medical_image = MedicalImaging.objects.create(
                        clinical_case=clinical_case,
                        full_image=image,
                        state='preview'
                    )
                    medical_image.save()
            
            return Response(
                {"message": "Images uploaded successfully", "clinical_case_id": clinical_case.id},
                status=status.HTTP_201_CREATED
            )
        except ClinicalCase.DoesNotExist:
            return Response(
                {"error": "Clinical case not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while processing the upload: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )