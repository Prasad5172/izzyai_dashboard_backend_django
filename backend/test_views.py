from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
from rest_framework import status
from payment.models import Payment
from django.db.models import Sum, FloatField, Value
from django.db.models.functions import Coalesce
from authentication.models import CustomUser
from clinic.models import Clinics,PatientFiles
from django.core.exceptions import ValidationError
import os
from django.core.files.storage import default_storage
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
import uuid
from django.utils import timezone
import boto3
import mimetypes
import environ
env = environ.Env()
environ.Env.read_env()
import io
import gzip
import fitz  # PyMuPDF
import zipfile
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageEnhance
import aspose.words as aw
import tempfile
import re
from clinic.models import DemoRequested
import random
import string
from django.utils.timezone import now
from datetime import datetime, timedelta
from sales_person.models import SalePersonActivityLog,SalePersons,SalePersonPipeline,SalesTarget
from django.shortcuts import get_object_or_404
from utils.MonthsShortHand import MONTH_ABBREVIATIONS
from django.db.models.functions import ExtractMonth,ExtractYear,Concat,Cast,ExtractWeek,ExtractQuarter,Round
from django.db.models import Count,Q, Sum, Count, Case, When, IntegerField,Subquery,OuterRef,F,CharField,Prefetch,ExpressionWrapper
from payment.models import Payment
from authentication.models import UserProfile

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME,  # Ensure this is set correctly
    config=Config(signature_version='s3v4')  # Force Signature Version 4
)

def compress_image(file):
    img = Image.open(file)
    compressed_io = io.BytesIO()
    img_format = img.format
    original_size = img.size

    if img_format in ["JPEG", "JPG"]:
        img = img.convert("RGB")
        img.save(compressed_io, format="JPEG", quality=40, optimize=True)
    elif img_format == "PNG":
        # Preserve transparency if present
        if img.mode != 'RGBA' and 'transparency' not in img.info:
            img = img.convert('RGB')
        else:
            img = img.convert('RGBA')
        
        # Try to compress while maintaining quality
        try:
            # First attempt with moderate compression
            img.save(compressed_io, format="PNG", optimize=True, compress_level=6)
            
            # Check if compression was effective
            compressed_io.seek(0, 2)  # Go to end
            compressed_size = compressed_io.tell()
            compressed_io.seek(0)  # Go back to beginning
            
            # If not effective, try more aggressive approach
            if original_size > 0 and compressed_size > 0.9 * original_size:
                compressed_io = io.BytesIO()
                
                # For RGB images, try color reduction
                if img.mode == 'RGB':
                    try:
                        # Count approximate unique colors
                        sample = list(img.getdata(0))[:1000]  # Sample first 1000 pixels
                        unique_sample = len(set(sample))
                        
                        # Only quantize if many colors
                        if unique_sample > 100:
                            img = img.quantize(colors=256, method=2).convert('RGB')
                    except Exception as e:
                        print(f"Color quantization error: {e}")
                
                # Save with moderate compression
                img.save(compressed_io, format="PNG", optimize=True, compress_level=6)
        except Exception as e:
            # Fallback to basic save
            print(f"Error during PNG compression: {e}")
            compressed_io = io.BytesIO()
            img.save(compressed_io, format="PNG")
    
    # Handle other formats
    else:
        # Just save with default settings
        img.save(compressed_io, format=img_format if img_format else "JPEG")
    

    compressed_io.seek(0)
    compressed_io.name = file.name
    new_size = compressed_io.getbuffer().nbytes
    return compressed_io, mimetypes.guess_type(file.name)[0] or "image/jpeg",original_size

def restore_original_quality(compressed_file, original_format=None):
    """
    Attempts to restore a compressed image to better quality.
    Note: This cannot fully restore original quality as compression is lossy.
    
    Args:
        compressed_file: The compressed image file object or path
        original_format: Optional format to save as (e.g., 'PNG', 'JPEG')
        
    Returns:
        BytesIO object containing the restored image
    """
    from PIL import Image, ImageEnhance
    import io
    
    # Open the compressed image
    if isinstance(compressed_file, str):
        # If it's a string path
        img = Image.open(compressed_file)
    elif hasattr(compressed_file, 'read'):
        # If it's a file-like object
        img = Image.open(compressed_file)
    else:
        raise ValueError("Input must be a file path or file-like object")
    
    # Get original format if not specified
    if original_format is None:
        original_format = img.format or 'PNG'
    
    # Convert to the appropriate color mode based on format
    if original_format.upper() in ['JPEG', 'JPG']:
        img = img.convert('RGB')
    elif original_format.upper() == 'PNG' and img.mode != 'RGBA':
        # Check if image might need alpha channel
        if 'transparency' in img.info:
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
    
    # Apply some enhancements to improve visual quality
    # Note: This cannot recover lost information but can improve appearance
    
    # 1. Enhance sharpness slightly
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)  # Sharpen by 20%
    
    # 2. Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)  # Increase contrast by 10%
    
    # Create output buffer
    output_io = io.BytesIO()
    
    # Save with high quality settings
    if original_format.upper() in ['JPEG', 'JPG']:
        img.save(output_io, format='JPEG', quality=95, subsampling=0)
    elif original_format.upper() == 'PNG':
        img.save(output_io, format='PNG', compress_level=1)  # Minimal compression
    else:
        # For other formats
        img.save(output_io, format=original_format)
    
    output_io.seek(0)
    return output_io

def restore_from_s3(bucket_name, file_key, original_format=None):
    """
    Retrieves a compressed image from S3 and attempts to restore its quality.
    
    Args:
        bucket_name: S3 bucket name
        file_key: Key of the file in S3
        original_format: Optional format to restore to (e.g., 'PNG', 'JPEG')
        
    Returns:
        BytesIO object containing the restored image
    """
    import boto3
    import io
    from PIL import Image
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    # Get the compressed image from S3
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        compressed_data = obj["Body"].read()
    except Exception as e:
        raise Exception(f"Error retrieving file from S3: {e}")
    
    # Create BytesIO object from the data
    compressed_io = io.BytesIO(compressed_data)
    
    # Detect format if not specified
    if original_format is None:
        try:
            img = Image.open(compressed_io)
            original_format = img.format
            compressed_io.seek(0)  # Reset file pointer
        except Exception:
            # Default to PNG if detection fails
            original_format = 'PNG'
    
    # Restore quality
    return restore_original_quality(compressed_io, original_format)

def compress_pdf(file):
    reader = PdfReader(file)
    writer = PdfWriter(clone_from=reader)
    
    for page in writer.pages:
        for img in page.images:
            img.replace(img.image, quality=80)
        page.compress_content_streams(level=9)
        
    writer.compress_identical_objects()
    
    output_pdf = io.BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    output_pdf.name = file.name
    
    input_size = file.size
    output_size = len(output_pdf.getvalue())
    
    compression_ratio = (1 - output_size / input_size) * 100
    print(f"Compressed from {input_size} to {output_size} bytes ({compression_ratio:.2f}% reduction)")
    
    return output_pdf, "application/pdf",output_size

def compress_file(file):
    compressed_io = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed_io, mode="wb") as gz_file:
        gz_file.write(file.read())
    compressed_io.seek(0)
    compressed_io.name = f"{file.name}.gz"
    return compressed_io, mimetypes.guess_type(file.name)[0] or "application/octet-stream"

def compress_docx_lossless(file):
    # Get original file size
    file.seek(0)
    file_content = file.read()
    input_size = len(file_content)
    
    # Create a temporary directory to work with the DOCX contents
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create paths
        input_path = os.path.join(temp_dir, "input.docx")
        extracted_path = os.path.join(temp_dir, "extracted")
        output_path = os.path.join(temp_dir, "output.docx")
        
        # Write the input file
        with open(input_path, 'wb') as f:
            f.write(file_content)
        
        # Extract the DOCX (which is a ZIP file)
        os.makedirs(extracted_path, exist_ok=True)
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)
        
        # Only compress images losslessly
        media_dir = os.path.join(extracted_path, "word", "media")
        if os.path.exists(media_dir):
            for filename in os.listdir(media_dir):
                file_path = os.path.join(media_dir, filename)
                
                # Only process PNG images - we can optimize these losslessly
                if filename.lower().endswith('.png'):
                    try:
                        # Open and optimize PNG losslessly
                        with Image.open(file_path) as img:
                            # Save with maximum lossless compression
                            img.save(file_path, format="PNG", optimize=True, compress_level=9)
                    except Exception as e:
                        print(f"Error processing image {filename}: {e}")
        
        # Optional: Clean up XML files without changing content
        # This removes whitespace and formatting in XML but preserves all content
        for root, _, files in os.walk(extracted_path):
            for file_name in files:
                if file_name.endswith('.xml'):
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Remove unnecessary whitespace in XML (doesn't affect document content)
                        content = re.sub(r'>\s+<', '><', content)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except Exception as e:
                        print(f"Error cleaning XML file {file_name}: {e}")
        
        # Create a new DOCX with maximum compression settings
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output_zip:
            # Walk through the extracted directory and add all files to the new ZIP
            for root, _, files in os.walk(extracted_path):
                for file_name in files:
                    abs_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(abs_path, extracted_path)
                    output_zip.write(abs_path, rel_path)
        
        # Read the compressed file into a BytesIO object
        with open(output_path, 'rb') as f:
            output_io = io.BytesIO(f.read())
    
    # Calculate compression ratio
    output_size = len(output_io.getvalue())
    compression_ratio = (1 - output_size / input_size) * 100
    print(f"Compressed from {input_size} to {output_size} bytes ({compression_ratio:.2f}% reduction)")
    
    # Restore original file name if available
    output_io.name = getattr(file, "name", "compressed.docx")
    output_io.seek(0)
    
    return output_io, "application/vnd.openxmlformats-officedocument.wordprocessingml.document",output_size

#role - clinic,slp,sale_person,sale_director,patient,admin,profile_image
def upload_to_s3(file, bucket_name, diagnosis_name, role, user_id, content_type):
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(file.name)[-1]
    file_name_without_ext = os.path.splitext(file.name)[0].replace(" ", "+")
    file_name = f"{diagnosis_name}_{unique_id}.{file_extension}" if diagnosis_name else f"{file_name_without_ext}_{unique_id}.{file_extension}"
    folder_path = f"uploads/{role}/{user_id}/{file_name}"
    
    s3.upload_fileobj(
        file, bucket_name, folder_path, 
        ExtraArgs={
            "ContentType": content_type,
            "ServerSideEncryption": "AES256"
        }
    )
    
    region = s3.get_bucket_location(Bucket=bucket_name).get('LocationConstraint', 'us-east-1')
    return {"object_url": f"https://s3.{region}.amazonaws.com/{bucket_name}/{folder_path}", "file_name": file_name, "file_path": folder_path, "content_type": content_type}

def generate_presigned_url(bucket_name, key, content_type, expiration=36000):
    try:
        return s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': key,
                'ResponseContentType': content_type
            },
            ExpiresIn=expiration,
        )
    except NoCredentialsError:
        return None

def get_s3_objects(bucket_name,role,user_id):
    print("get_s3_objects")
    folder_prefix = f"uploads/{role}/{user_id}/"
    objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
    if 'Contents' in objects:
        return [obj['Key'] for obj in objects['Contents']]
    return []

def get_all_files(bucket_name,role,user_id):
    print("get_all_files")
    object_keys = get_s3_objects(bucket_name,role,user_id)
    s3_url = f"https://{bucket_name}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"
    files = [{'url': s3_url + key} for key in object_keys]
    return files

def file_exists_in_s3(bucket_name, folder_path):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
    return 'Contents' in response

def delete_from_s3(bucket_name, file_path):
    try:
        if not file_exists_in_s3(bucket_name, file_path):
            return {"error": "Wrong file name - Provide correct file name with Extension"}
        response = s3.delete_object(Bucket=bucket_name, Key=file_path)
        return {"message": "File deleted successfully", "file_name": file_path}
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}
    
def rename_s3_file(bucket_name, role, user_id, old_file_name,new_file_name):
    unique_id = str(uuid.uuid4())[:8]
    file_extension = old_file_name.split('.')[-1]
    
    new_file_name = f"{new_file_name}_{unique_id}.{file_extension}"  # Generate a new name
    old_key = f"uploads/{role}/{user_id}/{old_file_name}"
    new_key = f"uploads/{role}/{user_id}/{new_file_name}"

    try:
        # Copy the file to the new key
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': old_key},
            Key=new_key
        )
        
        # Delete the old file after copying
        s3.delete_object(Bucket=bucket_name, Key=old_key)

        file_url = f"https://{bucket_name}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{new_key}"
        
        return {"message": "File renamed successfully", "new_file_name": new_file_name, "file_url": file_url}
    except Exception as e:
        return {"error": f"Failed to rename file: {str(e)}"}


# Define file upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [
    "image/jpeg", "image/png", 
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # .docx
]
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"]

def validate_file(file):
    """ Validate file size and type before uploading """
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds {MAX_FILE_SIZE / (1024 * 1024)}MB limit.")
    print(file.content_type)
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(f"Unsupported file type-{file.content_type}.")
    
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file extension.")

#need to implement - https://chatgpt.com/share/67c9c8a5-f30c-8012-9259-2ad24ca3e270
class Test(APIView):
    def post(self, request):
        try:
            file = request.FILES.get('file')
            user_id = request.GET.get('user_id')
            role = request.GET.get('role')
            diagnosis_name = request.GET.get('diagnosis_name', None)

            if not file or not user_id or not role:
                return Response({'error': 'File, UserID, and Role are required'}, status=400)

            user = CustomUser.objects.get(user_id=user_id)
            
            try:
                validate_file(file)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            file_extension = os.path.splitext(file.name)[-1].lower()
            content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            
            if file_extension in ['.jpg', '.jpeg', '.png']:
                file, content_type,original_size = compress_image(file)
            elif file_extension == '.pdf':
                file, content_type,original_size = compress_pdf(file)
            elif file_extension not in ['.zip', '.tar.gz', '.gz', '.bz2']:
                file, content_type,original_size = compress_docx_lossless(file)

            result = upload_to_s3(file, AWS_STORAGE_BUCKET_NAME, diagnosis_name, role, user_id, content_type)

            patient_file = PatientFiles.objects.create(
                file_name=result['file_name'],
                diagnosis_name=diagnosis_name,
                file_url=result['object_url'],
                file_path=result['file_path'],
                user=user,
                role=role,
                content_type=result['content_type']
            )

            return Response({
                'message': 'File uploaded successfully',
                'file_id': patient_file.file_id,
                **result
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self,request):
        try:
            file_id = request.GET.get('file_id')
            file = PatientFiles.objects.filter(file_id=file_id).first()
            content_type= file.content_type
            parsed_url = generate_presigned_url(AWS_STORAGE_BUCKET_NAME, file.file_path, content_type)
            return Response({"file":parsed_url,"content_type":content_type},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error occurred: {str(e)}'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    #we can save file path in model and no need to compute manually
    def delete(self,request):
        try:
            file_id = request.GET.get('file_id')
            file = PatientFiles.objects.filter(file_id=file_id).first()
            file_path = file.file_path
            file_name = file.file_name
            role = file.role
            user_id = file.user_id
            response = delete_from_s3(AWS_STORAGE_BUCKET_NAME,file_path)
            file.delete()
            return Response(response,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        try:
            file_id = request.GET.get('file_id')
            new_file_name = request.GET.get('file_name')

            if new_file_name is None or new_file_name == "" or new_file_name == "null":
                return Response({"error": "New file name is required"}, status=status.HTTP_400_BAD_REQUEST)

            file = PatientFiles.objects.get(file_id=file_id)
            # Rename the file in S3
            response = rename_s3_file(AWS_STORAGE_BUCKET_NAME, file.role, file.user_id, file.file_name,new_file_name)

            if "error" in response:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            # Update only the file name and file path in the database
            file.file_name = response['new_file_name']
            file.file_path = response['file_url']
            file.upload_timestamp = timezone.now()
            file.save()

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class DownloadFileView(APIView):
    def get(self, request):
        try:
            # Get file ID from request
            file_id = request.GET.get('file_id')
            if not file_id:
                return Response({"error": "File ID is required"}, status=400)
            
            # Get format for response - file or json
            return_info = request.GET.get('info', '').lower() == 'true'
            
            # Retrieve file information from database
            file = PatientFiles.objects.get(file_id=file_id)
            
            # Initialize S3 client (assuming you have AWS credentials configured)
            s3 = boto3.client('s3')
            
            try:
                # Get the file object from S3
                obj = s3.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file.file_path)
                file_data = obj["Body"].read()
                file_content_type = obj.get('ContentType', file.content_type)
                
                # Store original size
                original_size = len(file_data)
                
                # Only process images
                if file_content_type.startswith('image/'):
                    # Create file-like object
                    file_obj = io.BytesIO(file_data)
                    
                    # Determine format from content type
                    format_map = {
                        'image/jpeg': 'JPEG', 
                        'image/png': 'PNG',
                        'image/gif': 'GIF'
                    }
                    image_format = format_map.get(file_content_type, None)
                    
                    # Open the image
                    img = Image.open(file_obj)
                    
                    # Get original dimensions
                    original_dimensions = img.size
                    
                    # Get original format if not determined from content type
                    if image_format is None:
                        image_format = img.format or 'PNG'
                    
                    # Convert to the appropriate color mode
                    if image_format.upper() in ['JPEG', 'JPG']:
                        img = img.convert('RGB')
                    elif image_format.upper() == 'PNG' and img.mode != 'RGBA':
                        # Check if image might need alpha channel
                        if 'transparency' in img.info:
                            img = img.convert('RGBA')
                        else:
                            img = img.convert('RGB')
                    
                    # Apply enhancements for better quality
                    # Enhance sharpness
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.2)  # Sharpen by 20%
                    
                    # Enhance contrast
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.1)  # Increase contrast by 10%
                    
                    # Create output buffer
                    output_io = io.BytesIO()
                    
                    # Save with high quality settings
                    if image_format.upper() in ['JPEG', 'JPG']:
                        img.save(output_io, format='JPEG', quality=95, subsampling=0)
                    elif image_format.upper() == 'PNG':
                        img.save(output_io, format='PNG', compress_level=1)  # Minimal compression
                    else:
                        img.save(output_io, format=image_format)
                    
                    output_io.seek(0)
                    response_data = output_io
                    
                    # Get restored size
                    restored_size = output_io.getbuffer().nbytes
                else:
                    # Non-image files are returned as-is
                    response_data = io.BytesIO(file_data)
                    restored_size = original_size
                    original_dimensions = None
                
                # If the user requested only information
                if return_info:
                    size_info = {
                        "file_id": file_id,
                        "file_name": file.file_name,
                        "content_type": file_content_type,
                        "original_size_bytes": original_size,
                        "original_size_kb": round(original_size / 1024, 2),
                        "restored_size_bytes": restored_size,
                        "restored_size_kb": round(restored_size / 1024, 2),
                        "size_ratio": round(restored_size / original_size if original_size > 0 else 0, 2)
                    }
                    
                    # Add dimensions if it's an image
                    if original_dimensions:
                        size_info["width"] = original_dimensions[0]
                        size_info["height"] = original_dimensions[1]
                    
                    return Response(size_info)
                else:
                    # Create file response with size information in headers
                    response = FileResponse(
                        response_data,
                        content_type=file_content_type,
                        as_attachment=True,
                        filename=file.file_name
                    )
                    
                    # Add size information in headers
                    response['X-Original-Size'] = str(original_size)
                    response['X-Restored-Size'] = str(restored_size)
                    response['X-Size-Ratio'] = str(round(restored_size / original_size if original_size > 0 else 0, 2))
                    
                    return response
                
            except Exception as s3_error:
                return Response({"error": f"Error retrieving file from storage: {str(s3_error)}"}, status=404)
                
        except PatientFiles.DoesNotExist:
            return Response({"error": "File not found"}, status=404)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=400)
        
class GetAllUserFiles(APIView):
    def get(self,request):
        try:
            role=request.GET.get('role')
            user_id=request.GET.get('user_id')
            #or we can get role form user_type in user table.
            files = get_all_files(AWS_STORAGE_BUCKET_NAME,role,user_id)
            return Response({"files": files},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)


class TestingAPI(APIView):
    def get(self, request):
        try:
            # Step 1: Optimized Sales Data Query
            salespersons = SalePersons.objects.select_related('user').prefetch_related(
                Prefetch(
                    'clinics__user_profiles__user__payments',
                    queryset=Payment.objects.filter(payment_status='Paid').only('amount')
                )
            ).alias(
                active_clinics_count=Count("clinics", distinct=True),
                total_revenue=Coalesce(
                    Sum(
                        "clinics__user_profiles__user__payments__amount",
                        filter=Q(clinics__user_profiles__user__payments__payment_status="Paid")
                    ),
                    Value(0.0, output_field=FloatField())
                ),
                total_users=Count("clinics__user_profiles", distinct=True)
            ).annotate(
                sales_per_clinic=Case(
                    When(
                        active_clinics_count__gt=0,
                        then=ExpressionWrapper(
                            F("total_users") / F("active_clinics_count"),
                            output_field=FloatField()
                        )
                    ),
                    default=Value(0),
                    output_field=FloatField()
                ),
                name=F("user__username"),
                active_clinics=F("active_clinics_count"),
                revenue_generated=F("total_revenue"),
                total_users = F("total_users")
            ).values(
                "sales_person_id",
                "country",
                "name",
                "active_clinics",
                "sales_per_clinic",
                "revenue_generated",
                "total_users"
            )

            # Step 2: Optimized Commission Data Query
            commission_data = SalePersons.objects.annotate(
                commission_amount=Coalesce(
                    Sum(
                        F('sales__subscription_count') * Value(50.0, output_field=FloatField()) *
                        (F('sales__commission_percent') / 100.0),
                        distinct=True,
                        output_field=FloatField()
                    ),
                    Value(0.0, output_field=FloatField())
                )
            ).values("sales_person_id", "commission_amount")

            # Step 3: Combine Results
            sales_dict = {item['sales_person_id']: item for item in salespersons}
            for commission in commission_data:
                sales_id = commission['sales_person_id']
                if sales_id in sales_dict:
                    sales_dict[sales_id]['commission_amount'] = commission['commission_amount']

            # Step 4: Final Result
            result = list(sales_dict.values())
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
