"""
TIER-2 MEMORY: Semantic Similarity Engine
Matches queries against historical data using semantic similarity
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Tuple, Any
import hashlib
from cogs.core.pst_timezone import get_now_pst

class SemanticSimilarityEngine(commands.Cog):
    """Semantic query matching and similarity scoring"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/semantic_index.json'
        self.query_history = []
        self.similarity_cache = {}
        self.load_index()
    
    def load_index(self):
        """Load semantic index"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.query_history = data.get('queries', [])
                    print(f"[SemanticSimilarity] ✅ Loaded {len(self.query_history)} indexed queries")
            except:
                self.query_history = []
        else:
            self.query_history = []
    
    def calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two strings (0-1)"""
        # Simple word-overlap similarity (in production use embedding models)
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        # Jaccard similarity
        return intersection / union if union > 0 else 0.0
    
    def find_similar_queries(self, query: str, threshold: float = 0.5) -> List[Dict]:
        """Find similar historical queries"""
        matches = []
        
        for historical in self.query_history:
            similarity = self.calculate_similarity(query, historical.get('query', ''))
            
            if similarity >= threshold:
                matches.append({
                    'query': historical.get('query'),
                    'similarity': similarity,
                    'timestamp': historical.get('timestamp'),
                    'result': historical.get('result')
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:10]
    
    def index_query(self, query: str, result: Any = None):
        """Index a query for future similarity matching"""
        self.query_history.append({
            'query': query,
            'result': result,
            'timestamp': get_now_pst().isoformat(),
            'hash': hashlib.md5(query.encode()).hexdigest()[:8]
        })
        
        # Keep last 10000 queries
        if len(self.query_history) > 10000:
            self.query_history = self.query_history[-10000:]
        
        self._save_index()
    
    def _save_index(self):
        """Save semantic index"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'queries': self.query_history}, f, indent=2, default=str)
    
    @commands.command(name='semanticsearch')
    async def semantic_search(self, ctx, *, query: str):
        """Search similar historical queries"""
        matches = self.find_similar_queries(query, threshold=0.4)
        
        if not matches:
            await ctx.send("❌ No similar queries found")
            return
        
        embed = discord.Embed(
            title="🔍 Semantic Query Search",
            description=f"Found {len(matches)} similar queries",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for match in matches[:5]:
            embed.add_field(
                name=f"Similarity: {match['similarity']:.1%}",
                value=f"`{match['query'][:50]}`\nResult: {str(match['result'])[:40]}...",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='queryindex')
    async def query_index_stats(self, ctx):
        """View query index statistics (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(
            title="📚 Query Index Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Indexed Queries", value=str(len(self.query_history)), inline=True)
        embed.add_field(name="Cache Entries", value=str(len(self.similarity_cache)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SemanticSimilarityEngine(bot))
