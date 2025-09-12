#!/usr/bin/env python3
"""
Debug retrieval system for "user attributes" query
"""

from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.config import FAISS_STORE_PATH
from src.retrievers.hybrid import HybridRetriever

def test_retrieval():
    """Test retrieval for user attributes query"""
    print("🔍 DEBUGGING RETRIEVAL SYSTEM")
    print("=" * 50)
    
    # Load data
    emb = OpenAIEmbeddings()
    vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
    docs = vs.docstore._dict
    
    corpus_texts = [d.page_content for d in docs.values()]
    corpus_meta = [d.metadata for d in docs.values()]
    
    print(f"📊 Corpus size: {len(corpus_texts)} documents")
    
    # Test query
    query = "Netmera'da kullanıcı attributes nasıl güncellenir?"
    print(f"🔍 Test query: {query}")
    
    # 1. Test FAISS directly
    print("\n1️⃣ FAISS Direct Search:")
    faiss_results = vs.similarity_search_with_score(query, k=10)
    
    for i, (doc, score) in enumerate(faiss_results[:5], 1):
        print(f"   {i}. Score: {score:.4f}")
        print(f"      Source: {doc.metadata.get('source', 'unknown')}")
        print(f"      Content: {doc.page_content[:100]}...")
        print()
    
    # 2. Test Hybrid Retriever
    print("\n2️⃣ Hybrid Retriever:")
    retriever = HybridRetriever(corpus_texts, corpus_meta)
    hybrid_results = retriever.retrieve(query, k=10)
    
    for i, result in enumerate(hybrid_results[:5], 1):
        print(f"   {i}. Score: {result['score']:.4f}")
        print(f"      Source: {result.get('source', 'unknown')}")
        print(f"      URL: {result.get('url', 'unknown')}")
        print(f"      Content: {result['text'][:100]}...")
        print()
    
    # 3. Check for specific terms
    print("\n3️⃣ Term Analysis:")
    search_terms = ["user", "attribute", "updateUser", "setCustomAttribute", "NMUserProfile"]
    
    for term in search_terms:
        matching_docs = 0
        for i, text in enumerate(corpus_texts):
            if term.lower() in text.lower():
                matching_docs += 1
        print(f"   '{term}': {matching_docs} documents contain this term")
    
    # 4. Look for user attributes specifically
    print("\n4️⃣ User Attributes Documents:")
    user_attr_docs = []
    for i, (text, meta) in enumerate(zip(corpus_texts, corpus_meta)):
        if "user" in text.lower() and "attribute" in text.lower():
            user_attr_docs.append((i, meta.get('source', 'unknown'), text[:200]))
    
    print(f"   Found {len(user_attr_docs)} documents with 'user' + 'attribute'")
    for i, (doc_idx, source, preview) in enumerate(user_attr_docs[:3], 1):
        print(f"   {i}. {source}")
        print(f"      {preview}...")
        print()
    
    return len(hybrid_results) > 0


def test_specific_file():
    """Test if specific user attributes file is in corpus"""
    print("\n5️⃣ Specific File Check:")
    
    target_file = "data/dev/netmera-developer-guide-platforms-android-user-and-attributes.txt"
    
    if Path(target_file).exists():
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   File exists: {target_file}")
        print(f"   File size: {len(content)} chars")
        print(f"   Contains 'updateUser': {'updateUser' in content}")
        print(f"   Contains 'setCustomAttribute': {'setCustomAttribute' in content}")
        print(f"   Preview: {content[:300]}...")
        
        # Check if this content is in FAISS
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        docs = vs.docstore._dict
        
        found_in_faiss = False
        for doc in docs.values():
            if "updateUser" in doc.page_content and "NMUserProfile" in doc.page_content:
                found_in_faiss = True
                print(f"   ✅ Similar content found in FAISS")
                print(f"   FAISS content preview: {doc.page_content[:200]}...")
                break
        
        if not found_in_faiss:
            print("   ❌ Content NOT found in FAISS - indexing issue!")
    else:
        print(f"   ❌ File not found: {target_file}")


def main():
    """Main debug function"""
    
    try:
        retrieval_works = test_retrieval()
        test_specific_file()
        
        print("\n📋 DIAGNOSIS:")
        if retrieval_works:
            print("✅ Retrieval system is working")
            print("🔍 Issue might be:")
            print("   - Query-document matching quality")
            print("   - Confidence threshold too high (0.4)")
            print("   - Weight balance (BM25:0.4, FAISS:0.4, Fuzzy:0.2)")
        else:
            print("❌ Retrieval system has issues")
            print("🔧 Potential fixes:")
            print("   - Re-index documents")
            print("   - Check document preprocessing")
            print("   - Adjust retrieval weights")
        
        print("\n💡 Recommendations:")
        print("1. Lower retrieval confidence threshold to 0.3")
        print("2. Increase BM25 weight for exact term matching")
        print("3. Add query preprocessing (synonyms: 'güncellenir' → 'update')")
        print("4. Check if Turkish query needs translation")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")


if __name__ == "__main__":
    main()

