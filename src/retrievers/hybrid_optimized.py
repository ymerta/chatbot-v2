"""
Optimized Hybrid Retriever - Better handling of failed queries
"""

from typing import List, Dict, Any
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from nltk.tokenize import word_tokenize

from src.config import BM25_WEIGHT, FAISS_WEIGHT, FUZZY_WEIGHT, FAISS_STORE_PATH

class OptimizedHybridRetriever:
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

        # Metin/metaveri
        self._corpus_texts = corpus_texts
        self._corpus_meta = corpus_meta
        
        # 🔧 OPTIMIZATION: Pre-compute text to index mapping
        self._text_to_idx = {text: idx for idx, text in enumerate(corpus_texts)}

    def _score_doc(self, q_tokens, q_text, idx, faiss_sim) -> float:
        """Optimized scoring with better normalization"""
        # 🔧 IMPROVED: Better BM25 normalization
        bm25_scores = self._bm25.get_scores(q_tokens)
        
        # Use percentile-based normalization instead of z-score
        bm25_percentile = np.percentile(bm25_scores, 95)  # 95th percentile as max
        bm25_norm = min(bm25_scores[idx] / (bm25_percentile or 1.0), 1.0)
        
        # 🔧 IMPROVED: Enhanced FAISS score handling
        # FAISS scores can be > 1, normalize to 0-1 range
        faiss_norm = min(faiss_sim / 1.5, 1.0)  # Adjust based on your score distribution
        
        # Fuzzy (only if enabled)
        fuzzy = 0
        if FUZZY_WEIGHT > 0:
            fuzzy = fuzz.partial_ratio(q_text.lower(), self._corpus_texts[idx][:1000].lower()) / 100.0

        # 🔧 OPTIMIZED: Weighted combination with boost for high scores
        base_score = BM25_WEIGHT * bm25_norm + FAISS_WEIGHT * faiss_norm + FUZZY_WEIGHT * fuzzy
        
        # Boost if both BM25 and FAISS agree (high relevance)
        if bm25_norm > 0.5 and faiss_norm > 0.5:
            base_score *= 1.2  # 20% boost for consensus
            
        return base_score

    def retrieve(self, query: str, k: int = 10, min_threshold: float = 0.1) -> List[Dict]:
        """
        Optimized retrieval with fallback strategies
        
        Args:
            k: Number of results to return (increased from 6)
            min_threshold: Minimum score threshold (lowered from default)
        """
        try:
            # 🔧 OPTIMIZATION 1: Get more candidates from FAISS
            faiss_docs = self.vs.similarity_search_with_score(query, k=min(100, len(self._corpus_texts)))
            
            if not faiss_docs:
                return self._fallback_retrieve(query, k)
            
            # 🔧 OPTIMIZATION 2: Faster text-to-index mapping
            q_tokens = word_tokenize(query.lower(), preserve_line=True)
            candidates = []
            
            for doc, sim in faiss_docs:
                # Use pre-computed mapping for faster lookup
                idx = self._text_to_idx.get(doc.page_content)
                if idx is None:
                    continue
                    
                score = self._score_doc(q_tokens, query, idx, sim)
                candidates.append((idx, score))

            if not candidates:
                return self._fallback_retrieve(query, k)

            # 🔧 OPTIMIZATION 3: Better filtering and ranking
            # Filter by minimum threshold
            candidates = [(idx, score) for idx, score in candidates if score >= min_threshold]
            
            if not candidates:
                # If no candidates meet threshold, lower it and try again
                candidates = [(idx, score) for idx, score in candidates if score >= min_threshold / 2]
            
            # Sort and limit
            best = sorted(candidates, key=lambda x: x[1], reverse=True)[:k]
            
            # 🔧 OPTIMIZATION 4: Enhanced result formatting
            out = []
            for idx, score in best:
                meta = self._corpus_meta[idx]
                result = {
                    "text": self._corpus_texts[idx],
                    "score": float(score),
                    "source": meta.get("source", "unknown"),
                    "url": meta.get("url", ""),
                    "confidence": min(score, 1.0)  # Add confidence field
                }
                out.append(result)
            
            return out
            
        except Exception as e:
            print(f"❌ Retrieval error: {e}")
            return self._fallback_retrieve(query, k)

    def _fallback_retrieve(self, query: str, k: int) -> List[Dict]:
        """
        Fallback retrieval strategy for failed queries
        Uses only BM25 with very low threshold
        """
        try:
            q_tokens = word_tokenize(query.lower(), preserve_line=True)
            bm25_scores = self._bm25.get_scores(q_tokens)
            
            # Get top BM25 results even with low scores
            top_indices = np.argsort(bm25_scores)[-k:][::-1]
            
            results = []
            for idx in top_indices:
                if bm25_scores[idx] > 0:  # Any positive score
                    meta = self._corpus_meta[idx]
                    results.append({
                        "text": self._corpus_texts[idx],
                        "score": float(bm25_scores[idx]),
                        "source": meta.get("source", "unknown"),
                        "url": meta.get("url", ""),
                        "confidence": min(bm25_scores[idx] / 10.0, 1.0),  # Very conservative confidence
                        "fallback": True  # Mark as fallback result
                    })
            
            print(f"🔄 Using fallback retrieval, found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"❌ Fallback retrieval also failed: {e}")
            return []

    def retrieve_with_expansion(self, query: str, expansion_terms: List[str], k: int = 10) -> List[Dict]:
        """
        Retrieve with query expansion - useful for technical terms
        """
        # Try original query first
        results = self.retrieve(query, k=k//2)
        
        # If poor results, try with expansion
        if not results or (results and results[0].get("confidence", 0) < 0.3):
            expanded_query = query + " " + " ".join(expansion_terms)
            expanded_results = self.retrieve(expanded_query, k=k//2)
            
            # Combine and deduplicate
            all_results = results + expanded_results
            seen_texts = set()
            unique_results = []
            
            for result in all_results:
                text_key = result["text"][:100]  # Use first 100 chars as key
                if text_key not in seen_texts:
                    unique_results.append(result)
                    seen_texts.add(text_key)
            
            # Re-sort by score
            unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return unique_results[:k]
        
        return results

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        return {
            "total_documents": len(self._corpus_texts),
            "bm25_weight": BM25_WEIGHT,
            "faiss_weight": FAISS_WEIGHT,
            "fuzzy_weight": FUZZY_WEIGHT,
            "avg_doc_length": np.mean([len(text) for text in self._corpus_texts]),
            "embedding_model": "text-embedding-3-large"
        }

# Backward compatibility alias
HybridRetriever = OptimizedHybridRetriever
