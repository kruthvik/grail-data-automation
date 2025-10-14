from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.window import WindowTypes
from bs4 import BeautifulSoup as bs
import requests as req
from fetchPDF import createPDF, downloadPDF, removeComments
import time

class CommentScraper():
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.links = []
        removeComments()
        

    def scrape(self, docNum, page_number):
            while True:
                url = base_url = f"https://www.regulations.gov/document/{docNum}/comment?pageNumber={page_number}"
                print(f"Scraping page {page_number}...")
                self.driver.get(url)

                try:
                    self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-type-comment")))
                except TimeoutException:
                    print("No comments found on this page. Stopping.")
                    break

                cards = self.driver.find_elements(By.CLASS_NAME, "card-type-comment")
                if not cards:
                    print("No comment cards found. Stopping.")
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

                        self.links.append(cmnt)

                        original_window = self.driver.current_window_handle
                        self.driver.switch_to.new_window(WindowTypes.TAB)

                        self.driver.get(full_url)

                        print(f"Opened URL {full_url}")

                        try:
                            self.wait.until(EC.presence_of_all_elements_located((By.ID, "mainContent")))
                            attachments = self.driver.find_elements(By.CSS_SELECTOR, "div.card.card-attachment")

                            if not attachments:
                                content = self.driver.find_element(By.CSS_SELECTOR, "#mainContent")
                                text = content.text

                                createPDF(text, posted, commenter, agency, doc_id)
                            else:
                                for attachment in attachments:
                                    # get the attachment
                                    link = attachment.find_element(By.XPATH, ".//a[@href]")
                                    downloadPDF(link.get_attribute("href"), posted, commenter, agency, doc_id)
                        except TimeoutException:
                            print("Failed to load comment page.")
                        finally:
                            time.sleep(0.5)
                            self.driver.close()
                            self.driver.switch_to.window(original_window)

                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        print("Error parsing comment:", e)
                        continue

                page_number += 1

    def cleanup(self):
        self.driver.quit()

    def getLinks(self):
        return self.links



if __name__ == "__main__":
    scraper = CommentScraper()
    docNum = input("Enter the Document ID: ")
    scraper.scrape(docNum, 1)
    scraper.cleanup()
    print(f"\nTotal links collected: {len(scraper.getLinks())}")
    for l in scraper.getLinks():
        print(l)

    print(scraper.getLinks()[1])
