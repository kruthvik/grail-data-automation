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
from commentManager import CommentManager
from logger_config import Logger

import dotenv
dotenv.load_dotenv()


class Environment:
    def __init__(self, ollama_key, url, ollama_model="llama3.2:latest", creds_file="service_account.json", sheetNum=1):
        self.sheetNum = sheetNum - 1
        self.url = url
        self.OLLAMA_MODEL = ollama_model  # ✅ Cloud model to use
        self.FIELDS = [
            "COMMENT-ID",
            "Filename",
            "Date Submitted",
            "Submitter Name",
            "Organization Name",
            "Organization Type",
            "501c Status",
            "Organization Type_NTEE",
            "Organization Role",
            "Contact Information",
            "Relevant Keywords",
            "Brief Summary of Comment",
            "Relevant Issues Addressed",
        ]
        self.cred_file = creds_file
        self.ollama_key = ollama_key

        self.setupLogger("env")
        self.setupOllama()
        self.setupGoogleSheet()

    def setupLogger(self, docNum):
        log_folder = f"./logs/analysis/{docNum}"
        self.logger = Logger(log_folder=log_folder)

    def setupOllama(self):
        try:
            self.ollama = Client(
                host="https://ollama.com",
                headers={
                    "Authorization": self.ollama_key,
                    "Content-Type": "application/json"
                }
            )
        except Exception as e:
            self.logger.log(f"Error setting up Ollama: {e}", level="ERROR")
            raise e

    def setupGoogleSheet(self):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.cred_file, [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ])
            client = gs.authorize(creds)
            self.spreadsheet = client.open_by_url(self.url)
        except Exception as e:
            self.logger.log(f"Error setting up Google Sheet: {e}", level="ERROR")
            raise e

    def chat(self, prompt):
        try:
            response = self.ollama.chat(model=self.OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
            raw_output = response["message"]["content"].strip()
            self.logger.log(f"Response: {raw_output}", level="INFO")
            return raw_output
        except Exception as e:
            self.logger.log(f"Error in chat: {e}", level="ERROR")
            raise e

    def addSheetRow(self, rowData):
        sheet = self.spreadsheet.get_worksheet(self.sheetNum)
        if sheet is None:
            print("❌ No worksheet found at index 0")
            return
        rowData = [str(x).strip() if x else "N/A" for x in rowData]
        sheet.append_row(rowData, value_input_option='USER_ENTERED')
        print("✅ Row added successfully.")


class CommentAnalysis:
    def __init__(self, env: Environment, docId: str):
        self.env = env
        self.docId = docId
        self.env.setupLogger(docId)
        self.logger = self.env.logger
        self.commentPath = f"./comments/{self.docId}"

    def extract_text_from_pdf(self, pdf_path: str) -> str:
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
            self.logger.log(f"Error extracting {pdf_path}: {e}", level="ERROR")
        return text.strip()

    @staticmethod
    def returnPrompt(field_subset: list[str], metadata: dict, context_text: str, relevantInfo="") -> str:

        prompt = f"""
            You are an AI data extraction assistant. You're job is to research important information about the background behind comments as part of federal RFIs/RFCs.

            Extract ONLY the following fields (in order) from the text and metadata below.
            Return in this format: [Field]: [Value]
            No extra explanations or markdown.
            
            You MUST fill out the relevant issues addressed and the brief summary. This is REQUIRED.
            
            Keep the data as accurate as possible; don't make leaps.
            
            Keep in mind the context of this analysis:
                The following entities are those which have responded to federal RFIs/RFCs related to AI and policy.

            Do NOT use quotes around values.
            Do NOT return empty or null; use 'N/A' if unknown.
            Do NOT change the order of fields.

            API Information regarding whether it is a nonprofit.
            NOTE: 
                For the API information, remember that this is a mere search of all entities with similar names. 
                Many of the entities aren't nonprofits and shouldn't be considered.
                These are just considerations to possibly assist in the field above.
                
                When determining organization role, remember to pick one of the following:
                    - pick one of the following: 
                        Citizen Engagement, Individual Expression/Specialization, Innovation, Political Advocacy, Service Provision, Social Capital Creation, Products, Services, Government Institution, Citizen, Infastructure

            If it is not an organization but an individual, write N/A for the organization name. You must fill out the type of organization it is through research but if you really can't, you may write N/A.


            Fields: {json.dumps(field_subset)}

            Metadata: {json.dumps(metadata)}

            Comment text: {context_text[:5000]}

            {f"""
            This document is situated within a group of documents as part of one comment in response to a federal RFI/RFC regarding AI policy.
            Here is the context of all prior documents:
            {relevantInfo}
            
            """ if relevantInfo else ""}"""
            
        return prompt

    @staticmethod
    def getBase(file):
        """
        Returns the base filename without attachment suffix or extension
        """
        base = os.path.splitext(file)[0]
        if "__attachment" in base:
            base = base.rsplit("__attachment", 1)[0]
        return base

    @staticmethod
    def organizeDuplicates(folder):
        """
        Groups files by base name (attachments included)
        """
        groups = {}
        for f in folder:
            base = CommentAnalysis.getBase(f)
            groups.setdefault(base, []).append(f)
        return list(groups.values())

    def getOrganizedFolder(self):
        files = [f for f in os.listdir(self.commentPath) if f.lower().endswith(".pdf")]
        return self.organizeDuplicates(files)

    def getMetadata(self, filename):
        base = os.path.splitext(filename)[0]
        metadataFile = f"{self.commentPath}/metadata.json"
        with open(metadataFile, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata.get(self.getBase(filename), None)

    def extractFolder(self):
        for group in self.getOrganizedFolder():
            self.analyzeComments(group)

    def analyzeComments(self, group):
        context = ""
        for file in group:
            res = self.analyzeComment(file, context)
            context += f"\nFilename: {res[1]}   Summary: {res[-2]}   Relevant Issues: {res[-1]}"

    def analyzeComment(self, file, relevantInfo=""):
        filePath = f"{self.commentPath}/{file}"
        text = self.extract_text_from_pdf(filePath)
        metadata = self.getMetadata(file)

        prompt = self.returnPrompt(self.env.FIELDS, metadata, text, relevantInfo)
        chatResponse = self.env.chat(prompt)
        response = self.interpolateResponse(chatResponse, metadata, file)
        response.append(text[:49000])
        self.env.addSheetRow(response)
        return response

    def interpolateResponse(self, chatResponse, metadata, filename):
        pattern = r"^[^:]+:\s*(.*)$"
        arr = [re.match(pattern, line).group(1) for line in chatResponse.splitlines() if re.match(pattern, line)]
        arr = [v for v in arr if len(v.strip()) > 0]
        arr = [str(x).strip().replace("\n", " ") or "N/A" for x in arr]

        arr[0] = metadata.get("comment_id", "")
        arr[1] = filename
        arr[2] = metadata.get("date", "")
        arr[3] = metadata.get("commenter", "")

        return arr


if __name__ == "__main__":
    docNum = "2021-10861"
    env = Environment(os.getenv("OLLAMA_KEY"), os.getenv("GOOGLE_SHEET_URL"), sheetNum=3)
    analyzer = CommentAnalysis(env, docNum)
    analyzer.extractFolder()
