"""
TIER-2 MEMORY: Memory Lifecycle Manager
Manages memory retention, archival, and cleanup policies
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class MemoryLifecycleManager(commands.Cog):
    """Memory retention and lifecycle management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/memory_lifecycle_config.json'
        self.archive_file = 'data/memory_archive.json'
        
        self.retention_policies = {
            'hot': 7,  # days - actively used memory
            'warm': 30,  # days - less frequently accessed
            'cold': 90,  # days - archived
            'expired': 180  # days - deleted
        }
        
        self.tiers = {
            'hot': [],
            'warm': [],
            'cold': [],
            'archive': []
        }
        
        self.load_config()
        self.lifecycle_management.start()
    
    def load_config(self):
        """Load lifecycle configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.retention_policies = data.get('retention', self.retention_policies)
                    self.tiers = data.get('tiers', self.tiers)
                    print(f"[MemoryLifecycle] ✅ Loaded lifecycle config")
            except:
                self._save_config()
        else:
            self._save_config()
    
    def move_to_tier(self, memory_id: str, source_tier: str, target_tier: str) -> bool:
        """Move memory between tiers"""
        if source_tier not in self.tiers or target_tier not in self.tiers:
            return False
        
        if memory_id in self.tiers[source_tier]:
            self.tiers[source_tier].remove(memory_id)
            self.tiers[target_tier].append(memory_id)
            self._save_config()
            return True
        
        return False
    
    def get_memory_tier(self, memory_id: str) -> Optional[str]:
        """Get current tier of memory"""
        for tier, memories in self.tiers.items():
            if memory_id in memories:
                return tier
        return None
    
    def archive_memory(self, memory_id: str, metadata: Dict = None):
        """Archive memory for long-term storage"""
        if os.path.exists(self.archive_file):
            with open(self.archive_file, 'r') as f:
                archive = json.load(f)
        else:
            archive = {'memories': []}
        
        archive['memories'].append({
            'id': memory_id,
            'archived_at': get_now_pst().isoformat(),
            'metadata': metadata or {}
        })
        
        # Keep last 100000 archived items
        if len(archive['memories']) > 100000:
            archive['memories'] = archive['memories'][-100000:]
        
        with open(self.archive_file, 'w') as f:
            json.dump(archive, f, default=str)
    
    def cleanup_expired(self) -> Dict:
        """Clean up expired memories"""
        results = {
            'moved_to_warm': 0,
            'moved_to_cold': 0,
            'archived': 0
        }
        
        # Hot -> Warm (7 days)
        hot_threshold = get_now_pst() - timedelta(days=self.retention_policies['hot'])
        # Warm -> Cold (30 days)
        warm_threshold = get_now_pst() - timedelta(days=self.retention_policies['warm'])
        # Cold -> Archive (90 days)
        cold_threshold = get_now_pst() - timedelta(days=self.retention_policies['cold'])
        
        # In production, would check access timestamps
        # For now, just log operations
        
        self._save_config()
        return results
    
    def get_lifecycle_stats(self) -> Dict:
        """Get memory lifecycle statistics"""
        return {
            'hot_memories': len(self.tiers['hot']),
            'warm_memories': len(self.tiers['warm']),
            'cold_memories': len(self.tiers['cold']),
            'archived': len(self.tiers['archive']),
            'total_memories': sum(len(v) for v in self.tiers.values()),
            'retention_policies': self.retention_policies
        }
    
    @tasks.loop(hours=6)
    async def lifecycle_management(self):
        """Periodic memory lifecycle management"""
        results = self.cleanup_expired()
        
        if sum(results.values()) > 0:
            print(f"[MemoryLifecycle] Cleanup: {results}")
    
    def _save_config(self):
        """Save lifecycle configuration"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump({
                'retention': self.retention_policies,
                'tiers': self.tiers
            }, f, indent=2, default=str)
    
    @commands.command(name='memorylifecycle')
    async def lifecycle_stats(self, ctx):
        """View memory lifecycle statistics"""
        stats = self.get_lifecycle_stats()
        
        embed = discord.Embed(
            title="📊 Memory Lifecycle Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🔥 Hot Memory", value=str(stats['hot_memories']), inline=True)
        embed.add_field(name="🌡️ Warm Memory", value=str(stats['warm_memories']), inline=True)
        embed.add_field(name="❄️ Cold Memory", value=str(stats['cold_memories']), inline=True)
        embed.add_field(name="📦 Archived", value=str(stats['archived']), inline=True)
        embed.add_field(name="📊 Total", value=str(stats['total_memories']), inline=True)
        
        embed.add_field(name="Retention Policies", value="━" * 25, inline=False)
        for tier, days in stats['retention_policies'].items():
            embed.add_field(name=tier.title(), value=f"{days} days", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemoryLifecycleManager(bot))
