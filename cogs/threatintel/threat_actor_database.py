import discord
from discord.ext import commands
import json
import os
import datetime
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/threat_actors.json'

class ThreatActorDatabaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_threat_actors(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def save_threat_actors(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def get_default_data(self):
        return {
            "threat_actors": [],
            "campaigns": [],
            "actor_counter": 0
        }

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='create_threat_actor')
    async def create_threat_actor(self, ctx, actor_name: str, actor_type: str, *, description: str):
        """Create a threat actor profile"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can create threat actor profiles.")
            return
        
        data = self.load_threat_actors()
        data["actor_counter"] += 1
        
        actor = {
            "id": data["actor_counter"],
            "name": actor_name,
            "type": actor_type,
            "description": description,
            "aliases": [],
            "known_tactics": [],
            "known_campaigns": [],
            "created_at": datetime.get_now_pst().isoformat(),
            "created_by": str(ctx.author),
            "threat_level": "medium"
        }
        
        data["threat_actors"].append(actor)
        self.save_threat_actors(data)
        
        embed = discord.Embed(title="✅ Threat Actor Created", color=discord.Color.green())
        embed.add_field(name="Actor Name", value=actor_name, inline=True)
        embed.add_field(name="Type", value=actor_type, inline=True)
        embed.add_field(name="Actor ID", value=f"TA-{actor['id']}", inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='add_actor_alias')
    async def add_actor_alias(self, ctx, actor_id: int, *, alias: str):
        """Add an alias to a threat actor"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can add aliases.")
            return
        
        data = self.load_threat_actors()
        actor = next((a for a in data["threat_actors"] if a["id"] == actor_id), None)
        
        if not actor:
            await ctx.send(f"❌ Threat actor TA-{actor_id} not found.")
            return
        
        actor["aliases"].append(alias)
        self.save_threat_actors(data)
        
        await ctx.send(f"✅ Alias '{alias}' added to {actor['name']}")

    @commands.command(name='threat_actor_detail')
    async def threat_actor_detail(self, ctx, actor_id: int):
        """View detailed threat actor information"""
        data = self.load_threat_actors()
        actor = next((a for a in data["threat_actors"] if a["id"] == actor_id), None)
        
        if not actor:
            await ctx.send(f"❌ Threat actor TA-{actor_id} not found.")
            return
        
        embed = discord.Embed(title=f"Threat Actor: {actor['name']}", color=discord.Color.red())
        embed.add_field(name="Type", value=actor["type"], inline=True)
        embed.add_field(name="Threat Level", value=actor["threat_level"], inline=True)
        embed.add_field(name="Description", value=actor["description"], inline=False)
        
        if actor["aliases"]:
            embed.add_field(name="Aliases", value=", ".join(actor["aliases"]), inline=False)
        
        if actor["known_tactics"]:
            embed.add_field(name="Known Tactics", value=", ".join(actor["known_tactics"][:5]), inline=False)
        
        embed.add_field(name="Known Campaigns", value=len(actor["known_campaigns"]), inline=True)
        embed.add_field(name="Created", value=actor["created_at"][:10], inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='add_actor_tactic')
    async def add_actor_tactic(self, ctx, actor_id: int, *, tactic: str):
        """Add a known tactic to a threat actor"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can add tactics.")
            return
        
        data = self.load_threat_actors()
        actor = next((a for a in data["threat_actors"] if a["id"] == actor_id), None)
        
        if not actor:
            await ctx.send(f"❌ Threat actor TA-{actor_id} not found.")
            return
        
        actor["known_tactics"].append(tactic)
        self.save_threat_actors(data)
        
        await ctx.send(f"✅ Tactic '{tactic}' added to {actor['name']}")

    @commands.command(name='threat_actors_list')
    async def threat_actors_list(self, ctx):
        """List all known threat actors"""
        data = self.load_threat_actors()
        
        if not data["threat_actors"]:
            await ctx.send("No threat actors in database.")
            return
        
        embed = discord.Embed(title="🚨 Known Threat Actors", color=discord.Color.red())
        embed.add_field(name="Total Actors", value=len(data["threat_actors"]), inline=True)
        
        for actor in data["threat_actors"]:
            threat_indicator = "🔴" if actor["threat_level"] == "critical" else "🟠" if actor["threat_level"] == "high" else "🟡"
            embed.add_field(
                name=f"{threat_indicator} {actor['name']} (TA-{actor['id']})",
                value=f"Type: {actor['type']}\nCampaigns: {len(actor['known_campaigns'])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='link_actor_campaign')
    async def link_actor_campaign(self, ctx, actor_id: int, *, campaign_id: str):
        """Link a campaign to a threat actor"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can link campaigns.")
            return
        
        data = self.load_threat_actors()
        actor = next((a for a in data["threat_actors"] if a["id"] == actor_id), None)
        
        if not actor:
            await ctx.send(f"❌ Threat actor TA-{actor_id} not found.")
            return
        
        actor["known_campaigns"].append(campaign_id)
        self.save_threat_actors(data)
        
        await ctx.send(f"✅ Campaign {campaign_id} linked to {actor['name']}")

async def setup(bot):
    await bot.add_cog(ThreatActorDatabaseCog(bot))
