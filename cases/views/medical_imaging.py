from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files import File

import io
import cv2
from cupy.cuda import is_available as is_cuda_available

from cases.models.medical_imaging import MedicalImaging
from oncovision.utils.image_filters import adaptiveBilateralFilter, cudaAdaptiveBilateralFilter


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
                    if is_cuda_available():
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

        return Response(
            {"message": "Medical images updated successfully."},
            status=status.HTTP_200_OK
        )
        