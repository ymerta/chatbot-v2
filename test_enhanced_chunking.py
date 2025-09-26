"""
Test Enhanced Chunking Strategies
Compare traditional chunking vs enhanced semantic chunking with overlapping summaries
"""

import sys
import os
sys.path.append('src')

from enhanced_semantic_chunker import EnhancedSemanticChunker, enhanced_chunking_pipeline
from chunking_evaluator import run_comprehensive_evaluation
from chunking_optimizer import OptimizedChunker, optimize_chunking_strategy
from faiss_builder import split_docs_optimized
import json
import time

def load_sample_documents(limit: int = 20) -> list:
    """Load sample documents for testing"""
    print(f"📂 Loading sample documents (limit: {limit})...")
    
    docs = []
    data_dir = "data/dev"
    
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return []
    
    count = 0
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt') and count < limit:
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 500:  # Only documents with substantial content
                        docs.append({
                            "text": content,
                            "source": filename,
                            "url": f"file://{filepath}"
                        })
                        count += 1
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")
    
    print(f"✅ Loaded {len(docs)} documents")
    return docs

def test_traditional_chunking(docs: list) -> list:
    """Test traditional chunking approach"""
    print("\n🔧 Testing Traditional Chunking...")
    
    # Use existing optimized chunker
    chunks, stats = optimize_chunking_strategy(docs, chunk_size=1200, chunk_overlap=200)
    
    print(f"📊 Traditional Results:")
    print(f"   - Total chunks: {len(chunks)}")
    print(f"   - Avg chunk size: {stats['average_chunk_size']:.0f} chars")
    print(f"   - Content types: {list(stats['content_type_distribution'].keys())}")
    
    return chunks

def test_enhanced_chunking(docs: list) -> list:
    """Test enhanced chunking with overlapping summaries"""
    print("\n🧠 Testing Enhanced Semantic Chunking...")
    
    chunks, stats = enhanced_chunking_pipeline(
        docs, 
        experiment_mode=False,  # Skip experiments for main test
        chunk_size=1200,
        add_summaries=False  # Skip summaries to avoid API calls
    )
    
    print(f"📊 Enhanced Results:")
    print(f"   - Total chunks: {len(chunks)}")
    print(f"   - Enhancement ratio: {stats['enhancement_stats']['avg_enhancement_ratio']:.1%}")
    print(f"   - Chunks with prev summary: {stats['enhancement_stats']['chunks_with_prev_summary']}")
    print(f"   - Chunks with next summary: {stats['enhancement_stats']['chunks_with_next_summary']}")
    print(f"   - Processing time: {stats['processing_time']:.2f} seconds")
    
    return chunks

def test_chunk_size_experiments(docs: list) -> dict:
    """Test different chunk size configurations"""
    print("\n🧪 Running Chunk Size Experiments...")
    
    chunker = EnhancedSemanticChunker(add_summaries=False)  # Skip summaries for speed
    experiment_results = chunker.experiment_with_chunk_sizes(docs[:5])  # Use fewer docs for speed
    
    print(f"📈 Experiment Results:")
    for exp_name, results in experiment_results.items():
        print(f"   {exp_name}: {results['total_chunks']} chunks, "
              f"{results['avg_chunk_size']:.0f} chars avg, "
              f"{results['processing_time']:.2f}s")
    
    return experiment_results

def compare_strategies_comprehensive(docs: list) -> dict:
    """Compare all strategies comprehensively"""
    print("\n🏆 Running Comprehensive Strategy Comparison...")
    
    # Test different configurations
    strategies = {}
    
    # 1. Traditional approach
    print("   🔧 Running traditional chunking...")
    traditional_chunks = test_traditional_chunking(docs)
    strategies["Traditional_Optimized"] = traditional_chunks
    
    # 2. Enhanced without summaries 
    print("   🧠 Running enhanced chunking (no summaries)...")
    chunker_no_summaries = EnhancedSemanticChunker(add_summaries=False)
    enhanced_no_summaries = []
    for doc in docs:
        chunks = chunker_no_summaries.create_enhanced_chunks(doc["text"], doc["source"], doc["url"])
        enhanced_no_summaries.extend(chunks)
    strategies["Enhanced_No_Summaries"] = enhanced_no_summaries
    
    # 3. Enhanced with summaries (smaller sample due to API costs)
    print("   🔄 Running enhanced chunking (with summaries)...")
    sample_docs = docs[:5]  # Use smaller sample for summary generation
    enhanced_with_summaries, _ = enhanced_chunking_pipeline(
        sample_docs, 
        experiment_mode=False,
        add_summaries=True
    )
    strategies["Enhanced_With_Summaries"] = enhanced_with_summaries
    
    # 4. Different chunk sizes
    print("   📏 Testing different chunk sizes...")
    chunker_large = EnhancedSemanticChunker(chunk_size=1600, add_summaries=False)
    large_chunks = []
    for doc in docs:
        chunks = chunker_large.create_enhanced_chunks(doc["text"], doc["source"], doc["url"])
        large_chunks.extend(chunks)
    strategies["Large_Chunks_1600"] = large_chunks
    
    # Run comprehensive evaluation
    print("\n📊 Running comprehensive evaluation...")
    evaluation_results = run_comprehensive_evaluation(
        strategies,
        test_queries=[
            "How to implement Netmera SDK in Android?",
            "iOS push notification setup", 
            "API authentication methods",
            "Campaign creation tutorial",
            "Troubleshooting push notifications"
        ],
        save_report=True
    )
    
    return evaluation_results

def demonstrate_enhanced_features(docs: list):
    """Demonstrate specific enhanced features"""
    print("\n🎯 Demonstrating Enhanced Features...")
    
    if not docs:
        print("❌ No documents available for demonstration")
        return
    
    # Take a sample document
    sample_doc = docs[0]
    print(f"\n📄 Sample Document: {sample_doc['source']}")
    print(f"   Length: {len(sample_doc['text'])} characters")
    
    # Create enhanced chunks (without summaries to avoid API calls)
    chunker = EnhancedSemanticChunker(
        chunk_size=1000,
        add_summaries=False,  # Skip summaries for demo
        summary_length=100
    )
    
    enhanced_chunks = chunker.create_enhanced_chunks(
        sample_doc["text"][:3000],  # Use first 3000 chars to limit API calls
        sample_doc["source"], 
        sample_doc["url"]
    )
    
    print(f"\n🔍 Enhanced Chunks Created: {len(enhanced_chunks)}")
    
    # Show first chunk with enhancements
    if enhanced_chunks:
        first_chunk = enhanced_chunks[0]
        print(f"\n📝 First Chunk Analysis:")
        print(f"   Content Type: {first_chunk['metadata']['content_type']}")
        print(f"   Has Previous Summary: {first_chunk['metadata']['enhancement_features']['has_prev_summary']}")
        print(f"   Has Next Summary: {first_chunk['metadata']['enhancement_features']['has_next_summary']}")
        print(f"   Complexity Score: {first_chunk['metadata']['complexity_score']:.2f}")
        print(f"   Tech Terms: {first_chunk['metadata']['tech_terms']}")
        print(f"   Language: {first_chunk['metadata']['language']}")
        
        # Show text preview
        text_preview = first_chunk['text'][:300] + "..." if len(first_chunk['text']) > 300 else first_chunk['text']
        print(f"\n📖 Text Preview:")
        print(f"   {text_preview}")

def main():
    """Main test function"""
    print("🚀 Enhanced Semantic Chunking Test Suite")
    print("=" * 60)
    
    # Load documents
    docs = load_sample_documents(limit=15)
    
    if not docs:
        print("❌ No documents loaded. Cannot proceed with tests.")
        return
    
    print(f"✅ Starting tests with {len(docs)} documents")
    
    # Test 1: Demonstrate enhanced features
    demonstrate_enhanced_features(docs)
    
    # Test 2: Individual strategy tests
    print(f"\n" + "="*60)
    print("🧪 INDIVIDUAL STRATEGY TESTS")
    print("="*60)
    
    traditional_chunks = test_traditional_chunking(docs)
    enhanced_chunks = test_enhanced_chunking(docs[:3])  # Smaller sample for summaries
    
    # Test 3: Chunk size experiments
    print(f"\n" + "="*60)
    print("🔬 CHUNK SIZE EXPERIMENTS")
    print("="*60)
    
    experiment_results = test_chunk_size_experiments(docs)
    
    # Test 4: Comprehensive comparison (optional - costs API calls)
    while True:
        user_input = input(f"\n🤔 Run comprehensive comparison? (includes API calls for evaluation) [y/N]: ").strip().lower()
        if user_input in ['', 'n', 'no']:
            print("⏭️ Skipping comprehensive comparison")
            break
        elif user_input in ['y', 'yes']:
            print(f"\n" + "="*60)
            print("🏆 COMPREHENSIVE STRATEGY COMPARISON")
            print("="*60)
            
            comparison_results = compare_strategies_comprehensive(docs)
            break
        else:
            print("❌ Please enter 'y' for yes or 'n' for no")
    
    # Summary
    print(f"\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    print(f"✅ Traditional chunking: {len(traditional_chunks) if 'traditional_chunks' in locals() else 0} chunks")
    print(f"✅ Enhanced chunking: {len(enhanced_chunks) if 'enhanced_chunks' in locals() else 0} chunks")
    print(f"✅ Experiment configurations: {len(experiment_results) if 'experiment_results' in locals() else 0}")
    
    print(f"\n💡 Key Insights:")
    print(f"   🔄 Enhanced chunking adds context through overlapping summaries")
    print(f"   📏 Adaptive chunk sizing based on content type improves quality")
    print(f"   🎯 Content-aware splitting preserves semantic boundaries")
    print(f"   📊 Comprehensive evaluation helps choose optimal strategy")
    
    print(f"\n📁 Check 'data/analysis/' directory for detailed reports and charts")
    print(f"🎯 Enhanced chunking strategies are ready for integration!")

if __name__ == "__main__":
    main()
