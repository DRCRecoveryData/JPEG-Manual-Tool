import os
from PIL import Image, ImageOps, ImageEnhance

def autoColorImages(self):
    # Prompt the user for the encrypted folder path
    encrypted_folder = input("Please enter the encrypted folder path to process images: ").strip()
    repaired_folder = os.path.join(encrypted_folder, "Repaired")

    if not os.path.exists(repaired_folder):
        self.outputText.append("Repaired folder not found.")
        return

    # List all JPG and JPEG files in the Repaired folder
    jpg_files = [f for f in os.listdir(repaired_folder) if f.lower().endswith((".jpg", ".jpeg"))]

    if not jpg_files:
        self.outputText.append("No JPG or JPEG files found in the Repaired folder.")
        return

    log_messages = []  # List to collect log messages

    for jpg_file in jpg_files:
        image_path = os.path.join(repaired_folder, jpg_file)
        try:
            # Open the original image
            with Image.open(image_path) as im:
                # Apply auto contrast
                im = ImageOps.autocontrast(im, cutoff=1)

                # Enhance sharpness
                sharpness_enhancer = ImageEnhance.Sharpness(im)
                im = sharpness_enhancer.enhance(3)  # Adjustable sharpness factor

                # Posterize the image
                im = ImageOps.posterize(im, bits=8)

                # Enhance color
                color_enhancer = ImageEnhance.Color(im)
                im = color_enhancer.enhance(3)  # Adjustable color enhancement factor

                # Check the original quality for saving
                original_quality = 95  # Default quality, adjust if needed

                # Attempt to read the original quality using Pillow's `info` dictionary
                with open(image_path, 'rb') as file:
                    im_info = Image.open(file).info
                    original_quality = im_info.get('quality', original_quality)  # Use 95 as a fallback

                # Save the processed image back in the Repaired folder with the same name and original quality
                im.save(image_path, quality=original_quality)
                log_messages.append(f"Auto color applied to {jpg_file} and saved with original quality.")
        except Exception as e:
            log_messages.append(f"Error processing image {jpg_file}: {str(e)}")

    # Append all log messages at once
    self.outputText.append("\n".join(log_messages))
    self.outputText.append("Auto Color process complete.")
