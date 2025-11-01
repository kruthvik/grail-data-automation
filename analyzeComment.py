<<<<<<< HEAD
from analyzeComments import extract_fields_ollama_list, analyze_comment_file
from fetchPDF import removeItems
import json
import os
import re


if __name__ == "__main__":
    print("🚀 Starting comment analysis...")
    pdf_file = input("Enter file name: ")
    
    metadata_all = json.load(open("metadata.json"))
    comments_folder = "./comments"

    pdf_path = os.path.join(comments_folder, pdf_file)
    key = re.sub(r"\.pdf$", "", pdf_file, flags=re.IGNORECASE)
    metadata = metadata_all.get(key, {})

    print(f"\n📄 Processing {pdf_file}...")
    result_list = analyze_comment_file(pdf_path, metadata, key)

    if result_list:
        print(f"✅ Extracted {len(result_list)} fields for {pdf_file}")
        print(result_list)
    else:
=======
from analyzeComments import extract_fields_ollama_list, analyze_comment_file
from fetchPDF import removeItems
import json
import os
import re


if __name__ == "__main__":
    print("🚀 Starting comment analysis...")
    pdf_file = input("Enter file name: ")
    
    metadata_all = json.load(open("metadata.json"))
    comments_folder = "./comments"

    pdf_path = os.path.join(comments_folder, pdf_file)
    key = re.sub(r"\.pdf$", "", pdf_file, flags=re.IGNORECASE)
    metadata = metadata_all.get(key, {})

    print(f"\n📄 Processing {pdf_file}...")
    result_list = analyze_comment_file(pdf_path, metadata, key)

    if result_list:
        print(f"✅ Extracted {len(result_list)} fields for {pdf_file}")
        print(result_list)
    else:
>>>>>>> 3b29589 (updated)
        print(f"⚠️ Skipped {pdf_file} due to extraction failure.")