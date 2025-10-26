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

notices = client.open_by_url("INSERT API ").sheet1


def getNumCol(): 
    col_values = notices.col_values(1)
    return sum(1 for cell in col_values if cell.strip() != "") - 1


def fetch_taken_terms():
    numCol = getNumCol()
    return [notices.cell(i, 1).value for i in range(2, numCol + 1)]


# uses the np and terms vars to fetch data from federalregister.gov
def scrape(np, terms, numCols):
    terms = terms.split(',')
    terms = [i[1:] if i[0] == " " else i for i in terms]
    
    for term in terms:
        url = f"https://www.federalregister.gov/api/v1/documents.json?per_page={np}&order=relevance&conditions[term]={term}&conditions[publication_date][gte]=2021-01-01"

        aRes = req.get(url).json()
        res = aRes["results"]

        searchTerms = [
            "request for ",
            "rfi",
            "rfc",  
            "anprms",
            "nprm"
        ]

        res = [i for i in res if any(j in i["title"].lower() for j in searchTerms)]

        nc = 0
        takenTerms = fetch_taken_terms()
        for i in res:
            if nc == numCols:
                return

            if i["title"] not in takenTerms:
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
                
                nc += 1

              

if __name__ == "__main__":
    numPages = input("Enter amount of pages to search: ")
    terms = input("Enter terms to search (separate by commas) (type nothing for all): ")
    
    if terms.strip() == "":
        terms = "artificial intelligence, foundation models, automated decision-making, machine learning, ai, ai systems, ai technologies, ai tools, ai applications, ai software, ai algorithms, ai regulation, ai policy"
    
    numCols = input("Enter number of notices to add: ")
    scrape(numPages, terms, int(numCols))
