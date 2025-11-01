# import fitz  # PyMuPDF
# from PIL import Image
# import pytesseract
# import io

# def extract_text_from_pdf(pdf_path: str) -> str:
#     """Extract text from PDF. Falls back to OCR if page has no text."""
#     text = ""
#     try:
#         doc = fitz.open(pdf_path)
#         for page in doc:
#             page_text = page.get_text("text")
#             if page_text.strip():
#                 text += page_text + "\n"
#             else:
#                 # Render page to image for OCR
#                 pix = page.get_pixmap(dpi=300)
#                 img = Image.open(io.BytesIO(pix.tobytes("png")))
#                 ocr_text = pytesseract.image_to_string(img)
#                 text += ocr_text + "\n"
#         doc.close()
#     except Exception as e:
#         print(f"Error extracting {pdf_path}: {e}")
#     return text.strip()

# # Example usage:
# pdf_file = './comments/CFPB_BarrettBurns_20210622.pdf'
# text = extract_text_from_pdf(pdf_file)
# print(text[:1000])  # print first 1000 chars




def formatData(data):
    res = [f"{k}: {v}" for k, v in data.items()]
    return "\n".join(res)

print(formatData({"Name": "John Doe", "Date": "2024-06-15", "Agency": "EPA"}))