<<<<<<< HEAD
import requests as req
from bs4 import BeautifulSoup as bs4
import json

def getAgency(docId):
    url = f"https://www.federalregister.gov/api/v1/documents/{docId}.json?fields[]=body_html_url"
    res = req.get(url).json()
    
    bodyUrl = res.get("body_html_url")
    
    if not bodyUrl:
        print("No body URL found.")
        return None

    bodyRes = req.get(bodyUrl)
    bodyUrl = bodyRes.text
    soup = bs4(bodyUrl, "html.parser")
    agency = soup.find("div", id="agency")
    if agency:
        agency = agency.text.strip().lower().replace("agency:", "").strip()
        if agency[-1] == ".":
            agency = agency[:-1].strip()
        return agency
    
    return None

def abbreviateAgency(agency_full):
    fname = "agency_abbreviations.json"
    with open(fname, "r") as f:
        AGENCY_ABBR = json.load(f)
        
    default = ''.join(word[0].upper() for word in agency_full.split() if word)
        
    return AGENCY_ABBR.get(agency_full, default)

if __name__ == "__main__":
    a = getAgency("2024-06547")
    print(a)
=======
import requests as req
from bs4 import BeautifulSoup as bs4
import json

def getAgency(docId):
    url = f"https://www.federalregister.gov/api/v1/documents/{docId}.json?fields[]=body_html_url"
    res = req.get(url).json()
    
    bodyUrl = res.get("body_html_url")
    
    if not bodyUrl:
        print("No body URL found.")
        return None

    bodyRes = req.get(bodyUrl)
    bodyUrl = bodyRes.text
    soup = bs4(bodyUrl, "html.parser")
    agency = soup.find("div", id="agency")
    if agency:
        agency = agency.text.strip().lower().replace("agency:", "").strip()
        if agency[-1] == ".":
            agency = agency[:-1].strip()
        return agency
    
    return None

def abbreviateAgency(agency_full):
    fname = "agency_abbreviations.json"
    with open(fname, "r") as f:
        AGENCY_ABBR = json.load(f)
        
    default = ''.join(word[0].upper() for word in agency_full.split() if word)
        
    return AGENCY_ABBR.get(agency_full, default)

if __name__ == "__main__":
    a = getAgency("2024-06547")
    print(a)
>>>>>>> 3b29589 (updated)
    print(abbreviateAgency(a))