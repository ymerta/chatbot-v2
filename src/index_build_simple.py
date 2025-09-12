#!/usr/bin/env python3
"""
Basit FAISS Index Builder - Mevcut chunking stratejisini korur
Eski index_build.py'ın basitleştirilmiş hali - sadece FAISS building
"""

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
from config import FAISS_STORE_PATH, BASE_DOC_URL, DATA_DIR

load_dotenv()

# Directories
SCRAPER_SAVE_DIR = os.path.join(DATA_DIR, "dev")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")

os.makedirs(CHUNKS_DIR, exist_ok=True)

# Source line regex
SOURCE_LINE_RE = re.compile(r"^\[SOURCE_URL\]:\s*(?P<url>\S+)\s*$", flags=re.IGNORECASE)

def load_scraped_documents() -> List[Dict]:
    """
    Web scraper'ın çıktılarını yükle
    Eski load_scraped_documents() fonksiyonunun aynısı
    """
    docs = []
    pattern = os.path.join(SCRAPER_SAVE_DIR, "*.txt")
    files = glob.glob(pattern)
    
    if not files:
        print(f"❌ {SCRAPER_SAVE_DIR} klasöründe .txt dosyası bulunamadı!")
        print("   Önce web scraper'ı çalıştırın: python src/web_scraper.py")
        return []
    
    print(f"📁 {len(files)} scraped dosya bulundu, yükleniyor...")
    
    for path in files:
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
    
    print(f"✅ {len(docs)} doküman yüklendi")
    return docs

def split_docs(texts: List[Dict]) -> List[Dict]:
    """
    Eski chunking stratejisi - değişiklik yok
    """
    print("🔧 Dokümanlar chunk'lara bölünüyor...")
    print("   Chunk size: 800, Overlap: 120")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = []
    
    for t in texts:
        splits = splitter.split_text(t["text"])
        for ch in splits:
            chunks.append({
                "text": ch, 
                "source": t["source"], 
                "url": t["url"]
            })
    
    print(f"✅ {len(chunks)} chunk oluşturuldu")
    return chunks

def build_faiss(chunks: List[Dict]) -> None:
    """
    FAISS index'i oluştur - eski versiyonun aynısı
    """
    print(f"🏗️ FAISS index oluşturuluyor...")
    
    # Mevcut FAISS'i backup'la
    if os.path.exists(FAISS_STORE_PATH):
        backup_path = f"{FAISS_STORE_PATH}_backup"
        import shutil
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(FAISS_STORE_PATH, backup_path)
        print(f"💾 Mevcut FAISS backup'landı: {backup_path}")
    
    emb = OpenAIEmbeddings()
    lc_texts = [c["text"] for c in chunks]
    lc_meta = [{"source": c["source"], "url": c["url"]} for c in chunks]

    vs = FAISS.from_texts(texts=lc_texts, embedding=emb, metadatas=lc_meta)
    vs.save_local(FAISS_STORE_PATH)
    
    print(f"✅ FAISS store kaydedildi: {FAISS_STORE_PATH}")
    print(f"   Toplam chunk: {len(chunks)}")

def save_chunks_to_disk(chunks: List[Dict]) -> None:
    """
    Debug/inceleme için chunk'ları kaydet
    """
    print(f"💾 Debug chunk'ları kaydediliyor...")
    
    for i, c in enumerate(chunks):
        out = os.path.join(CHUNKS_DIR, f"{i:06d}.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"[SOURCE_URL]: {c['url']}\n[SOURCE_FILE]: {c['source']}\n\n{c['text']}")
    
    print(f"✅ {len(chunks)} chunk kaydedildi: {CHUNKS_DIR}")

def main(save_chunk_files: bool = False):
    """
    Ana function - sadece FAISS building
    Web scraping kısmı kaldırıldı
    """
    print("🔨 Netmera FAISS Index Builder (Simple)")
    print("=" * 50)
    
    # FAISS dizinini oluştur
    os.makedirs(os.path.dirname(FAISS_STORE_PATH), exist_ok=True)
    
    # 1. Scraped dokümanları yükle
    base_texts = load_scraped_documents()
    if not base_texts:
        print("⚠️  Scraped doküman bulunamadı.")
        print("   Önce web scraper'ı çalıştırın:")
        print("     python src/web_scraper.py")
        return False

    print(f"📊 Toplam doküman: {len(base_texts)}")
    for doc in base_texts:
        print(f"   - {doc['source']} ({len(doc['text'])} karakter)")

    # 2. Chunk'lara böl
    chunks = split_docs(base_texts)

    # 3. (Opsiyonel) chunk dosyalarını diske kaydet
    if save_chunk_files:
        save_chunks_to_disk(chunks)

    # 4. FAISS'i oluştur
    build_faiss(chunks)
    
    print(f"\n🎉 FAISS index başarıyla oluşturuldu!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Netmera Simple FAISS Index Builder")
    parser.add_argument("--save-chunks", action="store_true",
                       help="Debug için chunk dosyalarını kaydet")
    
    args = parser.parse_args()
    
    success = main(save_chunk_files=args.save_chunks)
    
    if not success:
        print("\n❌ İşlem başarısız!")
        exit(1)
