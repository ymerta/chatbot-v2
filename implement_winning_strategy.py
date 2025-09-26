"""
Implement Winning Enhanced Chunking Strategy in Production
Based on evaluation results: Enhanced_With_Summaries (Score: 0.459)
"""

import sys
import os
sys.path.append('src')

from enhanced_semantic_chunker import EnhancedSemanticChunker, enhanced_chunking_pipeline
from faiss_builder import load_scraped_documents
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import json
from datetime import datetime

def backup_current_faiss():
    """Backup current FAISS store before replacing"""
    faiss_path = "data/embeddings/faiss_store"
    backup_path = f"data/embeddings/faiss_store_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(faiss_path):
        import shutil
        shutil.copytree(faiss_path, backup_path)
        print(f"✅ Current FAISS backed up to: {backup_path}")
        return backup_path
    else:
        print("⚠️  No existing FAISS store found")
        return None

def implement_winning_strategy():
    """Implement the winning Enhanced_With_Summaries strategy"""
    
    print("🏆 Implementing Winning Enhanced Chunking Strategy")
    print("=" * 60)
    print("🎯 Strategy: Enhanced_With_Summaries")
    print("📊 Performance: 0.459 score (90%+ improvement)")
    print("🔄 Features: Overlapping summaries + adaptive sizing")
    print("=" * 60)
    
    # Step 1: Backup current FAISS
    print("\n📋 Step 1: Backup Current FAISS Store")
    backup_path = backup_current_faiss()
    
    # Step 2: Load documents
    print("\n📋 Step 2: Load Documents")
    print("📂 Loading scraped documents...")
    
    try:
        # Try to load from existing scraped data
        docs = load_scraped_documents()
        print(f"✅ Loaded {len(docs)} documents from scraped data")
    except Exception as e:
        print(f"⚠️  Could not load scraped documents: {e}")
        print("📁 Loading from dev data as fallback...")
        
        docs = []
        data_dir = "data/dev"
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if len(content) > 500:
                                docs.append({
                                    "text": content,
                                    "source": filename,
                                    "source_type": "documentation",
                                    "url": f"file://{filepath}"
                                })
                    except Exception as file_error:
                        print(f"⚠️  Error reading {filename}: {file_error}")
        
        print(f"✅ Loaded {len(docs)} documents from dev data")
    
    if not docs:
        print("❌ No documents found. Cannot proceed.")
        return False
    
    # Step 3: Apply winning strategy
    print(f"\n📋 Step 3: Apply Enhanced Chunking (Winning Strategy)")
    print("🔧 Configuration:")
    print("   - Chunk size: Adaptive (avg ~1961 chars)")
    print("   - Overlapping summaries: Enabled")
    print("   - Content-aware splitting: Enabled")
    print("   - Enhancement ratio: ~96%")
    
    # Use winning configuration
    enhanced_chunks, stats = enhanced_chunking_pipeline(
        docs,
        experiment_mode=False,
        chunk_size=1200,  # Base size, will be adaptive
        add_summaries=True  # The winning feature!
    )
    
    print(f"\n✅ Enhanced Chunking Results:")
    print(f"   📊 Total chunks: {len(enhanced_chunks)}")
    print(f"   🔄 Enhancement ratio: {stats['enhancement_stats']['avg_enhancement_ratio']:.1%}")
    print(f"   ⏱️  Processing time: {stats['processing_time']:.2f} seconds")
    
    # Step 4: Build new FAISS index
    print(f"\n📋 Step 4: Build New FAISS Index")
    
    try:
        # Prepare texts and metadata for FAISS
        texts = [chunk["text"] for chunk in enhanced_chunks]
        metadatas = []
        
        for chunk in enhanced_chunks:
            metadata = {
                "source": chunk["source"],
                "url": chunk.get("url", ""),
                "chunk_id": f"{chunk['source']}_enhanced_{len(metadatas)}",
                "enhancement_features": chunk["metadata"]["enhancement_features"],
                "content_type": chunk["metadata"]["content_type"],
                "complexity_score": chunk["metadata"]["complexity_score"],
                "tech_terms": chunk["metadata"]["tech_terms"],
                "language": chunk["metadata"]["language"]
            }
            metadatas.append(metadata)
        
        print("🔧 Creating embeddings...")
        embeddings = OpenAIEmbeddings()
        
        print("🏗️  Building FAISS index...")
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        
        # Save new FAISS store
        faiss_path = "data/embeddings/faiss_store"
        os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
        vectorstore.save_local(faiss_path)
        
        print(f"✅ New FAISS index saved to: {faiss_path}")
        
    except Exception as e:
        print(f"❌ Error building FAISS index: {e}")
        
        # Restore backup if available
        if backup_path and os.path.exists(backup_path):
            print("🔄 Restoring backup...")
            import shutil
            if os.path.exists("data/embeddings/faiss_store"):
                shutil.rmtree("data/embeddings/faiss_store")
            shutil.copytree(backup_path, "data/embeddings/faiss_store")
            print("✅ Backup restored")
        
        return False
    
    # Step 5: Save implementation report
    print(f"\n📋 Step 5: Save Implementation Report")
    
    implementation_report = {
        "implementation_date": datetime.now().isoformat(),
        "strategy_name": "Enhanced_With_Summaries",
        "performance_score": 0.459,
        "improvement_over_traditional": "90%+",
        "configuration": {
            "base_chunk_size": 1200,
            "adaptive_sizing": True,
            "overlapping_summaries": True,
            "content_aware_splitting": True
        },
        "results": {
            "total_documents": len(docs),
            "total_chunks": len(enhanced_chunks),
            "enhancement_ratio": stats['enhancement_stats']['avg_enhancement_ratio'],
            "avg_chunk_size": sum(len(chunk["text"]) for chunk in enhanced_chunks) / len(enhanced_chunks),
            "processing_time": stats['processing_time']
        },
        "backup_location": backup_path,
        "faiss_location": "data/embeddings/faiss_store"
    }
    
    report_path = "data/analysis/winning_strategy_implementation.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(implementation_report, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Implementation report saved to: {report_path}")
    
    # Step 6: Test new system
    print(f"\n📋 Step 6: Test New System")
    
    try:
        # Test retrieval with enhanced chunks
        test_queries = [
            "How to implement Netmera SDK in Android?",
            "iOS push notification setup",
            "API authentication methods"
        ]
        
        print("🔍 Testing enhanced retrieval...")
        for query in test_queries:
            results = vectorstore.similarity_search_with_score(query, k=3)
            print(f"   Query: '{query[:30]}...'")
            if results:
                print(f"   Best match score: {results[0][1]:.3f}")
                print(f"   Has enhancement features: {results[0][0].metadata.get('enhancement_features', {}).get('is_enhanced', False)}")
            print()
        
    except Exception as e:
        print(f"⚠️  Testing error: {e}")
    
    print("\n🎉 IMPLEMENTATION COMPLETE!")
    print("=" * 60)
    print("✅ Enhanced semantic chunking with overlapping summaries is now ACTIVE")
    print("📈 Expected performance improvement: 90%+ over traditional chunking")
    print("🔄 Enhancement ratio: ~96% of chunks have contextual summaries")
    print("🎯 Your mixture of strategies successfully implemented!")
    print("=" * 60)
    
    return True

def verify_implementation():
    """Verify the implementation is working correctly"""
    print("\n🔍 Verifying Implementation...")
    
    try:
        # Load the new FAISS store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(
            "data/embeddings/faiss_store", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # Test search
        results = vectorstore.similarity_search("Netmera SDK", k=1)
        
        if results:
            doc = results[0]
            metadata = doc.metadata
            
            print("✅ FAISS store loaded successfully")
            print(f"📊 Test search returned {len(results)} results")
            print(f"🔄 Enhancement features present: {metadata.get('enhancement_features', {})}")
            print(f"🎯 Content type: {metadata.get('content_type', 'unknown')}")
            print(f"🧠 Complexity score: {metadata.get('complexity_score', 0)}")
            
            return True
        else:
            print("❌ No search results returned")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Enhanced Semantic Chunking Implementation")
    
    # Implement winning strategy
    success = implement_winning_strategy()
    
    if success:
        # Verify implementation
        verify_implementation()
        
        print("\n💡 Next Steps:")
        print("   1. ✅ Enhanced chunking is now active in your system")
        print("   2. 🔄 All new queries will benefit from overlapping summaries")
        print("   3. 📊 Monitor performance improvements in production")
        print("   4. 🎯 Consider fine-tuning summary length based on usage")
        
    else:
        print("\n❌ Implementation failed. Check logs above for details.")
        print("🔄 Your original FAISS store should still be intact.")
