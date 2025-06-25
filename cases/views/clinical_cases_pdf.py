from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from django.http import FileResponse
from io import BytesIO

from PIL import Image as PILImage
from PIL import ImageDraw

import urllib.request
import tempfile
import datetime
import os

from cases.models.clinical_case import ClinicalCase
from cases.models.medical_imaging import MedicalImaging
from cases.models.lung_nodule import LungNodule


class ClinicalCasePDFView(APIView):
    """
    API view to generate a PDF report for a clinical case.
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
            
            # Create a BytesIO buffer to receive PDF data
            buffer = BytesIO()
            
            # Create the PDF document using ReportLab with more space for content
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=54,  # Reduced margins to allow more space
                leftMargin=54,
                topMargin=72,
                bottomMargin=72
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles with better spacing
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                alignment=1,  # Center alignment
                spaceAfter=20,  # Reduced spacing
                fontSize=18,
                leading=24  # Increased line height to prevent cutting
            )
            
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,  # Reduced spacing
                alignment=1,  # Center alignment
                leading=18  # Increased line height
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leading=14  # Increased line height
            )
            
            # Add title and summary section to first page
            title = Paragraph(f"REPORTE DE TOMOGRAFÍAS DEL CASO {pk}", title_style)
            elements.append(title)
            
            # Get patient info if available
            patient_info = ""
            if clinical_case.patient:
                patient = clinical_case.patient
                patient_info = f"<b>Paciente:</b> {patient.names} {patient.last_names}<br/>"
                patient_info += f"<b>Identificación:</b> {patient.id_number or '-'}<br/>"
                patient_info += f"<b>Historia Clínica:</b> {patient.clinical_history or '-'}<br/>"
            
            if patient_info:
                elements.append(Paragraph(patient_info, normal_style))
                elements.append(Spacer(1, 12))
                
            # Get related medical images and nodules
            medical_images = MedicalImaging.objects.filter(clinical_case=clinical_case)
            total_images = medical_images.count()
            
            # Count images with nodules
            images_with_nodules = 0
            total_nodules = 0
            nodule_images = []
            
            for img in medical_images:
                nodules = LungNodule.objects.filter(medical_imaging=img)
                if nodules.exists():
                    images_with_nodules += 1
                    total_nodules += nodules.count()
                    # Store image and its nodules for later
                    nodule_images.append((img, list(nodules)))
            
            # Add case summary
            elements.append(Paragraph("Resumen del Caso", subtitle_style))
            
            # Date information
            date_info = f"<b>Fecha de creación:</b> {clinical_case.created_at.strftime('%d/%m/%Y %H:%M')}<br/>"
            date_info += f"<b>Fecha del reporte:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
            elements.append(Paragraph(date_info, normal_style))
            elements.append(Spacer(1, 12))
            
            # Create summary table
            summary_data = [
                ["Imágenes analizadas", "Imágenes con detecciones", "Nódulos detectados"],
                [str(total_images), str(images_with_nodules), str(total_nodules)]
            ]
            
            summary_table = Table(summary_data, colWidths=[150, 150, 150])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(summary_table)
            
            if total_nodules > 0:
                # Add a page break before the detailed section if there's content
                elements.append(PageBreak())
                elements.append(Paragraph("Detalle de Imágenes con Nódulos", title_style))
                
                # Loop through images with nodules - each in its own page
                for img_idx, (img, nodules) in enumerate(nodule_images):
                    # If not the first image, add page break
                    if img_idx > 0:
                        elements.append(PageBreak())
                        
                    # Add image title at the top of each page
                    elements.append(Paragraph(f"Imagen {img_idx+1}", subtitle_style))
                    
                    # Create a temp file for the processed image
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                        # Use full_image URL
                        image_url = img.full_image.url
                        
                        # If the URL is relative, make it absolute
                        if not image_url.startswith(('http://', 'https://')):
                            image_url = request.build_absolute_uri(image_url)
                            
                        # Download the image
                        try:
                            urllib.request.urlretrieve(image_url, temp_img.name)
                            
                            # Open image and prepare for drawing
                            pil_img = PILImage.open(temp_img.name)
                            
                            # Convert to RGB if needed (in case it's grayscale)
                            if pil_img.mode != 'RGB':
                                pil_img = pil_img.convert('RGB')
                                
                            # Create a transparent overlay for soft highlighting
                            overlay = PILImage.new('RGBA', pil_img.size, (0, 0, 0, 0))
                            draw = ImageDraw.Draw(overlay)
                            
                            # Calculate optimal image size to fit on page with nodule table
                            # For letter size with margins, aim for about 400-450px width
                            max_width = 450  # max width in pixels
                            original_width, original_height = pil_img.size
                            ratio = 1.0
                            
                            # Make the image smaller if it's too large
                            if original_width > max_width:
                                ratio = max_width / original_width
                                new_height = int(original_height * ratio)
                                pil_img = pil_img.resize((max_width, new_height), PILImage.LANCZOS)
                                overlay = overlay.resize((max_width, new_height), PILImage.LANCZOS)
                                draw = ImageDraw.Draw(overlay)
                                
                            # Draw soft bounding boxes for each nodule
                            for nodule in nodules:
                                # Calculate position based on resize ratio
                                box_x = int(nodule.x_position * original_width * ratio)
                                box_y = int(nodule.y_position * original_height * ratio)
                                box_w = int(nodule.width * original_width * ratio)
                                box_h = int(nodule.height * original_height * ratio)
                                
                                # Draw a semi-transparent highlight rectangle
                                draw.rectangle(
                                    [
                                        (box_x - box_w / 2, box_y - box_h / 2), 
                                        (box_x + box_w / 2, box_y + box_h / 2)
                                    ],
                                    outline=(255, 255, 0, 230),  # Yellow with alpha
                                    width=3
                                )
                                
                                # Add a subtle fill for better visibility
                                draw.rectangle(
                                    [
                                        (box_x - box_w / 2, box_y - box_h / 2), 
                                        (box_x + box_w / 2, box_y + box_h / 2)
                                    ],
                                    fill=(255, 255, 0, 50)  # Very transparent yellow
                                )
                            
                            # Composite the original image with the overlay
                            pil_img = PILImage.alpha_composite(
                                pil_img.convert('RGBA'), 
                                overlay
                            ).convert('RGB')
                            
                            # Save the modified image
                            pil_img.save(temp_img.name)
                            
                            # Create a centered image with appropriate size for the page
                            # Use a slightly smaller width to ensure it fits well
                            image_path = temp_img.name
                            img_obj = Image(image_path, width=420, height=None)  # Maintain aspect ratio but ensure page fit
                            
                            # Center the image with a single column table
                            centered_image = Table([[img_obj]], colWidths=[450])
                            centered_image.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ]))
                            elements.append(centered_image)
                            elements.append(Spacer(1, 15))  # Adequate space before the table
                            
                            # Create table for nodule details - now below the image
                            nodule_rows = [["Nódulo", "Tipo de malignidad", "Confianza"]]
                            for idx, nodule in enumerate(nodules):
                                confidence_pct = f"{nodule.confidence * 100:.2f}%" if nodule.confidence is not None else "N/A"
                                nodule_rows.append([
                                    f"#{idx+1}", 
                                    nodule.get_malignancy_type_display(), 
                                    confidence_pct
                                ])
                            
                            # Make the table slightly smaller to ensure it fits on the page
                            nodule_table = Table(nodule_rows, colWidths=[90, 190, 140])
                            nodule_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            
                            # Center the table with another wrapper table
                            centered_table = Table([[nodule_table]], colWidths=[420])
                            centered_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ]))
                            elements.append(centered_table)
                            
                        except Exception as e:
                            elements.append(Paragraph(f"Error processing image: {str(e)}", normal_style))
                        
                        # Clean up temporary file
                        try:
                            os.unlink(temp_img.name)
                        except:
                            pass  # Ignore cleanup errors
                            
            else:
                elements.append(Paragraph("No se detectaron nódulos en las imágenes analizadas.", normal_style))
            
            # Build the PDF document
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()
            
            # Create the HTTP response with PDF content
            response = FileResponse(
                BytesIO(pdf),
                as_attachment=True,
                filename=f"reporte_caso_{pk}.pdf"
            )
            
            return response
            
        except ClinicalCase.DoesNotExist:
            return Response(
                {"error": "Clinical case not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error generating PDF report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        