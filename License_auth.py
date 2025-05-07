import os
import json
import re
from difflib import SequenceMatcher
import pandas as pd

# ---------------------------
# Folder paths
# ---------------------------
BARCODE_FOLDER      = "output_barcode"         # barcode/back‐scan JSONs
FRONT_FOLDER        = "output_face_json"       # front‐scan JSONs
OUTPUT_JSON_FOLDER  = "output_comparison"      # where we dump detailed JSON + Excel
OUTPUT_EXCEL_FILE   = os.path.join(OUTPUT_JSON_FOLDER, "comparison_report.xlsx")

os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)

# ---------------------------
# Helpers
# ---------------------------
def load_json(path):
    with open(path,'r') as f:
        return json.load(f)

def normalize_date_string(s):
    return re.sub(r'\D','', s)

def normalize_address(addr):
    if not isinstance(addr,str): return addr
    cleaned = " ".join(addr.replace("\n"," ").split()).lower()
    # truncate ZIP to 5 digits
    return re.sub(r"(\d{5})\d+", r"\1", cleaned)

def compare_date(f, b):
    details = {}
    if isinstance(f,dict):
        fc = (f.get("day"),f.get("month"),f.get("year"))
    else:
        fc = None
    if isinstance(b,dict):
        bc = (b.get("day"),b.get("month"),b.get("year"))
    else:
        bc = None
    details["front_components"] = fc
    details["back_components"]  = bc
    details["components_match"] = (fc==bc)

    fo = f.get("originalString","") if isinstance(f,dict) else str(f)
    bo = b.get("originalString","") if isinstance(b,dict) else str(b)
    fn = normalize_date_string(fo)
    bn = normalize_date_string(bo)
    details["normalized_front"] = fn
    details["normalized_back"]  = bn
    details["original_match"]   = (fn==bn)

    return (details["components_match"] and details["original_match"], details)

def compare_str(f, b, fuzzy=False, threshold=0.75):
    fs = str(f or "").strip().lower()
    bs = str(b or "").strip().lower()
    if fuzzy:
        ratio = SequenceMatcher(None, fs, bs).ratio()
        return (ratio>=threshold, fs, bs, ratio)
    return (fs==bs, fs, bs, None)

def compare_field(front, back, field):
    r = {"field":field}
    if field=="firstName":
        fv = front.get("firstName","").strip().lower()
        bf = back.get("firstName","").strip().lower()
        bm = back.get("middleName","").strip().lower()
        combo = bf + (" "+bm if bm and bm!="none" else "")
        r["front"],r["back"] = fv, combo
        r["match"] = (fv==combo or fv.startswith(bf))
        r["details"] = {"back_first":bf,"back_middle":bm,"combined_back":combo}

    elif field in ("dateOfBirth","dateOfExpiry"):
        fv = front.get(field,{})
        bv = back.get(field,{})
        m,d = compare_date(fv,bv)
        r["front"]   = fv.get("originalString","")
        r["back"]    = bv.get("originalString","")
        r["match"]   = m
        r["details"] = d

    elif field=="address":
        fa = normalize_address(front.get("address",""))
        ba = normalize_address(back.get("address",""))
        m,fn,bn,ratio = compare_str(fa,ba,fuzzy=True,threshold=0.75)
        r["front"],r["back"],r["match"] = fn, bn, m
        r["details"] = {"fuzzyRatio":ratio}

    elif field=="age":
        try:
            fv = int(front.get("age",0))
            bv = int(back.get("age",0))
        except:
            fv = front.get("age"); bv = back.get("age")
        r["front"],r["back"],r["match"] = fv, bv, (fv==bv)

    else:
        m,fn,bn,_ = compare_str(front.get(field,""), back.get(field,""), fuzzy=False)
        r["front"],r["back"],r["match"] = fn, bn, m

    return r

def compare_all(front, back, fields):
    overall = True
    details = {}
    for fld in fields:
        comp = compare_field(front, back, fld)
        details[fld] = comp
        if not comp["match"]:
            overall = False
    return overall, details

# ---------------------------
# Main
# ---------------------------
def main():
    barcode_js = {f for f in os.listdir(BARCODE_FOLDER) if f.endswith(".json")}
    front_js   = {f for f in os.listdir(FRONT_FOLDER)   if f.endswith(".json")}
    common     = barcode_js & front_js

    unpaired = []
    for f in barcode_js-common:
        unpaired.append({"Folder":BARCODE_FOLDER, "File Name":f})
    for f in front_js-common:
        unpaired.append({"Folder":FRONT_FOLDER, "File Name":f})

    summary     = []
    details_map = {}
    # no 'restrictions' in here:
    fields = ["firstName","lastName","documentNumber","address","dateOfBirth","dateOfExpiry","age"]

    for fn in sorted(common):
        bd = load_json(os.path.join(BARCODE_FOLDER,fn)).get("result",{})
        fd = load_json(os.path.join(FRONT_FOLDER,fn)).get("result",{})
        ok, det = compare_all(fd, bd, fields)

        details_map[fn] = {
            "authentic": ok,
            "comparison": det,
            "checkedFields": fields,
            "frontScanTimestamp": load_json(os.path.join(FRONT_FOLDER,fn)).get("finishTime",""),
            "backScanTimestamp":  load_json(os.path.join(BARCODE_FOLDER,fn)).get("finishTime","")
        }

        # still pull restrictions into summary:
        front_res = fd.get("restrictions","") or fd.get("driverLicenseDetailedInfo",{}).get("restrictions","")
        back_res  = bd.get("restrictions","")
        summary.append({
            "First Name":         fd.get("firstName",""),
            "Last Name":          fd.get("lastName",""),
            "Document Number":    fd.get("documentNumber",""),
            "Restrictions Front": front_res,
            "Restrictions Back":  back_res,
            "Authentic":          ok,
            "File Name":          fn
        })

        # dump per‐file detailed JSON
        with open(os.path.join(OUTPUT_JSON_FOLDER, fn),"w") as outf:
            json.dump(details_map[fn], outf, indent=4)

    # write Excel
    writer = pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine="openpyxl")
    df = pd.DataFrame(summary)
    cols = ["First Name","Last Name","Document Number",
            "Restrictions Front","Restrictions Back","Authentic","File Name"]
    df[cols].to_excel(writer, sheet_name="Comparison", index=False)
    pd.DataFrame(unpaired).to_excel(writer, sheet_name="Unpaired", index=False)
    writer.close()

    print(f"Saved JSONs + Excel to {OUTPUT_JSON_FOLDER}")

if __name__=="__main__":
    main()