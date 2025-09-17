"""
Query router to decide between FAISS vector search vs GraphRAG
"""

import re
import logging
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query type enumeration"""
    VECTOR = "vector"    # Use FAISS vector search
    GRAPH = "graph"      # Use GraphRAG
    HYBRID = "hybrid"    # Use both approaches

class RetrievalStrategy(Enum):
    """Retrieval strategy for hybrid context merging"""
    GRAPH_FIRST = "graph_first"      # Graph primary, vector fallback
    VECTOR_FIRST = "vector_first"    # Vector primary, graph fallback  
    BALANCED_HYBRID = "balanced_hybrid"  # Equal weight to both

class QueryRouter:
    """Routes queries to appropriate retrieval method"""
    
    def __init__(self):
        """Initialize query router with routing rules"""
        
        # Patterns that suggest graph-based retrieval (relationships, workflows)
        self.graph_patterns = [
            # Relationship queries
            r'\b(?:how|nasıl).*(?:connect|bağlan|relate|ilişki|depend|bağımlı)\b',
            r'\b(?:what|ne|hangi).*(?:affect|etkile|impact|sonuç|cause|neden)\b',
            r'\b(?:which|hangi).*(?:require|gerektir|need|ihtiyaç|depend|bağımlı)\b',
            
            # Workflow and process queries
            r'\b(?:step|adım|process|süreç|workflow|akış|procedure|prosedür)\b',
            r'\b(?:first|ilk|then|sonra|next|sonraki|after|sonra|before|önce)\b',
            r'\b(?:order|sıra|sequence|dizi|flow|akış)\b',
            
            # Integration and setup queries
            r'\b(?:integrate|entegre|setup|kurulum|configure|yapılandır|install|yükle)\b.*\b(?:with|ile|and|ve)\b',
            r'\b(?:prerequisite|ön\s*koşul|requirement|gereksinim|dependency|bağımlılık)\b',
            
            # Multi-component queries
            r'\b(?:both|her\s*ikisi|together|birlikte|combine|birleştir)\b',
            r'\b(?:between|arasında|across|boyunca|through|üzerinden)\b',
            
            # Comparison and difference queries
            r'\b(?:difference|fark|farklar|karşılaştır|compare|comparison)\b',
            r'\b(?:vs|versus|ile.*arasında|.*ile.*fark)\b',
            r'\b(?:iOS.*Android|Android.*iOS)\b',
            
            # Error and troubleshooting with context
            r'\b(?:error|hata|problem|sorun|issue|mesele).*(?:when|zaman|while|iken|during|sırasında)\b',
            r'\b(?:fix|düzelt|solve|çöz|resolve|çözümle).*(?:by|ile|using|kullanarak)\b',
        ]
        
        # Patterns that suggest vector-based retrieval (definitions, single concepts)
        self.vector_patterns = [
            # Definition queries
            r'\b(?:what\s+is|nedir|what\s+are|nelerdir|define|tanımla)\b',
            r'\b(?:explain|açıkla|describe|tarif\s+et|overview|genel\s+bakış)\b',
            
            # Simple parameter/setting queries
            r'\b(?:parameter|parametre|setting|ayar|option|seçenek|value|değer)\b',
            r'\b(?:default|varsayılan|example|örnek|sample|numune)\b',
            
            # Single feature queries
            r'\b(?:feature|özellik|function|fonksiyon|capability|yetenek)\b\s*(?!.*\b(?:with|ile|and|ve|together|birlikte)\b)',
            
            # Documentation lookup
            r'\b(?:documentation|dokümantasyon|guide|rehber|manual|kılavuz|reference|referans)\b',
            r'\b(?:code|kod|example|örnek|snippet|parça)\b\s*(?!.*\b(?:integration|entegrasyon|setup|kurulum)\b)',
        ]
        
        # Keywords that strongly suggest graph retrieval
        self.graph_keywords = [
            'workflow', 'akış', 'integration', 'entegrasyon', 'setup', 'kurulum',
            'configure', 'yapılandır', 'implement', 'uygula', 'dependency', 'bağımlılık',
            'prerequisite', 'önkoşul', 'requirement', 'gereksinim', 'process', 'süreç',
            'procedure', 'prosedür', 'flow', 'akış', 'connect', 'bağlan', 'relationship', 'ilişki'
        ]
        
        # Keywords that strongly suggest vector retrieval
        self.vector_keywords = [
            'definition', 'tanım', 'explain', 'açıkla', 'overview', 'genel bakış',
            'parameter', 'parametre', 'setting', 'ayar', 'example', 'örnek',
            'documentation', 'dokümantasyon', 'reference', 'referans', 'guide', 'rehber'
        ]
        
        # Compile regex patterns
        self.compiled_graph_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.graph_patterns]
        self.compiled_vector_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.vector_patterns]
    
    def route_query(self, query: str) -> Dict[str, any]:
        """Route query with hybrid context merging strategy"""
        query_lower = query.lower().strip()
        
        # Calculate scores for each approach
        graph_score = self._calculate_graph_score(query_lower)
        vector_score = self._calculate_vector_score(query_lower)
        
        logger.debug(f"Query routing scores - Graph: {graph_score}, Vector: {vector_score}")
        
        # Determine primary strategy and context merging approach
        if graph_score > vector_score + 0.3:  # Strong graph preference
            strategy = RetrievalStrategy.GRAPH_FIRST
            primary_method = QueryType.GRAPH
        elif vector_score > graph_score + 0.3:  # Strong vector preference
            strategy = RetrievalStrategy.VECTOR_FIRST  
            primary_method = QueryType.VECTOR
        else:  # Balanced or close scores - always use both
            strategy = RetrievalStrategy.BALANCED_HYBRID
            primary_method = QueryType.HYBRID
        
        return {
            'route_type': primary_method,
            'strategy': strategy,
            'graph_score': graph_score,
            'vector_score': vector_score,
            'use_context_merging': True,  # Always true for hybrid approach
            'reasoning': self._get_strategy_reasoning(strategy, graph_score, vector_score)
        }
    
    def _calculate_graph_score(self, query: str) -> float:
        """Calculate graph retrieval score"""
        score = 0.0
        
        # Pattern matching
        for pattern in self.compiled_graph_patterns:
            if pattern.search(query):
                score += 0.3
        
        # Keyword matching
        for keyword in self.graph_keywords:
            if keyword in query:
                score += 0.2
        
        # Multi-entity indicators
        if self._count_entities_in_query(query) >= 2:
            score += 0.4
        
        # Question words that suggest relationships
        relationship_words = ['how', 'nasıl', 'why', 'neden', 'when', 'ne zaman', 'where', 'nerede']
        for word in relationship_words:
            if word in query:
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_vector_score(self, query: str) -> float:
        """Calculate vector retrieval score"""
        score = 0.0
        
        # Pattern matching
        for pattern in self.compiled_vector_patterns:
            if pattern.search(query):
                score += 0.3
        
        # Keyword matching
        for keyword in self.vector_keywords:
            if keyword in query:
                score += 0.2
        
        # Simple question indicators
        simple_starters = ['what is', 'nedir', 'what are', 'nelerdir', 'explain', 'açıkla']
        for starter in simple_starters:
            if query.startswith(starter):
                score += 0.4
                break
        
        # Single concept queries (short queries often want definitions)
        if len(query.split()) <= 4:
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _count_entities_in_query(self, query: str) -> int:
        """Count potential entities in query"""
        # Simple heuristic: look for technical terms, camelCase, etc.
        entity_indicators = [
            'sdk', 'api', 'ios', 'android', 'gradle', 'push', 'notification',
            'campaign', 'segment', 'analytics', 'netmera', 'config', 'setup',
            'installation', 'integration', 'error', 'exception'
        ]
        
        count = 0
        for indicator in entity_indicators:
            if indicator in query:
                count += 1
        
        # Look for camelCase or PascalCase (likely entity names)
        camel_case_pattern = r'\b[a-z]+[A-Z][a-zA-Z]*\b'
        pascal_case_pattern = r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b'
        
        count += len(re.findall(camel_case_pattern, query))
        count += len(re.findall(pascal_case_pattern, query))
        
        return count
    
    def get_routing_explanation(self, query: str) -> Dict[str, any]:
        """Get detailed explanation of routing decision"""
        query_lower = query.lower().strip()
        
        routing_result = self.route_query(query)
        
        # Find matching patterns
        matching_graph_patterns = []
        for i, pattern in enumerate(self.compiled_graph_patterns):
            if pattern.search(query_lower):
                matching_graph_patterns.append(self.graph_patterns[i])
        
        matching_vector_patterns = []
        for i, pattern in enumerate(self.compiled_vector_patterns):
            if pattern.search(query_lower):
                matching_vector_patterns.append(self.vector_patterns[i])
        
        return {
            'query': query,
            'route_type': routing_result['route_type'].value,
            'strategy': routing_result['strategy'].value,
            'graph_score': routing_result['graph_score'],
            'vector_score': routing_result['vector_score'],
            'matching_graph_patterns': matching_graph_patterns,
            'matching_vector_patterns': matching_vector_patterns,
            'entity_count': self._count_entities_in_query(query_lower),
            'reasoning': routing_result['reasoning']
        }
    
    def _get_strategy_reasoning(self, strategy: RetrievalStrategy, graph_score: float, vector_score: float) -> str:
        """Get human-readable reasoning for strategy decision"""
        if strategy == RetrievalStrategy.GRAPH_FIRST:
            return f"Graph-first strategy (Graph: {graph_score:.2f}, Vector: {vector_score:.2f}) - Primary focus on relationships, vector as context enrichment"
        elif strategy == RetrievalStrategy.VECTOR_FIRST:
            return f"Vector-first strategy (Vector: {vector_score:.2f}, Graph: {graph_score:.2f}) - Primary focus on definitions, graph as relationship context"
        elif strategy == RetrievalStrategy.BALANCED_HYBRID:
            return f"Balanced hybrid strategy (Graph: {graph_score:.2f}, Vector: {vector_score:.2f}) - Equal weight to both graph and vector contexts"
        else:
            return "Unknown strategy"

