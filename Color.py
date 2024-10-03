import os
from PIL import Image, ImageOps, ImageEnhance

def autoColorImages(self):
    repaired_folder = os.path.join(self.encrypted_folder_input.text().strip(), "Repaired")

    if not os.path.exists(repaired_folder):
        self.outputText.append("Repaired folder not found.")
        return

    jpg_files = [f for f in os.listdir(repaired_folder) if f.lower().endswith(".jpg")]

    if not jpg_files:
        self.outputText.append("No JPG files found in the Repaired folder.")
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

                # Save the processed image back using the same quality as the original
                original_quality = 95  # Default quality, adjust if needed

                # Check if the original file can be opened as a binary and read its quality if available
                with open(image_path, 'rb') as file:
                    # Attempt to read the original quality using Pillow's `info` dictionary
                    im_info = Image.open(file).info
                    original_quality = im_info.get('quality', original_quality)  # Use 95 as a fallback

                # Save the processed image with the original quality
                im.save(image_path, quality=original_quality)
                log_messages.append(f"Auto color applied to {jpg_file} and saved with original quality.")
        except Exception as e:
            log_messages.append(f"Error processing image {jpg_file}: {str(e)}")

    # Append all log messages at once
    self.outputText.append("\n".join(log_messages))
    self.outputText.append("Auto Color process complete.")
