import requests as req
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io
from tqdm import tqdm
from findAgency import getAgency
from datetime import datetime as dt

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gs.authorize(creds)

<<<<<<< HEAD
notices = client.open_by_url("INSERT API ").sheet1
=======
notices = client.open_by_url("https://docs.google.com/spreadsheets/d/1G1YjFpOYcAnBcHTZq5ySl956VeT6fJRmrSlFiVESCec/edit?gid=0#gid=0").sheet1
>>>>>>> 3b29589 (updated)


def getNumCol(): 
    col_values = notices.col_values(1)
    return sum(1 for cell in col_values if cell.strip() != "") - 1


def fetch_taken_terms():
    numCol = getNumCol()
<<<<<<< HEAD
    return [notices.cell(i, 1).value for i in range(2, numCol + 1)]


# uses the np and terms vars to fetch data from federalregister.gov
def scrape(np, terms, numCols):
    terms = terms.split(',')
    terms = [i[1:] if i[0] == " " else i for i in terms]
    
    for term in terms:
        url = f"https://www.federalregister.gov/api/v1/documents.json?per_page={np}&order=relevance&conditions[term]={term}&conditions[publication_date][gte]=2021-01-01"

        aRes = req.get(url).json()
        res = aRes["results"]
=======
    ids = [notices.cell(i, 8).value for i in range(2, numCol + 1)]
    ids = [i.strip() for i in ids if i]

    return ids


"""
FIELDS:
    NUM PAGES
    TERMS 
    NUM NOTICES TO ADD
    DOCKET TYPE
    ORDER
    STARTING DATE
"""


# uses the np and terms vars to fetch data from federalregister.gov
def scrape(np, terms, numCols, docketType, order, date):
    takenTerms = fetch_taken_terms()
    for term in terms:
        url = f"https://www.federalregister.gov/api/v1/documents.json?per_page={np}&order={order}&conditions[term]={term}&conditions[publication_date][gte]={date}&conditions[type]={docketType}"

        print("Fetching:", url)
        aRes = req.get(url).json()
        res = aRes.get("results", [])
        
        if not res:
            print("End of search")
            continue
>>>>>>> 3b29589 (updated)

        searchTerms = [
            "request for ",
            "rfi",
<<<<<<< HEAD
            "rfc",  
            "anprms",
            "nprm"
=======
            "rfc",
            "seeks comment",
            "seeking comment",
            "comments requested",
            "public comment",
            "nprm",
            "proposed rule",
            "notice of proposed rulemaking",
            "notice of",
            "extension of comment",
            "request for information",
>>>>>>> 3b29589 (updated)
        ]

        res = [i for i in res if any(j in i["title"].lower() for j in searchTerms)]

        nc = 0
<<<<<<< HEAD
        takenTerms = fetch_taken_terms()
        for i in res:
            if nc == numCols:
                return

            if i["title"] not in takenTerms:
=======
        for i in res:
            if nc == numCols:
                return
            
            if i["document_number"] not in takenTerms:
>>>>>>> 3b29589 (updated)
                docNum = i['document_number']
                commentDateUrl = f"https://www.federalregister.gov/api/v1/documents/{docNum}.json?fields[]=comments_close_on"
                commentDate = req.get(commentDateUrl).json()
                finalCommentDate = commentDate["comments_close_on"] 

                print("Adding notice:", i["title"])
                
                publicationDate = dt.strptime(i['publication_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
                
                if finalCommentDate:
                    finalCommentDate = dt.strptime(finalCommentDate, "%Y-%m-%d").strftime("%m/%d/%Y")

                newrow = [i["title"], getAgency(docNum).title(), publicationDate, f"{publicationDate} - {finalCommentDate}", i['abstract'], i['html_url'], ""]
                notices.append_row(newrow)
<<<<<<< HEAD
=======
                takenTerms.append(i["document_number"])
>>>>>>> 3b29589 (updated)
                
                nc += 1

              

if __name__ == "__main__":
<<<<<<< HEAD
    numPages = input("Enter amount of pages to search: ")
    terms = input("Enter terms to search (separate by commas) (type nothing for all): ")
    
    if terms.strip() == "":
        terms = "artificial intelligence, foundation models, automated decision-making, machine learning, ai, ai systems, ai technologies, ai tools, ai applications, ai software, ai algorithms, ai regulation, ai policy"
    
    numCols = input("Enter number of notices to add: ")
    scrape(numPages, terms, int(numCols))
=======
    numPages = input("Enter amount of pages to search (DEFAULT: 10): ")
    terms = input("Enter terms to search (separate by commas) (type nothing for all): ")
    
    if terms.strip() != "":
        terms = terms.split(',')
        terms = [i[1:] if i[0] == " " else i for i in terms]
    else:
        terms = [
            "artificial intelligence",
            "algorithm",
            "artificial general intelligence",
            "artificial narrow intelligence",
            "chat-based generative pre-trained transformer",
            "transformer models",
            "self-attention mechanism",
            "computer vision",
            "critical ai",
            "data",
            "training data",
            "hallucination",
            "human-centered perspective",
            "intelligence augmentation",
            "intelligent tutoring systems",
            "adaptive learning",
            "interpretable machine learning",
            "black boxes",
            "machine learning",
            "neural networks",
            "deep learning",
            "natural language processing",
            "robots",
            "explainable machine learning",
            "foundation models",
            "automated decision-making",
            "ai",
            "ai systems",
            "ai technologies",
            "ai tools",
            "ai applications",
            "ai software",
            "ai algorithms",
            "ai regulation",
            "ai policy"
        ]

    
    numCols = input("Enter number of notices to add (DEFAULT: 5): ")
    docketType = input("Enter docket type (RULE, PRORULE, DEFAULT: NOTICE, PRESDOCU): ")
    order = input("Enter order (DEFAULT: relevance, newest, oldest, executive_order_number): ")
    date = input("Enter date (YYYY-MM-DD) (DEFAULT: 2021-01-01): ")

    if not numCols:
        numCols = 5
    if not docketType:
        docketType = "NOTICE"
    if not date:
        date = "2021-01-01"
    if not order:
        order = "relevance"

    scrape(numPages, terms, int(numCols), docketType, order, date)
>>>>>>> 3b29589 (updated)
