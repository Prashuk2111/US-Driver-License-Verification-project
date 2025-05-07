import os
import requests
import json
import base64

# API credentials and endpoint.
API_SECRET = "a9e3371f-7872-4ff6-a2aa-b05263f52841"  # For internal reference only.
AUTH_TOKEN = "Bearer MTFlZGRmMDQ3MDdhNDZlN2FiYmQ4NTYxN2U2ZDgxYmM6YTllMzM3MWYtNzg3Mi00ZmY2LWEyYWEtYjA1MjYzZjUyODQx"
API_URL = "https://api.microblink.com/v1/recognizers/blinkid"

# Folders for input and outputs.
INPUT_FOLDER = "input_face"
OUTPUT_JSON_FOLDER = "output_face_json"
OUTPUT_IMAGE_FOLDER = "output_face_img"

def encode_image(image_path):
    """Reads an image file and returns its Base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def call_api(img_b64):
    """
    Calls the BlinkID API with the given image (in Base64).
    Uses returnFaceImage to retrieve the face image.
    Returns the JSON response.
    """
    payload = {
        "returnFullDocumentImage": False,
        "returnFaceImage": True,
        "returnSignatureImage": False,
        "allowBlurFilter": False,
        "allowUnparsedMrzResults": False,
        "allowUnverifiedMrzResults": True,
        "validateResultCharacters": True,
        "anonymizationMode": "FULL_RESULT",
        "anonymizeImage": True,
        "ageLimit": 0,
        "imageSource": img_b64,
        "scanCroppedDocumentImage": False
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": AUTH_TOKEN
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"API error: {response.status_code} {response.text}")
        return None
    return response.json()

def save_json(data, output_path):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved JSON output to {output_path}")

def save_image(b64_str, output_path):
    try:
        image_data = base64.b64decode(b64_str)
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Saved face image to {output_path}")
    except Exception as e:
        print(f"Error saving image: {e}")

def get_output_filenames(result, fallback_name):
    """
    Returns a tuple (json_filename, image_filename) based on the extracted names.
    If firstName and lastName are missing, fallback_name will be used.
    """
    res = result.get("result", {})
    first_name = res.get("firstName")
    last_name = res.get("lastName")
    if first_name and last_name:
        base_filename = f"{first_name.split()[0]}_{last_name}"
    else:
        base_filename = fallback_name
    return base_filename + ".json", base_filename + ".jpg"

def main():
    # Ensure output directories exist
    os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_IMAGE_FOLDER, exist_ok=True)
    
    # Process each image in the input folder.
    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            input_path = os.path.join(INPUT_FOLDER, filename)
            print(f"\nProcessing {input_path}...")
            
            img_b64 = encode_image(input_path)
            response_data = call_api(img_b64)
            if response_data is None:
                print(f"Failed to process {filename}.")
                continue
            
            # Determine output file names using extracted person details or fallback.
            json_filename, image_filename = get_output_filenames(response_data, os.path.splitext(filename)[0])
            json_output_path = os.path.join(OUTPUT_JSON_FOLDER, json_filename)
            image_output_path = os.path.join(OUTPUT_IMAGE_FOLDER, image_filename)
            
            # Save the JSON response.
            save_json(response_data, json_output_path)
            
            # Extract and save the face image.
            face_b64 = response_data.get("result", {}).get("faceImageBase64")
            if face_b64:
                save_image(face_b64, image_output_path)
            else:
                print("No face image found in the API response.")

if __name__ == "__main__":
    main()