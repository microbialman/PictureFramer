import os
import pillow_heif
from PIL import Image, ExifTags

def convert_images_to_jpeg(folder):
    # Ensure the folder exists
    if not os.path.isdir(folder):
        print(f"Folder '{folder}' not found.")
        return
    
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            if ext in ['.jpg', '.jpeg']:
                continue  # Skip JPEG files
            
            try:
                if ext == '.heic':
                    heif_image = pillow_heif.open_heif(filepath)
                    image = Image.frombytes(
                        heif_image.mode, heif_image.size, heif_image.data, "raw", heif_image.mode, 0, 1
                    )
                else:
                    image = Image.open(filepath)
                
                # Handle orientation using EXIF data
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    exif = image._getexif()
                    if exif and orientation in exif:
                        if exif[orientation] == 3:
                            image = image.rotate(180, expand=True)
                        elif exif[orientation] == 6:
                            image = image.rotate(270, expand=True)
                        elif exif[orientation] == 8:
                            image = image.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    pass  # No EXIF orientation data
                
                # Convert and replace the original file
                new_filepath = os.path.join(folder, f"{name}.jpg")
                image.save(new_filepath, "JPEG", quality=95)
                os.remove(filepath)  # Remove original file
                print(f"Converted: {filename} -> {name}.jpg")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    convert_images_to_jpeg("Images")
