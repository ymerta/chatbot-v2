import json
from rapidfuzz import fuzz

class FAQMatcher:
    def __init__(self, faq_path: str):
        with open(faq_path, "r", encoding="utf-8") as f:
            self.faq_qa_map = json.load(f)

    def check(self, query: str, threshold: int = 70):
        best = (None, -1, None) 
        for key, entry in self.faq_qa_map.items():
            score = fuzz.partial_ratio(query.lower(), key.replace("_", " ").lower())
            if score > best[1]:
                best = (entry["answer"], score, entry.get("source"))
        if best[1] >= threshold:
            return {"answer": best[0], "source": best[2]}
        return None