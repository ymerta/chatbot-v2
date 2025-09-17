"""
Query expansion and reformulation for Netmera domain-specific terminology
Provides semantic bridging between Turkish/English and technical concepts
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExpandedQuery:
    """Result of query expansion"""
    original_query: str
    expanded_query: str
    added_terms: List[str]
    detected_entities: List[str]
    language: str
    expansion_confidence: float

class NetmeraTaxonomy:
    """Netmera domain-specific taxonomy and synonym mapping"""
    
    def __init__(self):
        """Initialize Netmera terminology mappings"""
        
        # Core Netmera concept mappings (bidirectional)
        self.concept_mappings = {
            # Audience & Segmentation
            "segment": ["audience", "segmentation", "user group", "kullanıcı grubu", "hedef kitle"],
            "audience": ["segment", "target group", "hedef kitle", "kullanıcı segmenti"],
            "targeting": ["hedefleme", "target", "segment selection", "kitle seçimi"],
            
            # Campaign & Messaging
            "kampanya": ["campaign", "messaging", "mesajlaşma", "bildirim kampanyası"],
            "campaign": ["kampanya", "messaging campaign", "notification campaign"],
            "journey": ["flow", "akış", "süreç", "kullanıcı yolculuğu", "user journey"],
            "flow": ["journey", "akış", "workflow", "süreç", "adım"],
            
            # Notification Types
            "push": ["push notification", "bildirim", "anlık bildirim", "mobil bildirim"],
            "webpush": ["web push", "web notification", "browser notification", "tarayıcı bildirimi"],
            "email": ["e-posta", "mail", "electronic mail", "elektronik posta"],
            "sms": ["text message", "kısa mesaj", "metin mesajı"],
            "in-app": ["uygulama içi", "in-app message", "app message"],
            
            # Permissions & Consent
            "izin": ["permission", "consent", "onay", "approval", "rıza"],
            "permission": ["izin", "consent", "approval", "onay"],
            "iys": ["permission management", "izin yönetimi", "consent management"],
            "opt-in": ["izin verme", "kayıt olma", "subscription"],
            "opt-out": ["izin iptal", "abonelik iptal", "unsubscribe"],
            
            # Technical Integration
            "sdk": ["software development kit", "geliştirme kiti", "entegrasyon"],
            "api": ["application programming interface", "programlama arayüzü"],
            "webhook": ["callback", "geri çağırma", "endpoint"],
            "token": ["api key", "authentication token", "kimlik doğrulama"],
            
            # Platforms & Technology
            "ios": ["iphone", "ipad", "apple", "objective-c", "swift"],
            "android": ["google", "java", "kotlin", "play store"],
            "react native": ["rn", "cross-platform", "hybrid app"],
            "flutter": ["dart", "cross-platform", "hybrid"],
            
            # Analytics & Tracking
            "analytics": ["analitik", "tracking", "izleme", "measurement", "ölçümleme"],
            "event": ["olay", "action", "eylem", "activity", "etkinlik"],
            "attribution": ["attribution", "kaynak takibi", "source tracking"],
            
            # UI Components
            "buton seti": ["button set", "action buttons", "cta buttons"],
            "button set": ["buton seti", "action buttons", "call-to-action"],
            "template": ["şablon", "layout", "design template"],
            
            # Localization
            "çok dilli": ["multi-language", "multilingual", "internationalization", "i18n"],
            "multi-language": ["çok dilli", "multilingual", "localization"],
            "türkçe": ["turkish", "tr", "turkey"],
            "english": ["ingilizce", "en", "international"],
        }
        
        # Technical error patterns
        self.error_patterns = {
            "hata": ["error", "exception", "failure", "issue", "problem"],
            "sorun": ["problem", "trouble", "issue", "difficulty"],
            "çökmə": ["crash", "failure", "breakdown"],
            "timeout": ["zaman aşımı", "connection timeout", "network timeout"],
            "401": ["unauthorized", "authentication error", "token invalid"],
            "403": ["forbidden", "permission denied", "access denied"],
            "404": ["not found", "endpoint not found", "resource missing"],
            "429": ["rate limit", "too many requests", "quota exceeded"],
            "500": ["server error", "internal error", "backend failure"],
        }
        
        # Platform-specific terms
        self.platform_terms = {
            "gradle": ["build system", "dependency management", "android build"],
            "cocoapods": ["ios dependency", "pod", "ios library management"],
            "npm": ["node package", "javascript dependency", "web package"],
            "maven": ["java dependency", "build tool"],
            "manifest": ["android manifest", "permission declaration"],
            "info.plist": ["ios configuration", "app settings", "ios manifest"],
            "firebase": ["fcm", "google messaging", "cloud messaging"],
            "apns": ["apple push", "ios notifications", "apple notification service"],
        }
        
        # Create reverse mappings for efficient lookup
        self.all_mappings = {}
        for main_term, synonyms in self.concept_mappings.items():
            self.all_mappings[main_term.lower()] = synonyms
            for synonym in synonyms:
                if synonym.lower() not in self.all_mappings:
                    self.all_mappings[synonym.lower()] = [main_term] + [s for s in synonyms if s != synonym]
        
        # Add error and platform terms
        for main_term, synonyms in {**self.error_patterns, **self.platform_terms}.items():
            self.all_mappings[main_term.lower()] = synonyms
            for synonym in synonyms:
                if synonym.lower() not in self.all_mappings:
                    self.all_mappings[synonym.lower()] = [main_term] + [s for s in synonyms if s != synonym]

class QueryExpander:
    """Expands queries with Netmera domain knowledge and semantic bridging"""
    
    def __init__(self):
        """Initialize query expander with Netmera taxonomy"""
        self.taxonomy = NetmeraTaxonomy()
        
        # Language detection patterns
        self.turkish_chars = set("çğıöşü")
        
        # Entity extraction patterns
        self.entity_patterns = [
            r'\b(?:Netmera|netmera)\b',  # Company name
            r'\b(?:SDK|API|FCM|APNS|iOS|Android)\b',  # Technical terms
            r'\b(?:push|notification|campaign|segment)\b',  # Core concepts
            r'\b(?:React\s+Native|Flutter|Xamarin)\b',  # Frameworks
            r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b',  # CamelCase (likely entity names)
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.entity_patterns]
    
    def detect_language(self, query: str) -> str:
        """Detect query language (Turkish vs English)"""
        query_lower = query.lower()
        turkish_char_count = sum(1 for char in query_lower if char in self.turkish_chars)
        return "tr" if turkish_char_count > 0 else "en"
    
    def extract_entities(self, query: str) -> List[str]:
        """Extract potential entities from query"""
        entities = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(query)
            entities.extend(matches)
        
        # Deduplicate and clean
        return list(set([entity.strip() for entity in entities if entity.strip()]))
    
    def find_synonyms(self, term: str) -> List[str]:
        """Find synonyms for a given term using taxonomy"""
        term_lower = term.lower().strip()
        
        # Direct lookup
        if term_lower in self.taxonomy.all_mappings:
            return self.taxonomy.all_mappings[term_lower][:5]  # Limit to top 5
        
        # Partial matching for compound terms
        synonyms = []
        for key, values in self.taxonomy.all_mappings.items():
            if term_lower in key or key in term_lower:
                synonyms.extend(values[:3])  # Fewer for partial matches
        
        return list(set(synonyms))[:5]  # Deduplicate and limit
    
    def expand_query(self, query: str, max_expansion_terms: int = 8) -> ExpandedQuery:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original user query
            max_expansion_terms: Maximum number of expansion terms to add
            
        Returns:
            ExpandedQuery with expanded terms and metadata
        """
        logger.debug(f"Expanding query: {query}")
        
        # Detect language
        language = self.detect_language(query)
        
        # Extract entities
        entities = self.extract_entities(query)
        
        # Find expansion terms
        expansion_terms = []
        query_words = query.lower().split()
        
        # Expand individual words and detected entities
        terms_to_expand = set(query_words + [e.lower() for e in entities])
        
        for term in terms_to_expand:
            synonyms = self.find_synonyms(term)
            expansion_terms.extend(synonyms)
        
        # Remove duplicates and terms already in query
        unique_expansions = []
        query_lower = query.lower()
        for term in expansion_terms:
            if (term.lower() not in query_lower and 
                term not in unique_expansions and 
                len(term.strip()) > 2):  # Skip very short terms
                unique_expansions.append(term)
        
        # Limit expansion terms
        limited_expansions = unique_expansions[:max_expansion_terms]
        
        # Build expanded query
        if limited_expansions:
            expanded_query = f"{query} {' '.join(limited_expansions)}"
            expansion_confidence = min(len(limited_expansions) / max_expansion_terms, 1.0)
        else:
            expanded_query = query
            expansion_confidence = 0.0
        
        logger.debug(f"Added {len(limited_expansions)} expansion terms: {limited_expansions}")
        
        return ExpandedQuery(
            original_query=query,
            expanded_query=expanded_query,
            added_terms=limited_expansions,
            detected_entities=entities,
            language=language,
            expansion_confidence=expansion_confidence
        )
    
    def create_cross_language_variants(self, query: str) -> List[str]:
        """Create cross-language query variants for better coverage"""
        variants = [query]
        language = self.detect_language(query)
        
        # Add translations for key terms
        words = query.split()
        translated_variants = []
        
        for word in words:
            synonyms = self.find_synonyms(word)
            # Filter synonyms to opposite language
            if language == "tr":
                en_synonyms = [s for s in synonyms if not any(c in self.turkish_chars for c in s.lower())]
                translated_variants.extend(en_synonyms[:2])
            else:
                tr_synonyms = [s for s in synonyms if any(c in self.turkish_chars for c in s.lower())]
                translated_variants.extend(tr_synonyms[:2])
        
        if translated_variants:
            cross_lang_query = f"{query} {' '.join(translated_variants[:4])}"
            variants.append(cross_lang_query)
        
        return variants
    
    def should_expand_query(self, initial_results_count: int, confidence: float) -> bool:
        """Determine if query should be expanded based on initial results"""
        # Expand if:
        # 1. Very few results (< 3)
        # 2. Low confidence (< 0.4)
        # 3. No results at all
        return (initial_results_count < 3 or 
                confidence < 0.4 or 
                initial_results_count == 0)
    
    def get_stats(self) -> Dict[str, any]:
        """Get expander statistics"""
        return {
            "taxonomy_terms": len(self.taxonomy.all_mappings),
            "concept_mappings": len(self.taxonomy.concept_mappings),
            "error_patterns": len(self.taxonomy.error_patterns),
            "platform_terms": len(self.taxonomy.platform_terms),
            "entity_patterns": len(self.entity_patterns)
        }
