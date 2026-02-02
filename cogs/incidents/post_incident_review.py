import discord
from discord.ext import commands
import json
import os
import datetime

DATA_FILE = 'data/post_incident_reviews.json'

class PostIncidentReviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_pir_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def save_pir_data(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def get_default_data(self):
        return {
            "reviews": [],
            "findings": [],
            "action_items": []
        }

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='create_pir')
    async def create_pir(self, ctx, incident_id: str, *, summary: str):
        """Create a post-incident review"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can create PIRs.")
            return
        
        data = self.load_pir_data()
        pir_id = len(data["reviews"]) + 1
        
        review = {
            "id": pir_id,
            "incident_id": incident_id,
            "summary": summary,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "created_by": str(ctx.author),
            "status": "draft",
            "severity": "medium",
            "findings": []
        }
        
        data["reviews"].append(review)
        self.save_pir_data(data)
        
        embed = discord.Embed(title="✅ PIR Created", color=discord.Color.green())
        embed.add_field(name="PIR ID", value=f"PIR-{pir_id}", inline=True)
        embed.add_field(name="Incident ID", value=incident_id, inline=True)
        embed.add_field(name="Status", value="Draft", inline=True)
        embed.add_field(name="Summary", value=summary, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='add_finding')
    async def add_finding(self, ctx, pir_id: int, severity: str, *, finding: str):
        """Add a finding to a PIR"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can add findings.")
            return
        
        data = self.load_pir_data()
        review = next((r for r in data["reviews"] if r["id"] == pir_id), None)
        
        if not review:
            await ctx.send(f"❌ PIR-{pir_id} not found.")
            return
        
        finding_entry = {
            "severity": severity,
            "description": finding,
            "added_at": datetime.datetime.utcnow().isoformat(),
            "added_by": str(ctx.author)
        }
        
        review["findings"].append(finding_entry)
        self.save_pir_data(data)
        
        embed = discord.Embed(title="✅ Finding Added", color=discord.Color.green())
        embed.add_field(name="PIR ID", value=f"PIR-{pir_id}", inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Finding", value=finding, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='pir_detail')
    async def pir_detail(self, ctx, pir_id: int):
        """View detailed PIR information"""
        data = self.load_pir_data()
        review = next((r for r in data["reviews"] if r["id"] == pir_id), None)
        
        if not review:
            await ctx.send(f"❌ PIR-{pir_id} not found.")
            return
        
        embed = discord.Embed(title=f"PIR-{pir_id}: {review['incident_id']}", color=discord.Color.blue())
        embed.add_field(name="Status", value=review["status"], inline=True)
        embed.add_field(name="Severity", value=review["severity"], inline=True)
        embed.add_field(name="Summary", value=review["summary"], inline=False)
        embed.add_field(name="Findings Count", value=len(review["findings"]), inline=True)
        embed.add_field(name="Created By", value=review["created_by"], inline=True)
        
        for i, finding in enumerate(review["findings"][:5]):
            embed.add_field(
                name=f"Finding {i+1} ({finding['severity']})",
                value=finding["description"][:100],
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='add_action_item')
    async def add_action_item(self, ctx, pir_id: int, owner: str, due_date: str, *, action: str):
        """Add an action item to a PIR"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can add action items.")
            return
        
        data = self.load_pir_data()
        
        action_item = {
            "pir_id": pir_id,
            "action": action,
            "owner": owner,
            "due_date": due_date,
            "status": "open",
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        data["action_items"].append(action_item)
        self.save_pir_data(data)
        
        await ctx.send(f"✅ Action item added for PIR-{pir_id}")

    @commands.command(name='pir_list')
    async def pir_list(self, ctx):
        """List all post-incident reviews"""
        data = self.load_pir_data()
        
        if not data["reviews"]:
            await ctx.send("No PIRs created yet.")
            return
        
        embed = discord.Embed(title="📋 Post-Incident Reviews", color=discord.Color.blue())
        
        for review in data["reviews"][-10:]:
            embed.add_field(
                name=f"PIR-{review['id']}: {review['incident_id']}",
                value=f"Status: {review['status']}\nFindings: {len(review['findings'])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PostIncidentReviewCog(bot))
