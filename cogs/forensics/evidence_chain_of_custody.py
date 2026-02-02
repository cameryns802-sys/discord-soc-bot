import discord
from discord.ext import commands
import json
import os
import datetime

DATA_FILE = 'data/evidence_chain_of_custody.json'

class EvidenceChainOfCustodyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_evidence_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def save_evidence_data(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def get_default_data(self):
        return {
            "evidence_items": [],
            "custody_log": [],
            "evidence_counter": 0
        }

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='collect_evidence')
    async def collect_evidence(self, ctx, evidence_type: str, *, description: str):
        """Collect and log evidence item"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can collect evidence.")
            return
        
        data = self.load_evidence_data()
        data["evidence_counter"] += 1
        
        evidence_item = {
            "id": data["evidence_counter"],
            "type": evidence_type,
            "description": description,
            "collected_at": datetime.datetime.utcnow().isoformat(),
            "collected_by": str(ctx.author),
            "status": "collected",
            "hash": "N/A",
            "location": "secure_storage"
        }
        
        data["evidence_items"].append(evidence_item)
        
        custody_entry = {
            "evidence_id": evidence_item["id"],
            "action": "collected",
            "timestamp": evidence_item["collected_at"],
            "user": str(ctx.author),
            "notes": "Evidence collected and logged"
        }
        
        data["custody_log"].append(custody_entry)
        self.save_evidence_data(data)
        
        embed = discord.Embed(title="✅ Evidence Collected", color=discord.Color.green())
        embed.add_field(name="Evidence ID", value=f"EV-{evidence_item['id']}", inline=True)
        embed.add_field(name="Type", value=evidence_type, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Status", value="Collected", inline=True)
        embed.set_footer(text=f"Collected by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name='transfer_evidence')
    async def transfer_evidence(self, ctx, evidence_id: int, *, new_custodian: str):
        """Transfer evidence custody"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can transfer evidence.")
            return
        
        data = self.load_evidence_data()
        evidence = next((e for e in data["evidence_items"] if e["id"] == evidence_id), None)
        
        if not evidence:
            await ctx.send(f"❌ Evidence EV-{evidence_id} not found.")
            return
        
        custody_entry = {
            "evidence_id": evidence_id,
            "action": "transferred",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user": str(ctx.author),
            "notes": f"Transferred to {new_custodian}"
        }
        
        data["custody_log"].append(custody_entry)
        self.save_evidence_data(data)
        
        embed = discord.Embed(title="✅ Evidence Transferred", color=discord.Color.green())
        embed.add_field(name="Evidence ID", value=f"EV-{evidence_id}", inline=True)
        embed.add_field(name="New Custodian", value=new_custodian, inline=True)
        embed.add_field(name="Transferred By", value=ctx.author, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='evidence_detail')
    async def evidence_detail(self, ctx, evidence_id: int):
        """View detailed evidence information"""
        data = self.load_evidence_data()
        evidence = next((e for e in data["evidence_items"] if e["id"] == evidence_id), None)
        
        if not evidence:
            await ctx.send(f"❌ Evidence EV-{evidence_id} not found.")
            return
        
        embed = discord.Embed(title=f"Evidence EV-{evidence_id}", color=discord.Color.blue())
        embed.add_field(name="Type", value=evidence["type"], inline=True)
        embed.add_field(name="Status", value=evidence["status"], inline=True)
        embed.add_field(name="Description", value=evidence["description"], inline=False)
        embed.add_field(name="Collected At", value=evidence["collected_at"], inline=True)
        embed.add_field(name="Collected By", value=evidence["collected_by"], inline=True)
        embed.add_field(name="Location", value=evidence["location"], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='chain_of_custody')
    async def chain_of_custody(self, ctx, evidence_id: int):
        """View complete chain of custody for evidence"""
        data = self.load_evidence_data()
        custody_entries = [e for e in data["custody_log"] if e["evidence_id"] == evidence_id]
        
        if not custody_entries:
            await ctx.send(f"❌ No custody records found for EV-{evidence_id}")
            return
        
        embed = discord.Embed(title=f"Chain of Custody - EV-{evidence_id}", color=discord.Color.blue())
        
        for entry in custody_entries:
            embed.add_field(
                name=f"{entry['action'].upper()} - {entry['timestamp'][:10]}",
                value=f"By: {entry['user']}\n{entry['notes']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='evidence_list')
    async def evidence_list(self, ctx):
        """List all collected evidence"""
        data = self.load_evidence_data()
        
        if not data["evidence_items"]:
            await ctx.send("No evidence collected yet.")
            return
        
        embed = discord.Embed(title="📦 Evidence Inventory", color=discord.Color.blue())
        
        for evidence in data["evidence_items"][-10:]:
            embed.add_field(
                name=f"EV-{evidence['id']}: {evidence['type']}",
                value=f"Status: {evidence['status']}\nCollected: {evidence['collected_at'][:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EvidenceChainOfCustodyCog(bot))
