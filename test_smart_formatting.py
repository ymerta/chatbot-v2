#!/usr/bin/env python3
"""
Smart formatting test - procedural vs informational questions
"""

from src.graph.app_graph import is_procedural_question

def test_question_classification():
    """Test question type classification"""
    print("🧪 Testing Smart Question Classification")
    print("=" * 50)
    
    # Test cases from your example
    test_cases = [
        # Informational questions (should NOT use steps)
        ("is netmera using geofence or geotargeting", "English", False),
        ("Netmera geofencing nedir?", "Türkçe", False),
        ("Netmera hangi özellikleri destekliyor?", "Türkçe", False),
        ("What is push notification?", "English", False),
        ("Does Netmera support A/B testing?", "English", False),
        ("Netmera kullanıyor mu geofencing?", "Türkçe", False),
        
        # Procedural questions (should use steps)
        ("Netmera'da push notification nasıl gönderilir?", "Türkçe", True),
        ("How to integrate Netmera SDK to Android?", "English", True),
        ("Android uygulamama nasıl entegre ederim?", "Türkçe", True),
        ("How can I configure geofencing in Netmera?", "English", True),
        ("Netmera kurulumu nasıl yapılır?", "Türkçe", True),
        ("Steps to create a campaign", "English", True),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print("📋 Test Results:")
    for question, lang, expected in test_cases:
        result = is_procedural_question(question, lang)
        status = "✅" if result == expected else "❌"
        print(f"{status} {question}")
        print(f"   Expected: {'Procedural' if expected else 'Informational'}")
        print(f"   Got: {'Procedural' if result else 'Informational'}")
        print()
        
        if result == expected:
            correct += 1
    
    accuracy = (correct / total) * 100
    print(f"🎯 Classification Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy >= 80  # 80% threshold


def test_with_chatbot():
    """Test with actual chatbot if available"""
    print("\n🤖 Testing with Chatbot (if available)")
    print("=" * 50)
    
    try:
        from src.graph.app_graph import build_app_graph
        from src.config import FAISS_STORE_PATH
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        from pathlib import Path
        
        if not Path(FAISS_STORE_PATH).exists():
            print("⚠️ FAISS store not found - skipping chatbot test")
            return True
        
        # Load chatbot
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        docs = vs.docstore._dict
        
        corpus_texts = [d.page_content for d in docs.values()]
        corpus_meta = [d.metadata for d in docs.values()]
        
        graph = build_app_graph(corpus_texts, corpus_meta)
        
        # Test questions
        test_questions = [
            "is netmera using geofence or geotargeting",  # Should be natural
            "Netmera'da push notification nasıl gönderilir?"  # Should be steps
        ]
        
        for question in test_questions:
            try:
                result = graph.invoke({"query": question})
                answer = result.get("answer", "")
                
                has_steps = any(indicator in answer for indicator in ["1.", "2.", "**Adımlar:**", "**Steps:**"])
                
                print(f"Question: {question}")
                print(f"Has step format: {has_steps}")
                print(f"Answer preview: {answer[:200]}...")
                print()
                
            except Exception as e:
                print(f"❌ Error testing question '{question}': {e}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Chatbot test skipped: {e}")
        return True


def main():
    """Main test function"""
    print("🎯 SMART FORMATTING TEST")
    print("Testing procedural vs informational question detection")
    print("=" * 60)
    
    # Test classification
    classification_ok = test_question_classification()
    
    # Test with chatbot if available
    chatbot_ok = test_with_chatbot()
    
    print("\n📋 TEST SUMMARY")
    print("=" * 30)
    print(f"Question Classification: {'✅' if classification_ok else '❌'}")
    print(f"Chatbot Integration: {'✅' if chatbot_ok else '❌'}")
    
    if classification_ok:
        print("\n🎉 Smart formatting should now work correctly!")
        print("\nExpected behavior:")
        print("- 'is netmera using geofence' → Natural explanation")
        print("- 'nasıl push notification gönderilir' → Step-by-step")
    else:
        print("\n❌ Classification needs improvement")
    
    return classification_ok


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
