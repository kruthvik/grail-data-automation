import requests as req
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime as dt
from tqdm import tqdm
from logger_config import Logger
import os
from dotenv import load_dotenv
from ollama import Client
from NoticeAnalyzer import NoticeAnalyzer

class Environment:
    def __init__(self, credentials_file="service_account.json"):
        load_dotenv()
       
        self.logger = Logger(log_folder="./logs/generation/")
        self.credentials_file = credentials_file 
        self.spreadsheet_url = os.getenv("NOTICE_SPREADSHEET_URL")
        
        self.setupOllama()
    
    def setupOllama(self):
        try:
            self.ollama = Client(host="http://localhost:11434")
        except Exception as e:
            self.logger.log(f"Error setting up Ollama: {e}", level="ERROR")
            raise e

    def chat(self, prompt):
        try:
            response = self.ollama.generate(model="llama3.2:latest", prompt=prompt)
            return response['response']
        except Exception as e:
            self.logger.log(f"Error in chat: {e}", level="ERROR")
            raise e


class FederalRegisterScraper:
    """A class to handle scraping and managing federal register notices."""
    
    # Default search terms
    DEFAULT_TERMS = [
        "artificial intelligence", "algorithm", "artificial general intelligence",
        "artificial narrow intelligence", "chat-based generative pre-trained transformer",
        "transformer models", "self-attention mechanism", "computer vision",
        "critical ai", "data", "training data", "hallucination",
        "human-centered perspective", "intelligence augmentation",
        "intelligent tutoring systems", "adaptive learning",
        "interpretable machine learning", "black boxes", "machine learning",
        "neural networks", "deep learning", "natural language processing",
        "robots", "explainable machine learning", "foundation models",
        "automated decision-making", "ai", "ai systems", "ai technologies",
        "ai tools", "ai applications", "ai software", "ai algorithms",
        "ai regulation", "ai policy"
    ]
    
    # Search terms to filter relevant notices
    SEARCH_TERMS = [
        "request for ", "rfi", "rfc", "seeks comment", "seeking comment",
        "comments requested", "public comment", "nprm", "proposed rule",
        "notice of proposed rulemaking", "notice of", "extension of comment",
        "request for information"
    ]
    
    def __init__(self, env: Environment = None):
        """Initialize the scraper with Google Sheets connection.
        
        Args:
            spreadsheet_url: URL of the Google Sheet to update
            credentials_file: Path to the service account JSON file
        """
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(env.credentials_file, self.scope)
        self.client = gs.authorize(self.creds)
        self.sheet = self.client.open_by_url(env.spreadsheet_url).sheet1
        
        self.env = env
        
        self.logger = env.logger
    
    def _get_row_count(self) -> int:
        """Get the number of non-empty rows in the sheet."""
        col_values = self.sheet.col_values(1)
        return sum(1 for cell in col_values if cell.strip() != "") - 1  # Subtract header
    
    def _get_existing_document_ids(self) -> List[str]:
        """Fetch existing document IDs from the sheet to avoid duplicates."""
        num_rows = self._get_row_count()
        if num_rows <= 0:
            return []
            
        ids = [self.sheet.cell(i, 8).value 
              for i in range(2, num_rows + 2)]  # +2 for 1-based index and header
        return [doc_id.strip() for doc_id in ids if doc_id]
    
    def _format_date(self, date_str: str, input_format: str = "%Y-%m-%d", 
                    output_format: str = "%m/%d/%Y") -> str:
        """Format date string from one format to another."""
        try:
            return dt.strptime(date_str, input_format).strftime(output_format)
        except (ValueError, TypeError):
            return ""
    
    def _process_notice(self, notice: Dict[str, Any]) -> Optional[List[str]]:
        """Process a single notice and return row data if valid."""
        doc_num = notice.get("document_number")
        if not doc_num:
            return None
            
        # Get comment close date
        comment_url = f"https://www.federalregister.gov/api/v1/documents/{doc_num}.json?fields[]=comments_close_on"
        try:
            comment_data = req.get(comment_url).json()
            final_comment_date = comment_data.get("comments_close_on")
        except Exception as e:
            self.logger.log(f"Error fetching comment data for {doc_num}: {e}", level="ERROR")
            return None
        
        # Format dates
        pub_date = self._format_date(notice.get("publication_date", ""))
        if final_comment_date:
            final_comment_date = self._format_date(final_comment_date)
        
        na = NoticeAnalyzer(doc_num)
        agency = na.getAgency()
        body = na.getText()
        
        print(notice.get('abstract'))
        if notice.get("abstract"):
            summary = self.env.chat(f"Summarize the following notice in 1-2 sentences: {notice.get("abstract")}")
        else:
            summary = self.env.chat("Summarize the following notice in 1-2 sentences: {body}")
            
        summary.replace("Here is a summary of the notice in 1-2 sentences:", "")

        if final_comment_date.lower() != "none":
            commentEndDate = final_comment_date
        else:
            commentEndDate = self.env.chat(f"What is the comment end date for the following notice? Return only the date with nothing else. Format is MM/DD/YYYY. Remember it is after the publication date {pub_date}. If it cannot be found, simply write NONE. DO NOT MAKE UP A FALSE DATE. {body}")
        
        docId = notice.get("document_number")
        
        # Prepare new row
        return [
            notice.get("title", ""),
            agency,
            pub_date,
            f"{pub_date} - {commentEndDate}" if commentEndDate else pub_date,
            summary,
            notice.get("html_url", ""),
            "",
            notice.get("type", "") , # Docket type
            docId
        ]
    
    def scrape_notices(self, search_terms: List[str], max_notices: int = 5, 
                      docket_type: str = "NOTICE", order: str = "relevance",
                      start_date: str = "2021-01-01") -> None:
        """Scrape federal register notices and add them to the sheet.
        
        Args:
            search_terms: List of terms to search for
            max_notices: Maximum number of notices to add
            docket_type: Type of docket to search for
            order: Sort order for results
            start_date: Start date for search (YYYY-MM-DD)
        """
        existing_ids = set(self._get_existing_document_ids())
        added_count = 0
        
        for term in search_terms:
            if added_count >= max_notices:
                break
                
            url = (
                f"https://www.federalregister.gov/api/v1/documents.json?"
                f"per_page={max_notices}&order={order}&conditions[term]={term}"
                f"&conditions[publication_date][gte]={start_date}&conditions[type]={docket_type}"
            )
            
            try:
                response = req.get(url)
                response.raise_for_status()
                data = response.json()
                notices = data.get("results", [])
                
                # Filter for relevant notices
                relevant_notices = [
                    n for n in notices 
                    if any(term in n.get("title", "").lower() 
                          for term in self.SEARCH_TERMS)
                    and n.get("document_number") not in existing_ids
                ]
                
                # Process and add notices
                for notice in relevant_notices:
                    if added_count >= max_notices:
                        break
                        
                    row_data = self._process_notice(notice)
                    if row_data:
                        self.sheet.append_row(row_data)
                        existing_ids.add(notice["document_number"])
                        added_count += 1
                        self.logger.log(f"Added notice: {notice.get('title', '')}")
                        
            except Exception as e:
                self.logger.log(f"Error processing term '{term}': {e}", level="ERROR")
                continue
    
    @classmethod
    def get_user_input(cls) -> dict:
        """Get user input for scraping parameters."""
        print("Federal Register Notice Scraper")
        print("-" * 30)
        
        # Get search terms
        terms_input = input("Enter terms to search (comma-separated, or leave empty for default): ")
        if terms_input.strip():
            terms = [t.strip() for t in terms_input.split(",")]
        else:
            terms = cls.DEFAULT_TERMS
        
        # Get other parameters
        max_notices = input("Maximum number of notices to add (default: 5): ") or "5"
        docket_type = input("Docket type (default: NOTICE): ") or "NOTICE"
        order = input("Sort order (relevance, newest, oldest; default: relevance): ") or "relevance"
        start_date = input("Start date (YYYY-MM-DD; default: 2021-01-01): ") or "2021-01-01"
        
        return {
            "search_terms": terms,
            "max_notices": int(max_notices),
            "docket_type": docket_type.upper(),
            "order": order.lower(),
            "start_date": start_date
        }


def main():
    # Load environment variables from .env file
    env = Environment()
    
    try:
        # Initialize scraper
        print(f"Connecting to spreadsheet: {env.spreadsheet_url}")
        scraper = FederalRegisterScraper(env)
        
        # Get user input
        params = FederalRegisterScraper.get_user_input()
        
        # Run the scraper
        print("\nStarting to scrape notices...")
        scraper.scrape_notices(**params)
        
        print("\nScraping completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if 'scraper' in locals():
            scraper.logger.log(f"Fatal error: {e}", level="ERROR")


if __name__ == "__main__":
    main()