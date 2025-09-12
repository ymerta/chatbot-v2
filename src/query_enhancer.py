"""
Enhanced Query Preprocessing for Better Retrieval
Specifically targets the failed queries in the screenshot
"""

import re
from typing import List, Dict

class QueryEnhancer:
    """Enhanced query preprocessing for better retrieval results"""
    
    def __init__(self):
        # Turkish to English technical term mapping
        self.turkish_tech_terms = {
            # Error/Problem terms
            "hata": ["error", "issue", "problem"],
            "sorun": ["problem", "issue", "trouble", "error"],
            "limit": ["limit", "size", "payload", "quota", "restriction"],
            "boyut": ["size", "payload", "limit", "length"],
            "aştım": ["exceed", "over", "limit", "maximum"],
            "alıyorum": ["getting", "receiving", "encountering"],
            
            # Network/Access terms
            "ip": ["ip address", "network", "connection"],
            "adres": ["address", "location", "endpoint"],
            "adresim": ["my address", "my ip", "address"],
            "engel": ["block", "blocked", "restrict", "ban"],
            "engellenmiş": ["blocked", "restricted", "banned"],
            "yapabilirim": ["can do", "solution", "fix", "resolve"],
            
            # Technical integration terms
            "entegrasyon": ["integration", "integrate", "setup"],
            "modül": ["module", "component", "feature"],
            "url": ["url", "link", "endpoint", "address"],
            "onay": ["consent", "approval", "permission"],
            "teslimat": ["delivery", "send", "dispatch"],
            
            # Communication terms
            "mesaj": ["message", "notification", "push"],
            "push": ["push notification", "notification", "alert"],
            "e-posta": ["email", "mail", "electronic mail"],
            "email": ["email", "e-mail", "mail", "messaging"]
        }
        
        # Common error patterns and their expansions
        self.error_patterns = {
            "push.*boyut.*limit": ["push notification size limit", "payload size", "message size"],
            "ip.*engel": ["ip blocked", "network blocked", "access denied"],
            "integrated.*modules": ["integration modules", "platform integration"],
            "email.*delivery": ["email delivery", "mail sending", "email onboarding"]
        }
        
        # Technical synonyms for better matching
        self.technical_synonyms = {
            "integration": ["entegrasyon", "setup", "configuration", "install"],
            "module": ["modül", "component", "feature", "plugin"],
            "delivery": ["teslimat", "sending", "dispatch", "transmission"],
            "onboarding": ["setup", "configuration", "initialization"],
            "consent": ["onay", "permission", "approval", "authorization"],
            "blocked": ["engel", "banned", "restricted", "denied"],
            "limit": ["boyut", "size", "quota", "maximum", "threshold"]
        }

    def enhance_query(self, query: str, lang: str = "turkish") -> str:
        """
        Enhanced query preprocessing with multiple strategies
        """
        original_query = query
        enhanced_query = query.lower()
        
        # 1. Turkish technical term translation
        if lang.lower() in ["türkçe", "turkish", "tr"]:
            enhanced_query = self._translate_turkish_terms(enhanced_query)
        
        # 2. Pattern-based expansion
        enhanced_query = self._expand_error_patterns(enhanced_query)
        
        # 3. Technical synonym expansion
        enhanced_query = self._add_technical_synonyms(enhanced_query)
        
        # 4. Specific fixes for screenshot queries
        enhanced_query = self._fix_specific_patterns(enhanced_query)
        
        # 5. Clean and deduplicate
        enhanced_query = self._clean_query(enhanced_query)
        
        print(f"🔧 Query enhanced: '{original_query}' -> '{enhanced_query}'")
        return enhanced_query

    def _translate_turkish_terms(self, query: str) -> str:
        """Translate Turkish technical terms to English"""
        for turkish, english_terms in self.turkish_tech_terms.items():
            if turkish in query:
                # Add English equivalents
                query += " " + " ".join(english_terms)
        return query

    def _expand_error_patterns(self, query: str) -> str:
        """Expand common error patterns"""
        for pattern, expansions in self.error_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                query += " " + " ".join(expansions)
        return query

    def _add_technical_synonyms(self, query: str) -> str:
        """Add technical synonyms for better matching"""
        words = query.split()
        for word in words:
            if word in self.technical_synonyms:
                query += " " + " ".join(self.technical_synonyms[word])
        return query

    def _fix_specific_patterns(self, query: str) -> str:
        """Specific fixes for known failing patterns"""
        
        # Push message size limit
        if "push" in query and ("boyut" in query or "limit" in query):
            query += " push notification payload size maximum length restriction"
        
        # IP blocking issues
        if "ip" in query and ("engel" in query or "block" in query):
            query += " ip address blocked network access denied whitelist firewall"
        
        # Integration modules
        if "integration" in query and "module" in query:
            query += " platform integration setup configuration api"
        
        # Email delivery
        if "email" in query and "delivery" in query:
            query += " email sending mail delivery smtp configuration"
        
        # Consent/URL issues
        if "consent" in query or "url" in query:
            query += " consent management url configuration privacy"
            
        return query

    def _clean_query(self, query: str) -> str:
        """Clean and deduplicate query terms"""
        # Remove extra spaces
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Remove duplicates while preserving order
        words = query.split()
        seen = set()
        cleaned_words = []
        for word in words:
            if word.lower() not in seen:
                cleaned_words.append(word)
                seen.add(word.lower())
        
        return " ".join(cleaned_words)

# Integration with existing preprocess_query function
def enhanced_preprocess_query(query: str, lang: str) -> str:
    """
    Drop-in replacement for existing preprocess_query function
    """
    enhancer = QueryEnhancer()
    
    # Apply existing logic
    enhanced_query = query
    
    # Turkish-English mapping (existing logic)
    tr_en_map = {
        "push bildirimi": "push notification",
        "itme bildirim": "push notification", 
        "segment": "user segment",
        "kampanya": "campaign",
        "analitik": "analytics",
        "otomasyon": "automation",
        "yolculuk": "journey",
        "entegrasyon": "integration"
    }
    
    for tr_term, en_term in tr_en_map.items():
        if tr_term in enhanced_query.lower():
            enhanced_query += f" {en_term}"
    
    # Apply new enhancement
    enhanced_query = enhancer.enhance_query(enhanced_query, lang)
    
    return enhanced_query


# Test function for specific failing queries
def test_query_enhancement():
    """Test enhancement on specific failing queries"""
    enhancer = QueryEnhancer()
    
    test_queries = [
        "Push mesaj boyutu limitini aştım hatası alıyorum",
        "IP adresim engellenmiş, ne yapabilirim?",
        "Integrated Modules Via Integration Short Url Consent Requests",
        "Email Delivery Onboarding"
    ]
    
    print("🧪 Testing Query Enhancement")
    print("=" * 50)
    
    for query in test_queries:
        enhanced = enhancer.enhance_query(query)
        print(f"Original: {query}")
        print(f"Enhanced: {enhanced}")
        print("-" * 30)

if __name__ == "__main__":
    test_query_enhancement()
