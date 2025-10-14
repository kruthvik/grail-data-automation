from docx import Document
from docx2pdf import convert
from random import randint
import requests as req
from bs4 import BeautifulSoup as bs
import random 
import re
import os
import glob

import os
import glob

def removeComments():
    files = glob.glob(os.path.join("comments/", "*"))
    for f in files:
        if os.path.isfile(f):
            try:
                os.remove(f)
                print(f"Deleted: {f}")
            except Exception as e:
                print(f"Failed to delete {f}: {e}")


def get_agency_prefix(notice_shortname, agency_full):
    """
    Determines the prefix for the filename.
    Uses notice_shortname if it starts with uppercase letters, otherwise uses mapping from agency name.
    """
    # Check if notice_shortname already starts with uppercase letters (e.g., DOE-HQ-2024-0007)
    if re.match(r"^[A-Z]{2,}", notice_shortname):
        parts = notice_shortname.split("-")
        parts[0] = parts[0].upper()
        return "-".join(parts)
    else:
        # Fallback: use mapping
        prefix = AGENCY_ABBR.get(agency_full, agency_full[:3].upper())
        return f"{prefix}-{notice_shortname}"

def make_filename(notice_shortname, commenter, posted_date, agency_full):
    # Get the proper prefix
    short = get_agency_prefix(notice_shortname, agency_full)

    # Clean commenter
    commenter_clean = re.sub(r"[^\w]", "", commenter)

    # Parse date to YYYYMMDD
    try:
        dt = datetime.strptime(posted_date, "%b %d, %Y")
        date_str = dt.strftime("%Y%m%d")
    except Exception:
        try:
            dt = datetime.fromisoformat(posted_date)
            date_str = dt.strftime("%Y%m%d")
        except Exception:
            date_str = "unknownDate"

    return f"{short}_{commenter_clean}-{date_str}"

# def fetchContent():
#     url = "https://www.regulations.gov/comment/DOT-OST-2024-0049-0018"
#     r = req.get(url)
#     soup = bs(r, "html.parser")

def createPDF(info, date, commenter, agency, doc_id):
    filename_base = make_filename(doc_id, commenter, date, agency)

    doc = Document()

    # Add a title
    doc.add_heading(f"Comment from {commenter}", level=0)

    # Add a paragraph
    doc.add_paragraph(f"Date: {date}\nAgency: {agency}\nID: {doc_id}")

    doc.add_paragraph(info)

    num = random.randint(1000, 9999)

    # Save the document
    doc.save(f"./comments/{filename_base}.docx")

    print(f"DOCX file saved as {filename_base}.docx")

    convert(f"./comments/{filename_base}.docx", f"./comments/{filename_base}.pdf")
    os.remove(f"./comments/{filename_base}.docx")

def downloadPDF(url, date, commenter, agency, doc_id):
    r = req.get(url)
    with open(f"./comments/{make_filename(doc_id, commenter, date, agency)}.pdf", "wb") as f:
        f.write(r.content)
    
    print(f"PDF file saved as {make_filename(doc_id, commenter, date, agency)}.pdf")
