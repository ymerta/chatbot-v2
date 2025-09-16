"""
Graph Store implementation using NetworkX for Netmera knowledge graph
"""

import logging
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Netmera domain entity"""
    id: str
    name: str
    type: str  # SDK, API, Feature, Platform, etc.
    description: str
    properties: Dict[str, Any]

@dataclass 
class Relationship:
    """Relationship between entities"""
    source: str
    target: str
    relation_type: str  # requires, implements, configures, etc.
    description: str
    properties: Dict[str, Any]

class NetmeraGraphStore:
    """NetworkX-based graph store for Netmera knowledge graph"""
    
    def __init__(self, graph_path: str = None):
        """Initialize graph store"""
        self.graph = nx.MultiDiGraph()
        self.graph_path = graph_path or "data/graph/netmera_knowledge_graph.pkl"
        self.entity_types = {
            "SDK": "Software Development Kit components",
            "API": "API endpoints and methods", 
            "Feature": "Platform features and capabilities",
            "Platform": "Target platforms (iOS, Android, Web)",
            "Configuration": "Configuration parameters and settings",
            "Error": "Error types and troubleshooting",
            "Procedure": "Step-by-step procedures",
            "Code": "Code examples and implementations"
        }
        
        # Load existing graph if available
        self.load_graph()
    
    def add_entity(self, entity: Entity) -> None:
        """Add entity to graph"""
        self.graph.add_node(
            entity.id,
            name=entity.name,
            type=entity.type,
            description=entity.description,
            **entity.properties
        )
        logger.debug(f"Added entity: {entity.name} ({entity.type})")
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add relationship between entities"""
        self.graph.add_edge(
            relationship.source,
            relationship.target,
            relation_type=relationship.relation_type,
            description=relationship.description,
            **relationship.properties
        )
        logger.debug(f"Added relationship: {relationship.source} --{relationship.relation_type}--> {relationship.target}")
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        if self.graph.has_node(entity_id):
            return dict(self.graph.nodes[entity_id])
        return None
    
    def get_neighbors(self, entity_id: str, max_hops: int = 2, relation_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get neighboring entities with traversal"""
        if not self.graph.has_node(entity_id):
            return []
        
        neighbors = []
        visited = set()
        queue = [(entity_id, 0)]  # (node_id, hop_count)
        
        while queue:
            current_id, hops = queue.pop(0)
            
            if hops > max_hops or current_id in visited:
                continue
                
            visited.add(current_id)
            
            # Get current node info
            if hops > 0:  # Don't include the starting node
                node_data = dict(self.graph.nodes[current_id])
                node_data['entity_id'] = current_id
                node_data['hop_distance'] = hops
                neighbors.append(node_data)
            
            # Add connected nodes to queue
            for neighbor_id in self.graph.neighbors(current_id):
                if neighbor_id not in visited:
                    # Check relationship type filter
                    edge_data = self.graph.get_edge_data(current_id, neighbor_id)
                    if relation_types:
                        edge_relations = [edge.get('relation_type') for edge in edge_data.values()]
                        if not any(rel in relation_types for rel in edge_relations):
                            continue
                    
                    queue.append((neighbor_id, hops + 1))
        
        return neighbors
    
    def find_entities_by_type(self, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find entities by type"""
        entities = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == entity_type:
                entity_data = dict(node_data)
                entity_data['entity_id'] = node_id
                entities.append(entity_data)
                
                if len(entities) >= limit:
                    break
        
        return entities
    
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search entities by name/description"""
        query_lower = query.lower()
        matches = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            name = node_data.get('name', '').lower()
            description = node_data.get('description', '').lower()
            
            # Simple text matching - could be enhanced with fuzzy matching
            score = 0
            if query_lower in name:
                score += 10
            if query_lower in description:
                score += 5
            
            if score > 0:
                entity_data = dict(node_data)
                entity_data['entity_id'] = node_id
                entity_data['match_score'] = score
                matches.append(entity_data)
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:limit]
    
    def get_subgraph(self, entity_ids: List[str], max_hops: int = 2) -> nx.MultiDiGraph:
        """Get subgraph containing specified entities and their neighbors"""
        subgraph_nodes = set(entity_ids)
        
        # Add neighbors for each entity
        for entity_id in entity_ids:
            neighbors = self.get_neighbors(entity_id, max_hops)
            for neighbor in neighbors:
                subgraph_nodes.add(neighbor['entity_id'])
        
        return self.graph.subgraph(subgraph_nodes).copy()
    
    def save_graph(self) -> None:
        """Save graph to disk"""
        os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
        with open(self.graph_path, 'wb') as f:
            pickle.dump(self.graph, f)
        logger.info(f"Graph saved to {self.graph_path}")
    
    def load_graph(self) -> None:
        """Load graph from disk"""
        if os.path.exists(self.graph_path):
            try:
                with open(self.graph_path, 'rb') as f:
                    self.graph = pickle.load(f)
                logger.info(f"Graph loaded from {self.graph_path}")
                logger.info(f"Graph stats: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            except Exception as e:
                logger.warning(f"Failed to load graph: {e}")
                self.graph = nx.MultiDiGraph()
        else:
            logger.info("No existing graph found, starting with empty graph")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'entity_types': {},
            'relation_types': {}
        }
        
        # Count entity types
        for _, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('type', 'Unknown')
            stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1
        
        # Count relation types
        for _, _, edge_data in self.graph.edges(data=True):
            relation_type = edge_data.get('relation_type', 'Unknown')
            stats['relation_types'][relation_type] = stats['relation_types'].get(relation_type, 0) + 1
        
        return stats
    
    def build_sample_graph(self) -> None:
        """Build a sample Netmera knowledge graph for testing"""
        logger.info("Building sample Netmera knowledge graph...")
        
        # Sample entities
        entities = [
            Entity("netmera_sdk", "Netmera SDK", "SDK", "Main Netmera SDK for mobile platforms", {"version": "latest"}),
            Entity("push_notification", "Push Notification", "Feature", "Send push notifications to users", {"category": "messaging"}),
            Entity("user_segmentation", "User Segmentation", "Feature", "Segment users based on behavior", {"category": "analytics"}),
            Entity("ios_platform", "iOS", "Platform", "Apple iOS platform", {"os": "iOS"}),
            Entity("android_platform", "Android", "Platform", "Google Android platform", {"os": "Android"}),
            Entity("campaign_api", "Campaign API", "API", "API for managing campaigns", {"endpoint": "/api/campaigns"}),
            Entity("analytics_dashboard", "Analytics Dashboard", "Feature", "View analytics and reports", {"category": "analytics"}),
            Entity("gradle_config", "Gradle Configuration", "Configuration", "Android Gradle setup", {"platform": "Android"}),
            Entity("api_key_config", "API Key Configuration", "Configuration", "Set up API key", {"required": True}),
        ]
        
        # Add entities
        for entity in entities:
            self.add_entity(entity)
        
        # Sample relationships
        relationships = [
            Relationship("netmera_sdk", "push_notification", "provides", "SDK provides push notification feature", {}),
            Relationship("netmera_sdk", "user_segmentation", "provides", "SDK provides segmentation feature", {}),
            Relationship("push_notification", "campaign_api", "uses", "Push notifications use campaign API", {}),
            Relationship("netmera_sdk", "ios_platform", "supports", "SDK supports iOS platform", {}),
            Relationship("netmera_sdk", "android_platform", "supports", "SDK supports Android platform", {}),
            Relationship("android_platform", "gradle_config", "requires", "Android platform requires Gradle config", {}),
            Relationship("netmera_sdk", "api_key_config", "requires", "SDK requires API key configuration", {}),
            Relationship("user_segmentation", "analytics_dashboard", "feeds_into", "Segmentation data feeds into analytics", {}),
            Relationship("campaign_api", "analytics_dashboard", "reports_to", "Campaign data appears in analytics", {}),
        ]
        
        # Add relationships
        for relationship in relationships:
            self.add_relationship(relationship)
        
        logger.info(f"Sample graph built: {self.get_stats()}")
        self.save_graph()

