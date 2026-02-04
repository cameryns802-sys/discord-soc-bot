"""
TIER-2 ADVERSARY: Behavior Profiler
Profiles adversary tactics, techniques, and patterns for attribution
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class AdversaryBehaviorProfiler(commands.Cog):
    """Adversary behavior analysis and profiling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/adversary_profiles.json'
        self.profiles = {}  # adversary_id -> profile_data
        self.load_profiles()
    
    def load_profiles(self):
        """Load adversary profiles"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.profiles = json.load(f)
                    print(f"[AdversaryProfiler] ✅ Loaded {len(self.profiles)} adversary profiles")
            except:
                self.profiles = {}
    
    def create_profile(self, adversary_id: str, name: str, initial_data: Dict = None) -> str:
        """Create new adversary profile"""
        self.profiles[adversary_id] = {
            'id': adversary_id,
            'name': name,
            'created_at': get_now_pst().isoformat(),
            'tactics': {},  # tactic -> count
            'techniques': {},  # technique -> count
            'tools': [],  # observed tools
            'targets': [],  # observed targets
            'patterns': [],  # behavioral patterns
            'confidence': 0.0,  # attribution confidence
            'last_seen': get_now_pst().isoformat(),
            'activity_count': 0
        }
        
        if initial_data:
            self.profiles[adversary_id].update(initial_data)
        
        self._save_profiles()
        return adversary_id
    
    def update_behavior(self, adversary_id: str, tactic: str, technique: str, tool: str = None):
        """Update adversary behavior record"""
        if adversary_id not in self.profiles:
            self.create_profile(adversary_id, f"Adversary_{adversary_id[:8]}")
        
        profile = self.profiles[adversary_id]
        
        # Update tactic count
        profile['tactics'][tactic] = profile['tactics'].get(tactic, 0) + 1
        
        # Update technique count
        profile['techniques'][technique] = profile['techniques'].get(technique, 0) + 1
        
        # Add tool if provided
        if tool and tool not in profile['tools']:
            profile['tools'].append(tool)
        
        profile['activity_count'] += 1
        profile['last_seen'] = get_now_pst().isoformat()
        
        self._save_profiles()
    
    def get_profile(self, adversary_id: str) -> Optional[Dict]:
        """Get adversary profile"""
        return self.profiles.get(adversary_id)
    
    def get_profile_stats(self, adversary_id: str) -> Dict:
        """Get statistics for profile"""
        profile = self.get_profile(adversary_id)
        if not profile:
            return {}
        
        top_tactic = max(profile['tactics'].items(), key=lambda x: x[1])[0] if profile['tactics'] else None
        top_technique = max(profile['techniques'].items(), key=lambda x: x[1])[0] if profile['techniques'] else None
        
        return {
            'name': profile['name'],
            'activity_count': profile['activity_count'],
            'unique_tactics': len(profile['tactics']),
            'unique_techniques': len(profile['techniques']),
            'tools_observed': len(profile['tools']),
            'top_tactic': top_tactic,
            'top_technique': top_technique,
            'confidence': profile['confidence']
        }
    
    def _save_profiles(self):
        """Save profiles"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.profiles, f, indent=2, default=str)
    
    @commands.command(name='adversaryprofile')
    async def show_profile(self, ctx, adversary_id: str):
        """Show adversary profile"""
        stats = self.get_profile_stats(adversary_id)
        
        if not stats:
            await ctx.send("❌ Profile not found")
            return
        
        embed = discord.Embed(
            title=f"🎯 {stats['name']} Profile",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Activity Count", value=str(stats['activity_count']), inline=True)
        embed.add_field(name="Confidence", value=f"{stats['confidence']:.1%}", inline=True)
        embed.add_field(name="Tactics Used", value=str(stats['unique_tactics']), inline=True)
        embed.add_field(name="Techniques Used", value=str(stats['unique_techniques']), inline=True)
        embed.add_field(name="Tools Observed", value=str(stats['tools_observed']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdversaryBehaviorProfiler(bot))
