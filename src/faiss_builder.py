#!/usr/bin/env python3
"""
FAISS Index Builder - Optimized Chunking
Sadece FAISS index oluşturma için - web scraping'den ayrı
"""

import os
import re
import glob
import json
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
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")

os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# Source line regex
SOURCE_LINE_RE = re.compile(r"^\[SOURCE_URL\]:\s*(?P<url>\S+)\s*$", flags=re.IGNORECASE)

def load_scraped_documents() -> List[Dict]:
    """
    Web scraper'ın çıktılarını yükle
    data/dev/ klasöründeki .txt dosyalarını okur
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
                # İlk satırda URL var mı kontrol et
                m = SOURCE_LINE_RE.match(line.strip())
                if m:
                    url = m.group("url")
                    continue  # URL satırını body'e katma
            body_lines.append(line)

        text = "\n".join(body_lines).strip()
        
        if not url:
            # URL bulunamazsa dosya adından tahmin et
            name = os.path.basename(path)[:-4]
            if name.startswith("netmera-user-guide-"):
                url = f"{BASE_DOC_URL}/netmera-user-guide/{name[len('netmera-user-guide-'):].replace('-', '/')}"
            elif name.startswith("netmera-developer-guide-"):
                url = f"{BASE_DOC_URL}/netmera-developer-guide/{name[len('netmera-developer-guide-'):].replace('-', '/')}"
            else:
                url = f"{BASE_DOC_URL}/{name.replace('-', '/')}"

        # Source type'ı belirle
        if "user-guide" in path:
            source_type = "user-guide"
        elif "developer-guide" in path:
            source_type = "developer-guide"
        else:
            source_type = "unknown"

        docs.append({
            "text": text,
            "source": os.path.basename(path),
            "source_type": source_type,
            "url": url,
            "char_count": len(text),
            "word_count": len(text.split())
        })
    
    print(f"✅ {len(docs)} doküman yüklendi")
    return docs

def detect_content_type(text: str) -> str:
    """İçerik tipini tespit et - optimized chunking için"""
    text_lower = text.lower()
    
    # Kod ağırlıklı içerik
    if ("```" in text or 
        "gradle" in text_lower or 
        "implementation" in text_lower or
        "json" in text_lower or
        re.search(r'\{[\s\S]*\}', text) or
        "curl" in text_lower):
        return "code"
    
    # API dokümantasyonu
    if ("api" in text_lower or 
        "endpoint" in text_lower or
        "http" in text_lower or
        "rest" in text_lower):
        return "api"
    
    # Adım adım kılavuzlar
    if (re.search(r'\n\d+\.', text) or
        "adım" in text_lower or
        "step" in text_lower or
        "nasıl" in text_lower):
        return "tutorial"
    
    
    return "general"

def detect_language(text: str) -> str:
    """Dil tespiti - Türkçe vs İngilizce"""
    turkish_chars = set('çğıöşüÇĞIİÖŞÜ')
    has_turkish_chars = any(char in text for char in turkish_chars)
    
    turkish_words = ['ve', 'bir', 'bu', 'için', 'ile', 'olan', 'nasıl', 'nedir', 'kullanım']
    english_words = ['the', 'and', 'or', 'how', 'what', 'with', 'from', 'that', 'this']
    
    text_lower = text.lower()
    turkish_count = sum(1 for word in turkish_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    
    if has_turkish_chars or turkish_count > english_count:
        return "turkish"
    return "english"

def split_docs_optimized(texts: List[Dict], 
                        chunk_size: int = 1200, 
                        chunk_overlap: int = 200) -> List[Dict]:
    """
    Optimized chunking strategy - content-aware splitting
    """
    print(f"🔧 Optimized chunking başlıyor...")
    print(f"   Chunk size: {chunk_size}")
    print(f"   Overlap: {chunk_overlap}")
    
    # Smart separators - yapıyı koruyacak şekilde
    separators = [
        "\n\n\n",      # Major section breaks
        "\n\n",        # Paragraph breaks
        "\n```\n",     # Code block endings
        "```\n",       # Code block starts  
        "\n### ",      # H3 headers
        "\n## ",       # H2 headers
        "\n# ",        # H1 headers
        "\n- ",        # List items
        "\n1. ",       # Numbered lists
        ". ",          # Sentence endings
        "! ",          # Exclamations
        "? ",          # Questions
        "\n",          # Line breaks
        " ",           # Spaces
        ""             # Character level (son çare)
    ]
    
    chunks = []
    stats = {
        "total_docs": len(texts),
        "content_type_distribution": {},
        "chunks_by_source": {},
        "size_distribution": []
    }
    
    for doc in texts:
        print(f"   📄 İşleniyor: {doc['source']} ({doc['char_count']} char)")
        
        # İçerik tipini tespit et
        content_type = detect_content_type(doc["text"])
        language = detect_language(doc["text"])
        
        # İçerik tipine göre chunk size ayarla
        if content_type == "code":
            # Kod için daha büyük chunk'lar
            adjusted_size = min(2000, int(chunk_size * 1.5))
            adjusted_overlap = min(300, int(chunk_overlap * 1.5))
        elif content_type == "api":
            # API docs için orta büyüklük
            adjusted_size = int(chunk_size * 1.2)
            adjusted_overlap = int(chunk_overlap * 1.2)
        elif content_type == "tutorial":
            # Tutorial için adımları bir arada tut
            adjusted_size = int(chunk_size * 1.3)
            adjusted_overlap = int(chunk_overlap * 1.1)
        else:
            adjusted_size = chunk_size
            adjusted_overlap = chunk_overlap
        
        # Text splitter oluştur
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=adjusted_size,
            chunk_overlap=adjusted_overlap,
            separators=separators,
            keep_separator=True,
            is_separator_regex=False
        )
        
        # Metni böl
        splits = splitter.split_text(doc["text"])
        
        for i, chunk_text in enumerate(splits):
            # Çok küçük chunk'ları atla (önemli keyword'ler yoksa)
            if len(chunk_text.strip()) < 100:
                important_keywords = ["api", "sdk", "implementation", "gradle", "netmera", "error"]
                if not any(keyword in chunk_text.lower() for keyword in important_keywords):
                    continue
            
            # Header'ları çıkar
            headers = re.findall(r'^#{1,6}\s+(.+)$', chunk_text, re.MULTILINE)
            
            # Kod dillerini tespit et
            code_languages = re.findall(r'```(\w+)', chunk_text)
            
            # Teknik terimler
            tech_terms = []
            netmera_terms = ["push notification", "segment", "campaign", "sdk", "api", 
                           "analytics", "automation", "journey", "gradle", "implementation"]
            
            chunk_lower = chunk_text.lower()
            for term in netmera_terms:
                if term in chunk_lower:
                    tech_terms.append(term)
            
            chunk_data = {
                "text": chunk_text.strip(),
                "source": doc["source"],
                "source_type": doc["source_type"],
                "url": doc["url"],
                "chunk_index": i,
                "total_chunks_in_doc": len(splits),
                "content_type": content_type,
                "language": language,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "has_code": "```" in chunk_text,
                "has_steps": bool(re.search(r'\n\d+\.', chunk_text)),
                "headers": headers,
                "code_languages": code_languages,
                "tech_terms": tech_terms
            }
            
            chunks.append(chunk_data)
        
        # İstatistikleri güncelle
        source = doc["source"]
        stats["chunks_by_source"][source] = stats["chunks_by_source"].get(source, 0) + len(splits)
        stats["content_type_distribution"][content_type] = \
            stats["content_type_distribution"].get(content_type, 0) + len(splits)
    
    # Final istatistikler
    stats["total_chunks"] = len(chunks)
    stats["size_distribution"] = [c["char_count"] for c in chunks]
    avg_size = sum(stats["size_distribution"]) / len(stats["size_distribution"])
    
    print(f"\n📊 Chunking sonuçları:")
    print(f"   Toplam chunk: {stats['total_chunks']}")
    print(f"   Ortalama boyut: {avg_size:.0f} karakter")
    print(f"   Boyut aralığı: {min(stats['size_distribution'])} - {max(stats['size_distribution'])}")
    
    print(f"\n🏷️ İçerik tipi dağılımı:")
    for content_type, count in stats["content_type_distribution"].items():
        percentage = (count / stats["total_chunks"]) * 100
        print(f"   {content_type}: {count} chunk ({percentage:.1f}%)")
    
    # İstatistikleri kaydet
    analysis_file = os.path.join(ANALYSIS_DIR, "chunking_analysis.json")
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"📈 Analiz kaydedildi: {analysis_file}")
    
    return chunks

def build_faiss(chunks: List[Dict], backup_existing: bool = True) -> None:
    """FAISS index'i oluştur"""
    print(f"\n🏗️ FAISS index oluşturuluyor...")
    
    # Mevcut FAISS'i backup'la
    if backup_existing and os.path.exists(FAISS_STORE_PATH):
        backup_path = f"{FAISS_STORE_PATH}_backup"
        import shutil
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(FAISS_STORE_PATH, backup_path)
        print(f"💾 Mevcut FAISS backup'landı: {backup_path}")
    
    # FAISS için verileri hazırla
    emb = OpenAIEmbeddings()
    texts = [chunk["text"] for chunk in chunks]
    metadatas = []
    
    for chunk in chunks:
        # FAISS için metadata'yı flatten et
        metadata = {
            "source": chunk["source"],
            "source_type": chunk["source_type"],
            "url": chunk["url"],
            "content_type": chunk["content_type"],
            "language": chunk["language"],
            "char_count": chunk["char_count"],
            "word_count": chunk["word_count"],
            "has_code": chunk["has_code"],
            "has_steps": chunk["has_steps"],
            "tech_terms": ",".join(chunk["tech_terms"]),
            "headers": ",".join(chunk["headers"]),
            "code_languages": ",".join(chunk["code_languages"])
        }
        metadatas.append(metadata)
    
    # FAISS vectorstore oluştur
    print(f"🚀 {len(chunks)} chunk için embedding'ler oluşturuluyor...")
    vs = FAISS.from_texts(texts=texts, embedding=emb, metadatas=metadatas)
    vs.save_local(FAISS_STORE_PATH)
    
    print(f"✅ FAISS index kaydedildi: {FAISS_STORE_PATH}")
    print(f"   Toplam chunk: {len(chunks)}")
    print(f"   Index boyutu: {get_faiss_size()}")

def get_faiss_size() -> str:
    """FAISS index boyutunu hesapla"""
    try:
        index_file = os.path.join(FAISS_STORE_PATH, "index.faiss")
        pkl_file = os.path.join(FAISS_STORE_PATH, "index.pkl")
        
        if os.path.exists(index_file) and os.path.exists(pkl_file):
            index_size = os.path.getsize(index_file)
            pkl_size = os.path.getsize(pkl_file)
            total_size = index_size + pkl_size
            
            if total_size > 1024*1024:
                return f"{total_size/(1024*1024):.1f} MB"
            else:
                return f"{total_size/1024:.1f} KB"
        return "Unknown"
    except:
        return "Unknown"

def save_chunks_debug(chunks: List[Dict], save_limit: int = 50) -> None:
    """Debug için chunk'ları diske kaydet"""
    debug_dir = os.path.join(CHUNKS_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    chunks_to_save = chunks[:save_limit] if save_limit else chunks
    
    for i, chunk in enumerate(chunks_to_save):
        filename = f"{i:06d}_{chunk['content_type']}_{chunk['language']}.txt"
        filepath = os.path.join(debug_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"[METADATA]\n")
            f.write(f"Source: {chunk['source']}\n")
            f.write(f"URL: {chunk['url']}\n")
            f.write(f"Content Type: {chunk['content_type']}\n")
            f.write(f"Language: {chunk['language']}\n")
            f.write(f"Char Count: {chunk['char_count']}\n")
            f.write(f"Has Code: {chunk['has_code']}\n")
            f.write(f"Tech Terms: {', '.join(chunk['tech_terms'])}\n")
            f.write(f"Headers: {', '.join(chunk['headers'])}\n")
            f.write("\n" + "="*60 + "\n\n")
            f.write(chunk['text'])
    
    print(f"🔍 Debug: {len(chunks_to_save)} chunk kaydedildi: {debug_dir}")

def main(chunk_size: int = 1200, 
         chunk_overlap: int = 200,
         backup_existing: bool = True,
         save_debug_chunks: bool = False):
    """
    Ana FAISS builder function
    
    Args:
        chunk_size: Hedef chunk boyutu
        chunk_overlap: Chunk'lar arası overlap
        backup_existing: Mevcut FAISS'i backup'la
        save_debug_chunks: Debug için chunk'ları kaydet
    """
    print("🔨 Netmera FAISS Index Builder")
    print("=" * 50)
    
    # FAISS dizinini oluştur
    os.makedirs(os.path.dirname(FAISS_STORE_PATH), exist_ok=True)
    
    # 1. Scraped dokümanlari yükle
    docs = load_scraped_documents()
    if not docs:
        return False
    
    # 2. Optimized chunking
    chunks = split_docs_optimized(docs, chunk_size, chunk_overlap)
    if not chunks:
        print("❌ Hiç chunk oluşturulamadı!")
        return False
    
    # 3. Debug chunks'ları kaydet (opsiyonel)
    if save_debug_chunks:
        save_chunks_debug(chunks)
    
    # 4. FAISS index'i oluştur
    build_faiss(chunks, backup_existing)
    
    print(f"\n🎉 FAISS index başarıyla oluşturuldu!")
    print(f"   Chunk parametreleri: size={chunk_size}, overlap={chunk_overlap}")
    print(f"   Toplam chunk: {len(chunks)}")
    print(f"   Index path: {FAISS_STORE_PATH}")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Netmera FAISS Index Builder")
    parser.add_argument("--chunk-size", type=int, default=1200,
                       help="Chunk boyutu (default: 1200)")
    parser.add_argument("--chunk-overlap", type=int, default=200,
                       help="Chunk overlap (default: 200)")
    parser.add_argument("--no-backup", action="store_true",
                       help="Mevcut FAISS'i backup'lama")
    parser.add_argument("--save-debug", action="store_true",
                       help="Debug için chunk'ları kaydet")
    
    args = parser.parse_args()
    
    success = main(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        backup_existing=not args.no_backup,
        save_debug_chunks=args.save_debug
    )
    
    if not success:
        print("\n❌ FAISS index oluşturulamadı!")
        print("   Önce web scraper'ı çalıştırın: python src/web_scraper.py")
        exit(1)
