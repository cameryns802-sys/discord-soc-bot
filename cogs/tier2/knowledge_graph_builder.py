"""
TIER-2 MEMORY: Knowledge Graph Builder
Constructs and maintains knowledge graphs from operational data
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Set, Tuple
from cogs.core.pst_timezone import get_now_pst

class KnowledgeGraphBuilder(commands.Cog):
    """Knowledge graph construction and querying"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/knowledge_graph.json'
        self.nodes = {}  # node_id -> node_data
        self.edges = []  # list of edge_data
        self.load_graph()
    
    def load_graph(self):
        """Load knowledge graph"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.nodes = data.get('nodes', {})
                    self.edges = data.get('edges', [])
                    print(f"[KnowledgeGraph] ✅ Loaded {len(self.nodes)} nodes, {len(self.edges)} edges")
            except:
                self.init_empty_graph()
        else:
            self.init_empty_graph()
    
    def init_empty_graph(self):
        """Initialize empty graph"""
        self.nodes = {}
        self.edges = []
        self._save_graph()
    
    def add_node(self, node_id: str, node_type: str, properties: Dict = None):
        """Add node to graph"""
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'properties': properties or {},
            'created_at': get_now_pst().isoformat(),
            'degree': 0
        }
        
        self._save_graph()
        return node_id
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, properties: Dict = None):
        """Add edge between nodes"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        edge = {
            'source': source_id,
            'target': target_id,
            'type': edge_type,
            'properties': properties or {},
            'created_at': get_now_pst().isoformat()
        }
        
        self.edges.append(edge)
        
        # Update node degrees
        self.nodes[source_id]['degree'] = self.nodes[source_id].get('degree', 0) + 1
        self.nodes[target_id]['degree'] = self.nodes[target_id].get('degree', 0) + 1
        
        self._save_graph()
        return True
    
    def find_neighbors(self, node_id: str, edge_type: str = None) -> List[str]:
        """Find neighboring nodes"""
        neighbors = []
        
        for edge in self.edges:
            if edge['source'] == node_id:
                if edge_type is None or edge['type'] == edge_type:
                    neighbors.append(edge['target'])
            elif edge['target'] == node_id:
                if edge_type is None or edge['type'] == edge_type:
                    neighbors.append(edge['source'])
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find shortest path between nodes (BFS)"""
        from collections import deque
        
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            node, path = queue.popleft()
            
            if node == target_id:
                return path
            
            if len(path) >= max_depth:
                continue
            
            for neighbor in self.find_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def get_subgraph(self, node_id: str, depth: int = 2) -> Tuple[Dict, List]:
        """Get subgraph around node"""
        nodes_result = {node_id: self.nodes.get(node_id, {})}
        edges_result = []
        visited = {node_id}
        
        # BFS to collect nodes and edges
        to_visit = [(node_id, 0)]
        
        while to_visit:
            current, current_depth = to_visit.pop(0)
            
            if current_depth >= depth:
                continue
            
            for neighbor in self.find_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    nodes_result[neighbor] = self.nodes.get(neighbor, {})
                    to_visit.append((neighbor, current_depth + 1))
                    
                    # Add edge
                    for edge in self.edges:
                        if (edge['source'] == current and edge['target'] == neighbor) or \
                           (edge['target'] == current and edge['source'] == neighbor):
                            edges_result.append(edge)
        
        return nodes_result, edges_result
    
    def get_graph_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        node_types = {}
        edge_types = {}
        
        for node in self.nodes.values():
            ntype = node.get('type', 'unknown')
            node_types[ntype] = node_types.get(ntype, 0) + 1
        
        for edge in self.edges:
            etype = edge.get('type', 'unknown')
            edge_types[etype] = edge_types.get(etype, 0) + 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': node_types,
            'edge_types': edge_types,
            'average_degree': sum(n.get('degree', 0) for n in self.nodes.values()) / len(self.nodes) if self.nodes else 0
        }
    
    def _save_graph(self):
        """Save knowledge graph"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'nodes': self.nodes, 'edges': self.edges}, f, indent=2, default=str)
    
    @commands.command(name='graphstats')
    async def graph_stats(self, ctx):
        """View knowledge graph statistics"""
        stats = self.get_graph_stats()
        
        embed = discord.Embed(
            title="📊 Knowledge Graph Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Nodes", value=str(stats['total_nodes']), inline=True)
        embed.add_field(name="Total Edges", value=str(stats['total_edges']), inline=True)
        embed.add_field(name="Avg Node Degree", value=f"{stats['average_degree']:.2f}", inline=True)
        
        if stats['node_types']:
            types_str = "\n".join([f"• {t}: {c}" for t, c in stats['node_types'].items()])
            embed.add_field(name="Node Types", value=types_str, inline=False)
        
        if stats['edge_types']:
            edges_str = "\n".join([f"• {t}: {c}" for t, c in stats['edge_types'].items()])
            embed.add_field(name="Edge Types", value=edges_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(KnowledgeGraphBuilder(bot))
