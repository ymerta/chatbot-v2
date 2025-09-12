"""
Netmera Documentation Scraper

This script scrapes all user-facing documentation pages from the Netmera User Guide sidebar and saves the cleaned
text content of each page into individual .txt files. Each file includes the source URL for traceability.

Steps:
1. Fetch all sidebar links under /netmera-user-guide/
2. Extract only the main readable content of each page
3. Clean the text by removing navigation, update info, and UI noise
4. Save as plain text files with structured filenames

Output:
- Text files saved under `data/documents/`, prefixed with `netmera-user-guide-`
- Each file begins with `[SOURCE_URL]: <url>` as the first line
"""
import requests
from bs4 import BeautifulSoup
import os
import time 

BASE_URL = "https://user.netmera.com"
START_PAGE = f"{BASE_URL}/netmera-user-guide/"
SAVE_FOLDER = "data/dev"

os.makedirs(SAVE_FOLDER, exist_ok=True)

GUIDES = [
    {
        "name": "user-guide",
        "start_page": f"{BASE_URL}/netmera-user-guide/",
        "path_prefix": "/netmera-user-guide",
        "file_prefix": "netmera-user-guide-",
    },
    {
        "name": "developer-guide",
        "start_page": f"{BASE_URL}/netmera-developer-guide/",
        "path_prefix": "/netmera-developer-guide",
        "file_prefix": "netmera-developer-guide-",
    },
]

# İsteklerde 403 riskini azaltmak için basit bir User-Agent
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Documentation Scraper; +https://user.netmera.com)"
}


def get_all_sidebar_links(start_page: str, path_prefix: str) -> list[str]:
    """
    Verilen başlangıç sayfasındaki <aside> içinde, belirtilen path_prefix ile
    başlayan tüm dahili linkleri listeler.
    """
    resp = requests.get(start_page, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for a in soup.select("aside a[href]"):
        href = a["href"].strip()
        # Sadece aynı site içindeki ilgili rehber yollarını al
        if href.startswith(path_prefix) and "http" not in href:
            links.add(f"{BASE_URL}{href}")

    return sorted(links)

def get_main_content(html):
    """
    Extracts the main content block from a documentation HTML page while preserving code block formatting.
    Handles <pre>, <code>, and other code elements specially to maintain structure.

    Args:
        html (str): Raw HTML content of the page.

    Returns:
        str: Extracted text content with preserved code formatting.
    """
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article") or soup
    
    # Find all code blocks and preserve their formatting
    code_blocks = main.find_all(['pre', 'code'])
    code_placeholders = {}
    
    # Replace code blocks with placeholders to preserve their formatting
    for i, code_block in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        
        # Extract text from code block while preserving whitespace and structure
        if code_block.name == 'pre':
            # For <pre> blocks, preserve all whitespace and line breaks
            code_text = code_block.get_text()
            # Ensure proper indentation (add 4 spaces to each line for readability)
            indented_lines = []
            for line in code_text.splitlines():
                if line.strip():  # Don't indent empty lines
                    indented_lines.append("    " + line)
                else:
                    indented_lines.append("")
            code_placeholders[placeholder] = "\n".join(indented_lines)
        else:
            # For inline <code> elements, preserve content but make it stand out
            code_text = code_block.get_text()
            code_placeholders[placeholder] = f"`{code_text}`"
        
        # Replace the code block with placeholder
        code_block.replace_with(placeholder)
    
    # Extract text normally from the rest of the content
    text = main.get_text(separator="\n").strip()
    
    # Restore code blocks with preserved formatting
    for placeholder, formatted_code in code_placeholders.items():
        text = text.replace(placeholder, formatted_code)
    
    return text

REMOVE_PHRASES = [
    "Netmera User Guide","Netmera Developer Guide", "Ctrl", "K", "Netmera Docs", "More", "⚡",
    "Was this helpful?", "Copy", "Previous", "Next", "Last updated",
    "On this page"
]

def clean_text(text):
    """
    Cleans the extracted page text by removing unwanted boilerplate phrases and short lines.

    Args:
        text (str): Raw text extracted from HTML.

    Returns:
        str: Cleaned, line-separated text suitable for embedding and retrieval.
    """
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(p in line for p in REMOVE_PHRASES):
            continue
        if len(line) <= 2:
            continue  
        cleaned.append(line)

    return "\n".join(cleaned)

def url_to_filename(url: str, file_prefix: str) -> str:
    """
    URL'yi dosya adına çevirir ve ilgili rehbere göre prefix ekler.
    """
    # netmera-*-guide/ sonrası path'i çıkar
    # Ör: https://user.netmera.com/netmera-developer-guide/sdk/ios
    # -> "sdk/ios"  -> "netmera-developer-guide-sdk-ios.txt"
    if "/netmera-user-guide/" in url:
        path = url.split("/netmera-user-guide/", 1)[1]
    elif "/netmera-developer-guide/" in url:
        path = url.split("/netmera-developer-guide/", 1)[1]
    else:
        # Beklenmeyen durum için son segmentleri kullan
        path = url.replace(BASE_URL, "").strip("/")

    safe = path.replace("/", "-").strip("-")
    return f"{file_prefix}{safe}.txt"

def fetch(url: str) -> str:
    """
    Basit fetch + küçük bekleme (rate-limit'e saygı).
    """
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(0.3)  # nazikçe
    return r.text

def scrape_and_save():
    total_pages = 0
    for guide in GUIDES:
        print(f"\n📚 {guide['name']} taranıyor: {guide['start_page']}")
        links = get_all_sidebar_links(guide["start_page"], guide["path_prefix"])
        print(f"✅ {len(links)} sayfa bulundu. İndiriliyor...")

        for url in links:
            try:
                html = fetch(url)
                raw_text = get_main_content(html)
                cleaned_text = clean_text(raw_text)
                filename = url_to_filename(url, guide["file_prefix"])
                out_path = os.path.join(SAVE_FOLDER, filename)

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"[SOURCE_URL]: {url}\n")
                    f.write(cleaned_text)

                total_pages += 1
                print(f"Kaydedildi: {filename}")
            except Exception as e:
                print(f"Hata ({url}): {e}")

    print(f"\n🏁 Bitti. Toplam {total_pages} sayfa kaydedildi.")

if __name__ == "__main__":
    scrape_and_save()