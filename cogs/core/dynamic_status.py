"""
DYNAMIC STATUS SYSTEM
Threat level-based status with rotating messages.

Threat Levels:
- 🟢 Normal: Default state, rotating messages
- 🟡 Elevated: Medium threats detected
- 🔴 Panic: Critical threats detected
- ⚫ Lockdown: System under attack

Status changes based on signal bus activity and threat scores.
"""

import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class DynamicStatus(commands.Cog):
    """Dynamic threat level status system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.current_level = 'normal'
        self.current_message_index = 0
        self.last_threat_time = None
        self.active_drill = None  # Track active drill
        self.active_threat = None  # Track active threat
        
        # Status messages for each threat level
        self.status_messages = {
            'normal': [
                "🟢 All systems nominal",
                "🟢 Security operations running",
                "🟢 No threats detected",
                "🟢 Monitoring 84+ systems",
                "🟢 Protection active"
            ],
            'elevated': [
                "🟡 Elevated threat level",
                "🟡 Monitoring increased activity",
                "🟡 Security alert active",
                "🟡 Investigating potential threats",
                "🟡 Enhanced monitoring enabled"
            ],
            'panic': [
                "🔴 CRITICAL THREAT DETECTED",
                "🔴 EMERGENCY RESPONSE ACTIVE",
                "🔴 SECURITY BREACH IN PROGRESS",
                "🔴 ALL HANDS ON DECK",
                "🔴 MAXIMUM SECURITY PROTOCOLS"
            ],
            'lockdown': [
                "⚫ LOCKDOWN INITIATED",
                "⚫ SYSTEM UNDER ATTACK",
                "⚫ DEFENSIVE MEASURES ACTIVE",
                "⚫ THREAT CONTAINMENT MODE",
                "⚫ ALL SYSTEMS LOCKED"
            ],
            'drill': [
                "🛡️ SECURITY DRILL ACTIVE",
                "🛡️ DRILL IN PROGRESS",
                "🛡️ THIS IS A DRILL",
                "🛡️ TRAINING EXERCISE",
                "🛡️ DRILL MODE ACTIVE"
            ]
        }
        
        self.rotate_status.start()
        self.setup_signal_listeners()
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus for threat detection"""
        signal_bus.subscribe('dynamic_status', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Monitor signals for threat level changes"""
        # Check for critical threats
        if signal.severity == 'CRITICAL':
            await self.set_threat_level('panic')
        elif signal.severity == 'HIGH':
            await self.set_threat_level('elevated')
        
        # Check for drill signals
        if 'drill' in str(signal.data).lower():
            await self.set_threat_level('elevated')
        
        # Check threat scorer for high scores
        if signal.source == 'threat_scorer':
            threat_score = signal.data.get('threat_score', 0)
            if threat_score >= 90:
                await self.set_threat_level('panic')
            elif threat_score >= 70:
                await self.set_threat_level('elevated')
    
    async def set_threat_level(self, level: str, reason: str = None):
        """Change threat level"""
        if level != self.current_level:
            self.current_level = level
            self.current_message_index = 0
            self.last_threat_time = get_now_pst()
            
            # Immediately update status
            await self.update_status()
            
            reason_str = f" ({reason})" if reason else ""
            print(f"[Dynamic Status] Threat level changed to: {level.upper()}{reason_str}")
    
    async def activate_drill_status(self, drill_type: str, protocol: str):
        """Activate drill mode status"""
        self.active_drill = {'type': drill_type, 'protocol': protocol}
        await self.set_threat_level('drill', f"DRILL: {drill_type} - {protocol}")
    
    async def deactivate_drill_status(self):
        """Deactivate drill mode and return to normal"""
        self.active_drill = None
        self.current_level = 'normal'
        self.current_message_index = 0
        await self.update_status()
        print("[Dynamic Status] Drill deactivated, returned to NORMAL")
    
    async def activate_threat_status(self, threat_name: str, severity: str):
        """Activate threat status"""
        self.active_threat = {'name': threat_name, 'severity': severity}
        
        # Map severity to threat level
        level_map = {
            'CRITICAL': 'panic',
            'HIGH': 'elevated',
            'MEDIUM': 'elevated',
            'LOW': 'normal'
        }
        
        level = level_map.get(severity, 'elevated')
        await self.set_threat_level(level, f"THREAT: {threat_name}")
    
    async def deactivate_threat_status(self):
        """Deactivate threat status and return to normal"""
        self.active_threat = None
        self.current_level = 'normal'
        self.current_message_index = 0
        await self.update_status()
        print("[Dynamic Status] Threat deactivated, returned to NORMAL")
    
    @tasks.loop(seconds=30)
    async def rotate_status(self):
        """Rotate status messages every 30 seconds"""
        await self.bot.wait_until_ready()
        
        # Don't auto-return to normal if drill or threat is active
        if self.active_drill or self.active_threat:
            await self.update_status()
            return
        
        # Check if we should return to normal
        if self.current_level != 'normal' and self.last_threat_time:
            time_since_threat = (get_now_pst() - self.last_threat_time).total_seconds()
            
            # Return to normal after 5 minutes for elevated, 10 minutes for panic
            if self.current_level == 'elevated' and time_since_threat > 300:
                self.current_level = 'normal'
                self.current_message_index = 0
                print("[Dynamic Status] Returned to NORMAL")
            elif self.current_level == 'panic' and time_since_threat > 600:
                self.current_level = 'normal'
                self.current_message_index = 0
                print("[Dynamic Status] Returned to NORMAL")
        
        # Only rotate messages in normal mode or during active threats
        if self.current_level == 'normal' or self.last_threat_time:
            await self.update_status()
    
    async def update_status(self):
        """Update bot status with current message"""
        messages = self.status_messages[self.current_level]
        message = messages[self.current_message_index]
        
        # Add drill/threat info to message if active
        if self.active_drill:
            message = f"{message} | {self.active_drill['type']} - {self.active_drill['protocol']}"
        elif self.active_threat:
            message = f"{message} | {self.active_threat['name']}"
        
        # Set appropriate presence status
        status_map = {
            'normal': discord.Status.online,
            'elevated': discord.Status.idle,
            'panic': discord.Status.dnd,
            'lockdown': discord.Status.dnd,
            'drill': discord.Status.idle
        }
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=message
        )
        
        await self.bot.change_presence(
            status=status_map[self.current_level],
            activity=activity
        )
        
        # Rotate to next message
        self.current_message_index = (self.current_message_index + 1) % len(messages)
    
    @commands.command(name='setstatus')
    async def set_status_cmd(self, ctx, level: str):
        """Manually set threat level (owner only)"""
        import os
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        level = level.lower()
        if level not in self.status_messages:
            await ctx.send(f"❌ Invalid level. Options: normal, elevated, panic, lockdown")
            return
        
        await self.set_threat_level(level)
        await ctx.send(f"✅ Threat level set to: **{level.upper()}**")
    
    @commands.command(name='lockdown')
    async def lockdown_cmd(self, ctx):
        """Initiate lockdown mode (owner only)"""
        import os
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        await self.set_threat_level('lockdown')
        
        embed = discord.Embed(
            title="⚫ LOCKDOWN INITIATED",
            description="All systems locked. Security protocols at maximum.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Status", value="⚫ LOCKDOWN MODE", inline=True)
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        print(f"[Dynamic Status] LOCKDOWN initiated by {ctx.author}")
    
    @commands.command(name='allclear')
    async def all_clear_cmd(self, ctx):
        """Return to normal status (owner only)"""
        import os
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        await self.set_threat_level('normal')
        
        embed = discord.Embed(
            title="🟢 ALL CLEAR",
            description="Threat level returned to normal. All systems nominal.",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Status", value="🟢 NORMAL", inline=True)
        embed.add_field(name="Cleared By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        print(f"[Dynamic Status] ALL CLEAR issued by {ctx.author}")
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.rotate_status.cancel()

async def setup(bot):
    await bot.add_cog(DynamicStatus(bot))
