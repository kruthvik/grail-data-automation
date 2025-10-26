from PIL import Image
import os
import json
import re
import fitz  # PyMuPDF
from ollama import Client
import pytesseract
import io
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from fetchPDF import removeItems

# ---------------- Fields ----------------
FIELDS = [
    "Organization Name",
    "Date Submitted",
    "Submitter Name",
    "Organization Type",
    "Contact Information",
    "COMMENT-ID",
    "Filename",
    "Brief Summary of Comment",
    "Relevant Issues Addressed"
]

# ---------------- Google Sheets setup ----------------
link = "https://docs.google.com/spreadsheets/d/1n7l_velbqHHLpHI_V0NYwU8m7KeDGIShvdbxJ4sX5Co/edit?gid=0#gid=0"

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])
client = gs.authorize(creds)
spreadsheet = client.open_by_url(link)

# ---------------- Ollama Cloud Client (Qwen-3) ----------------
# Make sure your token has access to the cloud model.
# You can set it as an environment variable instead of hardcoding it for security.
ollama = Client(
    host="https://ollama.com",  # ✅ Correct endpoint for Ollama Cloud
    headers={
        "Authorization": "Bearer 118347b4d2404a13ad59ea034ea6c88e.y3rHTTlshlZgTcmr8Riqh5Sb",
        "Content-Type": "application/json"
    }
)
OLLAMA_MODEL = "qwen3-coder:480b-cloud"  # ✅ Cloud model to use

# ---------------- Helper: Append a row to sheet ----------------
def add_sheet_row(sheetNum, rowData):
    sheet = spreadsheet.get_worksheet(sheetNum - 1)
    if sheet is None:
        print(f"❌ No worksheet found at index {sheetNum - 1}")
        return
    rowData = [str(x).strip() if x else "N/A" for x in rowData]
    sheet.append_row(rowData, value_input_option='USER_ENTERED')
    print("✅ Row added successfully.")

# ---------------- PDF text extraction ----------------
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
            else:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text + "\n"
        doc.close()
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
    return text.strip()

# ---------------- Ollama extraction ----------------
def extract_fields_ollama_list(text: str, metadata: dict, log_prefix="", pdf_path="") -> list[str] | None:
    os.makedirs("./logs", exist_ok=True)

    def log_output(name, content):
        with open(f"./logs/{log_prefix}_{name}.txt", "w", encoding="utf-8") as f:
            f.write(content)

    def formatData(data):
        res = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(res)

    def query_ollama(field_subset: list[str], context_text: str, tag="full") -> list[str] | None:
        prompt = f"""
            You are an AI data extraction assistant.

            Extract ONLY the following fields (in order) from the text and metadata below.
            Return in this format: [Field]: [Value]
            No extra explanations or markdown.

            Do NOT use quotes around values.
            Do NOT return empty or null; use 'N/A' if unknown.
            Do NOT change the order of fields.

            Fields to extract:
            {json.dumps(field_subset)}

            Metadata:
            {json.dumps(metadata)}

            Comment text:
            {context_text[:5000]}
        """

        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_output = response["message"]["content"].strip()

            logStr = raw_output + "\n" + formatData(metadata)
            log_output(tag, logStr)

            pattern = r"^[^:]+:\s*(.*)$"
            arr = [re.match(pattern, line).group(1) for line in raw_output.splitlines() if re.match(pattern, line)]
            arr = [v for v in arr if len(v.strip()) > 0]

            arr = [str(x).strip().replace("\n", " ") or "N/A" for x in arr]
            arr[1] = metadata.get("date", "N/A")
            arr[2] = metadata.get("commenter", "N/A")
            arr[5] = metadata.get("comment_id", "N/A")
            arr[6] = os.path.basename(pdf_path)

            return arr
        except Exception as e:
            print(f"❌ Extraction failed for {tag}: {e}")
            return None

    result = query_ollama(FIELDS, text, tag="full")
    if result and len(result) == len(FIELDS):
        return result

    return result or []

# ---------------- Main analysis ----------------
def analyze_comment_file(pdf_file: str, metadata: dict, key: str = "") -> list[str] | None:
    text = extract_text_from_pdf(pdf_file)
    if not text:
        print(f"Skipping {pdf_file} (empty or unreadable)")
        return None
    prefix = os.path.splitext(os.path.basename(pdf_file))[0]
    return extract_fields_ollama_list(text, metadata, log_prefix=prefix, pdf_path=pdf_file)

# ---------------- Run pipeline ----------------
if __name__ == "__main__":
    print("🚀 Starting comment analysis...")
    sheetNum = input("Enter sheet num: ")
    
    metadata_all = json.load(open("metadata.json"))
    comments_folder = "./comments"

    removeItems("logs/", removeMetadata=False)

    for pdf_file in os.listdir(comments_folder):
        if not pdf_file.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(comments_folder, pdf_file)
        key = re.sub(r"\.pdf$", "", pdf_file, flags=re.IGNORECASE)
        metadata = metadata_all.get(key, {})

        print(f"\n📄 Processing {pdf_file}...")
        result_list = analyze_comment_file(pdf_path, metadata, key)

        if result_list:
            print(f"✅ Extracted {len(result_list)} fields for {pdf_file}")
            print(result_list)
            add_sheet_row(int(sheetNum), result_list)
        else:
            print(f"⚠️ Skipped {pdf_file} due to extraction failure.")

    print("\n🎯 All done!")
