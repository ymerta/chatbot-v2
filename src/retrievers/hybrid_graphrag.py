"""
Hybrid retriever combining FAISS vector search with GraphRAG knowledge graph retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..graphrag.graph_store import NetmeraGraphStore
from ..graphrag.graph_retriever import GraphRAGRetriever
from ..graphrag.query_router import QueryRouter, QueryType
from .hybrid import HybridRetriever

logger = logging.getLogger(__name__)

@dataclass
class HybridGraphRAGContext:
    """Combined context from FAISS and GraphRAG"""
    vector_context: List[Dict[str, Any]]
    graph_context: Optional[Dict[str, Any]]
    routing_info: Dict[str, Any]
    combined_confidence: float

class HybridGraphRAGRetriever:
    """
    Hybrid retriever that intelligently combines FAISS vector search 
    with GraphRAG knowledge graph retrieval
    """
    
    def __init__(self, corpus_texts: List[str], corpus_meta: List[Dict[str, Any]]):
        """Initialize hybrid GraphRAG retriever"""
        # Initialize existing FAISS-based hybrid retriever
        self.vector_retriever = HybridRetriever(corpus_texts, corpus_meta)
        
        # Initialize GraphRAG components
        self.graph_store = NetmeraGraphStore()
        self.graph_retriever = GraphRAGRetriever(self.graph_store)
        self.query_router = QueryRouter()
        
        # Initialize graph if empty
        if self.graph_store.graph.number_of_nodes() == 0:
            logger.info("Building sample knowledge graph...")
            self.graph_store.build_sample_graph()
        
        logger.info(f"Hybrid GraphRAG retriever initialized with {self.graph_store.graph.number_of_nodes()} graph nodes")
    
    def retrieve(self, query: str, k: int = 5) -> HybridGraphRAGContext:
        """
        Retrieve context using hybrid FAISS + GraphRAG approach
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            Combined context from both retrievers
        """
        logger.debug(f"Hybrid retrieval for query: {query}")
        
        # Step 1: Route query to determine approach
        route_type = self.query_router.route_query(query)
        routing_info = self.query_router.get_routing_explanation(query)
        
        logger.info(f"Query routed to: {route_type.value}")
        
        # Step 2: Retrieve using appropriate method(s)
        vector_context = []
        graph_context = None
        
        if route_type in [QueryType.VECTOR, QueryType.HYBRID]:
            # Use existing FAISS-based retrieval
            vector_docs = self.vector_retriever.retrieve(query, k=k)
            vector_context = [
                {
                    "text": doc.get("text", ""),
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                    "score": doc.get("hybrid_score", 0),
                    "retrieval_method": "vector"
                }
                for doc in vector_docs
            ]
            logger.debug(f"Vector retrieval found {len(vector_context)} documents")
        
        if route_type in [QueryType.GRAPH, QueryType.HYBRID]:
            # Use GraphRAG retrieval
            graph_result = self.graph_retriever.retrieve(query, max_entities=5, max_hops=2)
            
            if graph_result.entities or graph_result.relationships:
                graph_context = {
                    "entities": graph_result.entities,
                    "relationships": graph_result.relationships,
                    "subgraph_info": graph_result.subgraph_info,
                    "confidence": graph_result.confidence,
                    "retrieval_method": "graph"
                }
                logger.debug(f"Graph retrieval found {len(graph_result.entities)} entities")
        
        # Step 3: Combine and rank results
        combined_confidence = self._calculate_combined_confidence(
            vector_context, graph_context, route_type
        )
        
        # Step 4: Fallback strategy
        if route_type == QueryType.GRAPH and (not graph_context or graph_context['confidence'] < 0.3):
            logger.info("Graph retrieval confidence low, falling back to vector search")
            if not vector_context:
                vector_docs = self.vector_retriever.retrieve(query, k=k)
                vector_context = [
                    {
                        "text": doc.get("text", ""),
                        "url": doc.get("url", ""),
                        "source": doc.get("source", ""), 
                        "score": doc.get("hybrid_score", 0),
                        "retrieval_method": "vector_fallback"
                    }
                    for doc in vector_docs
                ]
            routing_info['fallback_used'] = True
        
        elif route_type == QueryType.VECTOR and not vector_context:
            logger.info("Vector retrieval failed, trying graph search")
            if not graph_context:
                graph_result = self.graph_retriever.retrieve(query, max_entities=3, max_hops=1)
                if graph_result.entities:
                    graph_context = {
                        "entities": graph_result.entities,
                        "relationships": graph_result.relationships,
                        "subgraph_info": graph_result.subgraph_info,
                        "confidence": graph_result.confidence,
                        "retrieval_method": "graph_fallback"
                    }
            routing_info['fallback_used'] = True
        
        return HybridGraphRAGContext(
            vector_context=vector_context,
            graph_context=graph_context,
            routing_info=routing_info,
            combined_confidence=combined_confidence
        )
    
    def format_context_for_llm(self, context: HybridGraphRAGContext, query: str) -> str:
        """Format combined context for LLM consumption"""
        formatted_parts = []
        
        # Add routing information
        route_type = context.routing_info.get('route_type', 'unknown')
        formatted_parts.append(f"=== HYBRID RETRIEVAL CONTEXT ===")
        formatted_parts.append(f"Query: {query}")
        formatted_parts.append(f"Routing: {route_type.upper()}")
        formatted_parts.append(f"Confidence: {context.combined_confidence:.2f}")
        formatted_parts.append("")
        
        # Add graph context if available
        if context.graph_context and context.graph_context.get('subgraph_info'):
            formatted_parts.append("=== KNOWLEDGE GRAPH INSIGHTS ===")
            formatted_parts.append(context.graph_context['subgraph_info'])
            formatted_parts.append("")
        
        # Add vector context
        if context.vector_context:
            formatted_parts.append("=== DOCUMENTATION SOURCES ===")
            for i, doc in enumerate(context.vector_context[:3], 1):  # Limit to top 3
                formatted_parts.append(f"=== SOURCE {i} ===")
                formatted_parts.append(f"URL: {doc.get('url', 'unknown')}")
                formatted_parts.append(f"Content: {doc.get('text', '')[:1000]}...")  # Limit content
                formatted_parts.append("")
        
        formatted_parts.append("=== END HYBRID CONTEXT ===")
        
        return "\n".join(formatted_parts)
    
    def _calculate_combined_confidence(self, vector_context: List[Dict[str, Any]], 
                                     graph_context: Optional[Dict[str, Any]], 
                                     route_type: QueryType) -> float:
        """Calculate combined confidence score"""
        confidences = []
        
        # Vector confidence (based on hybrid scores)
        if vector_context:
            vector_scores = [doc.get('score', 0) for doc in vector_context]
            vector_confidence = sum(vector_scores) / len(vector_scores) if vector_scores else 0
            confidences.append(vector_confidence)
        
        # Graph confidence
        if graph_context:
            graph_confidence = graph_context.get('confidence', 0)
            confidences.append(graph_confidence)
        
        if not confidences:
            return 0.0
        
        # Weight confidences based on routing decision
        if route_type == QueryType.GRAPH:
            # Prioritize graph confidence
            if graph_context:
                return graph_context.get('confidence', 0) * 0.8 + (confidences[0] if len(confidences) > 1 else 0) * 0.2
        elif route_type == QueryType.VECTOR:
            # Prioritize vector confidence
            if vector_context:
                vector_confidence = confidences[0] if confidences else 0
                return vector_confidence * 0.8 + (graph_context.get('confidence', 0) if graph_context else 0) * 0.2
        else:
            # Hybrid: equal weight
            return sum(confidences) / len(confidences)
        
        return sum(confidences) / len(confidences)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        vector_stats = self.vector_retriever.get_stats() if hasattr(self.vector_retriever, 'get_stats') else {}
        graph_stats = self.graph_store.get_stats()
        
        return {
            "vector_retriever": vector_stats,
            "graph_store": graph_stats,
            "hybrid_mode": "enabled"
        }
