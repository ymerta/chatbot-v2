from typing import List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from src.config import CHAT_MODEL, SYSTEM_PROMPT, FAQ_URL
from src.faq.faq import FAQMatcher
from src.retrievers.hybrid import HybridRetriever

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

def detect_lang_and_passthrough(state: BotState) -> BotState:
    q = state["query"].strip()
    # Basit sezgi: Türkçe karakter içeriyorsa TR
    lang = "Türkçe" if any(ch in "çğıöşü" for ch in q.lower()) else "English"
    state.update({"lang": lang, "translated_query": q})
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
    return state

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
    g.add_node("faq", faq_check_node(faq))
    g.add_node("retrieve", retrieve_node(retriever))
    g.add_node("decide", decide_node)
    g.add_node("generate", generate_answer_node(llm))
    g.add_node("suggest", suggest_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("detect")
    g.add_edge("detect", "faq")
    g.add_conditional_edges("faq", route_after_faq, {"finalize":"finalize","retrieve":"retrieve"})
    g.add_conditional_edges("retrieve", route_after_retrieve, {"generate":"generate","suggest":"suggest"})
    g.add_edge("generate", "finalize")
    g.add_edge("suggest", "finalize")

    return g.compile()