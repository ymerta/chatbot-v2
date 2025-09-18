#!/usr/bin/env python3
"""
FAISS Store'u template olmadan yeniden oluştur
"""

import os
import sys
import pickle
from typing import List, Dict
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    import faiss
    import numpy as np
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Make sure you have the required packages installed")
    sys.exit(1)

# Configuration
SCRAPED_DATA_DIR = "data/dev"
FAISS_STORE_PATH = "data/embeddings/faiss_store"

def load_documents() -> List[Dict]:
    """Load all scraped documents"""
    print(f"📂 Loading documents from {SCRAPED_DATA_DIR}...")
    
    if not os.path.exists(SCRAPED_DATA_DIR):
        print(f"❌ {SCRAPED_DATA_DIR} directory not found!")
        return []
    
    docs = []
    files = [f for f in os.listdir(SCRAPED_DATA_DIR) if f.endswith('.txt')]
    total_files = len(files)
    
    print(f"📊 Found {total_files} text files")
    
    for i, filename in enumerate(files):
        file_path = os.path.join(SCRAPED_DATA_DIR, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                continue
            
            # Extract URL from first line if it exists
            lines = content.split('\n')
            url = None
            text_start_idx = 0
            
            if lines and lines[0].startswith('[SOURCE_URL]:'):
                url = lines[0].replace('[SOURCE_URL]:', '').strip()
                text_start_idx = 1
            
            # Get the actual content (NO CODE FORMATTING)
            actual_content = '\n'.join(lines[text_start_idx:]).strip()
            
            if actual_content:
                docs.append({
                    "text": actual_content,
                    "source": filename,
                    "url": url
                })
                
        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")
        
        if (i + 1) % 50 == 0:
            print(f"  📖 Processed {i + 1}/{total_files} files")
    
    print(f"✅ Loaded {len(docs)}/{total_files} documents successfully")
    return docs

def chunk_documents(docs: List[Dict]) -> List[Dict]:
    """Split documents into chunks - NO CODE FORMATTING"""
    print("✂️ Chunking documents...")
    
    # Simple separators - NO CODE BLOCK SEPARATORS
    separators = [
        "\n\n",        # Paragraph breaks
        "\n",          # Line breaks
        " ",           # Spaces
        ""             # Character level
    ]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=separators,
        keep_separator=True
    )
    
    chunks = []
    total_docs = len(docs)
    
    for i, doc in enumerate(docs):
        try:
            # Split the text (NO SPECIAL PROCESSING)
            splits = splitter.split_text(doc["text"])
            
            for j, chunk_text in enumerate(splits):
                if len(chunk_text.strip()) < 50:  # Skip very small chunks
                    continue
                    
                chunks.append({
                    "text": chunk_text.strip(),
                    "source": doc["source"], 
                    "url": doc.get("url"),
                    "chunk_id": f"{doc['source']}_chunk_{j}"
                })
                
        except Exception as e:
            print(f"⚠️ Error chunking {doc['source']}: {e}")
        
        if (i + 1) % 50 == 0:
            print(f"  ✂️ Processed {i + 1}/{total_docs} documents")
    
    print(f"✅ Created {len(chunks)} chunks from {total_docs} documents")
    return chunks

def build_faiss_index(chunks: List[Dict]) -> bool:
    """Build FAISS index from chunks"""
    print("🔧 Building FAISS index...")
    
    # Get API key from environment or secrets
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            # Try reading from streamlit secrets
            import toml
            secrets_path = ".streamlit/secrets.toml"
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)
                api_key = secrets.get("OPENAI_API_KEY")
                os.environ["OPENAI_API_KEY"] = api_key
                print("✅ API key loaded from secrets.toml")
        except:
            pass
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        print("💡 Set environment variable or add to .streamlit/secrets.toml")
        return False
    
    # Create embeddings
    embeddings = OpenAIEmbeddings()
    
    # Prepare documents for FAISS
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "source": chunk["source"],
                "url": chunk.get("url", ""),
                "chunk_id": chunk.get("chunk_id", "")
            }
        )
        documents.append(doc)
    
    print(f"📊 Creating embeddings for {len(documents)} documents...")
    
    # Create FAISS store
    try:
        vector_store = FAISS.from_documents(documents, embeddings)
        
        print("💾 Saving FAISS store...")
        
        # Save the store
        os.makedirs(os.path.dirname(FAISS_STORE_PATH), exist_ok=True)
        vector_store.save_local(FAISS_STORE_PATH)
        
        # Show file sizes
        index_path = os.path.join(FAISS_STORE_PATH, "index.faiss")
        pkl_path = os.path.join(FAISS_STORE_PATH, "index.pkl")
        
        size_info = []
        if os.path.exists(index_path):
            size_mb = os.path.getsize(index_path) / (1024*1024)
            size_info.append(f"index.faiss: {size_mb:.2f} MB")
        
        if os.path.exists(pkl_path):
            size_mb = os.path.getsize(pkl_path) / (1024*1024)  
            size_info.append(f"index.pkl: {size_mb:.2f} MB")
        
        print(f"✅ FAISS store saved to {FAISS_STORE_PATH}")
        print(f"📊 File sizes: {', '.join(size_info)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating FAISS store: {e}")
        return False

def main():
    """Main rebuild process"""
    print("🚀 FAISS Store Rebuild Starting (NO TEMPLATES)")
    print("=" * 60)
    print("⚠️  Code formatting is DISABLED")
    print("⚠️  No curl templates will be applied")
    print("⚠️  Raw HTML text extraction only")
    print("=" * 60)
    
    # Step 1: Load documents
    print("\n📚 1. Loading Documents")
    docs = load_documents()
    if not docs:
        print("❌ No documents found!")
        return
    
    # Step 2: Chunk documents  
    print("\n✂️ 2. Chunking Documents")
    chunks = chunk_documents(docs)
    if not chunks:
        print("❌ No chunks created!")
        return
    
    # Step 3: Build FAISS index
    print("\n🔧 3. Building FAISS Index")
    success = build_faiss_index(chunks)
    
    if success:
        print("\n🎉 FAISS Store rebuilt successfully!")
        print("💡 Raw HTML text - no code formatting")
        print("💡 Curl commands will appear as scraped from web")
    else:
        print("\n❌ FAISS Store rebuild failed!")

if __name__ == "__main__":
    main()
