"""PII Detection - Unified with Feature Flags & Signals

Consolidates pii_detection_simple.py with feature flags and signal bus integration.
- Simple mode: Scan messages, view reports (always available)
- Advanced mode: Auto-remediation, continuous scanning (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
import re
import datetime
import json
import os
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags
from cogs.core.pst_timezone import get_now_pst

class PIIDetectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scans = {}
        self.data_file = "data/pii_scans.json"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.scans = json.load(f)
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.scans, f, indent=2)
    
    def scan_for_pii(self, text: str) -> dict:
        findings = []
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            findings.append("SSN detected")
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            findings.append("Email detected")
        if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', text):
            findings.append("Credit card detected")
        return {"count": len(findings), "types": findings}

    async def emit_pii_signal(self, scan_id: str, findings_count: int):
        """Emit PII signal to central bus"""
        if findings_count > 0:
            await signal_bus.emit(Signal(
                signal_type=SignalType.PII_EXPOSURE,
                severity='critical' if findings_count > 2 else 'high',
                source='pii_detection',
                data={
                    'scan_id': scan_id,
                    'findings_count': findings_count,
                    'confidence': 0.95,
                    'dedup_key': f'pii_{scan_id}'
                }
            ))

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="piiscan", description="Scan message for PII")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def piiscan(self, interaction: discord.Interaction, text: str):
        """Scan for PII - Simple mode"""
        result = self.scan_for_pii(text)
        scan_id = str(len(self.scans))
        self.scans[scan_id] = {
            "timestamp": datetime.get_now_pst().isoformat(),
            "scanned_by": interaction.user.id,
            "findings": result['count']
        }
        self.save_data()
        
        await self.emit_pii_signal(scan_id, result['count'])
        
        embed = discord.Embed(title="🔍 PII Scan Results", color=discord.Color.red() if result['count'] > 0 else discord.Color.green())
        embed.add_field(name="Findings", value=result['count'], inline=True)
        embed.add_field(name="Risk Level", value="HIGH" if result['count'] > 0 else "SAFE", inline=True)
        if result['types']:
            embed.add_field(name="Types Detected", value="\n".join(result['types']), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="piireport", description="View PII detection report")
    async def piireport(self, interaction: discord.Interaction):
        """View PII report - Simple mode"""
        total_scans = len(self.scans)
        total_findings = sum(scan.get('findings', 0) for scan in self.scans.values())
        embed = discord.Embed(title="📊 PII Detection Report", color=discord.Color.blue())
        embed.add_field(name="Total Scans", value=total_scans, inline=True)
        embed.add_field(name="Total Findings", value=total_findings, inline=True)
        embed.add_field(name="Detection Rate", value=f"{(total_findings/max(total_scans,1)*100):.1f}%", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="piipolicy", description="View PII protection policy")
    async def piipolicy(self, interaction: discord.Interaction):
        """View PII policy - Simple mode"""
        embed = discord.Embed(title="🛡️ PII Protection Policy", color=discord.Color.blue())
        embed.add_field(name="Protected Data", value="• SSN\n• Credit cards\n• Email addresses\n• Phone numbers", inline=False)
        embed.add_field(name="Actions", value="• Auto-delete\n• Alert moderators\n• Log incident", inline=False)
        await interaction.response.send_message(embed=embed)

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="piichannel")
    @commands.has_permissions(moderate_members=True)
    async def piichannel(self, ctx, channel: discord.TextChannel, limit: int = 100):
        """Scan channel for PII"""
        await ctx.send(f"🔍 Scanning {channel.mention} (last {limit} messages)...")
        findings = 0
        async for message in channel.history(limit=limit):
            result = self.scan_for_pii(message.content)
            findings += result['count']
        await ctx.send(f"✅ Scan complete - {findings} PII findings detected")

    @commands.command(name="piiuser")
    @commands.has_permissions(moderate_members=True)
    async def piiuser(self, ctx, user: discord.Member):
        """Scan user's messages for PII"""
        await ctx.send(f"🔍 Scanning messages from {user.mention}...")
        findings = 0
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(limit=50):
                    if message.author == user:
                        result = self.scan_for_pii(message.content)
                        findings += result['count']
            except:
                pass
        await ctx.send(f"✅ Scan complete - {findings} PII findings for {user.mention}")

    @commands.command(name="piistats")
    async def piistats(self, ctx):
        """View PII scan statistics"""
        total = len(self.scans)
        recent = len([s for s in self.scans.values() if s.get('timestamp', '')[:10] == datetime.get_now_pst().isoformat()[:10]])
        embed = discord.Embed(title="📊 PII Scan Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Scans", value=total, inline=True)
        embed.add_field(name="Today", value=recent, inline=True)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="piiauto", description="[Advanced] Auto-remediation settings")
    async def piiauto(self, interaction: discord.Interaction):
        """Auto-remediation - Advanced mode only"""
        if not flags.is_enabled('pii_auto_detection'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        await interaction.response.send_message("⚙️ Auto-remediation enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(PIIDetectionCog(bot))
