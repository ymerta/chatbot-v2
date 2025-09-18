#!/usr/bin/env python3
"""
Netmera Documentation Web Scraper
Sadece web scraping işlemi için - FAISS indexing'den ayrı
"""

import os
import re
import glob
import time
import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv

# Proje config
from config import BASE_DOC_URL, DATA_DIR

load_dotenv()

# Directories
SCRAPER_SAVE_DIR = os.path.join(DATA_DIR, "dev")
os.makedirs(SCRAPER_SAVE_DIR, exist_ok=True)

# Configuration
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
    "Netmera User Guide", "Netmera Developer Guide", "Ctrl", "K", "Netmera Docs", 
    "More", "⚡", "Was this helpful?", "Copy", "Previous", "Next", "Last updated",
    "On this page"
]

def get_all_sidebar_links(start_page: str, path_prefix: str) -> List[str]:
    """Sidebar'dan tüm link'leri topla"""
    print(f"   Sayfa analiz ediliyor: {start_page}")
    resp = requests.get(start_page, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    
    for a in soup.select("aside a[href]"):
        href = a["href"].strip()
        if href.startswith(path_prefix) and "http" not in href:
            links.add(f"{BASE_URL}{href}")
    
    print(f"   {len(links)} link bulundu")
    return sorted(links)

def get_main_content(html: str) -> str:
    """
    Ana içeriği çıkar - basit metin çıkarma
    """
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article") or soup
    
    # Basit metin çıkarma
    text = main.get_text(separator="\n").strip()
    
    return text

def clean_text(text: str) -> str:
    """Metni temizle - gereksiz satırları kaldır"""
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
    """URL'den dosya adı oluştur"""
    if "/netmera-user-guide/" in url:
        path = url.split("/netmera-user-guide/", 1)[1]
    elif "/netmera-developer-guide/" in url:
        path = url.split("/netmera-developer-guide/", 1)[1]
    else:
        path = url.replace(BASE_URL, "").strip("/")
    
    safe = path.replace("/", "-").strip("-")
    return f"{file_prefix}{safe}.txt"

def fetch_page(url: str) -> str:
    """Tek bir sayfayı indir"""
    print(f"     İndiriliyor: {url}")
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(0.3)  # Rate limiting
    return r.text

def scrape_guide(guide_config: dict) -> int:
    """Tek bir guide'ı scrape et"""
    print(f"\n📚 {guide_config['name']} scraping başlıyor...")
    print(f"   Start page: {guide_config['start_page']}")
    
    # Link'leri topla
    links = get_all_sidebar_links(guide_config["start_page"], guide_config["path_prefix"])
    
    if not links:
        print("   ⚠️ Hiç link bulunamadı!")
        return 0
    
    print(f"   ✅ {len(links)} sayfa bulundu, indirme başlıyor...")
    
    # Her sayfayı indir
    success_count = 0
    for i, url in enumerate(links, 1):
        try:
            # İçeriği indir
            html = fetch_page(url)
            raw_text = get_main_content(html)
            cleaned = clean_text(raw_text)
            
            # Dosya adı oluştur ve kaydet
            filename = url_to_filename(url, guide_config["file_prefix"])
            out_path = os.path.join(SCRAPER_SAVE_DIR, filename)
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"[SOURCE_URL]: {url}\n")
                f.write(cleaned)
            
            success_count += 1
            print(f"     ✅ [{i}/{len(links)}] {filename}")
            
        except Exception as e:
            print(f"     ❌ [{i}/{len(links)}] Hata ({url}): {e}")
    
    print(f"   📊 {guide_config['name']}: {success_count}/{len(links)} sayfa başarılı")
    return success_count

def check_existing_files() -> dict:
    """Mevcut dosyaları kontrol et"""
    existing_files = glob.glob(os.path.join(SCRAPER_SAVE_DIR, "*.txt"))
    
    stats = {
        "total_files": len(existing_files),
        "user_guide_files": len([f for f in existing_files if "user-guide" in f]),
        "developer_guide_files": len([f for f in existing_files if "developer-guide" in f]),
        "files": [os.path.basename(f) for f in existing_files]
    }
    
    return stats

def main(force_scrape: bool = False, guides_to_scrape: List[str] = None):
    """
    Ana scraping function
    
    Args:
        force_scrape: Mevcut dosyalar varsa bile yeniden scrape et
        guides_to_scrape: Sadece belirli guide'ları scrape et (None = hepsi)
    """
    print("🕷️  Netmera Documentation Web Scraper")
    print("=" * 50)
    
    # Mevcut dosyaları kontrol et
    existing_stats = check_existing_files()
    print(f"📁 Mevcut dosyalar: {existing_stats['total_files']}")
    print(f"   User Guide: {existing_stats['user_guide_files']} dosya")
    print(f"   Developer Guide: {existing_stats['developer_guide_files']} dosya")
    
    if existing_stats['total_files'] > 0 and not force_scrape:
        print("\n🟢 Mevcut dosyalar bulundu. Scraping atlanıyor.")
        print("   Yeniden scrape etmek için --force kullanın")
        return existing_stats
    
    if force_scrape and existing_stats['total_files'] > 0:
        print(f"\n🔄 Force mode: {existing_stats['total_files']} mevcut dosya silinecek")
        for f in glob.glob(os.path.join(SCRAPER_SAVE_DIR, "*.txt")):
            os.remove(f)
        print("   ✅ Mevcut dosyalar temizlendi")
    
    # Scraping başlat
    print(f"\n🚀 Scraping başlıyor...")
    total_scraped = 0
    
    guides_to_process = GUIDES
    if guides_to_scrape:
        guides_to_process = [g for g in GUIDES if g["name"] in guides_to_scrape]
        print(f"   Sadece şu guide'lar işlenecek: {guides_to_scrape}")
    
    for guide in guides_to_process:
        scraped_count = scrape_guide(guide)
        total_scraped += scraped_count
    
    # Sonuç
    print(f"\n🏁 Scraping tamamlandı!")
    print(f"   Toplam indirilen sayfa: {total_scraped}")
    print(f"   Dosyalar kaydedildi: {SCRAPER_SAVE_DIR}")
    
    # Final istatistik
    final_stats = check_existing_files()
    print(f"\n📊 Final istatistikler:")
    print(f"   Toplam dosya: {final_stats['total_files']}")
    print(f"   User Guide: {final_stats['user_guide_files']}")
    print(f"   Developer Guide: {final_stats['developer_guide_files']}")
    
    return final_stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Netmera Documentation Web Scraper")
    parser.add_argument("--force", action="store_true", 
                       help="Mevcut dosyalar varsa bile yeniden scrape et")
    parser.add_argument("--guides", nargs="+", 
                       choices=["user-guide", "developer-guide"],
                       help="Sadece belirli guide'ları scrape et")
    
    args = parser.parse_args()
    
    main(force_scrape=args.force, guides_to_scrape=args.guides)
