import os

image_folder = 'images/'  # Replace with the actual path to your image folder
output_js_file = 'filenames.js'

# Initialize an empty list to store file paths
image_files = []

# Recursively walk through the image folder and its subfolders
for root, dirs, files in os.walk(image_folder):
    for file in files:
        if not file.startswith('.'):  # Ignore hidden files
            file_path = os.path.join(root, file)
            image_files.append(file_path)

# Create a JavaScript array containing the file paths
js_array = "const imageFilePaths = " + str(image_files)

# Write the JavaScript array to a .js file
with open(output_js_file, 'w') as js_file:
    js_file.write(js_array)

print(f"File paths saved to {output_js_file}")