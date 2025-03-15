import os
import json
import boto3
import uuid
from datetime import datetime

# AWS S3 Configuration (Replace with your credentials)
s3 = boto3.client('s3', aws_access_key_id="", aws_secret_access_key="")
bucket_name = "archibus-chatbot-rag"

# Root folder where extracted images are stored
root_folder = r"C:\\Users\\Aryan\\Documents\\Archibus Docs\\Extracted"

def generate_unique_key(folder_path, filename):
    """Generates a unique S3 object key using folder structure, timestamp, and UUID."""
    folder_name = os.path.basename(folder_path)  # Extract folder name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Timestamp
    unique_id = uuid.uuid4().hex[:6]  # Short UUID
    ext = os.path.splitext(filename)[1]  # Get file extension
    
    return f"{folder_name}/{timestamp}_{unique_id}{ext}"

def upload_to_s3(image_path, bucket_name):
    """Uploads an image to S3 with a unique object key and returns its URL."""
    folder_path = os.path.dirname(image_path)  # Get parent folder
    filename = os.path.basename(image_path)  # Extract filename
    object_key = generate_unique_key(folder_path, filename)  # Create unique key

    try:
        s3.upload_file(image_path, bucket_name, object_key)
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        print(f"✅ Uploaded: {filename} → {image_url}")
        return object_key, image_url
    except Exception as e:
        print(f"❌ Failed to upload {filename}: {e}")
        return None, None

def scan_and_upload_images(root_folder, bucket_name):
    """Recursively scans folders, uploads images to S3, and saves their mappings."""
    image_mapping = {}

    for folder_path, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                local_path = os.path.join(folder_path, filename)  # Full file path
                object_key, s3_url = upload_to_s3(local_path, bucket_name)
                
                if object_key and s3_url:
                    image_mapping[object_key] = s3_url  # Store mapping

    # Save mapping as JSON
    mapping_file = os.path.join(root_folder, "s3_image_mapping.json")
    with open(mapping_file, "w") as f:
        json.dump(image_mapping, f, indent=4)

    print(f"\n✅ Uploaded {len(image_mapping)} images. Mapping saved to: {mapping_file}")

# Run the script
scan_and_upload_images(root_folder, bucket_name)
