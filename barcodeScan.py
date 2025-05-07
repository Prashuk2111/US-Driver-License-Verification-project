import os
import requests
import json
import base64

# API secret for internal reference (not used directly in the header)
API_SECRET = "a9e3371f-7872-4ff6-a2aa-b05263f52841"

# The IDBarcode endpoint URL and Authorization header
API_URL = "https://api.microblink.com/v1/recognizers/id-barcode"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "Bearer MTFlZGRmMDQ3MDdhNDZlN2FiYmQ4NTYxN2U2ZDgxYmM6YTllMzM3MWYtNzg3Mi00ZmY2LWEyYWEtYjA1MjYzZjUyODQx"
}

def encode_image_to_base64(image_path):
    """Reads an image file and encodes it to a Base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def scan_barcode(image_path):
    """Sends the image to the Microblink IDBarcode endpoint and returns the JSON response."""
    image_base64 = encode_image_to_base64(image_path)
    payload = {
        "imageSource": image_base64,
        "inputString": "",
        "ageLimit": 0
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code != 200:
        print(f"Error processing {image_path}: {response.status_code} {response.text}")
        return None
    return response.json()

def save_json(data, output_folder, fallback_name):
    """Saves the JSON response to a file named using firstName and lastName (if available), otherwise fallback_name."""
    result = data.get("result", {})
    first_name = result.get("firstName")
    last_name = result.get("lastName")
    if first_name and last_name:
        filename = f"{first_name}_{last_name}.json"
    else:
        filename = f"{fallback_name}.json"
    output_path = os.path.join(output_folder, filename)
    with open(output_path, "w") as outfile:
        json.dump(data, outfile, indent=4)
    print(f"Saved {output_path}")

def main():
    input_folder = "input_barcode"    # Folder with input images
    output_folder = "output_barcode"  # Folder for JSON outputs
    os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(input_folder, filename)
            print(f"Processing {image_path}...")
            data = scan_barcode(image_path)
            if data:
                base_name = os.path.splitext(filename)[0]
                save_json(data, output_folder, base_name)

if __name__ == "__main__":
    main()