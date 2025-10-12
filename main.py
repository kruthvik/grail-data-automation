import requests as req
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gs.authorize(creds)

notices = client.open_by_url("URL OF SPREADSHEET").sheet1


def getNumCol(): 
    col_values = notices.col_values(1)
    return sum(1 for cell in col_values if cell.strip() != "") - 1


def fetch_taken_terms():
    numCol = getNumCol()
    print(numCol)
    return [notices.cell(i, 1).value for i in range(2, numCol + 1)]


# uses the np and terms vars to fetch data from federalregister.gov
def scrape(np, terms):
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

        for i in res:
            if i["title"] not in fetch_taken_terms():
                docNum = i['document_number']

                commentDateUrl = f"https://www.federalregister.gov/api/v1/documents/{docNum}.json?fields[]=comments_close_on"
                commentDate = req.get(commentDateUrl).json()
                print(commentDate)
                finalCommentDate = commentDate["comments_close_on"]


                agencyNames = [m['name'] for m in i['agencies']]
                newrow = [i["title"], ', '.join(agencyNames), i['publication_date'], finalCommentDate, i['abstract'], i['html_url'], ""]
                notices.append_row(newrow)
                    
scrape(500,"artificial intelligence")
