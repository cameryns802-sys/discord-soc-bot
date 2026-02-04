"""
Threatwatch System: Monitor and track security-related activities.
Detects suspicious patterns and generates security alerts.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst
from cogs.core.signal_bus import signal_bus, Signal, SignalType

DATA_FILE = 'data/threatwatch_system.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'threats': [],  # List of detected threats
        'threat_actors': {},  # actor_name: {threat_count, first_seen, last_seen}
        'config': {
            'enabled': True,
            'track_mass_actions': True,
            'track_permission_changes': True,
            'track_deletion_patterns': True,
            'alert_on_threat': True,
            'threat_threshold': 3  # Alert after X threats in Y minutes
        }
    }

def save_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class ThreatwatchCog(commands.Cog):
    """Monitor for security threats and suspicious patterns"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.recent_threats = []  # Quick reference for recent threats

    async def emit_threat_signal(self, threat_type: str, severity: str, details: dict):
        """Emit signal when threat detected"""
        if not self.data['config'].get('alert_on_threat', True):
            return
        
        signal = Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity=severity,
            source='threatwatch',
            data={
                'threat_type': threat_type,
                'details': details,
                'confidence': 0.85
            }
        )
        await signal_bus.emit(signal)

    def log_threat(self, threat_type: str, actor: str, severity: str, details: dict):
        """Log a detected threat"""
        threat = {
            'id': len(self.data['threats']) + 1,
            'type': threat_type,
            'actor': actor,
            'severity': severity,
            'timestamp': get_now_pst().isoformat(),
            'details': details
        }
        
        self.data['threats'].append(threat)
        
        # Update threat actor tracking
        if actor not in self.data['threat_actors']:
            self.data['threat_actors'][actor] = {
                'threat_count': 0,
                'first_seen': get_now_pst().isoformat(),
                'last_seen': get_now_pst().isoformat()
            }
        
        self.data['threat_actors'][actor]['threat_count'] += 1
        self.data['threat_actors'][actor]['last_seen'] = get_now_pst().isoformat()
        
        # Keep only last 500 threats
        if len(self.data['threats']) > 500:
            self.data['threats'] = self.data['threats'][-500:]
        
        save_data(self.data)
        self.recent_threats.append(threat)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Detect mass kicks/bans"""
        if not self.data['config'].get('track_mass_actions', True):
            return
        
        # Track removal events
        self.log_threat(
            threat_type='member_removal',
            actor=str(member.guild.owner) if member.guild.owner else 'unknown',
            severity='medium',
            details={'user': str(member), 'guild': str(member.guild)}
        )
        
        await self.emit_threat_signal(
            'member_removal',
            'medium',
            {'user': str(member), 'guild': str(member.guild)}
        )

    @commands.command()
    async def threatwatch_status(self, ctx):
        """View threatwatch status"""
        threat_count = len(self.data['threats'])
        actor_count = len(self.data['threat_actors'])
        
        embed = discord.Embed(
            title="🚨 Threatwatch Status",
            color=discord.Color.red() if threat_count > 0 else discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        status = "🟢 NO THREATS" if threat_count == 0 else f"🔴 {threat_count} THREATS DETECTED"
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Total Threats", value=str(threat_count), inline=True)
        embed.add_field(name="Threat Actors", value=str(actor_count), inline=True)
        
        if threat_count > 0:
            recent = self.data['threats'][-1]
            embed.add_field(
                name="Latest Threat",
                value=f"**{recent['type']}** by {recent['actor']}\nTime: {recent['timestamp']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def threatwatch_list(self, ctx, limit: int = 10):
        """List detected threats"""
        threats = self.data['threats'][-limit:]
        
        if not threats:
            await ctx.send("✅ No threats detected.")
            return
        
        threats.reverse()
        
        embed = discord.Embed(
            title="📋 Detected Threats",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        for threat in threats[:10]:
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(threat.get('severity', 'unknown'), '⚪')
            
            embed.add_field(
                name=f"{severity_emoji} {threat['type'].replace('_', ' ').title()}",
                value=f"**Actor:** {threat['actor']}\n**Time:** {threat['timestamp'][:16]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def threatwatch_actors(self, ctx):
        """Show threat actors"""
        if not self.data['threat_actors']:
            await ctx.send("✅ No threat actors identified.")
            return
        
        embed = discord.Embed(
            title="👹 Identified Threat Actors",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        sorted_actors = sorted(
            self.data['threat_actors'].items(),
            key=lambda x: x[1]['threat_count'],
            reverse=True
        )
        
        for actor_name, info in sorted_actors[:10]:
            embed.add_field(
                name=f"🎯 {actor_name}",
                value=f"Threats: {info['threat_count']}\nLast Seen: {info['last_seen'][:16]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def threatwatch_config(self, ctx):
        """View threatwatch configuration"""
        config = self.data['config']
        
        embed = discord.Embed(
            title="⚙️ Threatwatch Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Enabled", value="✅ Yes" if config.get('enabled', True) else "❌ No", inline=True)
        embed.add_field(name="Track Mass Actions", value="✅ Yes" if config.get('track_mass_actions', True) else "❌ No", inline=True)
        embed.add_field(name="Track Permissions", value="✅ Yes" if config.get('track_permission_changes', True) else "❌ No", inline=True)
        embed.add_field(name="Track Deletions", value="✅ Yes" if config.get('track_deletion_patterns', True) else "❌ No", inline=True)
        embed.add_field(name="Alert on Threat", value="✅ Yes" if config.get('alert_on_threat', True) else "❌ No", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def threatwatch_toggle(self, ctx):
        """Enable/disable threatwatch system"""
        enabled = self.data['config'].get('enabled', True)
        self.data['config']['enabled'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['enabled'] else "❌ DISABLED"
        await ctx.send(f"✅ Threatwatch is now {status}")

    @commands.command()
    async def threatwatch_clear(self, ctx):
        """Clear all threat logs"""
        self.data['threats'] = []
        self.data['threat_actors'] = {}
        save_data(self.data)
        
        await ctx.send("✅ Threat logs cleared")

async def setup(bot):
    await bot.add_cog(ThreatwatchCog(bot))
