"""
GRAPH ENGINE - Entity Relationship & Threat Graphs

Enterprise threat graph for:
- Relationships between users, assets, threats
- Attack path analysis
- Blast radius calculation
- Correlation discovery

This is Neo4j-like but in-memory for Discord scale.
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

from cogs.core.pst_timezone import get_now_pst


class RelationshipType:
    """Entity relationship types"""
    ACCESSED = "accessed"
    COMPROMISED = "compromised"
    CREATED_BY = "created_by"
    OWNS = "owns"
    MEMBER_OF = "member_of"
    CONTAINS = "contains"
    EXPLOITS = "exploits"
    COMMUNICATES_WITH = "communicates_with"
    SIMILAR_TO = "similar_to"
    CAUSED_BY = "caused_by"
    RELATED_TO = "related_to"


@dataclass
class GraphNode:
    """Entity node in threat graph"""
    node_id: str
    node_type: str  # "user", "asset", "threat", "event", "vulnerability"
    properties: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=get_now_pst)
    last_seen: datetime = field(default_factory=get_now_pst)
    risk_score: float = 0.5


@dataclass
class GraphEdge:
    """Relationship between nodes"""
    source_id: str
    target_id: str
    edge_type: str
    properties: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=get_now_pst)
    weight: float = 1.0  # For importance scoring


class ThreatGraph:
    """In-memory threat graph for correlation & analysis"""
    
    def __init__(self):
        self.file = 'data/threat_graph.json'
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self.node_index: Dict[str, Set[str]] = defaultdict(set)  # Type -> node IDs
        
        self.load_graph()
    
    def load_graph(self):
        """Load graph from disk"""
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct nodes
                    for node_id, node_data in data.get('nodes', {}).items():
                        node = GraphNode(
                            node_id=node_id,
                            node_type=node_data['node_type'],
                            properties=node_data.get('properties', {}),
                            created_at=datetime.fromisoformat(node_data['created_at']),
                            last_seen=datetime.fromisoformat(node_data['last_seen']),
                            risk_score=node_data.get('risk_score', 0.5)
                        )
                        self.nodes[node_id] = node
                        self.node_index[node.node_type].add(node_id)
                    
                    # Reconstruct edges
                    for edge_data in data.get('edges', []):
                        edge = GraphEdge(
                            source_id=edge_data['source_id'],
                            target_id=edge_data['target_id'],
                            edge_type=edge_data['edge_type'],
                            properties=edge_data.get('properties', {}),
                            created_at=datetime.fromisoformat(edge_data['created_at']),
                            weight=edge_data.get('weight', 1.0)
                        )
                        self.edges.append(edge)
                        self.adjacency[edge.source_id].append(edge.target_id)
                        self.reverse_adjacency[edge.target_id].append(edge.source_id)
            except Exception as e:
                print(f"[Graph Engine] Load error: {e}")
    
    def save_graph(self):
        """Save graph to disk"""
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        
        nodes_dict = {}
        for node_id, node in self.nodes.items():
            nodes_dict[node_id] = {
                'node_type': node.node_type,
                'properties': node.properties,
                'created_at': node.created_at.isoformat(),
                'last_seen': node.last_seen.isoformat(),
                'risk_score': node.risk_score
            }
        
        edges_list = []
        for edge in self.edges:
            edges_list.append({
                'source_id': edge.source_id,
                'target_id': edge.target_id,
                'edge_type': edge.edge_type,
                'properties': edge.properties,
                'created_at': edge.created_at.isoformat(),
                'weight': edge.weight
            })
        
        with open(self.file, 'w') as f:
            json.dump({
                'nodes': nodes_dict,
                'edges': edges_list
            }, f, indent=2)
    
    def add_node(self, node_id: str, node_type: str, properties: Dict = None) -> GraphNode:
        """Add node to graph"""
        if node_id in self.nodes:
            self.nodes[node_id].last_seen = get_now_pst()
            return self.nodes[node_id]
        
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties or {}
        )
        self.nodes[node_id] = node
        self.node_index[node_type].add(node_id)
        self.save_graph()
        return node
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, 
                 properties: Dict = None, weight: float = 1.0) -> GraphEdge:
        """Add relationship edge"""
        
        # Ensure nodes exist
        if source_id not in self.nodes:
            self.add_node(source_id, "unknown")
        if target_id not in self.nodes:
            self.add_node(target_id, "unknown")
        
        # Create edge
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {},
            weight=weight
        )
        
        self.edges.append(edge)
        self.adjacency[source_id].append(target_id)
        self.reverse_adjacency[target_id].append(source_id)
        self.save_graph()
        return edge
    
    def find_paths(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths between two nodes (BFS)"""
        paths = []
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            if current == target_id:
                paths.append(path)
                continue
            
            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited or len(path) < 3:
                    queue.append((neighbor, path + [neighbor]))
        
        return paths
    
    def get_blast_radius(self, node_id: str, max_hops: int = 3) -> Dict:
        """Calculate blast radius from compromised node"""
        affected = {node_id}
        current_level = {node_id}
        
        for hop in range(max_hops):
            next_level = set()
            for node in current_level:
                for neighbor in self.adjacency.get(node, []):
                    if neighbor not in affected:
                        next_level.add(neighbor)
            affected.update(next_level)
            current_level = next_level
        
        return {
            'compromised_node': node_id,
            'affected_nodes': list(affected),
            'affected_count': len(affected),
            'by_type': self._count_by_type(affected)
        }
    
    def get_threat_paths(self, threat_id: str) -> Dict:
        """Get all paths from threat to high-value targets"""
        crown_jewels = self._identify_crown_jewels()
        threat_paths = {}
        
        for target_id in crown_jewels:
            paths = self.find_paths(threat_id, target_id, max_depth=4)
            if paths:
                threat_paths[target_id] = paths
        
        return threat_paths
    
    def _identify_crown_jewels(self) -> List[str]:
        """Identify high-value targets (nodes with high risk score)"""
        high_risk = [
            node_id for node_id, node in self.nodes.items()
            if node.risk_score > 0.8
        ]
        return high_risk
    
    def _count_by_type(self, node_ids: Set[str]) -> Dict:
        """Count nodes by type"""
        counts = defaultdict(int)
        for node_id in node_ids:
            if node_id in self.nodes:
                counts[self.nodes[node_id].node_type] += 1
        return dict(counts)
    
    def get_node_relationships(self, node_id: str) -> Dict:
        """Get all relationships for a node"""
        incoming = self.reverse_adjacency.get(node_id, [])
        outgoing = self.adjacency.get(node_id, [])
        
        return {
            'node_id': node_id,
            'incoming': incoming,
            'outgoing': outgoing,
            'total_connections': len(incoming) + len(outgoing)
        }
    
    def search_nodes(self, node_type: str = None, properties: Dict = None) -> List[GraphNode]:
        """Search nodes by type and properties"""
        results = []
        
        if node_type:
            candidates = [self.nodes[nid] for nid in self.node_index.get(node_type, [])]
        else:
            candidates = list(self.nodes.values())
        
        for node in candidates:
            if properties:
                if all(node.properties.get(k) == v for k, v in properties.items()):
                    results.append(node)
            else:
                results.append(node)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        
        for node in self.nodes.values():
            node_types[node.node_type] += 1
        
        for edge in self.edges:
            edge_types[edge.edge_type] += 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'crown_jewels': len(self._identify_crown_jewels()),
            'avg_connections': len(self.edges) / len(self.nodes) if self.nodes else 0
        }


# Global threat graph instance
threat_graph = ThreatGraph()
