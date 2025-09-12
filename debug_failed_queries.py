#!/usr/bin/env python3
"""
Debug Failed Queries - Retrieval problemi analizi
Başarısız sorguları analiz edip retrieval optimizasyonu yapma
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_query_retrieval(query: str, expected_content: str = None) -> Dict[str, Any]:
    """Tek bir sorgunun retrieval performansını test et"""
    try:
        from config import FAISS_STORE_PATH
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        from retrievers.hybrid import HybridRetriever
        
        # FAISS store'u yükle
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        docs = vs.docstore._dict
        
        # Corpus hazırla
        corpus_texts = [d.page_content for d in docs.values()]
        corpus_meta = [d.metadata for d in docs.values()]
        
        # Hybrid retriever oluştur
        retriever = HybridRetriever(corpus_texts, corpus_meta)
        
        # Query'yi test et
        print(f"\n🔍 Testing query: '{query}'")
        results = retriever.retrieve(query, k=6)
        
        analysis = {
            "query": query,
            "total_results": len(results),
            "results": results,
            "top_score": results[0]["score"] if results else 0,
            "retrieval_quality": "good" if results and results[0]["score"] > 0.5 else "poor"
        }
        
        # Sonuçları yazdır
        print(f"📊 Total results: {len(results)}")
        if results:
            print(f"🏆 Top score: {results[0]['score']:.3f}")
            print(f"📄 Top result preview: {results[0]['text'][:200]}...")
            
            if expected_content:
                found_expected = any(expected_content.lower() in result['text'].lower() 
                                   for result in results)
                analysis["found_expected"] = found_expected
                print(f"🎯 Expected content found: {found_expected}")
        else:
            print("❌ No results found!")
            
        return analysis
        
    except Exception as e:
        print(f"❌ Error testing query: {e}")
        return {"query": query, "error": str(e)}

def test_problematic_queries():
    """Ekran görüntüsündeki problemli sorguları test et"""
    
    test_cases = [
        {
            "query": "Push mesaj boyutu limitini aştım hatası alıyorum",
            "expected": ["push", "limit", "boyut", "size", "payload"],
            "category": "error_handling"
        },
        {
            "query": "IP adresim engellenmiş, ne yapabilirim?",
            "expected": ["ip", "blocked", "engel", "whitelist"],
            "category": "network_issues"
        },
        {
            "query": "Integrated Modules Via Integration Short Url Consent Requests",
            "expected": ["integration", "module", "consent", "url"],
            "category": "technical_integration"
        },
        {
            "query": "Email Delivery Onboarding",
            "expected": ["email", "delivery", "onboarding"],
            "category": "email_setup"
        }
    ]
    
    print("🧪 Testing Problematic Queries")
    print("=" * 50)
    
    results = []
    for test_case in test_cases:
        result = test_query_retrieval(test_case["query"])
        result.update(test_case)
        results.append(result)
        
        # Kısa analiz
        if result.get("total_results", 0) == 0:
            print(f"🔴 FAILED: No results for '{test_case['query']}'")
        elif result.get("top_score", 0) < 0.3:
            print(f"🟡 WEAK: Low confidence for '{test_case['query']}'")
        else:
            print(f"🟢 OK: Good results for '{test_case['query']}'")
    
    return results

def analyze_retrieval_gaps():
    """Retrieval sistemindeki boşlukları analiz et"""
    print("\n🔍 Analyzing Retrieval System Gaps")
    print("=" * 50)
    
    # Common failure patterns
    failure_patterns = [
        "Türkçe error messages",
        "Network/IP related issues", 
        "Specific error codes",
        "Integration module names",
        "Email delivery specifics"
    ]
    
    recommendations = []
    
    for pattern in failure_patterns:
        print(f"\n📋 Pattern: {pattern}")
        
        if "Türkçe" in pattern:
            print("   💡 Recommendation: Improve Turkish-English query translation")
            recommendations.append("enhance_turkish_translation")
            
        elif "Network" in pattern:
            print("   💡 Recommendation: Add network troubleshooting docs")
            recommendations.append("add_network_docs")
            
        elif "error codes" in pattern:
            print("   💡 Recommendation: Create error code mapping")
            recommendations.append("create_error_mapping")
            
        elif "Integration" in pattern:
            print("   💡 Recommendation: Improve technical term matching")
            recommendations.append("improve_technical_matching")
            
        elif "Email" in pattern:
            print("   💡 Recommendation: Enhance email-specific retrieval")
            recommendations.append("enhance_email_retrieval")
    
    return recommendations

def suggest_optimizations(test_results: List[Dict], recommendations: List[str]):
    """Somut optimizasyon önerileri"""
    print("\n🚀 Optimization Recommendations")
    print("=" * 50)
    
    # 1. Retrieval optimizations
    print("\n1️⃣ Retrieval Optimizations:")
    
    failed_queries = [r for r in test_results if r.get("total_results", 0) == 0]
    weak_queries = [r for r in test_results if 0 < r.get("top_score", 0) < 0.3]
    
    if failed_queries:
        print(f"   ❌ {len(failed_queries)} queries returned no results")
        print("   💡 Solution: Lower similarity threshold or expand search")
        
    if weak_queries:
        print(f"   🟡 {len(weak_queries)} queries had weak relevance")
        print("   💡 Solution: Adjust BM25/FAISS weights or improve chunking")
    
    # 2. Content gaps
    print("\n2️⃣ Content Gap Solutions:")
    if "add_network_docs" in recommendations:
        print("   🌐 Add network troubleshooting documentation")
        
    if "create_error_mapping" in recommendations:
        print("   🔢 Create error code to solution mapping")
        
    if "enhance_email_retrieval" in recommendations:
        print("   📧 Improve email delivery documentation coverage")
    
    # 3. Technical improvements
    print("\n3️⃣ Technical Improvements:")
    if "enhance_turkish_translation" in recommendations:
        print("   🇹🇷 Improve Turkish query preprocessing")
        
    if "improve_technical_matching" in recommendations:
        print("   🔧 Add technical term synonyms and expansions")
    
    # 4. Immediate actions
    print("\n4️⃣ Immediate Actions:")
    print("   📈 Reduce similarity threshold from 0.5 to 0.3")
    print("   🔄 Increase retrieval results from 6 to 10")
    print("   🎯 Add query expansion for technical terms")
    print("   📝 Improve chunk metadata for better filtering")

def main():
    """Ana debug function"""
    print("🔧 Netmera Chatbot - Failed Query Analysis")
    print("=" * 60)
    
    # Environment check
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found")
        return
    
    try:
        # 1. Test problematic queries
        test_results = test_problematic_queries()
        
        # 2. Analyze gaps
        recommendations = analyze_retrieval_gaps()
        
        # 3. Suggest optimizations
        suggest_optimizations(test_results, recommendations)
        
        # 4. Summary
        print(f"\n📋 Summary:")
        total_tests = len(test_results)
        failed_tests = len([r for r in test_results if r.get("total_results", 0) == 0])
        success_rate = ((total_tests - failed_tests) / total_tests) * 100
        
        print(f"   Tests run: {total_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate < 80:
            print(f"   🔴 Retrieval needs optimization!")
        elif success_rate < 90:
            print(f"   🟡 Retrieval could be improved")
        else:
            print(f"   🟢 Retrieval performing well")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()
