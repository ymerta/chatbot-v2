try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from typing import List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from src.config import CHAT_MODEL, SYSTEM_PROMPT
from src.retrievers.hybrid import HybridRetriever

class BotState(TypedDict, total=False):
    query: str
    lang: str
    translated_query: str
    docs: List[Document]            # burada string tutacağız (uyum için)
    citations: List[str]
    answer: Optional[str]
    retrieval_conf: float

def detect_lang_and_passthrough(state: BotState) -> BotState:
    q = state["query"].strip()
    # Basit sezgi: Türkçe karakter içeriyorsa TR
    lang = "Türkçe" if any(ch in "çğıöşü" for ch in q.lower()) else "English"
    state.update({"lang": lang, "translated_query": q})
    return state

def detect_conversational_intent(state: BotState) -> BotState:
    """Conversational intent detection - disabled for direct Q&A only"""
    # Selamlama fonksiyonu devre dışı - sadece sorulara cevap ver
    # state["conversational_response"] artık set edilmeyecek
    return state


def preprocess_query(query: str, lang: str) -> str:
    """Enhanced query preprocessing - Better Turkish-English mapping + error handling"""
    q_lower = query.lower()
    
    # Enhanced Turkish -> English term mapping
    if lang == "Türkçe":
        term_mapping = {
            # Existing terms
            "güncellenir": "update",
            "güncelleme": "update", 
            "kullanıcı": "user",
            "özellik": "attribute",
            "özellikler": "attributes",
            "nasıl": "how",
            "kurulum": "install setup",
            "entegrasyon": "integration",
            "yapılandırma": "configuration",
            "ayarlama": "setup configuration",
            "gönderim": "send",
            "bildirim": "notification",
            "kampanya": "campaign",
            "segment": "segment",
            "analitik": "analytics",
            
            # 🔧 NEW: Error and problem handling terms
            "hata": "error issue problem",
            "sorun": "problem issue trouble error",
            "limit": "limit size payload quota restriction",
            "boyut": "size payload limit length",
            "aştım": "exceed over limit maximum",
            "alıyorum": "getting receiving encountering",
            
            # 🔧 NEW: Network and access terms
            "ip": "ip address network connection",
            "adres": "address location endpoint",
            "adresim": "my address my ip address",
            "engel": "block blocked restrict ban",
            "engellenmiş": "blocked restricted banned",
            "yapabilirim": "can do solution fix resolve",
            
            # 🔧 NEW: Technical and integration terms
            "modül": "module component feature",
            "url": "url link endpoint address",
            "onay": "consent approval permission",
            "teslimat": "delivery send dispatch",
            "mesaj": "message notification push",
            "push": "push notification alert",
            "e-posta": "email mail electronic mail",
            "email": "email e-mail mail messaging"
        }
        
        # Enhanced query expansion
        enhanced_query = query
        for tr_term, en_term in term_mapping.items():
            if tr_term in q_lower:
                enhanced_query += f" {en_term}"
        
        # 🔧 NEW: Pattern-based expansion for common issues
        if "push" in q_lower and ("boyut" in q_lower or "limit" in q_lower):
            enhanced_query += " push notification payload size maximum length restriction"
        
        if "ip" in q_lower and ("engel" in q_lower or "block" in q_lower):
            enhanced_query += " ip address blocked network access denied whitelist firewall"
            
    else:
        enhanced_query = query
        
        # 🔧 NEW: English query expansion for technical terms
        if "integration" in q_lower and "module" in q_lower:
            enhanced_query += " platform integration setup configuration api"
        
        if "email" in q_lower and "delivery" in q_lower:
            enhanced_query += " email sending mail delivery smtp configuration"
    
    return enhanced_query

def retrieve_node(retriever: HybridRetriever):
    def _inner(state: BotState) -> BotState:
        q = state["translated_query"]
        lang = state["lang"]
        
        # Preprocess query to add English terms
        enhanced_q = preprocess_query(q, lang)
        
        items = retriever.retrieve(enhanced_q, k=10)
        state["docs"] = items
        
        # Better confidence calculation based on actual scores
        if items:
            max_score = max(item.get("score", 0) for item in items)
            # Normalize score to 0-1 range (scores can be > 1)
            conf = min(max_score / 1.5, 1.0)  # Lowered divisor for better confidence
        else:
            conf = 0.0
            
        state["retrieval_conf"] = conf
        return state
    return _inner

def decide_node(state: BotState) -> BotState:
    return state  # routing fonksiyonları ayrı

def generate_answer_node(llm: ChatOpenAI):
    def _inner(state: BotState) -> BotState:
        lang = state["lang"]
        q = state["translated_query"]
        docs = state.get("docs", [])
        
        # Enhanced context formatting
        formatted_contexts = []
        for i, doc in enumerate(docs[:3], 1):  # Limit to top 3 most relevant
            text = doc.get("text", "")
            source = doc.get("url", "unknown")
            
            # Preserve code formatting if present
            if any(indicator in text.lower() for indicator in ["gradle", "json", "xml", "implementation", "```", "curl"]):
                text = text.replace("\n\n", "\n").strip()  # Clean up extra newlines
            
            formatted_contexts.append(f"=== KAYNAK {i} ===\n{text}\n(URL: {source})\n")
        
        ctx = "\n".join(formatted_contexts)
        sys = SYSTEM_PROMPT
        
        # 🔧 SIMPLIFIED: No forced formatting based on question type
        if lang == "Türkçe":
            prompt = f"""Soru: {q}

Belgeler:
{ctx}

Yukarıdaki belgeleri kullanarak TÜRKÇE cevap verin. Gerekirse adımlar halinde açıklayın."""
        else:
            prompt = f"""Question: {q}

Documentation:
{ctx}

Answer in ENGLISH using the documentation above. Use steps if needed."""

        out = llm.invoke([{"role":"system","content":sys},{"role":"user","content":prompt}]).content
        
        # Post-process the answer
        out = post_process_answer(out, lang)

        # SADECE İLK URL
        primary = next((d.get("url") for d in docs if d.get("url")), None)
        state["citations"] = [primary] if primary else []
        state["answer"] = out
        return state
    return _inner

# 🔧 REMOVED: is_procedural_question function - was causing accuracy issues


def post_process_answer(answer: str, lang: str) -> str:
    """Answer'ı post-process et - minimal formatting"""
    # Just clean up and return - no emoji additions
    return answer.strip()

def needs_clarification_check(state: BotState) -> BotState:
    """Sorunun açıklayıcı soru gerekip gerekmediğini kontrol et (SIMPLIFIED)"""
    query = state["translated_query"].lower()
    
    # Sadece çok belirsiz sorular için clarification iste
    very_ambiguous = [
        len(query.split()) < 3,  # Çok kısa sorular
        query in ["help", "yardım", "nasıl", "how"]  # Tek kelime sorular
    ]
    
    state["needs_clarification"] = any(very_ambiguous)
    return state

def clarify_question_node(llm: ChatOpenAI):
    """Açıklayıcı soru oluşturur"""
    def _inner(state: BotState) -> BotState:
        lang = state["lang"]
        query = state["translated_query"]
        
        # Açıklayıcı soru prompt'u
        if lang == "Türkçe":
            clarify_prompt = f"""
Kullanıcının sorusu: "{query}"

Bu soru belirsiz bilgiler içeriyor. Kullanıcıya daha iyi yardım edebilmek için açıklayıcı bir soru sor.

Açıklayıcı soru türleri:
- Platform/SDK: "Hangi platform için? (iOS/Android/Web/React Native)"
- Versiyon: "Hangi Android Studio versiyonu kullanıyorsunuz?"
- Dil: "Kotlin mi Java ile mi geliştiriyorsunuz?"
- Detay: "Hangi hata mesajını görüyorsunuz?"
- Ortam: "Development mi production ortamında?"

Kısa ve net bir açıklayıcı soru üret:
"""
        else:
            clarify_prompt = f"""
User's question: "{query}"

This question contains ambiguous information. Ask a clarifying question to better help the user.

Clarifying question types:
- Platform/SDK: "Which platform? (iOS/Android/Web/React Native)"
- Version: "Which Android Studio version are you using?"
- Language: "Are you using Kotlin or Java?"
- Details: "What error message do you see?"
- Environment: "Development or production environment?"

Generate a short and clear clarifying question:
"""
        
        # LLM'den açıklayıcı soru al
        response = llm.invoke([
            {"role": "system", "content": "Sen yardımcı bir asistansın. Kullanıcıya açıklayıcı sorular sorarak daha iyi yardım ediyorsun."},
            {"role": "user", "content": clarify_prompt}
        ]).content.strip()
        
        state["clarifying_question"] = response
        state["answer"] = response  # UI için
        return state
    return _inner


def finalize_node(state: BotState) -> BotState:
    # Finalize işlemi - artık conversational response yok
    return state

def route_after_retrieve(state: BotState) -> str:
    """Retrieval'dan sonra nereye gideceğini belirle - HER ZAMAN GENERATE"""
    # Clarification özelliği kaldırıldı - her zaman direkt cevap ver
    return "generate"

# route_after_clarification_check fonksiyonu kaldırıldı - artık kullanılmıyor

def build_app_graph(corpus_texts, corpus_meta):
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    retriever = HybridRetriever(corpus_texts, corpus_meta)

    g = StateGraph(BotState)
    
    # Node'ları ekle (clarification node'ları kaldırıldı)
    g.add_node("detect", detect_lang_and_passthrough)
    g.add_node("retrieve", retrieve_node(retriever))
    g.add_node("generate", generate_answer_node(llm))
    g.add_node("finalize", finalize_node)

    # Basitleştirilmiş graph flow - clarification kaldırıldı
    g.set_entry_point("detect")
    g.add_edge("detect", "retrieve")
    g.add_edge("retrieve", "generate")  # Direkt generate'e git
    g.add_edge("generate", "finalize")

    return g.compile()