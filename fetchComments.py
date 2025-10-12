from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    def scrape(self, base_url, page_number):
        while True:
            url = base_url.format(page_number)
            print(f"Scraping page {page_number}...")
            self.driver.get(url)

            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-type-comment")))
            except:
                print("No comments found on this page. Stopping.")
                break

            cards = self.driver.find_elements(By.CLASS_NAME, "card-type-comment")
            if not cards:
                print("No comment cards found. Stopping.")
                break

            for card in cards:
                try:
                    link_tag = card.find_element(By.TAG_NAME, "a")
                    href = link_tag.get_attribute("href")
                    if href and href not in self.links:
                        self.links.append(href)
                except:
                    continue

            print(f"Collected {len(self.links)} links so far.")

            page_number += 1
        time.sleep(1) 

    def cleanup(self):
        self.driver.quit()

    def getLinks(self):
        return self.links

if __name__ == "__main__":
    scraper = CommentScraper()
    scraper.scrape("https://www.regulations.gov/search/comment?filter=240802-0209&pageNumber={}", 1)
    scraper.cleanup()
    print(f"\nTotal links collected: {len(scraper.getLinks())}")
    for l in scraper.getLinks():
        print(l)
