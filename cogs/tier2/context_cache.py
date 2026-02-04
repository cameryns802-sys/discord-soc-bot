"""
TIER-2 MEMORY SUBSYSTEM: Context Cache
Manages contextual information caching for rapid decision-making
Part of Sentinel Advanced Intelligence Platform
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Any
from collections import OrderedDict
from cogs.core.pst_timezone import get_now_pst

class ContextCache(commands.Cog):
    """Context caching system for reduced latency"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cache_file = 'data/context_cache.json'
        self.memory = {}  # In-memory cache
        self.access_stats = {}  # Track cache hits/misses
        self.ttl_seconds = 3600  # Default 1 hour TTL
        self.max_cache_size = 10000
        
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self.load_cache()
        self.cleanup_expired.start()
    
    def load_cache(self):
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.memory = json.load(f)
                print(f"[ContextCache] ✅ Loaded {len(self.memory)} cached items")
            except:
                self.memory = {}
    
    def save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.memory, f, indent=2, default=str)
    
    def set_context(self, key: str, value: Any, ttl_seconds: int = None):
        """Cache a context value"""
        ttl = ttl_seconds or self.ttl_seconds
        expires_at = (get_now_pst() + timedelta(seconds=ttl)).isoformat()
        
        self.memory[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': get_now_pst().isoformat(),
            'access_count': 0
        }
        
        # Enforce max cache size
        if len(self.memory) > self.max_cache_size:
            # Remove oldest accessed items
            sorted_items = sorted(
                self.memory.items(),
                key=lambda x: x[1].get('access_count', 0)
            )
            for key_to_remove, _ in sorted_items[:100]:
                del self.memory[key_to_remove]
        
        self.save_cache()
    
    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve cached context"""
        if key not in self.memory:
            self.access_stats[key] = self.access_stats.get(key, 0)
            return None
        
        entry = self.memory[key]
        
        # Check expiration
        expires_at = datetime.fromisoformat(entry['expires_at'])
        if get_now_pst() > expires_at:
            del self.memory[key]
            return None
        
        # Update access count
        entry['access_count'] = entry.get('access_count', 0) + 1
        self.access_stats[key] = self.access_stats.get(key, 0) + 1
        
        return entry['value']
    
    def invalidate_context(self, key: str):
        """Remove cached context"""
        if key in self.memory:
            del self.memory[key]
            self.save_cache()
    
    def clear_context_pattern(self, pattern: str):
        """Clear all contexts matching pattern"""
        import re
        regex = re.compile(pattern)
        to_remove = [k for k in self.memory.keys() if regex.search(k)]
        
        for key in to_remove:
            del self.memory[key]
        
        self.save_cache()
        return len(to_remove)
    
    @tasks.loop(minutes=30)
    async def cleanup_expired(self):
        """Remove expired cache entries"""
        now = get_now_pst()
        expired = []
        
        for key, entry in self.memory.items():
            expires_at = datetime.fromisoformat(entry['expires_at'])
            if now > expires_at:
                expired.append(key)
        
        for key in expired:
            del self.memory[key]
        
        if expired:
            self.save_cache()
            print(f"[ContextCache] Cleaned up {len(expired)} expired entries")
    
    @commands.command(name='cachestats')
    async def cache_stats(self, ctx):
        """View cache statistics (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        # Calculate hit/miss rate
        total_access = sum(self.access_stats.values())
        hit_rate = (sum(v for k, v in self.access_stats.items() if k in self.memory) / total_access * 100) if total_access > 0 else 0
        
        embed = discord.Embed(
            title="📊 Context Cache Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Cached Items", value=str(len(self.memory)), inline=True)
        embed.add_field(name="Max Size", value=str(self.max_cache_size), inline=True)
        embed.add_field(name="Cache Utilization", value=f"{(len(self.memory) / self.max_cache_size * 100):.1f}%", inline=True)
        
        embed.add_field(name="Total Access Count", value=str(total_access), inline=True)
        embed.add_field(name="Unique Keys Accessed", value=str(len(self.access_stats)), inline=True)
        embed.add_field(name="Hit Rate (est)", value=f"{hit_rate:.1f}%", inline=True)
        
        embed.add_field(name="Default TTL", value=f"{self.ttl_seconds // 3600}h", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ContextCache(bot))
