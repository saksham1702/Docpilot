import time
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")

def get_embedding(text: str):
    """Call Modal API to get embedding vector."""
    try:
        resp = requests.post(EMBEDDING_API_URL, json={"text": text}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as e:
        print(f"[ERROR] Embedding API error: {e}")
    return None

def test_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("[OK] Connected to PostgreSQL successfully!")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")

def discover_links(base_url: str, allowed_prefix: str):
    """Discover all documentation links from a page."""
    links = set()
    try:
        resp = requests.get(base_url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)
                # Only include links within the docs section
                if full_url.startswith(allowed_prefix) and "#" not in full_url:
                    links.add(full_url)
    except Exception as e:
        print(f"[ERROR] Link discovery error: {e}")
    return links

def scrape_and_store(url: str, library_name: str):
    """Scrape a documentation URL and store it with embeddings."""
    print(f"[SCRAPE] {url}...")
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            title = soup.title.string if soup.title else "No Title"
            text_content = soup.get_text(separator=" ", strip=True)[:2000]
            
            print(f"[DOC] {title} ({len(text_content)} chars)")
            
            embedding = get_embedding(text_content)
            
            if embedding:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO doc_chunks (content, url, library_name, version, embedding) VALUES (%s, %s, %s, %s, %s)",
                    (text_content, url, library_name, "latest", embedding)
                )
                conn.commit()
                cur.close()
                conn.close()
                print(f"[STORED]")
                return True
        else:
            print(f"[WARN] {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")
    return False

def crawl_docs(start_url: str, library_name: str, allowed_prefix: str, max_pages: int = 50):
    """Crawl all pages starting from a base URL."""
    visited = set()
    to_visit = {start_url}
    count = 0
    
    while to_visit and count < max_pages:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)
        
        if scrape_and_store(url, library_name):
            count += 1
            # Discover more links from this page
            new_links = discover_links(url, allowed_prefix)
            to_visit.update(new_links - visited)
        
        time.sleep(0.5)  # Be polite
    
    print(f"[DONE] Crawled {count} pages for {library_name}")
    return count

def run_worker():
    time.sleep(5)
    test_db_connection()
    
    print("[START] Starting Pathway docs crawl...")
    crawl_docs(
        start_url="https://pathway.com/developers/user-guide/introduction/welcome/",
        library_name="pathway",
        allowed_prefix="https://pathway.com/developers/",
        max_pages=30
    )
    
    print("[DONE] Crawling complete!")
    
    while True:
        print("Worker idle. Sleeping for 300 seconds...")
        time.sleep(300)

if __name__ == "__main__":
    run_worker()
