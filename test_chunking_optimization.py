#!/usr/bin/env python3
"""
Test script to benchmark chunking optimization performance
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chunking_optimizer import OptimizedChunker, ChunkAnalyzer, CHUNKING_PRESETS
from config import FAISS_STORE_PATH, DATA_DIR

def benchmark_retrieval_performance():
    """Benchmark retrieval performance with different chunking strategies"""
    print("🏁 Benchmarking Retrieval Performance")
    print("=" * 50)
    
    test_queries = [
        "How to implement push notifications in Android?",
        "Netmera SDK integration gradle implementation",
        "User segmentation API endpoint documentation",
        "Campaign creation step by step guide",
        "Analytics reporting dashboard setup",
        "Troubleshooting push notification delivery issues"
    ]
    
    # Test current setup if exists
    if os.path.exists(FAISS_STORE_PATH):
        print("📊 Testing current FAISS setup...")
        current_stats = test_retrieval_performance(test_queries, "current")
        print(f"   Average retrieval time: {current_stats['avg_time']:.3f}s")
        print(f"   Average results per query: {current_stats['avg_results']:.1f}")
    else:
        print("⚠️  Current FAISS store not found")
        current_stats = None
    
    # Test optimized setups would require rebuilding FAISS stores
    # For now, just show the analysis
    
    return current_stats

def test_retrieval_performance(queries: List[str], setup_name: str) -> Dict:
    """Test retrieval performance for a given setup"""
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        
        # Load FAISS store
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        
        total_time = 0
        total_results = 0
        
        for query in queries:
            start_time = time.time()
            results = vs.similarity_search(query, k=6)
            end_time = time.time()
            
            total_time += (end_time - start_time)
            total_results += len(results)
        
        return {
            "setup": setup_name,
            "avg_time": total_time / len(queries),
            "avg_results": total_results / len(queries),
            "total_queries": len(queries)
        }
        
    except Exception as e:
        print(f"❌ Error testing {setup_name}: {e}")
        return {"error": str(e)}

def analyze_chunk_quality():
    """Analyze the quality of current chunks"""
    print("\n🔍 Analyzing Chunk Quality")
    print("=" * 50)
    
    if not os.path.exists(FAISS_STORE_PATH):
        print("❌ FAISS store not found")
        return
    
    analyzer = ChunkAnalyzer(FAISS_STORE_PATH)
    stats = analyzer.analyze_current_chunks()
    
    if "error" in stats:
        print(f"❌ Analysis failed: {stats['error']}")
        return
    
    print(f"📈 Quality Metrics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Average size: {stats['avg_size']:.0f} chars")
    print(f"   Size distribution: {stats['min_size']} - {stats['max_size']} chars")
    
    # Quality indicators
    sizes = stats['sizes']
    too_small = sum(1 for s in sizes if s < 200)
    too_large = sum(1 for s in sizes if s > 2000)
    optimal = len(sizes) - too_small - too_large
    
    print(f"\n📊 Size Quality:")
    print(f"   Too small (<200 chars): {too_small} ({too_small/len(sizes)*100:.1f}%)")
    print(f"   Optimal (200-2000 chars): {optimal} ({optimal/len(sizes)*100:.1f}%)")
    print(f"   Too large (>2000 chars): {too_large} ({too_large/len(sizes)*100:.1f}%)")
    
    # Content type distribution
    print(f"\n🏷️ Content Types:")
    for content_type, count in stats['content_types'].items():
        percentage = (count / stats['total_chunks']) * 100
        print(f"   {content_type}: {count} ({percentage:.1f}%)")
    
    return stats

def recommend_optimization():
    """Recommend optimization strategy based on current analysis"""
    print("\n💡 Optimization Recommendations")
    print("=" * 50)
    
    # Analyze current setup
    if not os.path.exists(FAISS_STORE_PATH):
        print("❌ No current FAISS store found")
        print("🚀 Recommendation: Run initial indexing with balanced preset")
        print("   Command: python src/index_build_optimized.py --preset balanced")
        return
    
    analyzer = ChunkAnalyzer(FAISS_STORE_PATH)
    stats = analyzer.analyze_current_chunks()
    
    if "error" in stats:
        print(f"❌ Cannot analyze current setup: {stats['error']}")
        return
    
    # Analyze statistics and recommend
    avg_size = stats['avg_size']
    sizes = stats['sizes']
    content_types = stats.get('content_types', {})
    
    print(f"📊 Current Setup Analysis:")
    print(f"   Average chunk size: {avg_size:.0f} characters")
    print(f"   Total chunks: {stats['total_chunks']}")
    
    # Size-based recommendations
    if avg_size < 600:
        print("\n⚠️  Chunks are too small on average")
        print("🎯 Recommendation: Use 'balanced' or 'tutorial_focused' preset")
        recommended_preset = "balanced"
    elif avg_size > 1500:
        print("\n⚠️  Chunks are quite large on average")
        print("🎯 Recommendation: Use 'faq_focused' preset for better granularity")
        recommended_preset = "faq_focused"
    else:
        print("\n✅ Chunk sizes are in acceptable range")
        
        # Content-based recommendations
        code_percentage = content_types.get('code', 0) / stats['total_chunks'] * 100
        api_percentage = content_types.get('api', 0) / stats['total_chunks'] * 100
        
        if code_percentage > 30:
            print("🎯 Recommendation: Use 'code_heavy' preset for better code context")
            recommended_preset = "code_heavy"
        elif api_percentage > 25:
            print("🎯 Recommendation: Use 'code_heavy' preset for API documentation")
            recommended_preset = "code_heavy"
        else:
            print("🎯 Recommendation: Current setup is good, consider 'balanced' for slight optimization")
            recommended_preset = "balanced"
    
    print(f"\n🚀 Recommended Action:")
    print(f"   python src/index_build_optimized.py --preset {recommended_preset}")
    print(f"   Description: {CHUNKING_PRESETS[recommended_preset]['description']}")
    
    return recommended_preset

def show_optimization_options():
    """Show available optimization options"""
    print("\n🛠️  Available Optimization Presets")
    print("=" * 50)
    
    for name, config in CHUNKING_PRESETS.items():
        print(f"\n📋 {name.upper()}:")
        print(f"   Chunk size: {config['chunk_size']} characters")
        print(f"   Overlap: {config['chunk_overlap']} characters")
        print(f"   Description: {config['description']}")
        
        # Use case recommendations
        if name == "balanced":
            print("   ✅ Best for: Mixed content, general purpose")
        elif name == "code_heavy":
            print("   ✅ Best for: Technical docs with lots of code examples")
        elif name == "faq_focused":
            print("   ✅ Best for: Short Q&A format, concise answers")
        elif name == "tutorial_focused":
            print("   ✅ Best for: Step-by-step guides, procedural content")

def main():
    """Main test function"""
    print("🧪 Netmera Chunking Optimization Test Suite")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set your OpenAI API key to run tests")
        return
    
    try:
        # 1. Analyze current quality
        analyze_chunk_quality()
        
        # 2. Show available options
        show_optimization_options()
        
        # 3. Get recommendations
        recommended_preset = recommend_optimization()
        
        # 4. Performance benchmark (if possible)
        # benchmark_retrieval_performance()
        
        print(f"\n🎯 Quick Start:")
        print(f"   1. Backup current setup (automatic)")
        print(f"   2. Run optimization:")
        print(f"      python src/index_build_optimized.py --preset {recommended_preset or 'balanced'}")
        print(f"   3. Test the chatbot with the new chunks")
        print(f"   4. If not satisfied, restore backup and try different preset")
        
        print(f"\n📚 For detailed analysis:")
        print(f"   python src/index_build_optimized.py --compare")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("🔧 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()
