import os
import requests
import pandas as pd

# ────── CONFIG ──────
API_URL    = "https://api-us.faceplusplus.com/facepp/v3/compare"
API_KEY    = "D-v7zzp5gbopznMuyddhyTWfLB9lb8RA"
API_SECRET = "BxvkDrjMhThRjNzGiuqWocaUAJJNFVqm"

LICENSE_FOLDER = "output_face_img"
SELFIE_FOLDER  = "selfie_img"
OUTPUT_FILE    = "output_comparison/face_comparison_report.xlsx"

# ────── FACE++ CALL ──────
def compare_faces(path1, path2):
    r = requests.post(
        API_URL,
        data={"api_key": API_KEY, "api_secret": API_SECRET},
        files={
            "image_file1": open(path1, "rb"),
            "image_file2": open(path2, "rb"),
        }
    )
    r.raise_for_status()
    return r.json()

# ────── MAIN ──────
def main():
    lic_files   = [f for f in os.listdir(LICENSE_FOLDER)
                   if f.lower().endswith((".jpg",".jpeg",".png"))]
    summary     = []
    unpaired    = []

    for fn in sorted(lic_files):
        lic_path    = os.path.join(LICENSE_FOLDER, fn)
        selfie_path = os.path.join(SELFIE_FOLDER, fn)

        if not os.path.isfile(selfie_path):
            unpaired.append({"File Name": fn})
            continue

        try:
            data = compare_faces(lic_path, selfie_path)
            conf = data.get("confidence", 0)
            thr  = data.get("thresholds", {}).get("1e-5", 0)
            match = conf >= thr
            summary.append({
                "File Name": fn,
                "Match":     match,
                "Confidence": round(conf,2),
                "Threshold":  round(thr,2),
            })
        except Exception as e:
            # treat as unpaired/error
            unpaired.append({"File Name": fn})
            print(f"Error comparing {fn}: {e}")

    # write to Excel
    df_sum = pd.DataFrame(summary)
    df_unp = pd.DataFrame(unpaired)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_sum.to_excel(writer, sheet_name="Comparison", index=False)
        df_unp.to_excel(writer, sheet_name="Unpaired",  index=False)

    print(f"\n✅ Done. Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()