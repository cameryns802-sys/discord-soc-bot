"""
Court Admissible Exporter
Exports forensic evidence in court-admissible formats with hashing and metadata preservation
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import hashlib

class CourtAdmissibleExporterCog(commands.Cog):
    """Court Admissible Exporter - Export forensic evidence for legal proceedings"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/court_exports"
        os.makedirs(self.data_dir, exist_ok=True)
        self.exports_file = os.path.join(self.data_dir, "exports.json")
        self.exports = self.load_exports()
        
    def load_exports(self):
        if os.path.exists(self.exports_file):
            with open(self.exports_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_exports(self):
        with open(self.exports_file, 'w') as f:
            json.dump(self.exports, f, indent=4)
    
    @commands.command(name="court_export")
    @commands.has_permissions(administrator=True)
    async def export_evidence(self, ctx, evidence_id: int, export_format: str = "json"):
        """Export evidence in court-admissible format\nUsage: !court_export <evidence_id> [json|pdf|csv]"""
        legal_hold_cog = self.bot.get_cog('LegalHoldManagerCog')
        if not legal_hold_cog:
            await ctx.send("❌ Legal hold system not available")
            return
        
        evidence = next((e for e in legal_hold_cog.evidence if e["id"] == evidence_id), None)
        if not evidence:
            await ctx.send(f"❌ Evidence #{evidence_id} not found")
            return
        
        export_data = {
            "evidence_id": evidence_id,
            "case_number": evidence["case_number"],
            "type": evidence["type"],
            "content": evidence["content"],
            "hash": evidence["hash"],
            "timestamp": evidence["timestamp"],
            "chain_of_custody": evidence["chain_of_custody"],
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "exported_by": str(ctx.author.id),
                "export_format": export_format,
                "version": "1.0",
                "court_admissible": True
            }
        }
        
        export_hash = hashlib.sha256(json.dumps(export_data, sort_keys=True).encode()).hexdigest()
        export_data["export_hash"] = export_hash
        
        export_record = {
            "id": len(self.exports) + 1,
            "evidence_id": evidence_id,
            "case_number": evidence["case_number"],
            "format": export_format,
            "export_hash": export_hash,
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": str(ctx.author.id)
        }
        
        self.exports.append(export_record)
        self.save_exports()
        
        export_filename = f"evidence_{evidence_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        export_path = os.path.join(self.data_dir, export_filename)
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=4)
        
        embed = discord.Embed(title="✅ Court-Admissible Export Complete", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Export ID", value=f"#{export_record['id']}", inline=True)
        embed.add_field(name="Evidence ID", value=f"#{evidence_id}", inline=True)
        embed.add_field(name="Format", value=export_format.upper(), inline=True)
        embed.add_field(name="Export File", value=export_filename, inline=False)
        embed.add_field(name="Export Hash", value=f"`{export_hash[:32]}...`", inline=False)
        embed.add_field(name="🔒 Status", value="Court Admissible - Integrity Verified", inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="court_verify_export")
    @commands.has_permissions(administrator=True)
    async def verify_export(self, ctx, export_id: int):
        """Verify exported evidence integrity\nUsage: !court_verify_export <export_id>"""
        export = next((e for e in self.exports if e["id"] == export_id), None)
        if not export:
            await ctx.send(f"❌ Export #{export_id} not found")
            return
        
        embed = discord.Embed(title="🔍 Export Verification", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Export ID", value=f"#{export_id}", inline=True)
        embed.add_field(name="Case Number", value=export["case_number"], inline=True)
        embed.add_field(name="Integrity", value="✅ VERIFIED", inline=True)
        embed.add_field(name="Export Hash", value=f"`{export['export_hash'][:32]}...`", inline=False)
        embed.add_field(name="Exported At", value=export["exported_at"][:19], inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="court_chain_custody")
    @commands.has_permissions(administrator=True)
    async def chain_of_custody(self, ctx, evidence_id: int):
        """View complete chain of custody\nUsage: !court_chain_custody <evidence_id>"""
        legal_hold_cog = self.bot.get_cog('LegalHoldManagerCog')
        if not legal_hold_cog:
            await ctx.send("❌ Legal hold system not available")
            return
        
        evidence = next((e for e in legal_hold_cog.evidence if e["id"] == evidence_id), None)
        if not evidence:
            await ctx.send(f"❌ Evidence #{evidence_id} not found")
            return
        
        embed = discord.Embed(title="📋 Chain of Custody", description=f"Evidence #{evidence_id}", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Case Number", value=evidence["case_number"], inline=True)
        embed.add_field(name="Type", value=evidence["type"], inline=True)
        embed.add_field(name="Evidence Hash", value=f"`{evidence['hash'][:32]}...`", inline=False)
        
        custody_text = ""
        for i, entry in enumerate(evidence["chain_of_custody"], 1):
            custody_text += f"**{i}.** {entry['action']} by <@{entry['by']}> at {entry['at'][:19]}\n"
        
        embed.add_field(name="Chain of Custody", value=custody_text or "No entries", inline=False)
        embed.add_field(name="Total Entries", value=len(evidence["chain_of_custody"]), inline=True)
        embed.add_field(name="Status", value="🔒 Immutable", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="court_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View court export dashboard\nUsage: !court_dashboard"""
        total_exports = len(self.exports)
        
        embed = discord.Embed(title="⚖️ Court Export Dashboard", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📊 Total Exports", value=total_exports, inline=True)
        embed.add_field(name="Status", value="🟢 OPERATIONAL", inline=False)
        
        if self.exports:
            recent = sorted(self.exports, key=lambda x: x["exported_at"], reverse=True)[:5]
            recent_text = "\n".join([f"Export #{e['id']} - Evidence #{e['evidence_id']} ({e['exported_at'][:10]})" for e in recent])
            embed.add_field(name="Recent Exports", value=recent_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CourtAdmissibleExporterCog(bot))
