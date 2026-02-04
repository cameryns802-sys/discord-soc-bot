# Bot Status System: Dynamic status with rotating messages and auto-threat response
import discord
from discord.ext import commands, tasks
import datetime
import random
from cogs.core.pst_timezone import get_now_pst

class BotStatusSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_status = "normal"
        self.current_message_index = 0
        self.status_history = []
        
        # Status messages for each threat level
        self.status_messages = {
            "normal": [
                "🟢 All Systems Operational",
                "🟢 Monitoring {} Servers",
                "🟢 SOC Online - No Threats",
                "🟢 Threat Level: Normal",
                "🟢 Security Status: Green"
            ],
            "elevated": [
                "🟡 Elevated Threat Level",
                "🟡 Active Monitoring Enhanced",
                "🟡 Suspicious Activity Detected",
                "🟡 SOC on Alert",
                "🟡 Security Status: Yellow"
            ],
            "panic": [
                "🔴 CRITICAL THREAT ACTIVE",
                "🔴 Incident Response in Progress",
                "🔴 High-Priority Alert",
                "🔴 Security Status: RED",
                "🔴 All Staff Respond"
            ],
            "lockdown": [
                "⚫ LOCKDOWN MODE ACTIVE",
                "⚫ Emergency Protocols Engaged",
                "⚫ All Access Restricted",
                "⚫ Critical Systems Only",
                "⚫ Containment in Progress"
            ]
        }
        
        self.status_rotation.start()

    def cog_unload(self):
        self.status_rotation.cancel()

    @tasks.loop(seconds=30)
    async def status_rotation(self):
        """Rotate bot status message every 30 seconds."""
        # Check if bot is ready and connected
        if not self.bot.ws or self.bot.is_closed():
            return
        
        try:
            messages = self.status_messages[self.current_status]
            message = messages[self.current_message_index]
            
            # Replace placeholders
            if "{}" in message:
                message = message.format(len(self.bot.guilds))
            
            # Set bot activity based on status
            activity_type = discord.ActivityType.watching
            if self.current_status == "panic":
                activity_type = discord.ActivityType.playing
            elif self.current_status == "lockdown":
                activity_type = discord.ActivityType.competing
            
            await self.bot.change_presence(
                activity=discord.Activity(type=activity_type, name=message),
                status=self._get_discord_status()
            )
            
            # Rotate to next message
            self.current_message_index = (self.current_message_index + 1) % len(messages)
        except Exception as e:
            print(f"[Status Rotation] Error: {e}")

    @status_rotation.before_loop
    async def before_status_rotation(self):
        await self.bot.wait_until_ready()

    def _get_discord_status(self):
        """Get Discord status color."""
        status_map = {
            "normal": discord.Status.online,
            "elevated": discord.Status.idle,
            "panic": discord.Status.dnd,
            "lockdown": discord.Status.dnd
        }
        return status_map.get(self.current_status, discord.Status.online)

    async def change_status(self, new_status: str, reason: str = "Manual change"):
        """Change bot status level."""
        if new_status not in self.status_messages:
            return False
        
        old_status = self.current_status
        self.current_status = new_status
        self.current_message_index = 0
        
        # Log status change
        self.status_history.append({
            "from": old_status,
            "to": new_status,
            "reason": reason,
            "time": datetime.get_now_pst()
        })
        
        # Immediately update status
        await self.status_rotation()
        return True

    @commands.command()
    async def status_set(self, ctx, status_level: str):
        """Set bot status level (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        status_level = status_level.lower()
        if status_level not in self.status_messages:
            await ctx.send(f"Invalid status. Use: normal, elevated, panic, lockdown")
            return
        
        success = await self.change_status(status_level, f"Manual by {ctx.author.mention}")
        if success:
            emoji_map = {"normal": "🟢", "elevated": "🟡", "panic": "🔴", "lockdown": "⚫"}
            embed = discord.Embed(
                title=f"{emoji_map[status_level]} Status Changed",
                description=f"Bot status set to **{status_level.upper()}**",
                color=discord.Color.green() if status_level == "normal" else discord.Color.orange() if status_level == "elevated" else discord.Color.red()
            )
            embed.add_field(name="Changed By", value=ctx.author.mention, inline=True)
            embed.add_field(name="Time", value=datetime.get_now_pst().strftime("%H:%M:%S"), inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def status_current(self, ctx):
        """View current bot status."""
        emoji_map = {"normal": "🟢", "elevated": "🟡", "panic": "🔴", "lockdown": "⚫"}
        color_map = {
            "normal": discord.Color.green(),
            "elevated": discord.Color.orange(),
            "panic": discord.Color.red(),
            "lockdown": discord.Color.dark_gray()
        }
        
        embed = discord.Embed(
            title=f"{emoji_map[self.current_status]} Current Status: {self.current_status.upper()}",
            color=color_map[self.current_status]
        )
        embed.add_field(name="Rotating Messages", value=str(len(self.status_messages[self.current_status])), inline=True)
        embed.add_field(name="Update Interval", value="30 seconds", inline=True)
        embed.add_field(name="Status Changes", value=str(len(self.status_history)), inline=True)
        
        # Show current rotation
        current_msg = self.status_messages[self.current_status][self.current_message_index]
        if "{}" in current_msg:
            current_msg = current_msg.format(len(self.bot.guilds))
        embed.add_field(name="Current Message", value=current_msg, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def status_history(self, ctx, limit: int = 10):
        """View status change history."""
        if not self.status_history:
            await ctx.send("No status changes recorded.")
            return
        
        recent = self.status_history[-limit:]
        desc = "\n".join([
            f"**{h['from'].upper()}** → **{h['to'].upper()}** - {h['reason']} ({h['time'].strftime('%H:%M:%S')})"
            for h in recent
        ])
        
        embed = discord.Embed(title="Status Change History", description=desc, color=discord.Color.blue())
        embed.set_footer(text=f"Total changes: {len(self.status_history)}")
        await ctx.send(embed=embed)

    @commands.command()
    async def status_auto_threat(self, ctx):
        """Simulate auto-threat response (test)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        # Simulate threat escalation
        await self.change_status("elevated", "Auto: Suspicious activity detected")
        await ctx.send("🟡 Auto-escalated to ELEVATED status")
        
        # Could integrate with incident_management, alert_routing, etc.

    @commands.command()
    async def status_auto_drill(self, ctx):
        """Activate drill status mode."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        await self.change_status("panic", "Auto: Security drill initiated")
        embed = discord.Embed(
            title="🔴 DRILL MODE ACTIVATED",
            description="Bot status elevated to PANIC for drill",
            color=discord.Color.red()
        )
        embed.add_field(name="Duration", value="Manual reset required", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def status_messages(self, ctx, status_level: str = None):
        """View all status messages for a level."""
        if status_level:
            status_level = status_level.lower()
            if status_level not in self.status_messages:
                await ctx.send(f"Invalid status. Use: normal, elevated, panic, lockdown")
                return
            messages = self.status_messages[status_level]
            emoji_map = {"normal": "🟢", "elevated": "🟡", "panic": "🔴", "lockdown": "⚫"}
            desc = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(messages)])
            embed = discord.Embed(
                title=f"{emoji_map[status_level]} {status_level.upper()} Messages",
                description=desc,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            # Show all
            embed = discord.Embed(title="All Status Messages", color=discord.Color.blue())
            for level, msgs in self.status_messages.items():
                emoji_map = {"normal": "🟢", "elevated": "🟡", "panic": "🔴", "lockdown": "⚫"}
                embed.add_field(
                    name=f"{emoji_map[level]} {level.upper()}",
                    value=f"{len(msgs)} messages",
                    inline=True
                )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotStatusSystemCog(bot))
