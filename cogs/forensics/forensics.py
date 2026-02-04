# Forensics & Evidence Management: Chain of custody and investigation tracking
import discord
from discord.ext import commands
import datetime
import hashlib
from cogs.core.pst_timezone import get_now_pst

class ForensicsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.evidence = {}  # evidence_id -> evidence data
        self.evidence_counter = 0
        self.investigations = {}  # investigation_id -> investigation data
        self.inv_counter = 0

    @commands.command()
    async def investigation_open(self, ctx, *, title: str):
        """Open a new investigation."""
        self.inv_counter += 1
        inv_id = self.inv_counter
        self.investigations[inv_id] = {
            "id": inv_id,
            "title": title,
            "status": "open",
            "created_by": ctx.author.id,
            "created_at": datetime.get_now_pst(),
            "evidence": [],
            "timeline": [],
            "conclusions": ""
        }
        embed = discord.Embed(title="Investigation Opened", description=f"Investigation #{inv_id}", color=discord.Color.blue())
        embed.add_field(name="Title", value=title, inline=False)
        embed.add_field(name="Opened By", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def evidence_collect(self, ctx, investigation_id: int, *, description: str):
        """Collect evidence for investigation."""
        if investigation_id not in self.investigations:
            await ctx.send(f"Investigation #{investigation_id} not found.")
            return
        self.evidence_counter += 1
        ev_id = self.evidence_counter
        # Create hash for evidence integrity
        ev_hash = hashlib.sha256(f"{ev_id}{description}{datetime.get_now_pst()}".encode()).hexdigest()
        self.evidence[ev_id] = {
            "id": ev_id,
            "investigation_id": investigation_id,
            "description": description,
            "hash": ev_hash,
            "collected_by": ctx.author.id,
            "collected_at": datetime.get_now_pst(),
            "status": "collected",
            "chain_of_custody": [{"action": "collected", "by": ctx.author.mention, "at": datetime.get_now_pst()}]
        }
        self.investigations[investigation_id]["evidence"].append(ev_id)
        self.investigations[investigation_id]["timeline"].append({
            "action": f"Evidence #{ev_id} collected",
            "by": ctx.author.mention,
            "at": datetime.get_now_pst()
        })
        embed = discord.Embed(title="Evidence Collected", description=description, color=discord.Color.green())
        embed.add_field(name="Evidence ID", value=f"#{ev_id}", inline=True)
        embed.add_field(name="Investigation", value=f"#{investigation_id}", inline=True)
        embed.add_field(name="Hash", value=f"||{ev_hash[:16]}...||", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def evidence_chain(self, ctx, evidence_id: int):
        """View evidence chain of custody."""
        if evidence_id not in self.evidence:
            await ctx.send(f"Evidence #{evidence_id} not found.")
            return
        ev = self.evidence[evidence_id]
        chain_desc = "\n".join([f"• {c['action']} by {c['by']} at {c['at'].strftime('%H:%M:%S')}" for c in ev["chain_of_custody"]])
        embed = discord.Embed(title=f"Chain of Custody - Evidence #{evidence_id}", description=chain_desc, color=discord.Color.blue())
        embed.add_field(name="Status", value=ev["status"].upper(), inline=True)
        embed.add_field(name="Hash", value=f"||{ev['hash'][:32]}...||", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def evidence_transfer(self, ctx, evidence_id: int, user: discord.Member):
        """Transfer evidence custody to another person."""
        if evidence_id not in self.evidence:
            await ctx.send(f"Evidence #{evidence_id} not found.")
            return
        ev = self.evidence[evidence_id]
        ev["chain_of_custody"].append({
            "action": f"transferred to {user.mention}",
            "by": ctx.author.mention,
            "at": datetime.get_now_pst()
        })
        embed = discord.Embed(title="Evidence Transferred", description=f"Evidence #{evidence_id} transferred", color=discord.Color.blue())
        embed.add_field(name="From", value=ctx.author.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def investigation_timeline(self, ctx, investigation_id: int):
        """View investigation timeline."""
        if investigation_id not in self.investigations:
            await ctx.send(f"Investigation #{investigation_id} not found.")
            return
        inv = self.investigations[investigation_id]
        timeline_desc = "\n".join([f"• {e['action']} by {e['by']}" for e in inv["timeline"][-15:]])
        embed = discord.Embed(title=f"Investigation #{investigation_id} Timeline", description=timeline_desc or "No events yet", color=discord.Color.blue())
        embed.add_field(name="Title", value=inv["title"], inline=False)
        embed.add_field(name="Evidence Count", value=str(len(inv["evidence"])), inline=True)
        embed.add_field(name="Status", value=inv["status"].upper(), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def investigation_close(self, ctx, investigation_id: int, *, conclusion: str):
        """Close an investigation with conclusions."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if investigation_id not in self.investigations:
            await ctx.send(f"Investigation #{investigation_id} not found.")
            return
        inv = self.investigations[investigation_id]
        inv["status"] = "closed"
        inv["conclusions"] = conclusion
        inv["timeline"].append({"action": "Investigation closed", "by": ctx.author.mention, "at": datetime.get_now_pst()})
        embed = discord.Embed(title=f"Investigation #{investigation_id} Closed", description=conclusion, color=discord.Color.green())
        embed.add_field(name="Evidence Collected", value=str(len(inv["evidence"])), inline=True)
        embed.add_field(name="Events", value=str(len(inv["timeline"])), inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ForensicsCog(bot))
