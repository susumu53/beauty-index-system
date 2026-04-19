import zipfile
import os

zip_name = "beauty-index-generator-updated.zip"
files_to_zip = ["beauty-index-generator.php"]

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in files_to_zip:
        if os.path.exists(file):
            zipf.write(file)
            print(f"Added {file} to {zip_name}")
        else:
            print(f"File {file} not found.")

print(f"Created {zip_name} successfully.")
