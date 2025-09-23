import os
import json
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Configuration ---
# Define the base URL of the website to scrape
BASE_URL = "https://hushbposervices.com"
OUTPUT_FILE = "website_data.json"
# Define a custom User-Agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Set a delay between requests to avoid overwhelming the server
REQUEST_DELAY = 1  # in seconds

# --- Helper Functions ---
def get_page_title(soup):
    """
    Extracts the title from the HTML <title> tag.
    Returns the title as a string or a default if not found.
    """
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        # Clean up the title string (e.g., remove " - Hush BPO Services")
        full_title = title_tag.string.strip()
        # You can add more specific logic here to clean up the titles if needed
        return full_title.split(' - ')[0]
    return "Untitled"

def is_valid_url(url):
    """
    Checks if a URL is a valid, crawlable link within the domain.
    """
    parsed_url = urlparse(url)
    return parsed_url.scheme in ['http', 'https'] and parsed_url.netloc == urlparse(BASE_URL).netloc and not parsed_url.fragment

def get_links_to_crawl(soup, current_url):
    """
    Extracts all valid, unvisited links from a page.
    """
    links = set()
    for anchor in soup.find_all('a', href=True):
        href = anchor.get('href')
        full_url = urljoin(current_url, href)
        if is_valid_url(full_url):
            links.add(full_url)
    return links

# --- Main Scraping Logic ---
def scrape_website_content_crawler():
    """
    Crawl and scrape a website starting from the base URL.
    Returns a list of dictionaries, where each dictionary represents a document.
    """
    scraped_documents = []
    to_visit = [BASE_URL]
    visited_urls = set()

    print(f"Starting crawl from: {BASE_URL}")

    while to_visit:
        full_url = to_visit.pop(0)

        # Skip if already visited to prevent loops
        if full_url in visited_urls:
            continue

        print(f"  -> Scraping page: {full_url}")
        visited_urls.add(full_url)
        
        try:
            response = requests.get(full_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content from the main body, avoiding headers and footers
            main_content = soup.find('main') or soup.find('article') or soup.find('div', {'id': 'content'})
            if main_content:
                page_text = main_content.get_text(separator=' ', strip=True)
            else:
                page_text = soup.get_text(separator=' ', strip=True)
                
            page_title = get_page_title(soup)
            
            # Create a document dictionary
            doc_id = os.path.basename(urlparse(full_url).path.strip('/')) or "home"
            document = {
                "id": doc_id,
                "text": page_text,
                "metadata": {
                    "source": full_url,
                    "title": page_title
                }
            }
            scraped_documents.append(document)
            
            # Discover new links to add to the queue
            new_links = get_links_to_crawl(soup, full_url)
            for link in new_links:
                if link not in visited_urls:
                    to_visit.append(link)

        except requests.exceptions.RequestException as e:
            print(f"Error scraping {full_url}: {e}")
        
        # Add a delay between requests
        time.sleep(REQUEST_DELAY)

    return scraped_documents

# --- Main Execution ---
if __name__ == "__main__":
    content_data = scrape_website_content_crawler()
    
    if content_data:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=4)
            print(f"Successfully scraped {len(content_data)} documents and saved to {OUTPUT_FILE}.")
        except Exception as e:
            print(f"Failed to write to file. Error: {e}")
    else:
        print("No content was scraped. Exiting.")