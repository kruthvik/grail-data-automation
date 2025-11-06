from bs4 import BeautifulSoup as bs4
import json
import requests as req


class NoticeAnalyzer:
    def __init__(self, docId):
        self.docId = docId
        self.url = f"https://www.federalregister.gov/api/v1/documents/{docId}.json?fields[]=body_html_url"
        
        self.soup = self.getSoup()
        
    def getText(self):
        return self.soup.get_text()
        
    def getAgency(self):
        agency = self.soup.find("div", id="agency")
        if agency:
            agency = agency.text.strip().lower().replace("agency:", "").strip()
            if agency[-1] == ".":
                agency = agency[:-1].strip()
            return agency.title()
        
        return None
        
    def getSoup(self):
        res = req.get(self.url).json()
        
        self.bodyUrl = res.get("body_html_url")
        
        if not self.bodyUrl:
            print("No body URL found.")
            return None

        bodyRes = req.get(self.bodyUrl)
        bodyText = bodyRes.text
        
        soup = bs4(bodyText, "html.parser")
        return soup
    
    @staticmethod
    def abbreviateAgency(agency):
        fname = "agency_abbreviations.json"
        with open(fname, "r") as f:
            AGENCY_ABBR = json.load(f)
            
        default = ''.join(word[0].upper() for word in agency.split() if word)
            
        return AGENCY_ABBR.get(agency, default)
    
if __name__ == "__main__":
    ba = BodyAnalyzer("2021-10861")
    print(ba.getAgency())
    