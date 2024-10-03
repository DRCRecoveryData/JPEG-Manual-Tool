import os
import numpy as np
from PIL import Image
import subprocess

def shift_mcu(jpg_file):
    if not os.path.isfile(jpg_file) or not jpg_file.lower().endswith((".jpg", ".jpeg")):
        print("Invalid file path. Please provide a valid JPEG file.")
        return

    try:
        img = Image.open(jpg_file)
        data = np.array(img, dtype=np.uint8)
    except Exception as e:
        print(f"Error opening image {jpg_file}: {str(e)}")
        return

    # Crop the height to remove bottom non-MCU corrupted blocks
    height_cropped = crop_non_mcu_blocks(data)

    # Re-calculate the data shape after cropping
    data_cropped = data[:height_cropped, :, :]

    # Detect the number of good MCU blocks after cropping
    num_good_mcu = auto_detect_shift(data_cropped)
    if num_good_mcu == 0:
        print(f"No MCU shift needed for {jpg_file}.")
        return

    # Calculate the adjusted MCU value for jpegrepair
    insert_value = max(num_good_mcu - 22, 0)  # Ensure the value does not go below 0
    print(f"Detected MCU value for {jpg_file}: {num_good_mcu}, using adjusted value: {insert_value}")

    # Create the Repaired folder in the same directory as the JPEG file
    repaired_folder = os.path.join(os.path.dirname(jpg_file), "Repaired")
    os.makedirs(repaired_folder, exist_ok=True)  # Create the Repaired folder if it does not exist

    # Save the cropped image to the Repaired folder with the same name
    cropped_image_path = os.path.join(repaired_folder, os.path.basename(jpg_file))
    output_img = Image.fromarray(data_cropped)
    output_img.save(cropped_image_path, "JPEG")
    print(f"Cropped image saved to: {cropped_image_path}")

    # Call jpegrepair.exe with the detected adjusted insert value
    output_repaired_path = os.path.join(repaired_folder, os.path.basename(jpg_file))
    command = f"jpegrepair.exe \"{cropped_image_path}\" \"{output_repaired_path}\" insert {insert_value}"
    print(f"Running command: {command}")

    # Run the command
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except Exception as e:
        print(f"An error occurred while running jpegrepair: {str(e)}")

    print(f"Processed image saved to: {output_repaired_path}")

def crop_non_mcu_blocks(data):
    block_size = 8
    height, width, _ = data.shape

    # Start from the bottom and crop any non-MCU blocks
    while height >= block_size:
        if not np.array_equal(data[height - block_size:height, :, :], np.ones((block_size, width, 3), dtype=np.uint8) * 128):
            break
        height -= block_size

    return height

def auto_detect_shift(data):
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

def process_folder(folder_path):
    if not os.path.isdir(folder_path):
        print("Invalid folder path. Please provide a valid directory.")
        return

    # Process all JPEG files in the specified folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg")):
            full_path = os.path.join(folder_path, filename)
            print(f"Processing file: {full_path}")
            shift_mcu(full_path)

if __name__ == "__main__":
    folder_path = input("Please enter the encrypted folder path to process JPEG files: ").strip()
    process_folder(folder_path)
