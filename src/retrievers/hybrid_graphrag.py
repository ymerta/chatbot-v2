"""
Hybrid retriever combining FAISS vector search with GraphRAG knowledge graph retrieval
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ..graphrag.graph_store import NetmeraGraphStore
from ..graphrag.graph_retriever import GraphRAGRetriever
from ..graphrag.query_router import QueryRouter, QueryType, RetrievalStrategy
from ..graphrag.query_expansion import QueryExpander, ExpandedQuery
from .hybrid import HybridRetriever

logger = logging.getLogger(__name__)

@dataclass
class HybridGraphRAGContext:
    """Combined context from FAISS and GraphRAG with source tracking and query expansion"""
    vector_context: List[Dict[str, Any]]
    graph_context: Optional[Dict[str, Any]]
    routing_info: Dict[str, Any]
    combined_confidence: float
    strategy: RetrievalStrategy
    context_sources: Dict[str, Any]  # Track source quality and types
    fallback_used: bool = False
    query_expansion: Optional[ExpandedQuery] = None  # Track query expansion details
    second_round_used: bool = False  # Track if second round retrieval was used

class HybridGraphRAGRetriever:
    """
    Hybrid retriever that intelligently combines FAISS vector search 
    with GraphRAG knowledge graph retrieval
    """
    
    def __init__(self, corpus_texts: List[str], corpus_meta: List[Dict[str, Any]]):
        """Initialize hybrid GraphRAG retriever with query expansion"""
        # Initialize existing FAISS-based hybrid retriever
        self.vector_retriever = HybridRetriever(corpus_texts, corpus_meta)
        
        # Initialize GraphRAG components
        self.graph_store = NetmeraGraphStore()
        self.graph_retriever = GraphRAGRetriever(self.graph_store)
        self.query_router = QueryRouter()
        self.query_expander = QueryExpander()  # NEW: Query expansion
        
        # Configuration for query expansion
        self.enable_query_expansion = True
        self.expansion_threshold_docs = 3  # Expand if fewer than 3 docs
        self.expansion_threshold_confidence = 0.4  # Expand if confidence < 0.4
        
        # Initialize graph if empty
        if self.graph_store.graph.number_of_nodes() == 0:
            logger.info("Building sample knowledge graph...")
            self.graph_store.build_sample_graph()
        
        logger.info(f"Hybrid GraphRAG retriever initialized with {self.graph_store.graph.number_of_nodes()} graph nodes and query expansion")
    
    def retrieve(self, query: str, k: int = 5) -> HybridGraphRAGContext:
        """
        Retrieve context using hybrid context merging approach with automatic query expansion.
        Always fetches both vector and graph contexts, with intelligent prioritization.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            Combined context from both retrievers with source tracking and expansion
        """
        logger.debug(f"Hybrid retrieval with context merging for query: {query}")
        
        # Step 1: Route query to determine strategy
        routing_result = self.query_router.route_query(query)
        strategy = routing_result['strategy']
        
        logger.info(f"Query strategy: {strategy.value}")
        
        # Step 2: Initial retrieval with original query
        vector_context, graph_context = self._retrieve_contexts(query, k)
        
        # Step 3: Assess if query expansion is needed
        expansion_used = None
        second_round_used = False
        fallback_used = False
        
        if self.enable_query_expansion:
            initial_vector_count = len(vector_context) if vector_context else 0
            initial_graph_confidence = graph_context.get('confidence', 0) if graph_context else 0
            
            # Calculate initial combined confidence
            initial_combined_confidence = self._calculate_combined_confidence_v2(
                vector_context, graph_context, strategy
            )
            
            # Check if expansion is needed
            needs_expansion = self.query_expander.should_expand_query(
                initial_results_count=initial_vector_count,
                confidence=initial_combined_confidence
            )
            
            if needs_expansion:
                logger.info("Initial results insufficient, expanding query...")
                
                # Expand query
                expansion_used = self.query_expander.expand_query(query)
                logger.debug(f"Expanded query: '{expansion_used.expanded_query}'")
                logger.debug(f"Added terms: {expansion_used.added_terms}")
                
                # Second round retrieval with expanded query
                vector_context2, graph_context2 = self._retrieve_contexts(
                    expansion_used.expanded_query, k
                )
                
                # Merge results from both rounds
                vector_context, graph_context = self._merge_retrieval_rounds(
                    vector_context, graph_context,
                    vector_context2, graph_context2
                )
                
                second_round_used = True
                logger.info(f"Query expansion added {len(vector_context2) if vector_context2 else 0} more vector docs")
        
        # Step 5: Create context source tracking
        context_sources = {
            "vector_available": bool(vector_context),
            "graph_available": bool(graph_context),
            "vector_quality": self._assess_vector_quality(vector_context),
            "graph_quality": self._assess_graph_quality(graph_context),
            "strategy_applied": strategy.value,
            "expansion_used": bool(expansion_used),
            "expansion_terms": expansion_used.added_terms if expansion_used else []
        }
        
        # Step 6: Calculate final combined confidence
        combined_confidence = self._calculate_combined_confidence_v2(
            vector_context, graph_context, strategy
        )
        
        return HybridGraphRAGContext(
            vector_context=vector_context,
            graph_context=graph_context,
            routing_info=routing_result,
            combined_confidence=combined_confidence,
            strategy=strategy,
            context_sources=context_sources,
            fallback_used=fallback_used,
            query_expansion=expansion_used,
            second_round_used=second_round_used
        )
    
    def format_context_for_llm(self, context: HybridGraphRAGContext, query: str) -> str:
        """Format combined context for LLM consumption with source type labels"""
        formatted_parts = []
        
        # Add routing information with strategy
        strategy = context.strategy.value
        route_type = context.routing_info.get('route_type', 'unknown')
        formatted_parts.append(f"=== HYBRID CONTEXT MERGE ===")
        formatted_parts.append(f"Query: {query}")
        formatted_parts.append(f"Strategy: {strategy.upper()}")
        formatted_parts.append(f"Primary Route: {route_type.upper()}")
        formatted_parts.append(f"Combined Confidence: {context.combined_confidence:.2f}")
        if context.fallback_used:
            formatted_parts.append("⚠️ Fallback strategy applied")
        formatted_parts.append("")
        
        # Add context quality summary with expansion info
        formatted_parts.append("=== CONTEXT SOURCES ===")
        sources = context.context_sources
        formatted_parts.append(f"📊 Vector Quality: {sources.get('vector_quality', 0):.2f} ({'✅' if sources.get('vector_available') else '❌'})")
        formatted_parts.append(f"🕸️ Graph Quality: {sources.get('graph_quality', 0):.2f} ({'✅' if sources.get('graph_available') else '❌'})")
        
        # Query expansion info
        if context.query_expansion:
            expansion = context.query_expansion
            formatted_parts.append(f"🔍 Query Expansion: ✅ (confidence: {expansion.expansion_confidence:.2f})")
            formatted_parts.append(f"📝 Added Terms: {', '.join(expansion.added_terms[:5])}")  # Show first 5 terms
            if context.second_round_used:
                formatted_parts.append("🔄 Second Round Retrieval: ✅")
        else:
            formatted_parts.append("🔍 Query Expansion: ❌")
        formatted_parts.append("")
        
        # Add graph context if available (prioritized based on strategy)
        if context.graph_context and context.graph_context.get('subgraph_info'):
            priority_label = "🔥 PRIMARY" if strategy == "graph_first" else "🔗 SECONDARY" if strategy == "vector_first" else "🟰 BALANCED"
            formatted_parts.append(f"=== {priority_label} - KNOWLEDGE GRAPH (source_type: knowledge_graph) ===")
            formatted_parts.append(f"Entities: {len(context.graph_context.get('entities', []))}")
            formatted_parts.append(f"Relationships: {len(context.graph_context.get('relationships', []))}")
            formatted_parts.append(f"Graph Confidence: {context.graph_context.get('confidence', 0):.2f}")
            formatted_parts.append("")
            formatted_parts.append("Graph Insights:")
            formatted_parts.append(context.graph_context['subgraph_info'])
            formatted_parts.append("")
        
        # Add vector context with source type labeling
        if context.vector_context:
            priority_label = "🔥 PRIMARY" if strategy == "vector_first" else "🔗 SECONDARY" if strategy == "graph_first" else "🟰 BALANCED"
            formatted_parts.append(f"=== {priority_label} - DOCUMENTATION (source_type: documentation) ===")
            for i, doc in enumerate(context.vector_context[:3], 1):  # Limit to top 3
                formatted_parts.append(f"--- SOURCE {i} (score: {doc.get('score', 0):.2f}) ---")
                formatted_parts.append(f"Type: {doc.get('source_type', 'documentation')}")
                formatted_parts.append(f"URL: {doc.get('url', 'unknown')}")
                formatted_parts.append(f"Content: {doc.get('text', '')[:800]}...")  # Limit content
                formatted_parts.append("")
        
        # Add usage instructions
        formatted_parts.append("=== CONTEXT USAGE INSTRUCTIONS ===")
        if strategy == "graph_first":
            formatted_parts.append("🎯 PRIORITY: Use knowledge graph insights as primary source, documentation as supporting details")
        elif strategy == "vector_first":
            formatted_parts.append("🎯 PRIORITY: Use documentation as primary source, graph insights for relationships/context")
        else:
            formatted_parts.append("🎯 BALANCED: Integrate both knowledge graph and documentation equally")
        
        formatted_parts.append("=== END HYBRID CONTEXT ===")
        
        return "\n".join(formatted_parts)
    
    def _retrieve_contexts(self, query: str, k: int) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Retrieve both vector and graph contexts for a given query"""
        vector_context = []
        graph_context = None
        
        # Fetch vector context
        try:
            vector_docs = self.vector_retriever.retrieve(query, k=k)
            vector_context = [
                {
                    "text": doc.get("text", ""),
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                    "score": doc.get("hybrid_score", 0),
                    "retrieval_method": "vector",
                    "source_type": "documentation"
                }
                for doc in vector_docs
            ]
            logger.debug(f"Vector retrieval found {len(vector_context)} documents for query: '{query}'")
        except Exception as e:
            logger.warning(f"Vector retrieval failed for query '{query}': {e}")
        
        # Fetch graph context
        try:
            graph_result = self.graph_retriever.retrieve(query, max_entities=5, max_hops=2)
            
            if graph_result.entities or graph_result.relationships:
                graph_context = {
                    "entities": graph_result.entities,
                    "relationships": graph_result.relationships,
                    "subgraph_info": graph_result.subgraph_info,
                    "confidence": graph_result.confidence,
                    "retrieval_method": "graph",
                    "source_type": "knowledge_graph"
                }
                logger.debug(f"Graph retrieval found {len(graph_result.entities)} entities for query: '{query}'")
        except Exception as e:
            logger.warning(f"Graph retrieval failed for query '{query}': {e}")
        
        return vector_context, graph_context
    
    def _merge_retrieval_rounds(self, vector1: List[Dict[str, Any]], graph1: Optional[Dict[str, Any]],
                               vector2: List[Dict[str, Any]], graph2: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Merge results from two retrieval rounds, avoiding duplicates"""
        
        # Merge vector contexts
        merged_vector = list(vector1) if vector1 else []
        if vector2:
            # Use URL/source as deduplication key
            existing_urls = {doc.get('url', '') for doc in merged_vector}
            for doc in vector2:
                doc_url = doc.get('url', '')
                if doc_url not in existing_urls:
                    # Mark as second round result
                    doc_copy = dict(doc)
                    doc_copy['retrieval_method'] = 'vector_expanded'
                    merged_vector.append(doc_copy)
                    existing_urls.add(doc_url)
        
        # Sort by score and limit
        merged_vector = sorted(merged_vector, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        # Merge graph contexts (combine entities and relationships)
        merged_graph = graph1
        if graph2 and graph2.get('entities'):
            if merged_graph:
                # Combine entities and relationships
                merged_entities = list(merged_graph.get('entities', []))
                merged_relationships = list(merged_graph.get('relationships', []))
                
                # Add new entities (avoid duplicates by entity name)
                existing_entity_names = {e.get('name', '') for e in merged_entities}
                for entity in graph2.get('entities', []):
                    if entity.get('name', '') not in existing_entity_names:
                        merged_entities.append(entity)
                
                # Add new relationships
                for rel in graph2.get('relationships', []):
                    merged_relationships.append(rel)
                
                # Update merged graph
                merged_graph['entities'] = merged_entities
                merged_graph['relationships'] = merged_relationships
                
                # Take higher confidence
                merged_graph['confidence'] = max(
                    merged_graph.get('confidence', 0),
                    graph2.get('confidence', 0)
                )
                
                # Update subgraph info
                if graph2.get('subgraph_info'):
                    merged_graph['subgraph_info'] += f"\n\n=== EXPANDED QUERY INSIGHTS ===\n{graph2['subgraph_info']}"
            else:
                merged_graph = graph2
                if merged_graph:
                    merged_graph['retrieval_method'] = 'graph_expanded'
        
        return merged_vector, merged_graph
    
    def _assess_vector_quality(self, vector_context: List[Dict[str, Any]]) -> float:
        """Assess quality of vector retrieval results"""
        if not vector_context:
            return 0.0
        
        scores = [doc.get('score', 0) for doc in vector_context]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Consider count and average score
        count_factor = min(len(vector_context) / 5, 1.0)  # Normalize to 5 docs
        return avg_score * 0.7 + count_factor * 0.3
    
    def _assess_graph_quality(self, graph_context: Optional[Dict[str, Any]]) -> float:
        """Assess quality of graph retrieval results"""
        if not graph_context:
            return 0.0
        
        base_confidence = graph_context.get('confidence', 0)
        entity_count = len(graph_context.get('entities', []))
        relationship_count = len(graph_context.get('relationships', []))
        
        # Boost confidence based on entity/relationship richness
        richness_factor = min((entity_count + relationship_count) / 10, 1.0)
        return base_confidence * 0.8 + richness_factor * 0.2
    
    def _calculate_combined_confidence_v2(self, vector_context: List[Dict[str, Any]], 
                                        graph_context: Optional[Dict[str, Any]], 
                                        strategy: RetrievalStrategy) -> float:
        """Calculate combined confidence score based on strategy"""
        vector_quality = self._assess_vector_quality(vector_context)
        graph_quality = self._assess_graph_quality(graph_context)
        
        if strategy == RetrievalStrategy.GRAPH_FIRST:
            # 70% graph, 30% vector
            return graph_quality * 0.7 + vector_quality * 0.3
        elif strategy == RetrievalStrategy.VECTOR_FIRST:
            # 70% vector, 30% graph
            return vector_quality * 0.7 + graph_quality * 0.3
        else:  # BALANCED_HYBRID
            # Equal weight
            return (vector_quality + graph_quality) / 2
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        vector_stats = self.vector_retriever.get_stats() if hasattr(self.vector_retriever, 'get_stats') else {}
        graph_stats = self.graph_store.get_stats()
        
        return {
            "vector_retriever": vector_stats,
            "graph_store": graph_stats,
            "hybrid_mode": "enabled"
        }
