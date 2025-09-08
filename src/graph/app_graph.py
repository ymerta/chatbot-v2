from src.config import CHAT_MODEL, SYSTEM_PROMPT, FAQ_URL
from src.faq.faq import FAQMatcher
from src.retrievers.hybrid import HybridRetriever
import re

class BotState(TypedDict, total=False):
    query: str
    lang: str
    translated_query: str
    faq_answer: Optional[str]
    docs: List[Document]            # burada string tutacağız (uyum için)
    citations: List[str]
    answer: Optional[str]
    suggestions: List[str]
    retrieval_conf: float
    conversational_response: Optional[str]  # Yeni alan: selamlama ve genel konuşma için

def detect_lang_and_passthrough(state: BotState) -> BotState:
    q = state["query"].strip()
    # Basit sezgi: Türkçe karakter içeriyorsa TR
    lang = "Türkçe" if any(ch in "çğıöşü" for ch in q.lower()) else "English"
    state.update({"lang": lang, "translated_query": q})
    return state

def detect_conversational_intent(state: BotState) -> BotState:
    """Selamlama ve genel konuşma tespiti"""
    q = state["translated_query"].lower().strip()
    lang = state["lang"]
    
    # Selamlama kalıpları
    greeting_patterns_tr = [
        r'\b(merhaba|selam|selamlar|iyi günler|iyi akşamlar|günaydın|hoş geldin|hey)\b',
        r'\b(merhaba|selam).*bot\b',
        r'\b(merhaba|selam).*asistan\b'
    ]
    
    greeting_patterns_en = [
        r'\b(hello|hi|hey|good morning|good afternoon|good evening|greetings)\b',
        r'\b(hello|hi).*bot\b',
        r'\b(hello|hi).*assistant\b'
    ]
    
    # Yardım teklifi kalıpları
    help_patterns_tr = [
        r'\b(yardım|help|nasıl yardımcı|ne yapabilirsin|ne yapıyorsun)\b',
        r'\b(hangi belgeler|hangi dokümanlar|hangi kaynaklar)\b',
        r'\b(nasıl çalışıyor|ne işe yarar)\b'
    ]
    
    help_patterns_en = [
        r'\b(help|how can you help|what can you do|what do you do)\b',
        r'\b(which documents|which sources|what documents)\b',
        r'\b(how does it work|what is it for)\b'
    ]
    
    patterns = greeting_patterns_tr + help_patterns_tr if lang == "Türkçe" else greeting_patterns_en + help_patterns_en
    
    for pattern in patterns:
        if re.search(pattern, q):
            if lang == "Türkçe":
                if any(re.search(p, q) for p in greeting_patterns_tr):
                    state["conversational_response"] = "Merhaba! 👋 Ben NetmerianBot, Netmera'nın dijital asistanıyım. Size Netmera ile ilgili sorularınızda yardımcı olabilirim. Hangi konuda bilgi almak istiyorsunuz?"
                elif any(re.search(p, q) for p in help_patterns_tr):
                    state["conversational_response"] = "Ben Netmera'nın resmi dokümantasyonu ve SSS'lerini kullanarak size yardımcı oluyorum. Netmera'nın kullanıcı kılavuzu ve geliştirici dokümantasyonundan bilgileri çekiyorum. Hangi konuda yardıma ihtiyacınız var?"
            else:
                if any(re.search(p, q) for p in greeting_patterns_en):
                    state["conversational_response"] = "Hello! 👋 I'm NetmerianBot, Netmera's digital assistant. I can help you with questions about Netmera. What would you like to know about?"
                elif any(re.search(p, q) for p in help_patterns_en):
                    state["conversational_response"] = "I help you by using Netmera's official documentation and FAQs. I retrieve information from Netmera's user guide and developer documentation. What do you need help with?"
            break
    
    return state

def faq_check_node(faq: FAQMatcher):
    def _inner(state: BotState) -> BotState:
        q = state["translated_query"]
        res = faq.check(q, threshold=70)
        if res:
            state["faq_answer"] = f"{res['answer']}\n\n📄 **Kaynak**: [FAQ]({res.get('source') or FAQ_URL})"
        return state
    return _inner

def retrieve_node(retriever: HybridRetriever):
    def _inner(state: BotState) -> BotState:
        q = state["translated_query"]
        items = retriever.retrieve(q, k=6)
        state["docs"] = items
        # Basit güven: ilk dokümanın skoru normalize edilmeden 0-1’e sıkıştırılmış gibi düşünelim
        conf = 0.6 if items else 0.0
        state["retrieval_conf"] = conf
        return state
    return _inner

def decide_node(state: BotState) -> BotState:
    return state  # routing fonksiyonları ayrı

def generate_answer_node(llm: ChatOpenAI):
    def _inner(state: BotState) -> BotState:
        lang = state["lang"]
        q = state["translated_query"]
        ctx = "\n\n---\n\n".join([d["text"] for d in state.get("docs", [])])
        sys = SYSTEM_PROMPT
        prompt = f"Question:\n{q}\n\nContext:\n{ctx}\n\nAnswer in {lang}. Cite sources."
        out = llm.invoke([{"role":"system","content":sys},{"role":"user","content":prompt}]).content

        # SADECE İLK URL
        primary = next((d.get("url") for d in state.get("docs", []) if d.get("url")), None)
        state["citations"] = [primary] if primary else []
        state["answer"] = out
        return state
    return _inner

def suggest_node(state: BotState) -> BotState:
    lang = state["lang"]
    if lang == "Türkçe":
        state["suggestions"] = [
            "Hangi SDK/platform? (iOS/Android/Web)",
            "Hangi ekran/hatayı görüyorsun?",
            "Konu başlığını biraz daha açar mısın?"
        ]
    else:
        state["suggestions"] = [
            "Which SDK/platform? (iOS/Android/Web)",
            "Which screen/error do you see?",
            "Could you expand the topic a bit?"
        ]
    return state

def finalize_node(state: BotState) -> BotState:
    if state.get("faq_answer"):
        state["answer"] = state["faq_answer"]
    elif state.get("conversational_response"):
        state["answer"] = state["conversational_response"]
    return state

def route_after_detect(state: BotState) -> str:
    """Dil tespitinden sonra conversational intent kontrolü yap"""
    return "conversational" if state.get("conversational_response") else "faq"

def route_after_conversational(state: BotState) -> str:
    """Conversational response varsa finalize'a git"""
    return "finalize" if state.get("conversational_response") else "faq"

def route_after_faq(state: BotState) -> str:
    return "finalize" if state.get("faq_answer") else "retrieve"

def route_after_retrieve(state: BotState) -> str:
    return "generate" if state.get("retrieval_conf", 0) >= 0.6 else "suggest"

def build_app_graph(corpus_texts, corpus_meta, faq_path: str):
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    faq = FAQMatcher(faq_path)
    retriever = HybridRetriever(corpus_texts, corpus_meta)

    g = StateGraph(BotState)
    g.add_node("detect", detect_lang_and_passthrough)
    g.add_node("conversational", detect_conversational_intent)
    g.add_node("faq", faq_check_node(faq))
    g.add_node("retrieve", retrieve_node(retriever))
    g.add_node("decide", decide_node)
    g.add_node("generate", generate_answer_node(llm))
    g.add_node("suggest", suggest_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("detect")
    g.add_edge("detect", "conversational")
    g.add_conditional_edges("conversational", route_after_conversational, {"finalize":"finalize","faq":"faq"})
    g.add_conditional_edges("faq", route_after_faq, {"finalize":"finalize","retrieve":"retrieve"})
    g.add_conditional_edges("retrieve", route_after_retrieve, {"generate":"generate","suggest":"suggest"})
    g.add_edge("generate", "finalize")