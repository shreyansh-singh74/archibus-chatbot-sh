import os
import sys
import fitz  # PyMuPDF
import re
import json
import hashlib
from pathlib import Path, WindowsPath
import logging
import traceback
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_extraction.log'),
        logging.StreamHandler()
    ]
)

# Enable Windows long path support
if sys.platform == 'win32':
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "LongPathsEnabled", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        logging.warning(f"Could not enable long paths in Windows registry: {e}")

def sanitize_filename(name):
    """Remove invalid characters from filenames"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def is_valid_image(image_bytes, min_size_kb=1):
    """Check if image meets minimum size requirements"""
    return len(image_bytes) >= min_size_kb * 1024

def shorten_path(path_str, max_length=180):
    """Create a shortened path that's git-friendly"""
    if len(path_str) <= max_length:
        return path_str
    
    # Create hash of the full path to ensure uniqueness
    path_hash = hashlib.md5(path_str.encode()).hexdigest()[:8]
    
    # Split path into components
    parts = path_str.split(os.sep)
    
    # If the path has many components, keep first, last and add a hash
    if len(parts) > 3:
        # Keep first folder, last folder, and a hash for uniqueness
        shortened = os.path.join(parts[0], "shortened_" + path_hash, parts[-1])
    else:
        # For shorter paths, just add a hash suffix
        shortened = os.path.join(parts[0], path_hash)
    
    return shortened

def extract_images_from_pdf_structure(input_folder, output_folder, min_image_size_kb=1, max_path_length=180):
    """Extract images while maintaining folder hierarchy but limiting path length"""
    try:
        # Convert to Path objects to handle paths
        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        
        # Create the output base folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Path mapping file to track original vs shortened paths
        path_map_file = output_folder / "path_mapping.json"
        path_mapping = {}
        
        # Load existing mapping if it exists
        if path_map_file.exists():
            with open(path_map_file, 'r') as f:
                path_mapping = json.load(f)
        
        # Statistics tracking
        total_pdfs = 0
        total_images = 0
        
        logging.info(f"Starting extraction from: {input_folder}")
        logging.info(f"Output directory: {output_folder}")

        # Walk through the input folder structure
        for root, dirs, files in os.walk(input_folder):
            current_path = Path(root)
            rel_path = current_path.relative_to(input_folder)
            rel_path_str = str(rel_path)
            
            # Apply path shortening if needed
            if len(rel_path_str) > max_path_length:
                shortened_rel_path = shorten_path(rel_path_str, max_path_length)
                current_output_dir = output_folder / shortened_rel_path
                
                # Store mapping of shortened to original path
                path_mapping[shortened_rel_path] = rel_path_str
                logging.info(f"Path shortened: {rel_path_str} -> {shortened_rel_path}")
            else:
                current_output_dir = output_folder / rel_path
            
            # Create output directory
            try:
                current_output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logging.error(f"Error creating directory {current_output_dir}: {e}")
                continue
            
            # Process PDF files
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            folder_has_images = False
            
            for pdf_file in pdf_files:
                # Shorten PDF filename if needed
                if len(pdf_file) > 80:
                    pdf_name = pdf_file[:-4]  # Remove .pdf extension
                    shortened_pdf_name = pdf_name[:40] + "..." + pdf_name[-30:] if len(pdf_name) > 75 else pdf_name
                    folder_name = shortened_pdf_name
                else:
                    folder_name = pdf_file[:-4]  # Remove .pdf extension
                
                pdf_path = current_path / pdf_file
                pdf_output_dir = current_output_dir / folder_name
                
                logging.info(f"\nProcessing PDF: {pdf_file}")
                
                try:
                    # Create folder for this PDF
                    pdf_output_dir.mkdir(parents=True, exist_ok=True)
                    
                    doc = fitz.open(str(pdf_path))
                    pdf_image_count = 0
                    
                    # Process each page
                    for page_num in range(len(doc)):
                        try:
                            page = doc[page_num]
                            image_list = page.get_images()
                            
                            for img_index, img in enumerate(image_list):
                                try:
                                    xref = img[0]
                                    base_image = doc.extract_image(xref)
                                    
                                    if base_image and is_valid_image(base_image["image"], min_image_size_kb):
                                        image_bytes = base_image["image"]
                                        image_ext = base_image["ext"]
                                        
                                        # Create filename
                                        image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                                        image_path = pdf_output_dir / image_filename
                                        
                                        # Save image
                                        image_path.write_bytes(image_bytes)
                                        
                                        pdf_image_count += 1
                                        folder_has_images = True
                                        logging.info(f"Extracted: {image_filename}")
                                        
                                except Exception as e:
                                    logging.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {str(e)}")
                                    continue
                        
                        except Exception as e:
                            logging.error(f"Error processing page {page_num + 1}: {str(e)}")
                            continue
                    
                    doc.close()
                    
                    # Update statistics
                    if pdf_image_count > 0:
                        total_pdfs += 1
                        total_images += pdf_image_count
                        logging.info(f"Extracted {pdf_image_count} images from '{pdf_file}'")
                    else:
                        # Keep empty folder
                        logging.info(f"No images found in '{pdf_file}'")
                    
                except Exception as e:
                    logging.error(f"Failed to process PDF '{pdf_file}': {str(e)}")
                    continue
            
            # Create empty folder if no images were found
            if not folder_has_images and str(rel_path) != '.':
                current_output_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created empty folder: {rel_path}")
        
        # Save path mapping
        with open(path_map_file, 'w') as f:
            json.dump(path_mapping, f, indent=2)
        
        # Print final report
        logging.info("\n=== Extraction Summary ===")
        logging.info(f"Total PDFs with images: {total_pdfs}")
        logging.info(f"Total images extracted: {total_images}")
        logging.info(f"Path mapping saved to: {path_map_file}")

    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        logging.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    # Use Windows extended-length path syntax
    input_folder = r"C:\Users\Aryan\Documents\Archibus Docs"
    output_folder = r"C:\Users\Aryan\Documents\Archibus Docs\Extracted"
    
    try:
        extract_images_from_pdf_structure(input_folder, output_folder, min_image_size_kb=1, max_path_length=180)
        print("Process completed successfully!")
    except Exception as e:
        print(f"Error: {e}")