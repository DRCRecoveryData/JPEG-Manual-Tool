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

    for jpg_file in jpg_files:
        image_path = os.path.join(repaired_folder, jpg_file)
        try:
            # Open image and check if it's a valid image
            with Image.open(image_path) as im:
                # Apply auto contrast
                im = ImageOps.autocontrast(im, cutoff=1)
                
                # Enhance sharpness
                sharpness_enhancer = ImageEnhance.Sharpness(im)
                im = sharpness_enhancer.enhance(3)

                # Posterize the image
                im = ImageOps.posterize(im, bits=8)

                # Enhance color
                color_enhancer = ImageEnhance.Color(im)
                im = color_enhancer.enhance(3)

                # Save the processed image back
                im.save(image_path, quality="maximum")
                self.outputText.append(f"Auto color applied to {jpg_file} and saved.")
        except Exception as e:
            self.outputText.append(f"Error processing image {jpg_file}: {str(e)}")

    self.outputText.append("Auto Color process complete.")
