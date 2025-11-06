from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.window import WindowTypes
from bs4 import BeautifulSoup as bs

from commentManager import CommentManager

import requests as req
import time
import re

from logger_config import Logger
from ollama import Client

ollama = Client(
    host="https://ollama.com",  # ✅ Correct endpoint for Ollama Cloud
    headers={
        "Authorization": "Bearer 118347b4d2404a13ad59ea034ea6c88e.y3rHTTlshlZgTcmr8Riqh5Sb",
        "Content-Type": "application/json"
    }
)

OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"  # ✅ Cloud model to use

class CommentScraper():
    def __init__(self, docNum=""):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.links = []
        self.docNum = docNum
        self.logger = Logger(log_folder=f"./logs/collection/{self.docNum}")
        self.commentManager = CommentManager(logger=self.logger, documentID=self.docNum)

    @staticmethod
    def isRelevant(abstract):
        if len(abstract) < 200:
            return False

        prompt = f"""
        The following document is a comment in response to a federal RFI/RFC or similar request for input.
        Determine if the following text is a relevant comment that addresses the topic of the request or a description of the comment. Keep in mind that a relevant comment is not one that is a mere description of the comment itself but one that accurately and lengthily responds to a federal notice.
        Respond with "Yes" if relevant, "No" if not. Only write "Yes" or "No" and nothing else.
        
        Document Abstract: {abstract}
        """
        
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response['message']['content'].strip().lower()
        return answer == "yes"

    def initialize(self):
        self.commentManager.setupFolders()
        self.driver.get(f"https://www.regulations.gov/search?filter={self.docNum}")
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card.card-type-notice")))
        except TimeoutException:
            self.logger.log("No document entries found.", level="WARNING")
            return

        ids = []
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".card.card-type-notice")
        for card in cards:
            try:
                # --- Title and link ---
                title_tag = card.find_element(By.CSS_SELECTOR, "h3.card-title a")
                title = title_tag.text.strip()
                url = title_tag.get_attribute("href")
                url = url if url.startswith("http") else "https://www.regulations.gov" + url

                # --- Metadata ---
                metadata_items = card.find_elements(By.CSS_SELECTOR, "div.card-metadata li")
                data = {}
                for li in metadata_items:
                    strong = li.find_element(By.TAG_NAME, "strong").text.strip().lower()
                    value = li.text.replace(li.find_element(By.TAG_NAME, "strong").text, "").strip()
                    data[strong] = value

                ids.append(data.get("id"))
            except Exception as e:
                self.logger.log(f"Error parsing entry: {e}", level="ERROR")
                continue

        return ids

    def scrape(self, docketId, page_number):
            while True:
                url = base_url = f"https://www.regulations.gov/document/{docketId}/comment?pageNumber={page_number}"
                self.logger.log(f"Scraping page {page_number}...")
                self.driver.get(url)

                try:
                    self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-type-comment")))
                except TimeoutException:
                    self.logger.log("No comments found on this page. Stopping.", level="WARNING")
                    break

                cards = self.driver.find_elements(By.CLASS_NAME, "card-type-comment")
                if not cards:
                    self.logger.log("No comment cards found. Stopping.", level="WARNING")
                    break

                for card in cards:
                    try:
                        # --- Commenter name and link ---
                        name_tag = card.find_element(By.CSS_SELECTOR, "h3.card-title a")
                        commenter = name_tag.text.strip().replace("Comment Submitted by ", "")
                        relative_url = name_tag.get_attribute("href")
                        full_url = relative_url if relative_url.startswith("http") else "https://www.regulations.gov" + relative_url

                        # --- Metadata section ---
                        metadata_items = card.find_elements(By.CSS_SELECTOR, "div.collapse li")
                        data = {}
                        for li in metadata_items:
                            strong = li.find_element(By.TAG_NAME, "strong").text.strip().lower()
                            value = li.text.replace(li.find_element(By.TAG_NAME, "strong").text, "").strip()
                            data[strong] = value

                        # --- Extract fields ---
                        agency = data.get("agency", "")
                        posted = data.get("posted", "")
                        comment_id = data.get("id", "")
                        doc_id = comment_id

                        cmnt = {
                            "date": posted,
                            "name": commenter,
                            "agency": agency,
                            "url": full_url,
                            "id": doc_id
                        }
                        
                        print(commenter)
                        print(full_url)
                        print(doc_id)
                        print(posted)
                        print(agency)

                        self.links.append(cmnt)

                        original_window = self.driver.current_window_handle
                        self.driver.switch_to.new_window(WindowTypes.TAB)

                        self.driver.get(full_url)

                        self.logger.log(f"Opened URL {full_url}")

                        try:
                            self.wait.until(EC.presence_of_all_elements_located((By.ID, "mainContent")))
                            attachments = self.driver.find_elements(By.CSS_SELECTOR, "div.card.card-attachment")
                            self.logger.log(f"Found attachments: {attachments}")
                            
                            content = self.driver.find_element(By.CSS_SELECTOR, "#mainContent")
                            abstract = content.text[:1000]  # First 1000 chars as abstract
                            relevantAbstract = CommentScraper.isRelevant(abstract)
                            
                            numAttachments = len(attachments) + (1 if relevantAbstract else 0)
                            attachmentNum = 0

                            if relevantAbstract:
                                attachmentNum += 1
                                self.logger.log(f"Relevant abstract detected — saving as attachment 1/{numAttachments}")
                                self.commentManager.createPDF(abstract, posted, commenter, agency, doc_id ,numAttachments=numAttachments, attachmentNum = attachmentNum)

                            self.logger.log(f"Found {len(attachments)} attachments")
                            
                            for attachment in attachments:
                                # get the attachment
                                links = [link.get_attribute('href') for link in attachment.find_elements(By.XPATH, ".//a[@href]")]
                                
                                if not links:
                                    self.logger.log(f"No links found for attachment {attachment}", level='WARNING')
                                    continue

                                link = next((i for i in links if 'pdf' in i), links[0])
                                attachmentNum += 1
                                
                                self.logger.log(f"Downloading attachment {attachmentNum}/{numAttachments} from {link}")
                                self.commentManager.downloadPDF(link, posted, commenter, agency, doc_id, numAttachments=numAttachments, attachmentNum = attachmentNum)
                            
                            if attachmentNum == 0:
                                self.logger.log("No PDF attachments found.", level="WARNING")

                        except TimeoutException:
                            self.logger.log("Failed to load comment page.", level="ERROR")
                            
                        finally:
                            time.sleep(0.5)
                            self.driver.close()
                            self.driver.switch_to.window(original_window)

                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        self.logger.log(f"Error parsing comment: {e}", level="ERROR")
                        continue

                page_number += 1

    # def getAgency():
        

    def cleanup(self):
        self.driver.quit()

    def getLinks(self):
        return self.links



if __name__ == "__main__":
    doc_id = input("Enter the Document ID: ")

    scraper = CommentScraper(doc_id)

    docketIds = scraper.initialize()
    
    for docketId in docketIds:
        scraper.scrape(docketId, 1)
    
    scraper.cleanup()

    print(f"\nTotal links collected: {len(scraper.getLinks())}")
    for l in scraper.getLinks():
        print(l)


    # print(scraper.getLinks()[1])
