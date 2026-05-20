import zipfile
import os


def unzip_file(zip_path, extract_to):
        
    print(f"Unzipping {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        
    print("Unzipping completed successfully!")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    unzip_file("data.zip", ".")
