import os
import json
import boto3

# 🏷️ Configuration
AWS_ACCESS_KEY_ID = "AKIA2YICAKUAOHJUBRWM"
AWS_SECRET_ACCESS_KEY = "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"
EXTRACTED_IMAGES_FOLDER = r"D:\\ArchiBusV2\\Extractor\\Extracted_Images"  # Path to extracted images
MAPPING_FILE = r"D:\\ArchiBusV2\\Extractor\\s3_upload\image_mapping.json"  # JSON output file
BUCKET_NAME = "archibus-chatbot-rag"  # Your S3 bucket name

# 🔹 Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_to_s3(image_path, image_name):
    """Uploads an image to S3 and returns its URL."""
    try:
        s3_client.upload_file(image_path, BUCKET_NAME, image_name, ExtraArgs={'ACL': 'public-read'})
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
    except Exception as e:
        print(f"❌ Error uploading {image_name}: {e}")
        return None

def process_images():
    """Uploads all extracted images and creates a mapping file."""
    all_metadata = []

    for image_name in os.listdir(EXTRACTED_IMAGES_FOLDER):
        image_path = os.path.join(EXTRACTED_IMAGES_FOLDER, image_name)
        if os.path.isfile(image_path):
            s3_url = upload_to_s3(image_path, image_name)
            if s3_url:
                metadata = {
                    "image_name": image_name,
                    "s3_url": s3_url,
                    "pdf_source": image_name.split("_page")[0] + ".pdf",
                    "page_number": int(image_name.split("_page")[1].split("_img")[0])
                }
                all_metadata.append(metadata)

    # Save mapping file
    with open(MAPPING_FILE, "w") as f:
        json.dump(all_metadata, f, indent=4)

    print(f"✅ Upload Complete! Mapping file saved at {MAPPING_FILE}")

if __name__ == "__main__":
    process_images()