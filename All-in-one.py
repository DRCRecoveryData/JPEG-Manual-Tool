import os
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import subprocess

class ImageProcessor:
    def __init__(self, output_text_widget=None):
        self.outputText = output_text_widget  # Assuming outputText is a text widget for logging

    # Function to load a file
    def load_file(self, filepath):
        with open(filepath, 'rb') as file:
            return file.read()

    # Function to find the last FF DA + 12 bytes in a reference JPEG file
    def find_ff_da_plus_12(self, data):
        marker = b'\xFF\xDA'
        index = data.rfind(marker)
        if index != -1:
            return data[:index + 12]  # Include FF DA + 12 bytes
        return None

    # Function to process the encrypted JPEG file
    def process_encrypted_jpeg(self, data):
        start_offset = 153605
        end_offset = -334
        return data[start_offset:end_offset]

    # Function to repair the JPEG files
    def repair_jpeg(self, reference_path, encrypted_path, output_folder):
        reference_data = self.load_file(reference_path)
        encrypted_data = self.load_file(encrypted_path)

        # Get the (1) part from the reference JPEG
        ref_part = self.find_ff_da_plus_12(reference_data)

        if ref_part is None:
            if self.outputText is not None:
                self.outputText.append(f"Could not find FF DA marker in {reference_path}")
            return

        # Get the (2) part from the encrypted JPEG
        encrypted_part = self.process_encrypted_jpeg(encrypted_data)

        # Merge (1) and (2)
        merged_data = ref_part + encrypted_part

        # Prepare the output file name and save it to the Repaired folder
        os.makedirs(output_folder, exist_ok=True)
        output_filename = os.path.join(output_folder, os.path.basename(encrypted_path).split('.')[0] + '.JPG')
        with open(output_filename, 'wb') as output_file:
            output_file.write(merged_data)

        if self.outputText is not None:
            self.outputText.append(f"Repaired file saved as {output_filename}")

    def shift_mcu(self, jpg_file):
        if not os.path.isfile(jpg_file) or not jpg_file.lower().endswith((".jpg", ".jpeg")):
            if self.outputText is not None:
                self.outputText.append(f"Invalid file path: {jpg_file}. Please provide a valid JPEG file.")
            return

        try:
            img = Image.open(jpg_file)
            data = np.array(img, dtype=np.uint8)
        except Exception as e:
            if self.outputText is not None:
                self.outputText.append(f"Error opening image {jpg_file}: {str(e)}")
            return

        # Crop the height to remove bottom non-MCU corrupted blocks
        height_cropped = self.crop_non_mcu_blocks(data)

        # Re-calculate the data shape after cropping
        data_cropped = data[:height_cropped, :, :]

        # Detect the number of good MCU blocks after cropping
        num_good_mcu = self.auto_detect_shift(data_cropped)
        if num_good_mcu == 0:
            if self.outputText is not None:
                self.outputText.append(f"No MCU shift needed for {jpg_file}.")
            return

        # Calculate the adjusted MCU value for jpegrepair
        insert_value = max(num_good_mcu - 22, 0)  # Ensure the value does not go below 0
        if self.outputText is not None:
            self.outputText.append(f"Detected MCU value for {jpg_file}: {num_good_mcu}, using adjusted value: {insert_value}")

        # Create the Repaired folder in the same directory as the JPEG file
        repaired_folder = os.path.join(os.path.dirname(jpg_file), "Repaired")
        os.makedirs(repaired_folder, exist_ok=True)  # Create the Repaired folder if it does not exist

        # Save the cropped image to the Repaired folder with the same name
        cropped_image_path = os.path.join(repaired_folder, os.path.basename(jpg_file))
        output_img = Image.fromarray(data_cropped)
        output_img.save(cropped_image_path, "JPEG")
        if self.outputText is not None:
            self.outputText.append(f"Cropped image saved to: {cropped_image_path}")

        # Call jpegrepair.exe with the detected adjusted insert value
        output_repaired_path = os.path.join(repaired_folder, os.path.basename(jpg_file).rsplit('.', 1)[0] + "_repaired.JPG")
        command = f"jpegrepair.exe \"{cropped_image_path}\" \"{output_repaired_path}\" insert {insert_value}"
        if self.outputText is not None:
            self.outputText.append(f"Running command: {command}")

        # Run the command
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.stdout:
                self.outputText.append(result.stdout)
            if result.stderr:
                self.outputText.append("Error: " + result.stderr)
        except Exception as e:
            if self.outputText is not None:
                self.outputText.append(f"An error occurred while running jpegrepair: {str(e)}")

        if self.outputText is not None:
            self.outputText.append(f"Processed image saved to: {output_repaired_path}")

    def crop_non_mcu_blocks(self, data):
        block_size = 8
        height, width, _ = data.shape

        # Start from the bottom and crop any non-MCU blocks
        while height >= block_size:
            if not np.array_equal(data[height - block_size:height, :, :], np.ones((block_size, width, 3), dtype=np.uint8) * 128):
                break
            height -= block_size

        return height

    def auto_detect_shift(self, data):
        block_size = 8
        height, width, _ = data.shape

        # Analyze the last scanline (last block row)
        last_scanline_start = height - block_size
        if last_scanline_start < 0:
            return 0  # Not enough data to process

        last_scanline = data[last_scanline_start:height, :, :]

        num_mcus = 0
        for j in range(0, width, block_size):
            if j + block_size <= width:  # Ensure we don't go out of bounds
                mcu = last_scanline[:, j:j + block_size, :]
                gray_mcu = np.ones((block_size, block_size, 3), dtype=np.uint8) * 128

                diff = np.abs(mcu.astype(int) - gray_mcu.astype(int))
                avg_diff = np.mean(diff)

                # Adjust threshold to allow for some variability in the image
                if avg_diff < 20:  # Increased threshold to 20 for potential slight color variations
                    num_mcus += 1

        return num_mcus

    def auto_color_images(self, repaired_folder):
        # List all JPG and JPEG files in the Repaired folder
        jpg_files = [f for f in os.listdir(repaired_folder) if f.lower().endswith((".jpg", ".jpeg"))]

        if not jpg_files:
            if self.outputText is not None:
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

                    # Save the processed image back in the Repaired folder with original quality
                    original_quality = 95  # Default quality, adjust if needed
                    im.save(image_path, quality=original_quality)
                    log_messages.append(f"Auto color applied to {jpg_file} and saved with quality {original_quality}.")
            except Exception as e:
                log_messages.append(f"Error processing image {jpg_file}: {str(e)}")

        # Append all log messages at once
        if self.outputText is not None:
            self.outputText.append("\n".join(log_messages))
            self.outputText.append("Auto Color process complete.")

    def process_folder(self, folder_path, reference_jpeg):
        output_folder = os.path.join(folder_path, "Repaired")
        os.makedirs(output_folder, exist_ok=True)

        # Process each encrypted JPEG file in the specified folder
        for filename in os.listdir(folder_path):
            if filename.lower().endswith((".jpg", ".jpeg")):
                encrypted_jpeg_path = os.path.join(folder_path, filename)
                self.repair_jpeg(reference_jpeg, encrypted_jpeg_path, output_folder)

        # After repairing, shift MCU and apply color adjustments
        for repaired_file in os.listdir(output_folder):
            if repaired_file.lower().endswith((".jpg", ".jpeg")):
                repaired_file_path = os.path.join(output_folder, repaired_file)
                self.shift_mcu(repaired_file_path)

        # After shifting, apply color adjustments
        self.auto_color_images(output_folder)

if __name__ == "__main__":
    reference_image_path = input("Please enter the reference JPEG file path: ").strip()
    folder_to_process = input("Please enter the encrypted folder path to process images: ").strip()
    
    processor = ImageProcessor()
    processor.process_folder(folder_to_process, reference_image_path)
