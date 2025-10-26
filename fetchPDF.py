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
import json as js
from datetime import datetime
from findAgency import abbreviateAgency

formatCommenter = lambda commenter: re.sub(r"(?i)^(comment submitted by|comment from)\s*", "", commenter).strip()

def removeItems(folder="comments/", removeMetadata=True):
    files = glob.glob(os.path.join(folder, "*"))
    for f in files:
        if os.path.isfile(f):
            try:
                os.remove(f)
                print(f"Deleted: {f}")
            except Exception as e:
                print(f"Failed to delete {f}: {e}")
    print("All files removed from", folder)
    
    if removeMetadata:
        with open("./metadata.json", "w", encoding="utf-8") as f:
            js.dump({}, f)
            print("Metadata reset.")
        
def loadJSON():
    try:
        with open("./metadata.json", "r", encoding="utf-8") as f:
            data = js.load(f)
            return data
    except FileNotFoundError:
        return {}

def make_filename(notice_shortname, commenter, posted_date, agency_full):
    agency_full = agency_full.lower()
    short = abbreviateAgency(agency_full)

    # Clean commenter
    commenter_clean = re.sub(r"[^\w]", "", formatCommenter(commenter))

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

    return f"{short}_{commenter_clean}_{date_str}"

def createPDF(info, date, commenter, agency, comment_id):
    commenter = formatCommenter(commenter)
    filename_base = make_filename(comment_id, commenter, date, agency)

    doc = Document()

    # Add a title
    doc.add_heading(f"Comment from {commenter}", level=0)

    # Add a paragraph
    doc.add_paragraph(f"Date: {date}\nAgency: {agency}\nID: {comment_id}")

    doc.add_paragraph(info)

    # Save the document
    doc.save(f"./comments/{filename_base}.docx")

    print(f"DOCX file saved as {filename_base}.docx")

    convert(f"./comments/{filename_base}.docx", f"./comments/{filename_base}.pdf")
    
    json = loadJSON()
    json[filename_base] = {
        "date": date,
        "commenter": commenter,
        "agency": agency,
        "comment_id": comment_id
    }
    
    with open(f"./metadata.json", "w", encoding="utf-8") as f:
        js.dump(json, f)
        print("updated")
    
    print(f"PDF file saved as {filename_base}.pdf")
    
    os.remove(f"./comments/{filename_base}.docx")

def downloadPDF(url, date, commenter, agency, comment_id):
    commenter = formatCommenter(commenter)
    
    r = req.get(url)
    fname = make_filename(comment_id, commenter, date, agency)
    
    with open(f"./comments/{fname}.pdf", "wb") as f:
        f.write(r.content)

    json = loadJSON()
    json[fname] = {
        "date": date,
        "commenter": commenter,
        "agency": agency,
        "comment_id": comment_id
    }
    
    with open(f"./metadata.json", "w", encoding="utf-8") as f:
        js.dump(json, f)
        print("updated")

    print(f"PDF file saved as {make_filename(comment_id, commenter, date, agency)}.pdf")
