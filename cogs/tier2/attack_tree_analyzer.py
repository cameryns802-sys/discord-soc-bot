"""
TIER-2 ADVERSARY: Attack Tree Analyzer
Analyzes attack trees and execution paths for threat modeling
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Tuple
from cogs.core.pst_timezone import get_now_pst

class AttackTreeAnalyzer(commands.Cog):
    """Attack tree construction and analysis"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/attack_trees.json'
        self.trees = {}  # tree_id -> tree_data
        self.load_trees()
    
    def load_trees(self):
        """Load attack trees"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.trees = json.load(f)
                    print(f"[AttackTree] ✅ Loaded {len(self.trees)} attack trees")
            except:
                self.trees = {}
    
    def create_tree(self, tree_id: str, root_goal: str) -> str:
        """Create attack tree"""
        self.trees[tree_id] = {
            'id': tree_id,
            'root_goal': root_goal,
            'nodes': [{'id': 'root', 'label': root_goal, 'type': 'OR', 'children': []}],
            'created_at': get_now_pst().isoformat(),
            'probability': 0.0,
            'impact': 0.0
        }
        
        self._save_trees()
        return tree_id
    
    def add_node(self, tree_id: str, parent_id: str, node_id: str, label: str, node_type: str = 'AND') -> bool:
        """Add node to tree"""
        if tree_id not in self.trees:
            return False
        
        tree = self.trees[tree_id]
        
        # Find parent and add child
        def find_and_add(nodes, parent_id, new_node):
            for node in nodes:
                if node['id'] == parent_id:
                    node.setdefault('children', []).append({
                        'id': node_id,
                        'label': label,
                        'type': node_type,
                        'children': []
                    })
                    return True
                
                if find_and_add(node.get('children', []), parent_id, new_node):
                    return True
            
            return False
        
        result = find_and_add(tree['nodes'], parent_id, None)
        
        if result:
            self._save_trees()
        
        return result
    
    def calculate_probability(self, tree_id: str) -> float:
        """Calculate attack success probability"""
        if tree_id not in self.trees:
            return 0.0
        
        tree = self.trees[tree_id]
        
        # Simplified: each leaf node has 50% probability
        # In production: use historical data or expert assessment
        leaf_count = self._count_leaves(tree['nodes'][0])
        
        return min(1.0, leaf_count * 0.1)
    
    def _count_leaves(self, node: Dict) -> int:
        """Count leaf nodes"""
        if not node.get('children'):
            return 1
        
        return sum(self._count_leaves(child) for child in node['children'])
    
    def get_attack_paths(self, tree_id: str) -> List[List[str]]:
        """Get all attack paths from root to leaves"""
        if tree_id not in self.trees:
            return []
        
        paths = []
        tree = self.trees[tree_id]
        
        def dfs(node, path):
            path.append(node['label'])
            
            if not node.get('children'):
                paths.append(path.copy())
            else:
                for child in node['children']:
                    dfs(child, path)
            
            path.pop()
        
        if tree['nodes']:
            dfs(tree['nodes'][0], [])
        
        return paths
    
    def _save_trees(self):
        """Save trees"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.trees, f, indent=2, default=str)
    
    @commands.command(name='attacktree')
    async def show_tree(self, ctx, tree_id: str):
        """Show attack tree"""
        if tree_id not in self.trees:
            await ctx.send("❌ Tree not found")
            return
        
        tree = self.trees[tree_id]
        paths = self.get_attack_paths(tree_id)
        probability = self.calculate_probability(tree_id)
        
        embed = discord.Embed(
            title=f"🌳 Attack Tree: {tree['root_goal']}",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Paths", value=str(len(paths)), inline=True)
        embed.add_field(name="Success Probability", value=f"{probability:.1%}", inline=True)
        
        if paths:
            embed.add_field(name="Sample Paths", value="\n".join([" → ".join(p[:3]) for p in paths[:3]]), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AttackTreeAnalyzer(bot))
