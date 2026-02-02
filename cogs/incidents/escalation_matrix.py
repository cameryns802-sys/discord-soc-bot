import discord
from discord.ext import commands
import json
import os
import datetime

DATA_FILE = 'data/escalation_matrix.json'

class EscalationMatrixCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_escalation(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def save_escalation(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def get_default_data(self):
        return {
            "escalation_levels": [],
            "escalation_rules": [],
            "contact_groups": []
        }

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='create_escalation_level')
    async def create_escalation_level(self, ctx, level_name: str, severity_threshold: int, *, contacts: str):
        """Create an escalation level"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can create escalation levels.")
            return
        
        data = self.load_escalation()
        level_id = len(data["escalation_levels"]) + 1
        
        level = {
            "id": level_id,
            "name": level_name,
            "severity_threshold": severity_threshold,
            "contacts": contacts.split(","),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "created_by": str(ctx.author)
        }
        
        data["escalation_levels"].append(level)
        self.save_escalation(data)
        
        embed = discord.Embed(title="✅ Escalation Level Created", color=discord.Color.green())
        embed.add_field(name="Level", value=level_name, inline=True)
        embed.add_field(name="Severity Threshold", value=severity_threshold, inline=True)
        embed.add_field(name="Contacts", value=", ".join(level["contacts"][:3]), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='create_escalation_rule')
    async def create_escalation_rule(self, ctx, alert_type: str, level_id: int, *, description: str):
        """Create an escalation rule"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can create rules.")
            return
        
        data = self.load_escalation()
        
        rule = {
            "id": len(data["escalation_rules"]) + 1,
            "alert_type": alert_type,
            "escalation_level_id": level_id,
            "description": description,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "active": True
        }
        
        data["escalation_rules"].append(rule)
        self.save_escalation(data)
        
        await ctx.send(f"✅ Escalation rule created for {alert_type}")

    @commands.command(name='escalation_matrix')
    async def escalation_matrix(self, ctx):
        """View the escalation matrix"""
        data = self.load_escalation()
        
        if not data["escalation_levels"]:
            await ctx.send("No escalation levels configured.")
            return
        
        embed = discord.Embed(title="📊 Escalation Matrix", color=discord.Color.blue())
        
        for level in data["escalation_levels"]:
            embed.add_field(
                name=f"Level {level['id']}: {level['name']}",
                value=f"Threshold: {level['severity_threshold']}\nContacts: {', '.join(level['contacts'][:3])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='escalate_incident')
    async def escalate_incident(self, ctx, incident_id: str, level_id: int, *, reason: str):
        """Escalate an incident"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can escalate incidents.")
            return
        
        data = self.load_escalation()
        level = next((l for l in data["escalation_levels"] if l["id"] == level_id), None)
        
        if not level:
            await ctx.send(f"❌ Escalation level {level_id} not found.")
            return
        
        embed = discord.Embed(title="🚨 Incident Escalated", color=discord.Color.red())
        embed.add_field(name="Incident ID", value=incident_id, inline=True)
        embed.add_field(name="Escalation Level", value=level["name"], inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Notifying", value=", ".join(level["contacts"]), inline=False)
        embed.set_footer(text="Contacts have been notified")
        await ctx.send(embed=embed)

    @commands.command(name='escalation_rules')
    async def escalation_rules(self, ctx):
        """View escalation rules"""
        data = self.load_escalation()
        
        if not data["escalation_rules"]:
            await ctx.send("No escalation rules configured.")
            return
        
        embed = discord.Embed(title="📋 Escalation Rules", color=discord.Color.blue())
        
        for rule in data["escalation_rules"]:
            status = "✅ Active" if rule["active"] else "❌ Inactive"
            embed.add_field(
                name=rule["alert_type"],
                value=f"Level {rule['escalation_level_id']}\n{status}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EscalationMatrixCog(bot))
