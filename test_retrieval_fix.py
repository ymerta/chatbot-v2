#!/usr/bin/env python3
"""
Test retrieval fixes for user attributes query
"""

from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.config import FAISS_STORE_PATH
from src.graph.app_graph import build_app_graph, preprocess_query

def test_query_preprocessing():
    """Test query preprocessing"""
    print("🔧 TESTING QUERY PREPROCESSING")
    print("=" * 50)
    
    test_queries = [
        ("Netmera'da kullanıcı attributes nasıl güncellenir?", "Türkçe"),
        ("Android entegrasyonu nasıl yapılır?", "Türkçe"),
        ("How to update user profile?", "English")
    ]
    
    for query, lang in test_queries:
        enhanced = preprocess_query(query, lang)
        print(f"Original: {query}")
        print(f"Enhanced: {enhanced}")
        print(f"Language: {lang}")
        print()


def test_improved_retrieval():
    """Test improved retrieval system"""
    print("🤖 TESTING IMPROVED CHATBOT")
    print("=" * 50)
    
    try:
        # Load chatbot
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        docs = vs.docstore._dict
        
        corpus_texts = [d.page_content for d in docs.values()]
        corpus_meta = [d.metadata for d in docs.values()]
        
        graph = build_app_graph(corpus_texts, corpus_meta)
        
        # Test problematic query
        query = "Netmera'da kullanıcı attributes nasıl güncellenir?"
        print(f"🔍 Test query: {query}")
        
        result = graph.invoke({"query": query})
        
        print(f"\n📊 Results:")
        print(f"   Answer: {result.get('answer', 'No answer')}")
        print(f"   Retrieval confidence: {result.get('retrieval_conf', 0):.3f}")
        print(f"   Citations: {result.get('citations', [])}")
        print(f"   Language: {result.get('lang', 'Unknown')}")
        
        # Check if we get a real answer or fallback
        answer = result.get('answer', '')
        if "yeterli bilgi bulunamadı" in answer or "Bu konuda yeterli bilgi" in answer:
            print("\n❌ Still getting fallback response")
            return False
        else:
            print("\n✅ Got detailed response!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🎯 RETRIEVAL FIXES TEST")
    print("Testing improvements for user attributes query")
    print("=" * 60)
    
    # Test preprocessing
    test_query_preprocessing()
    
    # Test improved system
    success = test_improved_retrieval()
    
    print("\n📋 SUMMARY")
    print("=" * 30)
    if success:
        print("✅ Retrieval fixes are working!")
        print("\nImprovements made:")
        print("   - Confidence threshold: 0.4 → 0.3")
        print("   - BM25 weight: 0.4 → 0.5 (better term matching)")
        print("   - Added Turkish-English term mapping")
        print("   - Improved confidence calculation")
    else:
        print("❌ Retrieval fixes need more work")
        print("\nNext steps:")
        print("   - Check document indexing")
        print("   - Adjust confidence threshold further")
        print("   - Improve term mapping")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)







