
# 🪪 US Driver License Verification System

This project is designed to verify US driver licenses by:
1. Extracting barcode data from the back of the license.
2. Extracting front data (name, DOB, photo, etc.) from the front.
3. Comparing both sides to authenticate the license.
4. Comparing the license photo with a selfie to ensure facial match.

---

## 📂 Folder Structure

- `input_barcode/` – back images of licenses (for barcode scan)
- `input_face/` – front images of licenses
- `selfie_img/` – driver's selfies for face verification
- `output_barcode/` – stores barcode scan results as JSON
- `output_face_json/` – stores front image data as JSON
- `output_face_img/` – cropped face images from license front
- `output_comparison/` – comparison JSONs and Excel reports

---

## 🔁 Workflow

### 1. `barcodeScan.py`
- Scans barcodes from back images in `input_barcode/`
- Saves parsed data as JSON in `output_barcode/`

### 2. `image_extraction.py`
- Extracts data from front license images in `input_face/`
- Saves data as JSON in `output_face_json/`
- Saves cropped face images in `output_face_img/`

### 3. `license_auth.py`
- Compares front and back data from `output_face_json/` and `output_barcode/`
- Outputs result JSONs and a summary Excel report (`comparison_report.xlsx`) in `output_comparison/`

### 4. `face_comparison.py`
- Compares selfies in `selfie_img/` with faces from `output_face_img/`
- Outputs `face_comparison_report.xlsx` in `output_comparison/`

---

## 📊 Output Summary

All final reports and comparison data are saved in the `output_comparison/` folder:
- `comparison_report.xlsx`: Validates license data
- `face_comparison_report.xlsx`: Validates facial match

---

## 🚀 Run Order

```bash
python barcodeScan.py
python image_extraction.py
python license_auth.py
python face_comparison.py
