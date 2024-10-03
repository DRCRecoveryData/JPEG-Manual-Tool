import os

# Function to load a file
def load_file(filepath):
    with open(filepath, 'rb') as file:
        return file.read()

# Function to find the last FF DA + 12 bytes in a reference JPEG file
def find_ff_da_plus_12(data):
    marker = b'\xFF\xDA'
    index = data.rfind(marker)
    if index != -1:
        return data[:index + 12]  # Include FF DA + 12 bytes
    return None

# Function to process the encrypted JPEG file
def process_encrypted_jpeg(data):
    start_offset = 153605
    end_offset = -334
    return data[start_offset:end_offset]

# Main function to repair the JPEG files
def repair_jpeg(reference_path, encrypted_path, output_folder):
    # Load reference JPEG and encrypted JPEG
    reference_data = load_file(reference_path)
    encrypted_data = load_file(encrypted_path)

    # Get the (1) part from the reference JPEG
    ref_part = find_ff_da_plus_12(reference_data)

    if ref_part is None:
        print(f"Could not find FF DA marker in {reference_path}")
        return

    # Get the (2) part from the encrypted JPEG
    encrypted_part = process_encrypted_jpeg(encrypted_data)

    # Merge (1) and (2)
    merged_data = ref_part + encrypted_part

    # Prepare the output file name and save it to the Repaired folder
    os.makedirs(output_folder, exist_ok=True)
    output_filename = os.path.join(output_folder, os.path.basename(encrypted_path).split('.')[0] + '.JPG')
    with open(output_filename, 'wb') as output_file:
        output_file.write(merged_data)

    print(f"Repaired file saved as {output_filename}")

# Prompt user for the folder path containing encrypted JPEG files
folder_path = input("Enter the path to the folder containing encrypted JPEG files: ")
reference_jpeg = input("Enter the path to the reference JPEG file: ")

# Output folder
output_folder = 'Repaired'

# Process each encrypted JPEG file in the specified folder
for filename in os.listdir(folder_path):
    if (filename.lower().startswith(('jpg.', 'jpeg.'))):
        encrypted_jpeg_path = os.path.join(folder_path, filename)
        repair_jpeg(reference_jpeg, encrypted_jpeg_path, output_folder)
