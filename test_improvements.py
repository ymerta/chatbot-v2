#!/usr/bin/env python3
"""
Test script to quickly verify the accuracy improvements
"""

import asyncio
import os
from pathlib import Path

def test_basic_functionality():
    """Test basic chatbot functionality with improvements"""
    print("🧪 Testing Basic Chatbot Functionality")
    print("=" * 50)
    
    try:
        # Test imports
        from src.graph.app_graph import build_app_graph
        from src.config import FAISS_STORE_PATH
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        
        print("✅ All imports successful")
        
        # Check if FAISS store exists
        if not Path(FAISS_STORE_PATH).exists():
            print("❌ FAISS store not found. Run: python src/index_build.py")
            return False
        
        print("✅ FAISS store found")
        
        # Load chatbot
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        docs = vs.docstore._dict
        
        corpus_texts = [d.page_content for d in docs.values()]
        corpus_meta = [d.metadata for d in docs.values()]
        
        graph = build_app_graph(corpus_texts, corpus_meta)
        print("✅ Chatbot graph compiled successfully")
        
        # Test queries
        test_queries = [
            "Netmera'da push notification nasıl gönderilir?",
            "Android SDK integration steps",
            "How to create user segments in Netmera?"
        ]
        
        print("\n🔍 Testing sample queries:")
        for i, query in enumerate(test_queries, 1):
            try:
                result = graph.invoke({"query": query})
                answer = result.get("answer", "")
                
                print(f"\n{i}. Query: {query}")
                print(f"   Answer length: {len(answer)} chars")
                print(f"   Has structured format: {'**Adımlar:**' in answer or '1.' in answer}")
                print(f"   Has technical terms: {any(term in answer.lower() for term in ['sdk', 'api', 'push', 'campaign'])}")
                print(f"   Has helpful indicators: {'💡' in answer or '⚠️' in answer}")
                
                if len(answer) > 100:
                    print(f"   Preview: {answer[:100]}...")
                
            except Exception as e:
                print(f"❌ Query {i} failed: {e}")
                return False
        
        print("\n✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


async def test_evaluation_system():
    """Test the evaluation system"""
    print("\n🧪 Testing Evaluation System")
    print("=" * 50)
    
    try:
        from src.evaluation import NetmeraEvaluator
        from src.evaluation.langsmith_evaluator import (
            accuracy_evaluator, 
            helpfulness_evaluator,
            completeness_evaluator,
            language_consistency_evaluator
        )
        
        print("✅ Evaluation imports successful")
        
        # Test evaluators with sample data
        sample_run = type('Run', (), {
            'outputs': {
                'answer': """Netmera'da push notification göndermek için şu adımları takip edin:

**Adımlar:**
1. Netmera dashboard'a giriş yapın
2. Sol menüden 'Campaigns' bölümüne tıklayın
3. 'Push Notifications' seçeneğini seçin
4. 'Create Campaign' butonuna tıklayın

💡 **İpucu:** Test gönderimi yaparak kampanyanızı kontrol edin
⚠️ **Dikkat:** Hedef kitleyi doğru seçtiğinizden emin olun

**Örnek kod:**
```java
implementation 'com.netmera:netmera-android:3.x.x'
```"""
            }
        })()
        
        sample_example = type('Example', (), {})()
        
        # Test each evaluator
        evaluators = [
            ("Accuracy", accuracy_evaluator),
            ("Helpfulness", helpfulness_evaluator), 
            ("Completeness", completeness_evaluator),
            ("Language Consistency", language_consistency_evaluator)
        ]
        
        print("\n📊 Testing evaluators:")
        for name, evaluator_func in evaluators:
            try:
                result = evaluator_func(sample_run, sample_example)
                score = result.get('score', 0)
                reason = result.get('reason', 'No reason')
                
                print(f"   {name}: {score:.3f} - {reason}")
                
            except Exception as e:
                print(f"❌ {name} evaluator failed: {e}")
                return False
        
        print("\n✅ Evaluation system test completed")
        return True
        
    except Exception as e:
        print(f"❌ Evaluation test failed: {e}")
        return False


def check_environment():
    """Check environment setup"""
    print("\n🧪 Checking Environment")
    print("=" * 50)
    
    checks = [
        ("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")),
        ("LANGSMITH_API_KEY", os.getenv("LANGSMITH_API_KEY")),
        ("FAISS Store", Path("data/embeddings/faiss_store").exists()),
        ("Evaluation DB", Path("EvaluationDB").exists()),
    ]
    
    all_good = True
    for name, status in checks:
        if status:
            print(f"✅ {name}")
        else:
            print(f"⚠️  {name} - Not configured/found")
            if name.endswith("_API_KEY"):
                all_good = False
    
    return all_good


def suggest_next_steps():
    """Suggest next steps based on test results"""
    print("\n💡 Recommended Next Steps")
    print("=" * 50)
    
    print("""
1. 🚀 Run Full Evaluation:
   python evaluate_chatbot.py --dataset all

2. 📊 Compare Results:
   python -m src.evaluation.reporting --recent 1

3. 🔄 Iterate Based on Results:
   - Check accuracy scores in LangSmith dashboard
   - Identify low-scoring examples
   - Further tune system prompt or evaluators

4. 📈 Monitor Performance:
   - Set up regular evaluations
   - Track improvements over time
   - A/B test different prompts

5. 🛠️ Advanced Improvements:
   - Query preprocessing for Turkish
   - Custom fine-tuning
   - Enhanced retrieval strategies
""")


async def main():
    """Main test function"""
    print("🎯 NETMERA CHATBOT ACCURACY IMPROVEMENTS TEST")
    print("=" * 60)
    
    # Environment check
    env_ok = check_environment()
    
    # Basic functionality test
    basic_ok = test_basic_functionality()
    
    # Evaluation system test
    eval_ok = await test_evaluation_system()
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 30)
    print(f"Environment: {'✅' if env_ok else '⚠️'}")
    print(f"Basic Functionality: {'✅' if basic_ok else '❌'}")
    print(f"Evaluation System: {'✅' if eval_ok else '❌'}")
    
    if all([basic_ok, eval_ok]):
        print("\n🎉 All core tests passed!")
        if not env_ok:
            print("⚠️  Some environment variables missing but system functional")
    else:
        print("\n❌ Some tests failed - check errors above")
    
    suggest_next_steps()
    
    return all([basic_ok, eval_ok])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
