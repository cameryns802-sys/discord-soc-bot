# Incident Response Playbooks - Pre-defined response procedures
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

DATA_FILE = 'data/playbooks.json'

def load_playbooks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return get_default_playbooks()
    return get_default_playbooks()

def get_default_playbooks():
    return {
        "playbooks": [
            {
                "id": 1,
                "name": "Ransomware Response",
                "category": "malware",
                "steps": [
                    "Isolate affected systems immediately",
                    "Preserve evidence and logs",
                    "Assess scope of infection",
                    "Notify stakeholders",
                    "Engage incident response team",
                    "Do NOT pay ransom until negotiation"
                ],
                "severity": "critical"
            },
            {
                "id": 2,
                "name": "Data Breach Response",
                "category": "data_breach",
                "steps": [
                    "Contain the breach immediately",
                    "Identify affected data",
                    "Notify legal and privacy teams",
                    "Prepare customer notification",
                    "Investigate root cause",
                    "Implement remediation"
                ],
                "severity": "critical"
            },
            {
                "id": 3,
                "name": "Phishing Attack Response",
                "category": "phishing",
                "steps": [
                    "Identify all affected users",
                    "Reset credentials immediately",
                    "Block malicious URLs",
                    "Scan for compromised accounts",
                    "User security awareness training",
                    "Monitor for secondary attacks"
                ],
                "severity": "high"
            },
            {
                "id": 4,
                "name": "DDoS Attack Response",
                "category": "network",
                "steps": [
                    "Activate DDoS mitigation",
                    "Monitor bandwidth and traffic",
                    "Coordinate with ISP",
                    "Route traffic through CDN",
                    "Implement rate limiting",
                    "Document attack patterns"
                ],
                "severity": "high"
            },
            {
                "id": 5,
                "name": "Insider Threat Response",
                "category": "insider_threat",
                "steps": [
                    "Alert HR and legal",
                    "Revoke access immediately",
                    "Preserve all evidence",
                    "Interview involved parties",
                    "Assess data accessed",
                    "Implement monitoring"
                ],
                "severity": "critical"
            }
        ]
    }

def save_playbooks(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class IncidentResponsePlaybookCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playbooks = load_playbooks()

    @commands.command(name='list_playbooks')
    async def list_playbooks(self, ctx):
        """List available incident response playbooks"""
        playbooks = self.playbooks.get('playbooks', [])
        
        embed = discord.Embed(
            title="📚 Incident Response Playbooks",
            description=f"Total: {len(playbooks)} playbooks available",
            color=discord.Color.blue()
        )
        
        for pb in playbooks:
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(pb.get('severity', 'unknown'), '❓')
            
            embed.add_field(
                name=f"{severity_emoji} {pb.get('name')} (ID: {pb.get('id')})",
                value=f"Category: {pb.get('category')}\nSteps: {len(pb.get('steps', []))}",
                inline=False
            )
        
        embed.set_footer(text="Use !playbook <id> to view details")
        await ctx.send(embed=embed)

    @commands.command(name='playbook')
    async def view_playbook(self, ctx, playbook_id: int):
        """View detailed incident response playbook"""
        playbooks = self.playbooks.get('playbooks', [])
        playbook = next((pb for pb in playbooks if pb.get('id') == playbook_id), None)
        
        if not playbook:
            await ctx.send("❌ Playbook not found")
            return
        
        severity_color = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.green()
        }.get(playbook.get('severity', 'unknown'), discord.Color.blue())
        
        embed = discord.Embed(
            title=f"📖 {playbook.get('name')}",
            color=severity_color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Category",
            value=playbook.get('category'),
            inline=True
        )
        embed.add_field(
            name="Severity",
            value=playbook.get('severity').upper(),
            inline=True
        )
        
        steps = playbook.get('steps', [])
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        embed.add_field(
            name="Response Steps",
            value=steps_text,
            inline=False
        )
        
        embed.set_footer(text="Follow these steps in order for effective incident response")
        await ctx.send(embed=embed)

    @commands.command(name='execute_playbook')
    async def execute_playbook(self, ctx, playbook_id: int):
        """Execute a playbook and create incident response task"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can execute playbooks")
            return
        
        playbooks = self.playbooks.get('playbooks', [])
        playbook = next((pb for pb in playbooks if pb.get('id') == playbook_id), None)
        
        if not playbook:
            await ctx.send("❌ Playbook not found")
            return
        
        embed = discord.Embed(
            title=f"✅ Playbook Execution Started",
            description=f"**{playbook.get('name')}**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Status",
            value="🔵 In Progress",
            inline=True
        )
        embed.add_field(
            name="Executed By",
            value=ctx.author.mention,
            inline=True
        )
        
        steps = playbook.get('steps', [])
        steps_with_checkboxes = "\n".join([f"☐ {step}" for step in steps])
        embed.add_field(
            name="Checklist",
            value=steps_with_checkboxes,
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='custom_playbook')
    async def add_custom_playbook(self, ctx, name: str):
        """Create a custom incident response playbook"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can create playbooks")
            return
        
        await ctx.send(f"✅ Started creating playbook: **{name}**\nReply with steps (one per message, type 'done' when finished)")
        
        steps = []
        while True:
            try:
                msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=300)
                if msg.content.lower() == 'done':
                    break
                steps.append(msg.content)
                await msg.add_reaction('✅')
            except:
                await ctx.send("❌ Timeout")
                return
        
        embed = discord.Embed(title="✅ Playbook Created", color=discord.Color.green())
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Steps", value=len(steps), inline=True)
        await ctx.send(embed=embed)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == 233662304272834560

async def setup(bot):
    await bot.add_cog(IncidentResponsePlaybookCog(bot))
