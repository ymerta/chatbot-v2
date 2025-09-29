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
from src.retrievers.hybrid_graphrag import HybridGraphRAGRetriever

class BotState(TypedDict, total=False):
    query: str
    lang: str
    translated_query: str
    docs: List[Document]            # burada string tutacağız (uyum için)
    graph_context: Optional[dict]   # GraphRAG context
    routing_info: Optional[dict]    # Query routing information
    citations: List[str]
    answer: Optional[str]
    retrieval_conf: float

def detect_lang_and_passthrough(state: BotState) -> BotState:
    q = state["query"].strip()
    q_lower = q.lower()
    
    # Türkçe karakterler kontrolü
    has_turkish_chars = any(ch in "çğıöşü" for ch in q_lower)
    
    # Türkçe kelimeler kontrolü (sadece belirgin Türkçe kelimeler)
    turkish_words = [
        'nasıl', 'nedir', 'neden', 'hangi', 'için', 'yapılır', 'kullanım', 
        'kurulum', 'ayar', 'sorun', 'hata', 'nerede', 'mi', 'mu', 'mı', 'mü'
    ]
    has_turkish_words = any(f' {word} ' in f' {q_lower} ' or q_lower.startswith(word) or q_lower.endswith(word) or
                           q_lower.endswith(f' {word}?') or q_lower.endswith(f' {word}.')
                           for word in turkish_words)
    
    # İngilizce kelimeler kontrolü (güçlü İngilizce göstergeleri)
    english_words = [
        'how', 'what', 'where', 'when', 'why', 'which', 'the', 'and', 'or', 'is',
        'are', 'can', 'will', 'should', 'would', 'could', 'setup', 'install',
        'configuration', 'error', 'problem', 'issue', 'with', 'from', 'to'
    ]
    has_english_words = any(f' {word} ' in f' {q_lower} ' or q_lower.startswith(word) or q_lower.endswith(word)
                           for word in english_words)
    
    # Dil belirleme mantığı (öncelik sırası önemli)
    if has_turkish_chars:
        lang = "Türkçe"
    elif has_turkish_words and not has_english_words:
        lang = "Türkçe"
    elif has_english_words:
        lang = "English"
    else:
        # Varsayılan olarak İngilizce (teknik terimler için)
        lang = "English"
    
    state.update({"lang": lang, "translated_query": q})
    return state

def detect_conversational_intent(state: BotState) -> BotState:
    """Conversational intent detection - disabled for direct Q&A only"""
    # Selamlama fonksiyonu devre dışı - sadece sorulara cevap ver
    # state["conversational_response"] artık set edilmeyecek
    return state


def preprocess_query(query: str, lang: str) -> str:
    """
    Enhanced query preprocessing with platform-specific expansion
    """
    enhanced_query = query
    
    # Platform query expansion
    platform_keywords = {
        "türkçe": ["platform", "destekl", "hangi", "platfor"],
        "english": ["platform", "support", "which", "what platforms"]
    }
    
    query_lower = query.lower()
    
    # Check if this is a platform-related query
    is_platform_query = False
    if lang == "Türkçe":
        is_platform_query = any(keyword in query_lower for keyword in platform_keywords["türkçe"])
    else:
        is_platform_query = any(keyword in query_lower for keyword in platform_keywords["english"])
    
    # Add platform-specific terms for better retrieval
    if is_platform_query:
        platform_terms = ["iOS", "Android", "React Native", "Unity", "Cordova", "Web", "Swift", "Kotlin"]
        enhanced_query += " " + " ".join(platform_terms)
        print(f"🎯 Platform query detected, enhanced: {enhanced_query}")
    
    # Original enhancement logic
    turkish_to_english = {
        "nasıl": "how",
        "nerede": "where", 
        "ne": "what",
        "hangi": "which",
        "kurulum": "setup installation",
        "entegrasyon": "integration",
        "platform": "platform iOS Android",
        "bildirim": "notification push",
        "segment": "segment user",
        "kampanya": "campaign message",
        "analitik": "analytics report",
        "otomasyon": "automation journey",
        "ayar": "settings configuration"
    }
    
    if lang == "Türkçe":
        for tr_word, en_equivalent in turkish_to_english.items():
            if tr_word in enhanced_query.lower():
                enhanced_query += f" {en_equivalent}"
    
    return enhanced_query

def retrieve_node(retriever):
    def _inner(state: BotState) -> BotState:
        q = state["translated_query"]
        lang = state["lang"]
        
        # Preprocess query to add English terms
        enhanced_q = preprocess_query(q, lang)
        
        # Check if we're using the new hybrid GraphRAG retriever
        if isinstance(retriever, HybridGraphRAGRetriever):
            # Use new hybrid retrieval with GraphRAG
            hybrid_context = retriever.retrieve(enhanced_q, k=10)
            
            # Convert vector context to legacy format for compatibility
            items = hybrid_context.vector_context
            
            # Store graph context and routing info
            state["graph_context"] = hybrid_context.graph_context
            state["routing_info"] = hybrid_context.routing_info
            
            # Calculate confidence from hybrid result
            conf = hybrid_context.combined_confidence
            
        else:
            # Use legacy HybridRetriever
            items = retriever.retrieve(enhanced_q, k=10)
            state["graph_context"] = None
            state["routing_info"] = None
            
            # Better confidence calculation based on actual scores
            if items:
                max_score = max(item.get("score", 0) for item in items)
                # Normalize score to 0-1 range (scores can be > 1)
                conf = min(max_score / 1.5, 1.0)  # Lowered divisor for better confidence
            else:
                conf = 0.0
        
        state["docs"] = items
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
        graph_context = state.get("graph_context")
        routing_info = state.get("routing_info", {})
        
        # Enhanced context formatting with GraphRAG integration
        formatted_contexts = []
        
        # Add graph context if available
        if graph_context and graph_context.get("subgraph_info"):
            if lang == "Türkçe":
                formatted_contexts.append(f"=== KAVRAM HARİTASI ===\n{graph_context['subgraph_info']}\n")
            else:
                formatted_contexts.append(f"=== KNOWLEDGE GRAPH ===\n{graph_context['subgraph_info']}\n")
        
        # Add traditional document context
        for i, doc in enumerate(docs[:3], 1):  # Limit to top 3 most relevant
            text = doc.get("text", "")
            source = doc.get("url", "unknown")
            
            # Basic text cleanup
            text = text.strip()
            
            formatted_contexts.append(f"=== KAYNAK {i} ===\n{text}\n(URL: {source})\n")
        
        ctx = "\n".join(formatted_contexts)
        sys = SYSTEM_PROMPT
        
        # Enhanced prompting for hybrid context merging
        # Handle case when routing_info is None (GraphRAG disabled)
        if routing_info is not None:
            route_type = routing_info.get('route_type', 'vector')
            strategy = routing_info.get('strategy', 'balanced_hybrid')
        else:
            route_type = 'vector'
            strategy = 'traditional_hybrid'
        
        # Check if we have hybrid GraphRAG context
        if graph_context and hasattr(state.get("retriever"), "format_context_for_llm"):
            # Use enhanced formatting from HybridGraphRAGRetriever
            ctx = state["retriever"].format_context_for_llm(graph_context, q)
            
            if lang == "Türkçe":
                if strategy == "graph_first":
                    prompt = f"""Soru: {q}

{ctx}

Bu hibrit context'i kullanarak TÜRKÇE kapsamlı bir cevap verin. 
🎯 ÖNCELİK: Knowledge graph insights'larını birincil kaynak olarak kullanın, documentation'ı destekleyici detaylar için kullanın.
İlgili bileşenler, bağımlılıklar ve workflow'ları dahil edin."""
                elif strategy == "vector_first":
                    prompt = f"""Soru: {q}

{ctx}

Bu hibrit context'i kullanarak TÜRKÇE kapsamlı bir cevap verin.
🎯 ÖNCELİK: Documentation'ı birincil kaynak olarak kullanın, graph insights'ları ilişkiler ve context için kullanın.
Gerekirse adımlar halinde açıklayın."""
                else:  # balanced_hybrid
                    prompt = f"""Soru: {q}

{ctx}

Bu hibrit context'i kullanarak TÜRKÇE kapsamlı bir cevap verin.
🎯 DENGELI: Hem knowledge graph hem documentation bilgilerini eşit şekilde entegre edin.
İlişkiler, bağımlılıklar ve detaylı açıklamaları birlikte sunun."""
            else:
                if strategy == "graph_first":
                    prompt = f"""Question: {q}

{ctx}

Answer in ENGLISH using this hybrid context comprehensively.
🎯 PRIORITY: Use knowledge graph insights as primary source, documentation for supporting details.
Include related components, dependencies, and workflows."""
                elif strategy == "vector_first":
                    prompt = f"""Question: {q}

{ctx}

Answer in ENGLISH using this hybrid context comprehensively.
🎯 PRIORITY: Use documentation as primary source, graph insights for relationships and context.
Use steps if needed."""
                else:  # balanced_hybrid
                    prompt = f"""Question: {q}

{ctx}

Answer in ENGLISH using this hybrid context comprehensively.
🎯 BALANCED: Integrate both knowledge graph and documentation information equally.
Present relationships, dependencies, and detailed explanations together."""
        else:
            # Fallback to traditional routing for non-GraphRAG contexts
            if lang == "Türkçe":
                if route_type == "graph":
                    prompt = f"""Soru: {q}

Kaynak Bilgiler:
{ctx}

Yukarıdaki bilgileri ve kavram haritasındaki ilişkileri kullanarak TÜRKÇE kapsamlı bir cevap verin. İlgili bileşenler ve bağımlılıkları da dahil edin."""
                else:
                    prompt = f"""Soru: {q}

Belgeler:
{ctx}

Yukarıdaki belgeleri kullanarak TÜRKÇE cevap verin. Gerekirse adımlar halinde açıklayın."""
            else:
                if route_type == "graph":
                    prompt = f"""Question: {q}

Source Information:
{ctx}

Answer in ENGLISH using the above information and knowledge graph relationships. Include related components and dependencies."""
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

def build_app_graph(corpus_texts, corpus_meta, use_graphrag=True):
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    
    # Choose retriever based on flag
    if use_graphrag:
        retriever = HybridGraphRAGRetriever(corpus_texts, corpus_meta)
        print("🔗 GraphRAG hybrid retriever initialized")
    else:
        retriever = HybridRetriever(corpus_texts, corpus_meta)
        print("📊 Traditional hybrid retriever initialized")

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