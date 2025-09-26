from typing import List, Dict, Any
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from nltk.tokenize import word_tokenize

from src.config import BM25_WEIGHT, FAISS_WEIGHT, FUZZY_WEIGHT, FAISS_STORE_PATH
from src.query_enhancer_v2 import QueryEnhancer

class HybridRetriever:
    def __init__(self, corpus_texts: List[str], corpus_meta: List[Dict[str, Any]]):
        # BM25
        self._tokenized = [word_tokenize(t.lower(), preserve_line=True) for t in corpus_texts]
        self._bm25 = BM25Okapi(self._tokenized)

        # FAISS (LangChain)
        self.emb = OpenAIEmbeddings()
        self.vs = FAISS.load_local(
            FAISS_STORE_PATH, self.emb,
            allow_dangerous_deserialization=True
        )

        # Metin/metaveri (fuzzy ve kaynak eşlemesi için)
        self._corpus_texts = corpus_texts
        self._corpus_meta  = corpus_meta  # [{"source":..., "url":...}, ...]
        
        # Query enhancer for better retrieval
        self.query_enhancer = QueryEnhancer()

    def _score_doc(self, q_tokens, q_text, idx, faiss_sim) -> float:
        # BM25 normalize
        bm25_scores = self._bm25.get_scores(q_tokens)
        mean = float(np.mean(bm25_scores))
        std  = float(np.std(bm25_scores) or 1.0)
        bm25_norm = (bm25_scores[idx] - mean) / std

        # Fuzzy (kırpılmış ilk 1000 char)
        fuzzy = fuzz.partial_ratio(q_text.lower(), self._corpus_texts[idx][:1000].lower()) / 100.0

        return BM25_WEIGHT*bm25_norm + FAISS_WEIGHT*faiss_sim + FUZZY_WEIGHT*fuzzy

    def retrieve(self, query: str, k: int = 6):
        # Enhanced query processing
        enhancement = self.query_enhancer.enhance_query_for_retrieval(query)
        query_type = enhancement['query_type']
        expanded_queries = enhancement['expanded_queries']
        optimal_k = enhancement['optimal_k']
        
        print(f"🔍 Query enhancement: {query_type}, K={optimal_k}, expansions={len(expanded_queries)}")
        
        # Use optimal K, but ensure we have enough for hybrid scoring
        faiss_k = max(optimal_k * 2, 20)  # At least 20 for good hybrid scoring
        
        # Collect results from all expanded queries
        all_faiss_docs = []
        seen_content = set()
        
        for expanded_query in expanded_queries:
            try:
                faiss_docs = self.vs.similarity_search_with_score(expanded_query, k=faiss_k)
                
                for doc, sim in faiss_docs:
                    # Use first 100 chars as unique identifier
                    content_id = hash(doc.page_content[:100])
                    
                    if content_id not in seen_content:
                        seen_content.add(content_id)
                        all_faiss_docs.append((doc, sim))
                        
            except Exception as e:
                print(f"⚠️ Error with expanded query '{expanded_query}': {e}")
                continue
        
        # If no results from expanded queries, fallback to original
        if not all_faiss_docs:
            all_faiss_docs = self.vs.similarity_search_with_score(query, k=faiss_k)
        
        # FAISS map: doc_id (biz metadata'dan source ile eşleştiririz)
        # Ancak LangChain dökümanlarını kendi corpus dizilerimizle bağlamak için
        # basit bir heuristic: text eşleşmesi üzerinden indeks bul.
        q_tokens = word_tokenize(query.lower(), preserve_line=True)
        candidates = []
        
        for doc, sim in all_faiss_docs:
            # text -> index tespiti (pratik ve hızlı; istersen metadata ile daha deterministik yap)
            try:
                idx = self._corpus_texts.index(doc.page_content)
            except ValueError:
                continue
                
            # Original hybrid score
            hybrid_score = self._score_doc(q_tokens, query, idx, sim)
            
            # Enhanced relevance score
            relevance_score = self.query_enhancer.calculate_relevance_score(
                doc.page_content, 
                doc.metadata, 
                query, 
                query_type
            )
            
            # Combine scores (give more weight to relevance for better ranking)
            final_score = (hybrid_score * 0.4) + (relevance_score * 0.6)
            
            candidates.append((idx, final_score, hybrid_score, relevance_score))

        if not candidates:
            return []

        # Skora göre sırala (final_score kullan)
        best = sorted(candidates, key=lambda x: x[1], reverse=True)[:optimal_k]
        out = []
        
        for idx, final_score, hybrid_score, relevance_score in best:
            meta = self._corpus_meta[idx]
            
            # Add debug info for enhanced queries (all types)
            debug_info = ""
            if query_type != "general":
                debug_info = f" [type:{query_type}, hybrid:{hybrid_score:.2f}, relevance:{relevance_score:.2f}]"
            
            out.append({
                "text": self._corpus_texts[idx],
                "score": float(final_score),
                "source": meta.get("source", "") + debug_info,
                "url": meta.get("url")
            })
            
        print(f"✅ Enhanced retrieval: {len(out)} results (type: {query_type})")
        return out