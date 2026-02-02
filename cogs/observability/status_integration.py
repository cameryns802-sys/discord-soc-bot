# Status Integration: Auto-trigger status changes from incidents, drills, alerts
import discord
from discord.ext import commands

class StatusIntegrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_status_cog(self):
        """Get the bot status system cog."""
        return self.bot.get_cog('BotStatusSystemCog')

    @commands.Cog.listener()
    async def on_incident_created(self, severity: str):
        """Auto-escalate status when incident created."""
        status_cog = await self.get_status_cog()
        if not status_cog:
            return
        
        if severity in ["critical", "high"]:
            await status_cog.change_status("panic", f"Auto: {severity.upper()} incident created")
        elif severity == "medium":
            await status_cog.change_status("elevated", "Auto: Medium incident created")

    @commands.Cog.listener()
    async def on_alert_critical(self, alert_type: str):
        """Auto-escalate on critical alerts."""
        status_cog = await self.get_status_cog()
        if not status_cog:
            return
        
        await status_cog.change_status("panic", f"Auto: Critical alert - {alert_type}")

    @commands.Cog.listener()
    async def on_drill_started(self, drill_type: str):
        """Auto-escalate during drills."""
        status_cog = await self.get_status_cog()
        if not status_cog:
            return
        
        await status_cog.change_status("elevated", f"Auto: {drill_type} drill started")

    @commands.Cog.listener()
    async def on_lockdown_activated(self):
        """Auto-escalate to lockdown."""
        status_cog = await self.get_status_cog()
        if not status_cog:
            return
        
        await status_cog.change_status("lockdown", "Auto: Emergency lockdown activated")

    @commands.command()
    async def status_trigger_incident(self, ctx, severity: str):
        """Manually trigger incident status change (test)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        await self.on_incident_created(severity.lower())
        await ctx.send(f"✅ Triggered status change for {severity.upper()} incident")

    @commands.command()
    async def status_trigger_drill(self, ctx, drill_type: str):
        """Manually trigger drill status change (test)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        await self.on_drill_started(drill_type)
        await ctx.send(f"✅ Triggered status change for {drill_type} drill")

    @commands.command()
    async def status_trigger_lockdown(self, ctx):
        """Manually trigger lockdown status (test)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        await self.on_lockdown_activated()
        await ctx.send("✅ Triggered LOCKDOWN status")

async def setup(bot):
    await bot.add_cog(StatusIntegrationCog(bot))
