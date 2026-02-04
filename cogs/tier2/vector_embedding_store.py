"""
TIER-2 MEMORY: Vector Embedding Store
Stores and retrieves high-dimensional vector embeddings for semantic search
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional
import hashlib
from cogs.core.pst_timezone import get_now_pst

class VectorEmbeddingStore(commands.Cog):
    """Vector embedding storage and similarity search"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vector_embeddings.json'
        self.embeddings = {}  # id -> {vector, metadata}
        self.load_embeddings()
    
    def load_embeddings(self):
        """Load embeddings"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.embeddings = data.get('embeddings', {})
                    print(f"[VectorStore] ✅ Loaded {len(self.embeddings)} embeddings")
            except:
                self.embeddings = {}
    
    def store_embedding(self, text: str, vector: List[float], metadata: Dict = None) -> str:
        """Store text embedding with metadata"""
        embed_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        self.embeddings[embed_id] = {
            'id': embed_id,
            'text': text[:500],  # Store first 500 chars
            'vector': vector,
            'metadata': metadata or {},
            'stored_at': get_now_pst().isoformat(),
            'dimension': len(vector)
        }
        
        # Keep last 50000 embeddings
        if len(self.embeddings) > 50000:
            # Remove oldest
            oldest_key = min(
                self.embeddings.keys(),
                key=lambda k: self.embeddings[k].get('stored_at', '')
            )
            del self.embeddings[oldest_key]
        
        self._save_embeddings()
        return embed_id
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(x ** 2 for x in vec1) ** 0.5
        magnitude2 = sum(x ** 2 for x in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def find_similar_embeddings(self, query_vector: List[float], limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Find similar embeddings"""
        similarities = []
        
        for embed_id, embedding in self.embeddings.items():
            similarity = self.cosine_similarity(query_vector, embedding['vector'])
            
            if similarity >= threshold:
                similarities.append({
                    'id': embed_id,
                    'text': embedding['text'],
                    'similarity': similarity,
                    'metadata': embedding.get('metadata')
                })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    def get_embedding(self, embed_id: str) -> Optional[Dict]:
        """Get embedding by ID"""
        return self.embeddings.get(embed_id)
    
    def delete_embedding(self, embed_id: str):
        """Delete embedding"""
        if embed_id in self.embeddings:
            del self.embeddings[embed_id]
            self._save_embeddings()
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        if not self.embeddings:
            return {}
        
        dimensions = set(e.get('dimension', 0) for e in self.embeddings.values())
        
        return {
            'total_embeddings': len(self.embeddings),
            'dimensions': list(dimensions),
            'oldest_embedding': min((e.get('stored_at', '') for e in self.embeddings.values())),
            'newest_embedding': max((e.get('stored_at', '') for e in self.embeddings.values()))
        }
    
    def _save_embeddings(self):
        """Save embeddings"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'embeddings': self.embeddings}, f, indent=2, default=str)
    
    @commands.command(name='vectorstats')
    async def vector_stats(self, ctx):
        """View vector embedding store statistics"""
        stats = self.get_statistics()
        
        if not stats:
            await ctx.send("❌ No embeddings stored yet")
            return
        
        embed = discord.Embed(
            title="📊 Vector Embedding Store Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Embeddings", value=str(stats['total_embeddings']), inline=True)
        embed.add_field(name="Dimensions", value=str(stats['dimensions']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VectorEmbeddingStore(bot))
