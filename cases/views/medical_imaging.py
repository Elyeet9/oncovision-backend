from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files import File

from inference_sdk import InferenceHTTPClient
from dotenv import load_dotenv
import cv2
import io
import os

from cases.models.medical_imaging import MedicalImaging
from cases.models.lung_nodule import LungNodule
from oncovision.utils.image_filters import adaptiveBilateralFilter, cudaAdaptiveBilateralFilter, CUDA_AVAILABLE
from oncovision.settings import PROCESSED_IMAGE_WIDTH, PROCESSED_IMAGE_HEIGHT


class MedicalImagingViewSet(APIView):
    """
    API view for handling medical imaging data.
    This view can be extended to implement methods for listing, creating,
    updating, and deleting medical imaging records.
    """

    def put(self, request, *args, **kwargs):
        # Get image_ids and status from request data
        image_ids = request.data.get('image_ids', [])
        new_state = request.data.get('new_state', None)

        if not image_ids or new_state is None:
            return Response(
                {"error": "image_ids and status are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the status of the medical images
        medical_images = MedicalImaging.objects.filter(id__in=image_ids)
        if not medical_images.exists():
            return Response(
                {"error": f"No medical images found with the provided IDs."},
                status=status.HTTP_404_NOT_FOUND
            )

        for image in medical_images:
            # Get the image name without the file path
            if not image.full_image:
                return Response(
                    {"error": f"Image {image.id} does not have an image uploaded."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            image_name = image.full_image.name.split('/')[-1]
            if image.state == 'preview' and new_state == 'ready':
                # Create a copy of the image in 512x512 resolution
                img = cv2.imread(image.full_image.path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                if img is not None:
                    resized_img = cv2.resize(img, (512, 512))
                    filtered_img = None
                    # Check if cuda is available
                    if CUDA_AVAILABLE:
                        # Use cupy to handle the image
                        filtered_img = cudaAdaptiveBilateralFilter(resized_img, window_size=5)
                    else:
                        filtered_img = adaptiveBilateralFilter(resized_img, window_size=5)
                    
                    # Save the processed image into the processed_image field
                    is_success, buffer = cv2.imencode('.png', filtered_img)
                    if not is_success:
                        return Response(
                            {"error": f"Failed to save image {image_name}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Save the image to the model
                    image_buffer = io.BytesIO(buffer)
                    image_file = File(image_buffer, name=f"processed_{image_name}")
                    image.processed_image.save(
                        f"processed_{image_name}",
                        image_file, save=False
                    )
                else:
                    return Response(
                        {"error": f"Failed to read image {image_name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                image.state = new_state
                image.save()
            elif image.state in ('ready' or 'error') and new_state == 'processing':
                # Set to processing state
                image.state = new_state
                image.save()

                # Get the api key
                load_dotenv()
                roboflow_api_key = os.getenv("ROBOFLOW_API_KEY")

                # Initialize the inference client
                inference_client = InferenceHTTPClient(
                    api_url="https://serverless.roboflow.com",
                    api_key=roboflow_api_key
                )
                if not image.processed_image:
                    return Response(
                        {"error": f"Image {image.id} does not have a processed image."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Get the inference
                result = inference_client.run_workflow(
                    workspace_name='oncovision',
                    workflow_id='detect-and-classify-2',
                    images={
                        "image": image.processed_image.path
                    },
                    use_cache=True
                )

                if not result or 'detection_predictions' not in result[0]:
                    image.state = 'error'
                    image.save()
                    return Response(
                        {"error": f"Failed to get predictions for image {image_name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Get the predictions
                predictions = result[0]['detection_predictions']['predictions']
                for prediction in predictions:
                    # Get the nodule data
                    width = prediction['width'] / PROCESSED_IMAGE_WIDTH
                    height = prediction['height'] / PROCESSED_IMAGE_HEIGHT
                    x_position = prediction['x'] / PROCESSED_IMAGE_WIDTH
                    y_position = prediction['y'] / PROCESSED_IMAGE_HEIGHT
                    malignancy_type = prediction['class']
                    confidence = prediction['confidence']
                    # Create a new lung nodule record
                    LungNodule.objects.create(
                        malignancy_type=malignancy_type,
                        x_position=x_position,
                        y_position=y_position,
                        width=width,
                        height=height,
                        medical_imaging=image,
                        confidence=confidence
                    )

                # Set to analyzed state
                image.state = 'analyzed'
                image.save()
                

        return Response(
            {"message": "Medical images updated successfully."},
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, *args, **kwargs):
        """
        Delete multiple medical imaging records.
        """
        # Get the image IDs from the response body
        image_ids = request.data.get('image_ids', [])
        if not image_ids:
            return Response(
                {"error": "image_ids is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete the medical images
        medical_images = MedicalImaging.objects.filter(id__in=image_ids)
        if not medical_images.exists():
            return Response(
                {"error": "No medical images found with the provided IDs."},
                status=status.HTTP_404_NOT_FOUND
            )

        for image in medical_images:
            image.delete()

        return Response(
            {"message": "Medical images deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
        

class MedicalImagingID(APIView):
    """
    API view to handle operations on a specific medical imaging record by ID.
    """

    def delete(self, request, *args, **kwargs):
        """
        Delete a medical imaging record by ID.
        """
        try:
            pk = kwargs['pk']
            medical_image = MedicalImaging.objects.get(id=pk)
            medical_image.delete()
            return Response(
                {"message": "Medical imaging record deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except MedicalImaging.DoesNotExist:
            return Response(
                {"error": "Medical imaging record not found."},
                status=status.HTTP_404_NOT_FOUND
            )