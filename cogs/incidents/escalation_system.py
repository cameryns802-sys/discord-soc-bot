# Escalation System: Multi-channel alert escalation and on-call management
import discord
from discord.ext import commands
import datetime

class EscalationSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.escalation_chains = {}  # chain_id -> {levels, assigned_to}
        self.on_call_roster = {}  # user_id -> {role, tier, availability}
        self.escalations = []  # escalation history
        self.chain_counter = 0

    @commands.command()
    async def escalation_create_chain(self, ctx, name: str, levels: int):
        """Create an escalation chain (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if levels < 1 or levels > 5:
            await ctx.send("Levels must be between 1 and 5.")
            return
        self.chain_counter += 1
        chain_id = self.chain_counter
        self.escalation_chains[chain_id] = {
            "id": chain_id,
            "name": name,
            "levels": [{f"level_{i+1}": None} for i in range(levels)],
            "created_at": datetime.datetime.utcnow()
        }
        embed = discord.Embed(title="Escalation Chain Created", description=f"Chain '{name}' with {levels} level(s)", color=discord.Color.green())
        embed.add_field(name="Chain ID", value=f"#{chain_id}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def escalation_assign(self, ctx, chain_id: int, level: int, user: discord.Member):
        """Assign user to escalation chain level (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        chain = self.escalation_chains.get(chain_id)
        if not chain:
            await ctx.send(f"Chain #{chain_id} not found.")
            return
        if level < 1 or level > len(chain["levels"]):
            await ctx.send(f"Level must be between 1 and {len(chain['levels'])}.")
            return
        chain["levels"][level - 1] = {f"level_{level}": user.id}
        embed = discord.Embed(title="Escalation Assignment", description=f"{user.mention} assigned to {chain['name']} Level {level}", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def oncall_register(self, ctx, tier: str = "tier1"):
        """Register for on-call duty (tier1/tier2/tier3)."""
        if tier.lower() not in ["tier1", "tier2", "tier3"]:
            await ctx.send("Tier must be: tier1, tier2, or tier3")
            return
        self.on_call_roster[ctx.author.id] = {
            "name": ctx.author.mention,
            "tier": tier.lower(),
            "availability": "available",
            "registered_at": datetime.datetime.utcnow()
        }
        embed = discord.Embed(title="On-Call Registered", description=f"{ctx.author.mention} registered for {tier.upper()}", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def oncall_unavailable(self, ctx):
        """Mark yourself as unavailable for on-call."""
        if ctx.author.id in self.on_call_roster:
            self.on_call_roster[ctx.author.id]["availability"] = "unavailable"
            embed = discord.Embed(title="On-Call Status", description=f"{ctx.author.mention} marked as UNAVAILABLE", color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command()
    async def oncall_available(self, ctx):
        """Mark yourself as available for on-call."""
        if ctx.author.id in self.on_call_roster:
            self.on_call_roster[ctx.author.id]["availability"] = "available"
            embed = discord.Embed(title="On-Call Status", description=f"{ctx.author.mention} marked as AVAILABLE", color=discord.Color.green())
            await ctx.send(embed=embed)

    @commands.command()
    async def oncall_roster(self, ctx, tier: str = None):
        """View on-call roster."""
        if tier and tier.lower() not in ["tier1", "tier2", "tier3"]:
            await ctx.send("Tier must be: tier1, tier2, or tier3")
            return
        if tier:
            roster = [f"{v['name']} - {v['availability'].upper()}" for v in self.on_call_roster.values() if v['tier'] == tier.lower()]
            title = f"On-Call Roster - {tier.upper()}"
        else:
            roster = [f"{v['name']} ({v['tier'].upper()}) - {v['availability'].upper()}" for v in self.on_call_roster.values()]
            title = "On-Call Roster"
        if not roster:
            await ctx.send("No one registered for on-call duty.")
            return
        embed = discord.Embed(title=title, description="\n".join(roster), color=discord.Color.blue())
        embed.set_footer(text=f"Total: {len(roster)} staff member(s)")
        await ctx.send(embed=embed)

    @commands.command()
    async def escalate_alert(self, ctx, severity: str, *, message: str):
        """Escalate alert through chain (critical/high/medium/low)."""
        if severity.lower() not in ["critical", "high", "medium", "low"]:
            await ctx.send("Severity must be: critical, high, medium, or low")
            return
        # Find on-call tier1 staff
        on_call_tier1 = [uid for uid, data in self.on_call_roster.items() if data['tier'] == 'tier1' and data['availability'] == 'available']
        if not on_call_tier1:
            await ctx.send("No tier1 on-call staff available. Escalation failed.")
            return
        # Notify first available
        for uid in on_call_tier1[:1]:
            user = await self.bot.fetch_user(uid)
            if user:
                try:
                    embed = discord.Embed(title=f"[ESCALATION] {severity.upper()}", description=message, color=discord.Color.red())
                    embed.add_field(name="Escalated By", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Timestamp", value=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                    await user.send(embed=embed)
                except:
                    pass
        self.escalations.append({"severity": severity, "message": message, "by": ctx.author.id, "time": datetime.datetime.utcnow()})
        embed = discord.Embed(title="Alert Escalated", description=f"Alert escalated to on-call tier1", color=discord.Color.orange())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EscalationSystemCog(bot))
