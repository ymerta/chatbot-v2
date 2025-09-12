#!/usr/bin/env python3
"""
Netmera Chatbot Accuracy Improvement Plan
LangSmith evaluation sonuçlarına göre accuracy artırma stratejileri
"""

from pathlib import Path
import json

def improve_system_prompt():
    """Geliştirilmiş system prompt"""
    
    improved_prompt = """You are NetmerianBot, Netmera's expert technical assistant with deep knowledge of mobile engagement platform features.

CORE RESPONSIBILITIES:
- Provide accurate, step-by-step technical guidance for Netmera platform
- Use proper Netmera terminology and technical concepts
- Give practical, actionable solutions with code examples when needed
- Structure responses with clear steps and helpful tips

RESPONSE GUIDELINES:
1. TECHNICAL ACCURACY: Always use correct Netmera terms (push notification, segment, campaign, SDK, API, etc.)
2. STEP-BY-STEP FORMAT: Break complex tasks into numbered steps
3. CODE EXAMPLES: Include relevant code snippets for technical questions
4. PRACTICAL TIPS: Add "💡 İpucu:" or "⚠️ Dikkat:" sections for important notes
5. TURKISH CONTEXT: For Turkish questions, use Turkish technical explanations but keep code/API terms in English

STRUCTURE YOUR ANSWERS:
```
[Brief Introduction]

**Adımlar:**
1. First step with details
2. Second step with code if needed
3. Third step with configuration

💡 **İpucu:** Helpful tips
⚠️ **Dikkat:** Important warnings

**Örnek:** Code example if applicable
```

If the provided context doesn't contain sufficient information, respond: "Bu konuda yeterli bilgi bulunamadı. Lütfen sorunuzu daha spesifik hale getirin veya Netmera dokümantasyonunu kontrol edin."

Answer in the same language as the question (Turkish/English).
"""
    
    return improved_prompt


def improve_retrieval_confidence():
    """Retrieval confidence threshold'u optimize et"""
    
    suggestions = {
        "current_threshold": 0.6,
        "recommended_threshold": 0.4,  # Daha düşük threshold, daha fazla generate
        "reasoning": "Çok yüksek threshold suggestion'a yönlendiriyor, generate node'a daha fazla trafik verelim"
    }
    
    return suggestions


def enhance_context_processing():
    """Context processing'i iyileştir"""
    
    enhanced_processing = """
def enhanced_generate_answer_node(llm: ChatOpenAI):
    def _inner(state: BotState) -> BotState:
        lang = state["lang"]
        q = state["translated_query"]
        docs = state.get("docs", [])
        
        # Context'i daha iyi formatla
        formatted_contexts = []
        for i, doc in enumerate(docs, 1):
            text = doc.get("text", "")
            source = doc.get("url", "")
            
            # Code formatting preservation için özel işlem
            if any(indicator in text.lower() for indicator in ["gradle", "json", "xml", "code", "```", "implementation"]):
                text = preserve_code_formatting(text)
            
            formatted_contexts.append(f"=== KAYNAK {i} ===\\n{text}\\n(Kaynak: {source})\\n")
        
        ctx = "\\n".join(formatted_contexts)
        
        # Enhanced prompt with better context usage
        sys = get_enhanced_system_prompt()
        
        # Netmera-specific prompt engineering
        netmera_context = f'''
Soru: {q}

Netmera Platform Bilgileri:
{ctx}

Lütfen yukarıdaki Netmera dokümantasyonunu kullanarak {lang} dilinde detaylı, adım adım bir cevap verin.
        '''
        
        out = llm.invoke([
            {"role": "system", "content": sys},
            {"role": "user", "content": netmera_context}
        ]).content
        
        # Post-process answer
        out = post_process_answer(out, lang)
        
        state["answer"] = out
        return state
    return _inner

def preserve_code_formatting(text: str) -> str:
    '''Code block'ları ve formatting'i koru'''
    # Implementation for preserving code structure
    pass

def post_process_answer(answer: str, lang: str) -> str:
    '''Answer'ı post-process et'''
    # Add emoji indicators, format code blocks, etc.
    pass
    """
    
    return enhanced_processing


def improve_retrieval_strategy():
    """Retrieval strategy'yi optimize et"""
    
    strategy = {
        "current_weights": {
            "BM25_WEIGHT": 0.3,
            "FAISS_WEIGHT": 0.5, 
            "FUZZY_WEIGHT": 0.2
        },
        "recommended_weights": {
            "BM25_WEIGHT": 0.4,  # Text matching artır
            "FAISS_WEIGHT": 0.4,  # Semantic search azalt
            "FUZZY_WEIGHT": 0.2   # Fuzzy aynı kalsın
        },
        "additional_improvements": [
            "Query preprocessing (Turkish stopwords removal)",
            "Netmera term expansion (push -> push notification)",
            "Multi-language query translation",
            "Context window optimization"
        ]
    }
    
    return strategy


def fix_web_scraping_issues():
    """Web scraping format problemlerini çöz (Memory'den)"""
    
    fixes = """
# Memory'deki problem: BeautifulSoup's get_text(separator="\\n") kod formatını bozuyor
# Çözüm: HTML parsing'i iyileştir

def improved_html_processing(soup):
    '''HTML processing'i iyileştir - kod formatını koru'''
    
    # Code blocks'ları özel işle
    code_blocks = soup.find_all(['pre', 'code', 'textarea'])
    code_placeholders = {}
    
    for i, block in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        code_placeholders[placeholder] = block.get_text()
        block.replace_with(placeholder)
    
    # Normal text extraction
    text = soup.get_text(separator="\\n")
    
    # Code blocks'ları geri koy
    for placeholder, code_content in code_placeholders.items():
        text = text.replace(placeholder, f"\\n```\\n{code_content}\\n```\\n")
    
    return text

# Curl command'ları ve JSON structure'ları için özel parsing
def preserve_technical_formatting(text):
    '''Teknik formatting'i koru'''
    
    # JSON formatting
    import re
    json_pattern = r'\\{[^}]+\\}'
    
    # Curl command formatting  
    curl_pattern = r'curl\\s+[^\\n]+'
    
    # Code indentation preservation
    # Implementation...
    
    return text
    """
    
    return fixes


def create_netmera_specific_evaluators():
    """Netmera'ya özel evaluator'lar"""
    
    evaluators = """
def netmera_terminology_evaluator(run, example):
    '''Netmera terminolojisi doğruluğu'''
    prediction = run.outputs.get("answer", "").lower()
    
    netmera_terms = {
        "push_notification": ["push notification", "push bildirim", "itme bildirim"],
        "segmentation": ["segment", "segmentasyon", "kullanıcı segment"],
        "campaign": ["kampanya", "campaign"],
        "sdk": ["sdk", "software development kit"],
        "api": ["api", "application programming interface"],
        "dashboard": ["dashboard", "panel", "kontrol panel"]
    }
    
    score = 0.0
    used_terms = []
    
    for category, terms in netmera_terms.items():
        if any(term in prediction for term in terms):
            score += 0.15
            used_terms.append(category)
    
    return {
        "key": "netmera_terminology",
        "score": min(score, 1.0),
        "reason": f"Used terms: {used_terms}"
    }

def technical_completeness_evaluator(run, example):
    '''Teknik completeness'''
    prediction = run.outputs.get("answer", "")
    
    completeness_indicators = {
        "step_by_step": ["1.", "2.", "3.", "adım", "step"],
        "code_examples": ["gradle", "json", "xml", "implementation", "```"],
        "configuration": ["ayar", "config", "setting", "yapılandır"],
        "troubleshooting": ["sorun", "problem", "hata", "error", "çözüm"]
    }
    
    score = 0.0
    found_indicators = []
    
    for category, indicators in completeness_indicators.items():
        if any(indicator in prediction.lower() for indicator in indicators):
            score += 0.25
            found_indicators.append(category)
    
    return {
        "key": "technical_completeness", 
        "score": min(score, 1.0),
        "reason": f"Found: {found_indicators}"
    }
    """
    
    return evaluators


def create_implementation_plan():
    """Implementation plan"""
    
    plan = {
        "phase_1_immediate": [
            "1. Update SYSTEM_PROMPT in config.py with enhanced version",
            "2. Lower retrieval confidence threshold from 0.6 to 0.4", 
            "3. Fix BM25/FAISS weight balance",
            "4. Add code formatting preservation in web scraping"
        ],
        
        "phase_2_medium": [
            "5. Enhance context processing in generate_answer_node",
            "6. Add post-processing for better answer formatting",
            "7. Implement query preprocessing (Turkish stopwords)",
            "8. Add Netmera-specific evaluators"
        ],
        
        "phase_3_advanced": [
            "9. Multi-language query translation",
            "10. Advanced context window optimization",
            "11. Real-time evaluation feedback loop",
            "12. Custom fine-tuning for Netmera domain"
        ],
        
        "expected_improvements": {
            "accuracy": "0.28 → 0.65+ (target)",
            "completeness": "0.27 → 0.60+ (target)", 
            "helpfulness": "0.05 → 0.55+ (target)"
        }
    }
    
    return plan


def main():
    """Ana fonksiyon - tüm iyileştirmeleri göster"""
    
    print("🎯 NETMERA CHATBOT ACCURACY IMPROVEMENT PLAN")
    print("=" * 60)
    
    print("\n📊 CURRENT PERFORMANCE:")
    print("- Accuracy: 0.28 (Target: 0.65+)")
    print("- Completeness: 0.27 (Target: 0.60+)")
    print("- Helpfulness: 0.05 (Target: 0.55+)")
    print("- Language Consistency: 1.00 ✅")
    
    print("\n🚀 IMPROVEMENT STRATEGIES:")
    
    print("\n1️⃣ ENHANCED SYSTEM PROMPT:")
    print("- Netmera-specific technical guidance")
    print("- Step-by-step formatting") 
    print("- Code examples integration")
    print("- Turkish context optimization")
    
    print("\n2️⃣ RETRIEVAL OPTIMIZATION:")
    print("- Lower confidence threshold (0.6 → 0.4)")
    print("- Rebalance BM25/FAISS weights")
    print("- Query preprocessing")
    print("- Context formatting improvement")
    
    print("\n3️⃣ WEB SCRAPING FIXES:")
    print("- Preserve code block formatting")
    print("- Fix curl command structure")
    print("- JSON formatting preservation")
    
    print("\n4️⃣ NETMERA-SPECIFIC EVALUATORS:")
    print("- Terminology accuracy")
    print("- Technical completeness")
    print("- Code example quality")
    
    print("\n📋 IMPLEMENTATION PHASES:")
    plan = create_implementation_plan()
    
    for phase, tasks in plan.items():
        if phase.startswith("phase"):
            print(f"\n{phase.upper()}:")
            for task in tasks:
                print(f"  {task}")
    
    print(f"\n🎯 EXPECTED RESULTS:")
    for metric, improvement in plan["expected_improvements"].items():
        print(f"  {metric}: {improvement}")
    
    print("\n💡 NEXT STEPS:")
    print("1. python improve_accuracy.py --phase 1")
    print("2. python evaluate_chatbot.py --dataset all")
    print("3. Compare before/after results")
    print("4. Iterate based on evaluation feedback")


if __name__ == "__main__":
    main()
    
