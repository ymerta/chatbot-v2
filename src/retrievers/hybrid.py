from typing import List, Dict, Any
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from nltk.tokenize import word_tokenize

from src.config import BM25_WEIGHT, FAISS_WEIGHT, FUZZY_WEIGHT, FAISS_STORE_PATH

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
        # FAISS top-k (LangChain üzerinden)
        faiss_docs = self.vs.similarity_search_with_score(query, k=50)  # daha geniş havuz
        # FAISS map: doc_id (biz metadata'dan source ile eşleştiririz)
        # Ancak LangChain dökümanlarını kendi corpus dizilerimizle bağlamak için
        # basit bir heuristic: text eşleşmesi üzerinden indeks bul.
        q_tokens = word_tokenize(query.lower(), preserve_line=True)
        candidates = []
        for doc, sim in faiss_docs:
            # text -> index tespiti (pratik ve hızlı; istersen metadata ile daha deterministik yap)
            try:
                idx = self._corpus_texts.index(doc.page_content)
            except ValueError:
                continue
            score = self._score_doc(q_tokens, query, idx, sim)
            candidates.append((idx, score))

        if not candidates:
            return []

        # Skora göre sırala
        best = sorted(candidates, key=lambda x: x[1], reverse=True)[:k]
        out = []
        for idx, score in best:
            meta = self._corpus_meta[idx]
            out.append({
                "text": self._corpus_texts[idx],
                "score": float(score),
                "source": meta.get("source"),
                "url": meta.get("url")
            })
        return out