import os
import pillow_heif
from PIL import Image, ExifTags, ImageOps

#Rclone command to run to sync the G photos album
RUN_RCLONE = True
RCLONE_COMMAND = "clone sync Photo:album/Frame ~/Dev/PictureFrame/GPhotos"
SOURCE_DR = "~/Dev/PictureFrame/GPhotos"
TARGET_DR = "~/Dev/PictureFrame/Images"

def convert_images_to_jpeg(folder, targfolder):
    # Ensure the folder exists
    if not os.path.isdir(folder):
        print(f"Folder '{folder}' not found.")
        return
    
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            new_filepath = os.path.join(targfolder, f"{name}.jpg")

            if os.path.isfile(new_filepath):
               pass

            else:
                
                try:
                    image = Image.open(filepath)    
                    image = ImageOps.exif_transpose(image)
                    image.save(new_filepath, "JPEG", quality=95)
                    print(f"Converted: {filename} -> {name}.jpg")

                except:
                    try:
                        heif_image = pillow_heif.open_heif(filepath)
                        image = Image.frombytes(heif_image.mode, heif_image.size, heif_image.data, "raw", heif_image.mode, 0, 1)
                        image.save(new_filepath, "JPEG", quality=95)
                        print(f"Converted: {filename} -> {name}.jpg")

                    except Exception as e:
                        print(f"Error processing {filename}: {e}")

if RUN_RCLONE:
    os.system(RCLONE_COMMAND)
convert_images_to_jpeg(SOURCE_DR, TARGET_DR)
