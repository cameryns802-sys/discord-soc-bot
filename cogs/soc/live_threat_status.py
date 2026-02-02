"""
Live Threat Status: Real-time threat level monitoring and bot status updates
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os

class LiveThreatStatus(commands.Cog):
    """Real-time threat level tracking and bot status"""
    
    def __init__(self, bot):
        self.bot = bot
        self.threat_file = 'data/threat_responses.json'
        self.status_file = 'data/threat_status.json'
        os.makedirs('data', exist_ok=True)
        self.update_bot_status.start()
    
    def _calculate_threat_level(self) -> tuple:
        """Calculate current threat level across all guilds"""
        if not os.path.exists(self.threat_file):
            return 'green', 0, 0
        
        try:
            with open(self.threat_file, 'r') as f:
                threats = json.load(f)
        except:
            return 'green', 0, 0
        
        # Filter to last 24 hours
        now = datetime.now(datetime.UTC)
        cutoff = now - timedelta(hours=24)
        
        active_threats = []
        for threat in threats:
            try:
                detected = datetime.fromisoformat(threat['detected_at'])
                if detected > cutoff and threat.get('status') == 'active':
                    active_threats.append(threat)
            except:
                pass
        
        if not active_threats:
            return 'green', 0, 0
        
        # Count by level
        critical = sum(1 for t in active_threats if t.get('level') == 'critical')
        high = sum(1 for t in active_threats if t.get('level') == 'high')
        medium = sum(1 for t in active_threats if t.get('level') == 'medium')
        
        # Determine overall level
        if critical > 0:
            level = 'red'
        elif high > 2:
            level = 'red'
        elif high > 0:
            level = 'orange'
        elif medium > 3:
            level = 'orange'
        elif medium > 0:
            level = 'yellow'
        else:
            level = 'green'
        
        return level, len(active_threats), critical
    
    @tasks.loop(minutes=2)
    async def update_bot_status(self):
        """Update bot status based on threat level"""
        level, count, critical = self._calculate_threat_level()
        
        status_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'orange': '🟠',
            'red': '🔴'
        }
        
        status_text = {
            'green': 'All Clear',
            'yellow': f'{count} Threats',
            'orange': f'{count} Active Threats',
            'red': f'🚨 {count} Critical Threats!'
        }
        
        emoji = status_emoji.get(level, '🟢')
        text = status_text.get(level, 'All Clear')
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{emoji} {text}"
        )
        
        try:
            await self.bot.change_presence(activity=activity)
        except:
            pass
    
    @update_bot_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='threatstatus')
    @commands.has_permissions(manage_guild=True)
    async def threatstatus(self, ctx):
        """Check current threat status"""
        await self._threatstatus_logic(ctx)
    
    @app_commands.command(name="threatstatus", description="Check current threat level")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threatstatus_slash(self, interaction: discord.Interaction):
        """Threat status using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._threatstatus_logic(ctx)
    
    async def _threatstatus_logic(self, ctx):
        """Threat status implementation"""
        level, count, critical = self._calculate_threat_level()
        
        # Get threat details
        if os.path.exists(self.threat_file):
            try:
                with open(self.threat_file, 'r') as f:
                    all_threats = json.load(f)
            except:
                all_threats = []
        else:
            all_threats = []
        
        # Filter to guild
        guild_id = str(ctx.guild.id)
        now = datetime.now(datetime.UTC)
        cutoff = now - timedelta(hours=24)
        
        threats = [
            t for t in all_threats 
            if t.get('guild_id') == guild_id
        ]
        
        active = [t for t in threats if t.get('status') == 'active']
        
        # Color based on level
        color_map = {
            'green': discord.Color.green(),
            'yellow': discord.Color.gold(),
            'orange': discord.Color.orange(),
            'red': discord.Color.red()
        }
        
        emoji_map = {
            'green': '🟢',
            'yellow': '🟡',
            'orange': '🟠',
            'red': '🔴'
        }
        
        embed = discord.Embed(
            title=f"{emoji_map[level]} Threat Status",
            description=self._get_threat_description(level),
            color=color_map[level],
            timestamp=datetime.now(datetime.UTC)
        )
        
        # Summary
        embed.add_field(
            name="📊 Summary",
            value=f"**Level:** {level.upper()}\n**Active:** {len(active)}\n**Critical:** {critical}",
            inline=True
        )
        
        # Threat breakdown
        if threats:
            levels = {}
            for t in threats:
                tlevel = t.get('level', 'unknown')
                levels[tlevel] = levels.get(tlevel, 0) + 1
            
            breakdown = "\n".join([f"**{k}:** {v}" for k, v in sorted(levels.items(), reverse=True)])
            embed.add_field(
                name="⚠️ Breakdown (24h)",
                value=breakdown,
                inline=True
            )
        
        # Recommendations
        if level == 'red':
            embed.add_field(
                name="🚨 ACTION REQUIRED",
                value="Critical threats detected! Check `/threathistory` for details.",
                inline=False
            )
        elif level == 'orange':
            embed.add_field(
                name="⚠️ ELEVATED ALERT",
                value="Multiple active threats. Monitor closely.",
                inline=False
            )
        elif level == 'yellow':
            embed.add_field(
                name="⚠️ WATCH",
                value="Low-level threats detected. Continue monitoring.",
                inline=False
            )
        else:
            embed.add_field(
                name="✅ STATUS",
                value="All clear. No active threats.",
                inline=False
            )
        
        # Recent threats
        if active:
            recent_text = ""
            for threat in active[:3]:
                recent_text += f"• **{threat['type']}** ({threat['level']}) - {threat.get('description', 'No description')[:50]}\n"
            
            embed.add_field(
                name="🔔 Recent Active Threats",
                value=recent_text,
                inline=False
            )
        
        embed.set_footer(text=f"Guild: {ctx.guild.id} • Last updated")
        
        await ctx.send(embed=embed)
    
    def _get_threat_description(self, level: str) -> str:
        """Get description for threat level"""
        descriptions = {
            'green': '✅ No active threats - All systems normal',
            'yellow': '⚠️ Low-level threats detected - Monitor activity',
            'orange': '🟠 Multiple active threats - Review immediately',
            'red': '🔴 CRITICAL THREATS - Take action now!'
        }
        return descriptions.get(level, 'Unknown')
    
    @commands.command(name='threatlevel')
    @commands.has_permissions(manage_guild=True)
    async def threatlevel(self, ctx):
        """Get quick threat level indicator"""
        await self._threatlevel_logic(ctx)
    
    @app_commands.command(name="threatlevel", description="Quick threat level indicator")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threatlevel_slash(self, interaction: discord.Interaction):
        """Threat level using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._threatlevel_logic(ctx)
    
    async def _threatlevel_logic(self, ctx):
        """Quick threat level"""
        level, count, critical = self._calculate_threat_level()
        
        emoji_map = {
            'green': '🟢',
            'yellow': '🟡',
            'orange': '🟠',
            'red': '🔴'
        }
        
        status_map = {
            'green': '✅ ALL CLEAR',
            'yellow': '⚠️ LOW THREAT',
            'orange': '🟠 ELEVATED',
            'red': '🔴 CRITICAL'
        }
        
        response = f"{emoji_map[level]} **{status_map[level]}**\n"
        if count > 0:
            response += f"Active threats: {count}\nCritical: {critical}"
        else:
            response += "No active threats detected"
        
        await ctx.send(response)

async def setup(bot):
    await bot.add_cog(LiveThreatStatus(bot))
