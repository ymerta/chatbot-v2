"""
GraphRAG retriever for knowledge graph-based question answering
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .graph_store import NetmeraGraphStore
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

@dataclass
class GraphContext:
    """Context retrieved from knowledge graph"""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    subgraph_info: str
    confidence: float

class GraphRAGRetriever:
    """Knowledge graph-based retriever for Netmera documentation"""
    
    def __init__(self, graph_store: NetmeraGraphStore):
        """Initialize GraphRAG retriever"""
        self.graph_store = graph_store
        self.entity_extractor = EntityExtractor()
        logger.info("GraphRAG retriever initialized")
    
    def retrieve(self, query: str, max_entities: int = 5, max_hops: int = 2) -> GraphContext:
        """Retrieve relevant context from knowledge graph"""
        logger.debug(f"GraphRAG retrieval for query: {query}")
        
        # Step 1: Extract anchor entities from query
        anchor_entities = self._extract_anchor_entities(query)
        logger.debug(f"Found anchor entities: {[e['name'] for e in anchor_entities]}")
        
        if not anchor_entities:
            # Fallback to search if no entities found
            anchor_entities = self.graph_store.search_entities(query, limit=3)
            logger.debug(f"Fallback search found: {[e['name'] for e in anchor_entities]}")
        
        if not anchor_entities:
            return GraphContext(entities=[], relationships=[], subgraph_info="", confidence=0.0)
        
        # Step 2: Expand context through graph traversal
        all_entities = []
        all_relationships = []
        
        for anchor in anchor_entities[:max_entities]:
            entity_id = anchor.get('entity_id')
            if not entity_id:
                continue
            
            # Get neighbors through graph traversal
            neighbors = self.graph_store.get_neighbors(entity_id, max_hops=max_hops)
            
            # Add anchor entity
            anchor['hop_distance'] = 0
            all_entities.append(anchor)
            
            # Add neighbors
            all_entities.extend(neighbors)
            
            # Get relationships for this entity
            relationships = self._get_entity_relationships(entity_id, neighbors)
            all_relationships.extend(relationships)
        
        # Step 3: Remove duplicates and rank by relevance
        unique_entities = self._deduplicate_entities(all_entities)
        unique_relationships = self._deduplicate_relationships(all_relationships)
        
        # Step 4: Generate contextual information
        subgraph_info = self._build_subgraph_description(unique_entities, unique_relationships, query)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(query, anchor_entities, unique_entities)
        
        logger.debug(f"Retrieved {len(unique_entities)} entities and {len(unique_relationships)} relationships")
        
        return GraphContext(
            entities=unique_entities,
            relationships=unique_relationships, 
            subgraph_info=subgraph_info,
            confidence=confidence
        )
    
    def _extract_anchor_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from query that exist in the graph"""
        # Extract entities from query text
        extracted_entities = self.entity_extractor.extract_entities(query)
        
        # Find matching entities in graph
        anchor_entities = []
        for extracted in extracted_entities:
            # Search for this entity in the graph
            matches = self.graph_store.search_entities(extracted.text, limit=1)
            if matches:
                best_match = matches[0]
                best_match['extraction_confidence'] = extracted.confidence
                best_match['query_text'] = extracted.text
                anchor_entities.append(best_match)
        
        # Also try direct search for the whole query
        direct_matches = self.graph_store.search_entities(query, limit=2)
        for match in direct_matches:
            # Avoid duplicates
            if not any(e.get('entity_id') == match.get('entity_id') for e in anchor_entities):
                match['extraction_confidence'] = 0.6
                match['query_text'] = query
                anchor_entities.append(match)
        
        # Sort by relevance score
        anchor_entities.sort(key=lambda x: x.get('match_score', 0) + x.get('extraction_confidence', 0), reverse=True)
        
        return anchor_entities
    
    def _get_entity_relationships(self, entity_id: str, neighbors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get relationships for an entity and its neighbors"""
        relationships = []
        
        # Get all edges involving this entity
        for neighbor in neighbors:
            neighbor_id = neighbor.get('entity_id')
            if not neighbor_id:
                continue
            
            # Get edge data between entity and neighbor
            if self.graph_store.graph.has_edge(entity_id, neighbor_id):
                edge_data = self.graph_store.graph.get_edge_data(entity_id, neighbor_id)
                for edge_key, edge_attrs in edge_data.items():
                    relationship = {
                        'source_id': entity_id,
                        'target_id': neighbor_id,
                        'source_name': self.graph_store.get_entity(entity_id).get('name', entity_id),
                        'target_name': neighbor.get('name', neighbor_id),
                        'relation_type': edge_attrs.get('relation_type', 'related'),
                        'description': edge_attrs.get('description', ''),
                        **edge_attrs
                    }
                    relationships.append(relationship)
            
            # Check reverse direction
            if self.graph_store.graph.has_edge(neighbor_id, entity_id):
                edge_data = self.graph_store.graph.get_edge_data(neighbor_id, entity_id)
                for edge_key, edge_attrs in edge_data.items():
                    relationship = {
                        'source_id': neighbor_id,
                        'target_id': entity_id,
                        'source_name': neighbor.get('name', neighbor_id),
                        'target_name': self.graph_store.get_entity(entity_id).get('name', entity_id),
                        'relation_type': edge_attrs.get('relation_type', 'related'),
                        'description': edge_attrs.get('description', ''),
                        **edge_attrs
                    }
                    relationships.append(relationship)
        
        return relationships
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities"""
        seen_ids = set()
        unique_entities = []
        
        for entity in entities:
            entity_id = entity.get('entity_id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _deduplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate relationships"""
        seen_rels = set()
        unique_relationships = []
        
        for rel in relationships:
            rel_key = (rel.get('source_id'), rel.get('target_id'), rel.get('relation_type'))
            if rel_key not in seen_rels:
                seen_rels.add(rel_key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def _build_subgraph_description(self, entities: List[Dict[str, Any]], 
                                   relationships: List[Dict[str, Any]], query: str) -> str:
        """Build a textual description of the retrieved subgraph"""
        if not entities:
            return ""
        
        # Build entity descriptions
        entity_descriptions = []
        for entity in entities[:10]:  # Limit to prevent too long context
            name = entity.get('name', 'Unknown')
            entity_type = entity.get('type', 'Unknown')
            description = entity.get('description', '')
            hop_distance = entity.get('hop_distance', 0)
            
            entity_desc = f"**{name}** ({entity_type})"
            if description:
                entity_desc += f": {description}"
            if hop_distance > 0:
                entity_desc += f" [Distance: {hop_distance} hops]"
            
            entity_descriptions.append(entity_desc)
        
        # Build relationship descriptions
        relationship_descriptions = []
        for rel in relationships[:15]:  # Limit relationships
            source = rel.get('source_name', 'Unknown')
            target = rel.get('target_name', 'Unknown') 
            relation_type = rel.get('relation_type', 'related')
            description = rel.get('description', '')
            
            rel_desc = f"- {source} **{relation_type}** {target}"
            if description:
                rel_desc += f": {description}"
            
            relationship_descriptions.append(rel_desc)
        
        # Combine into comprehensive description
        context_parts = []
        
        if entity_descriptions:
            context_parts.append("## Relevant Entities:")
            context_parts.extend(entity_descriptions)
        
        if relationship_descriptions:
            context_parts.append("\n## Relationships:")
            context_parts.extend(relationship_descriptions)
        
        # Add summary
        if entity_descriptions and relationship_descriptions:
            summary = f"\n## Summary:\nFound {len(entities)} related entities and {len(relationships)} relationships relevant to the query about: {query}"
            context_parts.append(summary)
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, query: str, anchor_entities: List[Dict[str, Any]], 
                            all_entities: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the retrieval"""
        if not anchor_entities:
            return 0.0
        
        # Base confidence from anchor entities
        anchor_confidence = sum(e.get('extraction_confidence', 0.5) for e in anchor_entities) / len(anchor_entities)
        
        # Boost confidence based on entity coverage
        entity_coverage = min(len(all_entities) / 10.0, 1.0)  # Normalize to 0-1
        
        # Boost confidence if we found strong matches
        match_confidence = sum(e.get('match_score', 0) for e in anchor_entities) / (len(anchor_entities) * 10.0)
        
        # Combined confidence
        confidence = (anchor_confidence * 0.5) + (entity_coverage * 0.3) + (match_confidence * 0.2)
        
        return min(confidence, 1.0)
    
    def format_context_for_llm(self, graph_context: GraphContext, query: str) -> str:
        """Format graph context for LLM consumption"""
        if not graph_context.entities and not graph_context.relationships:
            return ""
        
        formatted_context = []
        formatted_context.append(f"=== KNOWLEDGE GRAPH CONTEXT ===")
        formatted_context.append(f"Query: {query}")
        formatted_context.append(f"Confidence: {graph_context.confidence:.2f}")
        formatted_context.append("")
        
        if graph_context.subgraph_info:
            formatted_context.append(graph_context.subgraph_info)
        
        formatted_context.append(f"\n=== END GRAPH CONTEXT ===")
        
        return "\n".join(formatted_context)

