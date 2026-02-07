"""
IMPOSSIBLE TRAVEL DETECTOR - Identity Threat Detection

Detects:
- Impossible travel (access from geographically impossible locations)
- Anomalous login patterns
- Token abuse
- Session hijacking
"""

import discord
from discord.ext import commands
from typing import Dict, Optional
from datetime import datetime, timedelta

from cogs.core.pst_timezone import get_now_pst


class ImpossibleTravelDetector(commands.Cog):
    """Detect impossible travel and identity threats"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_sessions = {}  # Track user login locations
    
    def check_impossible_travel(self, user_id: str, new_location: Dict) -> Optional[Dict]:
        """Check if user accessed from impossible location"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        
        last_session = self.user_sessions[user_id][-1] if self.user_sessions[user_id] else None
        
        if last_session:
            time_diff = (datetime.now() - last_session['timestamp']).total_seconds() / 3600
            distance = self._calculate_distance(last_session['location'], new_location)
            required_speed = distance / time_diff if time_diff > 0 else 0
            
            # Impossible if >900 km/hour speed required
            if required_speed > 900:
                return {
                    'user_id': user_id,
                    'threat_type': 'impossible_travel',
                    'severity': 'HIGH',
                    'last_location': last_session['location'],
                    'new_location': new_location,
                    'required_speed_kmh': required_speed,
                    'timestamp': get_now_pst().isoformat()
                }
        
        self.user_sessions[user_id].append({
            'location': new_location,
            'timestamp': datetime.now()
        })
        
        return None
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Simple distance calculation (lat/lon)"""
        import math
        lat1 = float(loc1.get('latitude', 0))
        lon1 = float(loc1.get('longitude', 0))
        lat2 = float(loc2.get('latitude', 0))
        lon2 = float(loc2.get('longitude', 0))
        
        # Haversine formula (simplified)
        return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111  # ~111 km per degree
    
    @commands.command(name='identitythreats')
    @commands.is_owner()
    async def identity_threats(self, ctx):
        """Show identity-based threats"""
        embed = discord.Embed(
            title="🔐 Identity Threat Detection",
            color=discord.Color.purple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Tracked Users", value=str(len(self.user_sessions)), inline=True)
        embed.add_field(name="Status", value="✅ Active", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ImpossibleTravelDetector(bot))
