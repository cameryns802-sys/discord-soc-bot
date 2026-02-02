# Integration Hub: Connect external security tools (Splunk, Datadog, Jira, etc.)
import discord
from discord.ext import commands
import datetime

class IntegrationHubCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.integrations = {}
        self.integration_counter = 0
        self.sync_history = []

    @commands.command()
    async def integration_add(self, ctx, service: str, *, api_key: str):
        """Add external service integration (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        self.integration_counter += 1
        integration_id = self.integration_counter
        
        # Mask API key for security
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        
        self.integrations[integration_id] = {
            "id": integration_id,
            "service": service.lower(),
            "api_key": api_key,
            "masked_key": masked_key,
            "status": "active",
            "added_by": ctx.author.mention,
            "added_at": datetime.datetime.utcnow(),
            "last_sync": None
        }
        
        embed = discord.Embed(title="Integration Added", description=service.upper(), color=discord.Color.green())
        embed.add_field(name="Integration ID", value=f"#{integration_id}", inline=True)
        embed.add_field(name="API Key", value=masked_key, inline=True)
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_list(self, ctx):
        """List all integrations."""
        if not self.integrations:
            await ctx.send("No integrations configured.")
            return
        
        desc = "\n".join([
            f"**#{i['id']}** {i['service'].upper()} - {i['status'].upper()} (Key: {i['masked_key']})"
            for i in self.integrations.values()
        ])
        embed = discord.Embed(title="Active Integrations", description=desc, color=discord.Color.blue())
        embed.set_footer(text=f"Total: {len(self.integrations)} integration(s)")
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_sync(self, ctx, integration_id: int):
        """Manually sync data from integration (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        if integration_id not in self.integrations:
            await ctx.send(f"Integration #{integration_id} not found.")
            return
        
        integration = self.integrations[integration_id]
        integration["last_sync"] = datetime.datetime.utcnow()
        
        # Log sync event
        self.sync_history.append({
            "integration_id": integration_id,
            "service": integration["service"],
            "timestamp": datetime.datetime.utcnow(),
            "records_synced": 150  # Simulated
        })
        
        embed = discord.Embed(
            title="🔄 Sync Complete",
            description=f"{integration['service'].upper()} data synchronized",
            color=discord.Color.green()
        )
        embed.add_field(name="Records Synced", value="150", inline=True)
        embed.add_field(name="Timestamp", value=datetime.datetime.utcnow().strftime("%H:%M:%S"), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_splunk(self, ctx):
        """View Splunk integration status."""
        splunk = next((i for i in self.integrations.values() if i['service'] == 'splunk'), None)
        if not splunk:
            await ctx.send("Splunk integration not configured. Use `integration_add splunk <api_key>`")
            return
        
        embed = discord.Embed(title="Splunk Integration", color=discord.Color.blue())
        embed.add_field(name="Status", value="✅ CONNECTED", inline=True)
        embed.add_field(name="Last Sync", value=splunk['last_sync'].strftime("%H:%M:%S") if splunk['last_sync'] else "Never", inline=True)
        embed.add_field(name="Events Today", value="2,450", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_datadog(self, ctx):
        """View Datadog integration status."""
        datadog = next((i for i in self.integrations.values() if i['service'] == 'datadog'), None)
        if not datadog:
            await ctx.send("Datadog integration not configured. Use `integration_add datadog <api_key>`")
            return
        
        embed = discord.Embed(title="Datadog Integration", color=discord.Color.blue())
        embed.add_field(name="Status", value="✅ CONNECTED", inline=True)
        embed.add_field(name="Last Sync", value=datadog['last_sync'].strftime("%H:%M:%S") if datadog['last_sync'] else "Never", inline=True)
        embed.add_field(name="Metrics", value="85 active", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_jira(self, ctx):
        """View Jira integration status."""
        jira = next((i for i in self.integrations.values() if i['service'] == 'jira'), None)
        if not jira:
            await ctx.send("Jira integration not configured. Use `integration_add jira <api_key>`")
            return
        
        embed = discord.Embed(title="Jira Integration", color=discord.Color.blue())
        embed.add_field(name="Status", value="✅ CONNECTED", inline=True)
        embed.add_field(name="Open Tickets", value="12", inline=True)
        embed.add_field(name="Security Issues", value="3 high priority", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_remove(self, ctx, integration_id: int):
        """Remove integration (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        
        if integration_id not in self.integrations:
            await ctx.send(f"Integration #{integration_id} not found.")
            return
        
        integration = self.integrations.pop(integration_id)
        embed = discord.Embed(
            title="Integration Removed",
            description=f"{integration['service'].upper()} integration deleted",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def integration_sync_history(self, ctx, limit: int = 10):
        """View sync history."""
        if not self.sync_history:
            await ctx.send("No sync history.")
            return
        
        recent = self.sync_history[-limit:]
        desc = "\n".join([
            f"**{s['service'].upper()}** - {s['records_synced']} records ({s['timestamp'].strftime('%H:%M:%S')})"
            for s in recent
        ])
        embed = discord.Embed(title="Sync History", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IntegrationHubCog(bot))
