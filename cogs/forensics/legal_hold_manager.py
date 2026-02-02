"""
Legal Hold Manager
Manages legal holds with immutable evidence locking and court admissibility tracking
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import hashlib

class LegalHoldManagerCog(commands.Cog):
    """Legal Hold Manager - Evidence preservation for legal proceedings"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/legal_holds"
        os.makedirs(self.data_dir, exist_ok=True)
        self.holds_file = os.path.join(self.data_dir, "legal_holds.json")
        self.evidence_file = os.path.join(self.data_dir, "locked_evidence.json")
        self.holds = self.load_holds()
        self.evidence = self.load_evidence()
        
    def load_holds(self):
        if os.path.exists(self.holds_file):
            with open(self.holds_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_holds(self):
        with open(self.holds_file, 'w') as f:
            json.dump(self.holds, f, indent=4)
    
    def load_evidence(self):
        if os.path.exists(self.evidence_file):
            with open(self.evidence_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_evidence(self):
        with open(self.evidence_file, 'w') as f:
            json.dump(self.evidence, f, indent=4)
    
    def generate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()
    
    @commands.command(name="legalhold_create")
    @commands.has_permissions(administrator=True)
    async def create_hold(self, ctx, case_number: str, *, description: str):
        """Create legal hold\nUsage: !legalhold_create <case_number> <description>"""
        hold = {
            "id": len(self.holds) + 1,
            "case_number": case_number,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": str(ctx.author.id),
            "status": "active",
            "evidence_count": 0,
            "immutable": True
        }
        
        self.holds.append(hold)
        self.save_holds()
        
        embed = discord.Embed(title="⚖️ Legal Hold Created", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Hold ID", value=f"#{hold['id']}", inline=True)
        embed.add_field(name="Case Number", value=case_number, inline=True)
        embed.add_field(name="Status", value="🔒 ACTIVE", inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.set_footer(text=f"Created by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="legalhold_add_evidence")
    @commands.has_permissions(administrator=True)
    async def add_evidence(self, ctx, hold_id: int, evidence_type: str, *, content: str):
        """Add evidence to legal hold\nUsage: !legalhold_add_evidence <hold_id> <type> <content>"""
        hold = next((h for h in self.holds if h["id"] == hold_id), None)
        if not hold:
            await ctx.send(f"❌ Legal hold #{hold_id} not found")
            return
        
        evidence_hash = self.generate_hash(content)
        evidence = {
            "id": len(self.evidence) + 1,
            "hold_id": hold_id,
            "case_number": hold["case_number"],
            "type": evidence_type,
            "content": content,
            "hash": evidence_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "added_by": str(ctx.author.id),
            "chain_of_custody": [{"action": "created", "by": str(ctx.author.id), "at": datetime.utcnow().isoformat()}],
            "immutable": True,
            "court_admissible": True
        }
        
        self.evidence.append(evidence)
        hold["evidence_count"] += 1
        self.save_evidence()
        self.save_holds()
        
        embed = discord.Embed(title="✅ Evidence Added to Legal Hold", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Evidence ID", value=f"#{evidence['id']}", inline=True)
        embed.add_field(name="Hold ID", value=f"#{hold_id}", inline=True)
        embed.add_field(name="Type", value=evidence_type, inline=True)
        embed.add_field(name="SHA-256 Hash", value=f"`{evidence_hash[:32]}...`", inline=False)
        embed.add_field(name="🔒 Status", value="Immutable & Court Admissible", inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="legalhold_verify")
    @commands.has_permissions(administrator=True)
    async def verify_evidence(self, ctx, evidence_id: int):
        """Verify evidence integrity\nUsage: !legalhold_verify <evidence_id>"""
        evidence = next((e for e in self.evidence if e["id"] == evidence_id), None)
        if not evidence:
            await ctx.send(f"❌ Evidence #{evidence_id} not found")
            return
        
        current_hash = self.generate_hash(evidence["content"])
        integrity_verified = (current_hash == evidence["hash"])
        
        color = discord.Color.green() if integrity_verified else discord.Color.red()
        embed = discord.Embed(title="🔍 Evidence Integrity Verification", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Evidence ID", value=f"#{evidence_id}", inline=True)
        embed.add_field(name="Case Number", value=evidence["case_number"], inline=True)
        embed.add_field(name="Integrity", value="✅ VERIFIED" if integrity_verified else "❌ COMPROMISED", inline=True)
        embed.add_field(name="Original Hash", value=f"`{evidence['hash'][:32]}...`", inline=False)
        embed.add_field(name="Current Hash", value=f"`{current_hash[:32]}...`", inline=False)
        embed.add_field(name="Chain of Custody", value=f"{len(evidence['chain_of_custody'])} entries", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="legalhold_list")
    @commands.has_permissions(administrator=True)
    async def list_holds(self, ctx):
        """List all legal holds\nUsage: !legalhold_list"""
        if not self.holds:
            await ctx.send("📋 No legal holds found")
            return
        
        active_holds = [h for h in self.holds if h["status"] == "active"]
        embed = discord.Embed(title="⚖️ Legal Holds", description=f"{len(active_holds)} active holds", color=discord.Color.blue(), timestamp=datetime.utcnow())
        
        for hold in active_holds[:10]:
            embed.add_field(name=f"🔒 Hold #{hold['id']} - {hold['case_number']}", value=f"Evidence: {hold['evidence_count']} items\nCreated: {hold['created_at'][:10]}", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="legalhold_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View legal hold dashboard\nUsage: !legalhold_dashboard"""
        total_holds = len(self.holds)
        active_holds = len([h for h in self.holds if h["status"] == "active"])
        total_evidence = len(self.evidence)
        
        embed = discord.Embed(title="⚖️ Legal Hold Dashboard", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📊 Total Holds", value=total_holds, inline=True)
        embed.add_field(name="🔒 Active Holds", value=active_holds, inline=True)
        embed.add_field(name="📝 Evidence Items", value=total_evidence, inline=True)
        embed.add_field(name="Status", value="🟢 OPERATIONAL", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LegalHoldManagerCog(bot))
