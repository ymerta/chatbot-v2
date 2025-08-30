import os
import re
import glob
from typing import List, Dict
from dotenv import load_dotenv

# LangChain
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Proje config
from src.config import FAISS_STORE_PATH, BASE_DOC_URL, DATA_DIR


load_dotenv()

# ----------------------------
# 0) Yol ayarları
# ----------------------------
SCRAPER_SAVE_DIR = os.path.join(DATA_DIR, "dev")
CHUNKS_DIR       = os.path.join(DATA_DIR, "chunks")  

os.makedirs(SCRAPER_SAVE_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)

# ----------------------------
# 1) (Opsiyonel) Inline scraper
#    - Eğer scraper’ı ayrı script olarak çalıştırmak istiyorsan bu bloğu kullanma;
#      doğrudan “python scraper.py” çalıştırırsın.
#    - Aşağıdaki fonksiyon, senin paylaştığın scraper kodunun birebir aynısıdır
#      ve gerekirse burada da çalıştırılabilir.
# ----------------------------
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://user.netmera.com"

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

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Documentation Scraper; +https://user.netmera.com)"
}

REMOVE_PHRASES = [
    "Netmera User Guide","Netmera Developer Guide", "Ctrl", "K", "Netmera Docs", "More", "⚡",
    "Was this helpful?", "Copy", "Previous", "Next", "Last updated",
    "On this page"
]



def get_all_sidebar_links(start_page: str, path_prefix: str) -> list[str]:
    resp = requests.get(start_page, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    for a in soup.select("aside a[href]"):
        href = a["href"].strip()
        if href.startswith(path_prefix) and "http" not in href:
            links.add(f"{BASE_URL}{href}")
    return sorted(links)

def get_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article")
    return (main or soup).get_text(separator="\n").strip()

def clean_text(text: str) -> str:
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
    if "/netmera-user-guide/" in url:
        path = url.split("/netmera-user-guide/", 1)[1]
    elif "/netmera-developer-guide/" in url:
        path = url.split("/netmera-developer-guide/", 1)[1]
    else:
        path = url.replace(BASE_URL, "").strip("/")
    safe = path.replace("/", "-").strip("-")
    return f"{file_prefix}{safe}.txt"

def fetch(url: str) -> str:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(0.3)
    return r.text

def scrape_if_needed(force: bool = False) -> None:
    """
    data/dev boşsa (veya force=True) tüm sayfaları indirir.
    """
    existing = glob.glob(os.path.join(SCRAPER_SAVE_DIR, "*.txt"))
    if existing and not force:
        print(f"🟢 Mevcut {len(existing)} dosya var; scrape atlanıyor. (force=True ile zorlayabilirsin)")
        return

    os.makedirs(SCRAPER_SAVE_DIR, exist_ok=True)
    total = 0
    for guide in GUIDES:
        print(f"\n📚 {guide['name']} taranıyor: {guide['start_page']}")
        links = get_all_sidebar_links(guide["start_page"], guide["path_prefix"])
        print(f"✅ {len(links)} sayfa bulundu. İndiriliyor...")

        for url in links:
            try:
                html = fetch(url)
                raw_text = get_main_content(html)
                cleaned = clean_text(raw_text)
                filename = url_to_filename(url, guide["file_prefix"])
                out_path = os.path.join(SCRAPER_SAVE_DIR, filename)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"[SOURCE_URL]: {url}\n")
                    f.write(cleaned)
                total += 1
                print(f"Kaydedildi: {filename}")
            except Exception as e:
                print(f"Hata ({url}): {e}")
    print(f"\n🏁 Bitti. Toplam {total} sayfa kaydedildi.")

# ----------------------------
# 2) Loader: scraper çıktılarını oku
# ----------------------------
SOURCE_LINE_RE = re.compile(r"^\[SOURCE_URL\]:\s*(?P<url>\S+)\s*$", flags=re.IGNORECASE)

def load_scraped_documents() -> List[Dict]:
    """
    data/dev altındaki .txt dosyalarını okur.
    Her dosyanın ilk satırı [SOURCE_URL]: ... olmalı.
    Dönen: [{"text": ..., "source": <filename>, "url": <url>}, ...]
    """
    docs = []
    for path in glob.glob(os.path.join(SCRAPER_SAVE_DIR, "*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        url = None
        body_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                m = SOURCE_LINE_RE.match(line.strip())
                if m:
                    url = m.group("url")
                    continue  # ilk satırı gövdeye katma
            body_lines.append(line)

        text = "\n".join(body_lines).strip()
        if not url:
            # URL bulunamazsa dosya adına göre tahmin et (fallback)
            name = os.path.basename(path)[:-4]
            if name.startswith("netmera-user-guide-"):
                url = f"{BASE_DOC_URL}/netmera-user-guide/{name[len('netmera-user-guide-'):].replace('-', '/')}"
            elif name.startswith("netmera-developer-guide-"):
                url = f"{BASE_DOC_URL}/netmera-developer-guide/{name[len('netmera-developer-guide-'):].replace('-', '/')}"
            else:
                url = f"{BASE_DOC_URL}/{name.replace('-', '/')}"

        docs.append({
            "text": text,
            "source": os.path.basename(path),
            "url": url
        })
    return docs

# ----------------------------
# 3) Split → Embedding → FAISS store
# ----------------------------
def split_docs(texts: List[Dict]) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = []
    for t in texts:
        for ch in splitter.split_text(t["text"]):
            chunks.append({"text": ch, "source": t["source"], "url": t["url"]})
    return chunks

def build_faiss(chunks: List[Dict]) -> None:
    emb = OpenAIEmbeddings()
    lc_texts   = [c["text"] for c in chunks]
    lc_meta    = [{"source": c["source"], "url": c["url"]} for c in chunks]

    vs = FAISS.from_texts(texts=lc_texts, embedding=emb, metadatas=lc_meta)
    vs.save_local(FAISS_STORE_PATH)
    print(f"✅ FAISS store kaydedildi: {FAISS_STORE_PATH} (toplam {len(chunks)} chunk)")

def save_chunks_to_disk(chunks: List[Dict]) -> None:
    # Debug/inceleme için her chunk’ı ayrı txt olarak kaydet (opsiyonel)
    for i, c in enumerate(chunks):
        out = os.path.join(CHUNKS_DIR, f"{i:06d}.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"[SOURCE_URL]: {c['url']}\n[SOURCE_FILE]: {c['source']}\n\n{c['text']}")

# ----------------------------
# 4) Main
# ----------------------------
def main(force_scrape: bool = False, save_chunk_files: bool = False):
    # 1) Gerekirse scrape et
      
 

    # <<< DİZİNLERİ BURADA OLUŞTUR >>>
    os.makedirs(os.path.dirname(FAISS_STORE_PATH), exist_ok=True)
    SCRAPER_SAVE_DIR = os.path.join(DATA_DIR, "dev")
    CHUNKS_DIR       = os.path.join(DATA_DIR, "chunks")
    os.makedirs(SCRAPER_SAVE_DIR, exist_ok=True)
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    scrape_if_needed(force=force_scrape)

    # 2) Dosyaları oku
    base_texts = load_scraped_documents()
    if not base_texts:
        print("⚠️ data/dev altında doküman bulunamadı. Scraper’ı kontrol et.")
        return

    # 3) Split
    chunks = split_docs(base_texts)

    # (opsiyonel) chunk dosyalarını diske dök
    if save_chunk_files:
        save_chunks_to_disk(chunks)

    # 4) FAISS’i inşa et
    build_faiss(chunks)

if __name__ == "__main__":
    # İlk denemede force_scrape=True ile tüm sayfaları indir,
    # sonraki çalıştırmalarda False bırakıp sadece index’i güncelle.
    main(force_scrape=False, save_chunk_files=False)