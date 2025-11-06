"""
INPUT: DOC-ID & COMMENT FOLDER
OUTPUT: TEXT FOLDER

GOAL:
Standardize comments into a human-readable Markdown format with metadata.
"""

from logger_config import Logger
from dotenv import load_dotenv
from ollama import Client
from PIL import Image

from standardizeFormat import standardizeFormat

import os
import fitz
import pytesseract
import io
import json
import shutil

load_dotenv()


class Environment:
    def __init__(self, documentId):
        self.documentId = documentId
        self.logFolder = f"./logs/standardization/{self.documentId}"
        self.OLLAMA_MODEL = "llama3.2:latest"  # Text generation model
        self.EMBED_MODEL = "mxbai-embed-large:latest"  # Embedding model

        self.setupLog()
        self.initAI()

    def setupLog(self):
        self.logger = Logger(log_folder=self.logFolder)

    def initAI(self):
        try:
            self.ollama = Client(host="http://localhost:11434")
        except Exception as e:
            self.logger.log(f"Error setting up Ollama: {e}", level="ERROR")
            raise e

    def chat(self, prompt):
        try:
            response = self.ollama.generate(
                model=self.OLLAMA_MODEL, prompt=prompt)
            return response['response']
        except Exception as e:
            self.logger.log(f"Error in chat: {e}", level="ERROR")
            raise e

    def embed(self, text):
        try:
            response = self.ollama.embed(model=self.EMBED_MODEL, input=text)
            print(response.get("embeddings", []))
            return response.get("embeddings", [])
        except Exception as e:
            self.logger.log(f"Error in embed: {e}", level="ERROR")
            raise e


class CommentStandardizer:

    @staticmethod
    def getFilenameBase(filename: str) -> str:
        return os.path.splitext(filename)[0]

    @staticmethod
    def getFilenameExtension(filename: str) -> str:
        return os.path.splitext(filename)[1]

    def __init__(self, env: Environment):
        self.env = env
        self.logger = self.env.logger
        self.commentFolder = f"./comments/{self.env.documentId}"
        self.targetFolder = f"./standardized_comments/{self.env.documentId}"
        self.metadataFile = f"{self.commentFolder}/metadata.json"
        self.embeddingsFolder = f"./embeddings/{self.env.documentId}"

        os.makedirs(self.targetFolder, exist_ok=True)
        os.makedirs(self.embeddingsFolder, exist_ok=True)
        self.setupFolder(self.targetFolder)
        self.setupFolder(self.embeddingsFolder)

    def setupFolder(self, folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                self.logger.log(
                    f"Error clearing {folder} folder: {e}", level="ERROR")

    def extractTextFromPDF(self, pdf_path: str) -> str:
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    page_text = page_text.encode(
                        'utf-8', errors='replace').decode('utf-8')
                    text += page_text + "\n"
                else:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    ocr_text = ocr_text.encode(
                        'utf-8', errors='replace').decode('utf-8')
                    text += ocr_text + "\n"
            doc.close()
        except Exception as e:
            self.logger.log(f"Error extracting {pdf_path}: {e}", level="ERROR")
        return text.strip()

    def getMetadata(self, filename):
        base = CommentStandardizer.getFilenameBase(filename)
        with open(self.metadataFile, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata.get(base, {})

    def createPrompt(self, metadata, info):
        return f"""
            You are an AI comment standardizer. Your job is to categorize the comment text based on the format below. Write it in markdown format.
            DO NOT SUMMARIZE THE COMMENT TEXT. INCLUDE IT AS IT IS JUST IN THE FORMAT GIVEN. Remove any text that is part of formatting such as page number or a table of content, etc.

            Metadata: {json.dumps(metadata)}
            {info}

            Return the standardized comment in this format:

            Filename: [Filename]
            Date Submitted: [Date Submitted]
            Submitter Name: [Submitter Name]
            Agency: [Agency]
            Comment ID: [Comment ID]

            Comment Text: [Comment Text]
            """

    def standardizeComment(self, filename):
        filePath = os.path.join(self.commentFolder, filename)
        commentText = self.extractTextFromPDF(filePath)
        metadata = self.getMetadata(filename)
        response = ""

        for i, chunk in enumerate(self.chunk_paragraphs(commentText)):
            prompt = self.createPrompt(
                metadata, chunk) if i == 0 else f"Do the same for this chunk:\n{chunk}"
            response += "\n" + self.env.chat(prompt)

        response = response.strip()
        self.logger.log(f"Standardization Response: {response}", level="INFO")
    
        return response

    def _sanitize_text_for_pdf(self, text: str) -> str:
        text = str(text)
        replacements = {
            '\uf0d8': ' ',
            '\uf0b7': '•',
            '\uf0d9': ' ',
            '\uf0da': ' ',
            '\uf0db': ' ',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        sanitized = []
        for char in text:
            if ord(char) < 128 or (ord(char) >= 160 and ord(char) < 0xD800) or (ord(char) >= 0xE000 and ord(char) < 0xFFFE):
                try:
                    char.encode('utf-8')
                    sanitized.append(char)
                except:
                    sanitized.append(' ')
            else:
                sanitized.append(' ')
        return ''.join(sanitized)

    def writeStandardizedComment(self, filename: str, standardizedComment: str):
        filenameBase = CommentStandardizer.getFilenameBase(filename)
        
        filePath = os.path.join(self.targetFolder, filenameBase)
        embeddingPath = os.path.join(self.embeddingsFolder, filenameBase)
        
        sanitized = self._sanitize_text_for_pdf(standardizedComment)
        embedding = self.env.embed(sanitized)
        
        with open(f"{filePath}.md", "w", encoding="utf-8") as f:
            f.write(sanitized)
            
        with open(f"{embeddingPath}.json", "w", encoding="utf-8") as f:
            json.dump(embedding, f)
            
        self.logger.log(
            f"Written standardized comment: {filePath}.md", level="INFO")
        self.logger.log(
            f"Written embedding: {embeddingPath}.json", level="INFO")

    def chunk_paragraphs(self, text, max_tokens=2000):
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            tokens = len(p.split())
            if current_len + tokens > max_tokens:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = tokens
            else:
                current_chunk.append(p)
                current_len += tokens
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        return chunks

    def standardizeComments(self):
        for filename in os.listdir(self.commentFolder):
            if filename.endswith(".pdf"):
                standardizedComment = self.standardizeComment(filename)
                try:
                    print(standardizedComment.encode(
                        'utf-8', errors='replace').decode('utf-8'))
                except:
                    print(
                        "[Comment processed but cannot display due to encoding issues]")
                self.writeStandardizedComment(filename, standardizedComment)


if __name__ == "__main__":
    documentId = input("Enter the document ID: ")
    
    env = Environment(documentId)
    
    standardizer = CommentStandardizer(env)
    standardizer.standardizeComments()
    
    standardizeFormat(documentId)
