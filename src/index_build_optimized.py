"""
Optimized Index Building with Enhanced Chunking Strategy
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

# Proje imports
from config import FAISS_STORE_PATH, BASE_DOC_URL, DATA_DIR
from chunking_optimizer import OptimizedChunker, ChunkAnalyzer, CHUNKING_PRESETS

load_dotenv()

# Directory setup
SCRAPER_SAVE_DIR = os.path.join(DATA_DIR, "dev")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")

os.makedirs(SCRAPER_SAVE_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

def load_scraped_documents() -> List[Dict]:
    """Load scraped documents from data/dev directory"""
    docs = []
    pattern = os.path.join(SCRAPER_SAVE_DIR, "*.txt")
    
    for file_path in glob.glob(pattern):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract source info from filename
        filename = os.path.basename(file_path)
        if filename.startswith("netmera-user-guide"):
            guide_type = "user-guide"
            base_url = f"{BASE_DOC_URL}/netmera-user-guide"
        elif filename.startswith("netmera-developer-guide"):
            guide_type = "developer-guide"
            base_url = f"{BASE_DOC_URL}/netmera-developer-guide"
        else:
            guide_type = "unknown"
            base_url = BASE_DOC_URL
        
        # Create document URL from filename
        url_part = filename.replace(".txt", "").replace("netmera-user-guide-", "").replace("netmera-developer-guide-", "")
        url_part = url_part.replace("_", "-")
        
        docs.append({
            "text": content,
            "source": guide_type,
            "url": f"{base_url}/{url_part}",
            "filename": filename
        })
    
    return docs

def analyze_current_setup():
    """Analyze current FAISS store before optimization"""
    print("📊 Analyzing current FAISS store...")
    
    analyzer = ChunkAnalyzer(FAISS_STORE_PATH)
    stats = analyzer.analyze_current_chunks()
    
    if "error" in stats:
        print(f"❌ Error analyzing current setup: {stats['error']}")
        return None
    
    print(f"📈 Current Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Average size: {stats['avg_size']:.0f} characters")
    print(f"   Size range: {stats['min_size']} - {stats['max_size']} characters")
    print(f"   Median size: {stats['median_size']:.0f} characters")
    
    print(f"\n📁 Source distribution:")
    for source, count in stats['sources'].items():
        print(f"   {source}: {count} chunks")
    
    print(f"\n🏷️ Content type distribution:")
    for content_type, count in stats['content_types'].items():
        print(f"   {content_type}: {count} chunks")
    
    # Save analysis
    analysis_file = os.path.join(ANALYSIS_DIR, "current_analysis.json")
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats

def split_docs_optimized(texts: List[Dict], preset: str = "balanced") -> List[Dict]:
    """Split documents using optimized chunking strategy"""
    print(f"🔧 Using chunking preset: {preset}")
    
    config = CHUNKING_PRESETS.get(preset, CHUNKING_PRESETS["balanced"])
    print(f"   Chunk size: {config['chunk_size']}")
    print(f"   Overlap: {config['chunk_overlap']}")
    print(f"   Description: {config['description']}")
    
    chunker = OptimizedChunker(
        chunk_size=config['chunk_size'],
        chunk_overlap=config['chunk_overlap']
    )
    
    all_chunks = []
    chunking_stats = {
        "original_docs": len(texts),
        "chunks_by_source": {},
        "content_type_distribution": {},
        "size_distribution": []
    }
    
    for doc in texts:
        print(f"   Processing: {doc['source']} - {doc.get('filename', 'unknown')}")
        
        chunks = chunker.split_code_aware(doc["text"], doc["source"], doc["url"])
        all_chunks.extend(chunks)
        
        # Update statistics
        source = doc["source"]
        chunking_stats["chunks_by_source"][source] = \
            chunking_stats["chunks_by_source"].get(source, 0) + len(chunks)
        
        for chunk in chunks:
            content_type = chunk["metadata"]["content_type"]
            chunking_stats["content_type_distribution"][content_type] = \
                chunking_stats["content_type_distribution"].get(content_type, 0) + 1
            chunking_stats["size_distribution"].append(len(chunk["text"]))
    
    # Calculate final statistics
    sizes = chunking_stats["size_distribution"]
    chunking_stats.update({
        "total_chunks": len(all_chunks),
        "avg_size": sum(sizes) / len(sizes) if sizes else 0,
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
        "median_size": sorted(sizes)[len(sizes)//2] if sizes else 0
    })
    
    print(f"\n📊 Chunking Results:")
    print(f"   Total chunks created: {chunking_stats['total_chunks']}")
    print(f"   Average chunk size: {chunking_stats['avg_size']:.0f} characters")
    print(f"   Size range: {chunking_stats['min_size']} - {chunking_stats['max_size']}")
    
    print(f"\n🏷️ Content type distribution:")
    for content_type, count in chunking_stats['content_type_distribution'].items():
        percentage = (count / chunking_stats['total_chunks']) * 100
        print(f"   {content_type}: {count} chunks ({percentage:.1f}%)")
    
    # Save chunking analysis
    analysis_file = os.path.join(ANALYSIS_DIR, f"chunking_analysis_{preset}.json")
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(chunking_stats, f, indent=2, ensure_ascii=False)
    
    return all_chunks

def build_faiss_optimized(chunks: List[Dict], backup_existing: bool = True) -> None:
    """Build FAISS store with optimized chunks"""
    if backup_existing and os.path.exists(FAISS_STORE_PATH):
        # Backup existing FAISS store
        backup_path = f"{FAISS_STORE_PATH}_backup"
        import shutil
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(FAISS_STORE_PATH, backup_path)
        print(f"✅ Existing FAISS store backed up to: {backup_path}")
    
    # Prepare data for FAISS
    emb = OpenAIEmbeddings()
    texts = [chunk["text"] for chunk in chunks]
    metadatas = []
    
    for chunk in chunks:
        # Flatten metadata for FAISS compatibility
        metadata = {
            "source": chunk["source"],
            "url": chunk["url"],
            "content_type": chunk["metadata"]["content_type"],
            "char_count": chunk["metadata"]["char_count"],
            "word_count": chunk["metadata"]["word_count"],
            "has_code": chunk["metadata"]["has_code"],
            "has_steps": chunk["metadata"]["has_steps"],
            "language": chunk["metadata"]["language"],
            "tech_terms": ",".join(chunk["metadata"]["tech_terms"]),
            "headers": ",".join(chunk["metadata"]["headers"]),
            "code_languages": ",".join(chunk["metadata"]["code_languages"])
        }
        metadatas.append(metadata)
    
    # Create and save FAISS store
    print(f"🚀 Building FAISS store with {len(chunks)} optimized chunks...")
    vs = FAISS.from_texts(texts=texts, embedding=emb, metadatas=metadatas)
    vs.save_local(FAISS_STORE_PATH)
    print(f"✅ Optimized FAISS store saved: {FAISS_STORE_PATH}")

def save_chunks_to_disk(chunks: List[Dict], preset: str = "balanced") -> None:
    """Save chunks to disk for inspection"""
    chunk_dir = os.path.join(CHUNKS_DIR, f"optimized_{preset}")
    os.makedirs(chunk_dir, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        filename = f"{i:06d}_{chunk['metadata']['content_type']}.txt"
        filepath = os.path.join(chunk_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"[SOURCE]: {chunk['source']}\n")
            f.write(f"[URL]: {chunk['url']}\n")
            f.write(f"[CONTENT_TYPE]: {chunk['metadata']['content_type']}\n")
            f.write(f"[CHAR_COUNT]: {chunk['metadata']['char_count']}\n")
            f.write(f"[TECH_TERMS]: {', '.join(chunk['metadata']['tech_terms'])}\n")
            f.write(f"[HAS_CODE]: {chunk['metadata']['has_code']}\n")
            f.write(f"[LANGUAGE]: {chunk['metadata']['language']}\n")
            f.write("\n" + "="*50 + "\n\n")
            f.write(chunk['text'])
    
    print(f"✅ Chunks saved to: {chunk_dir}")

def compare_strategies():
    """Compare different chunking strategies"""
    print("🔬 Comparing chunking strategies...")
    
    # Load documents
    docs = load_scraped_documents()
    if not docs:
        print("❌ No documents found to analyze")
        return
    
    results = {}
    
    for preset_name, config in CHUNKING_PRESETS.items():
        print(f"\n📋 Testing preset: {preset_name}")
        chunks = split_docs_optimized(docs, preset_name)
        
        results[preset_name] = {
            "total_chunks": len(chunks),
            "avg_size": sum(len(c["text"]) for c in chunks) / len(chunks),
            "content_types": {}
        }
        
        # Count content types
        for chunk in chunks:
            ct = chunk["metadata"]["content_type"]
            results[preset_name]["content_types"][ct] = \
                results[preset_name]["content_types"].get(ct, 0) + 1
    
    # Save comparison
    comparison_file = os.path.join(ANALYSIS_DIR, "strategy_comparison.json")
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Strategy Comparison Summary:")
    for preset, stats in results.items():
        print(f"   {preset}: {stats['total_chunks']} chunks, "
              f"avg {stats['avg_size']:.0f} chars")
    
    return results

def main(preset: str = "balanced", 
         analyze_current: bool = True,
         save_chunks: bool = False,
         backup_existing: bool = True,
         compare_all: bool = False):
    """
    Main optimization function
    
    Args:
        preset: Chunking strategy preset to use
        analyze_current: Whether to analyze current FAISS store
        save_chunks: Whether to save chunks to disk for inspection
        backup_existing: Whether to backup existing FAISS store
        compare_all: Whether to compare all chunking strategies
    """
    print("🚀 Netmera Documentation Chunking Optimization")
    print("=" * 60)
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(FAISS_STORE_PATH), exist_ok=True)
    
    # Analyze current setup if requested
    if analyze_current and os.path.exists(FAISS_STORE_PATH):
        analyze_current_setup()
        print()
    
    # Compare strategies if requested
    if compare_all:
        compare_strategies()
        return
    
    # Load documents
    print("📁 Loading scraped documents...")
    docs = load_scraped_documents()
    if not docs:
        print("❌ No documents found in data/dev directory")
        print("   Run the scraper first to collect documentation")
        return
    
    print(f"✅ Loaded {len(docs)} documents")
    
    # Split with optimized strategy
    print(f"\n🔧 Applying optimized chunking strategy...")
    chunks = split_docs_optimized(docs, preset)
    
    # Save chunks for inspection if requested
    if save_chunks:
        save_chunks_to_disk(chunks, preset)
    
    # Build optimized FAISS store
    print(f"\n🏗️ Building optimized FAISS store...")
    build_faiss_optimized(chunks, backup_existing)
    
    print(f"\n✅ Optimization complete!")
    print(f"   Preset used: {preset}")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   FAISS store: {FAISS_STORE_PATH}")
    
    if backup_existing:
        print(f"   Backup: {FAISS_STORE_PATH}_backup")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize chunking strategy for Netmera documentation")
    parser.add_argument("--preset", default="balanced", 
                       choices=list(CHUNKING_PRESETS.keys()),
                       help="Chunking strategy preset to use")
    parser.add_argument("--no-analyze", action="store_true",
                       help="Skip analyzing current FAISS store")
    parser.add_argument("--save-chunks", action="store_true",
                       help="Save chunks to disk for inspection")
    parser.add_argument("--no-backup", action="store_true",
                       help="Don't backup existing FAISS store")
    parser.add_argument("--compare", action="store_true",
                       help="Compare all chunking strategies")
    
    args = parser.parse_args()
    
    main(
        preset=args.preset,
        analyze_current=not args.no_analyze,
        save_chunks=args.save_chunks,
        backup_existing=not args.no_backup,
        compare_all=args.compare
    )
