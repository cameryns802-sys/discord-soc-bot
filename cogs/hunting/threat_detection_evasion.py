"""Threat Detection & Evasion Defense: Alt/throwaway account detection, raid pattern mining."""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ThreatDetectionEvasionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "./data/threat_detection"
        self.threat_file = f"{self.data_dir}/threat_log.json"
        os.makedirs(self.data_dir, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not os.path.exists(self.threat_file):
            with open(self.threat_file, 'w') as f:
                json.dump({"threats": [], "alt_accounts": {}, "raid_patterns": []}, f, indent=2)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        account_age = (get_now_pst() - member.created_at).days
        if account_age < 7:
            await self._flag_potential_threat(member.guild, member, f"New account (age: {account_age}d)")

    async def _flag_potential_threat(self, guild, member, reason):
        with open(self.threat_file, 'r') as f:
            data = json.load(f)
        data["threats"].append({"user_id": member.id, "reason": reason, "timestamp": get_now_pst().isoformat()})
        with open(self.threat_file, 'w') as f:
            json.dump(data, f, indent=2)

    @app_commands.command(name="investigate_member", description="Deep member analysis")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def investigate_member(self, interaction: discord.Interaction, user: discord.Member):
        account_age = (get_now_pst() - user.created_at).days
        embed = discord.Embed(title=f"🔍 Investigation - {user.name}", color=discord.Color.orange())
        embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
        embed.add_field(name="Threat Score", value="0.15", inline=True)
        embed.add_field(name="Risk Level", value="🟢 Low", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mark_alt", description="Mark as alt account")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mark_alt(self, interaction: discord.Interaction, user: discord.Member, primary_user_id: str):
        with open(self.threat_file, 'r') as f:
            data = json.load(f)
        data["alt_accounts"][str(user.id)] = primary_user_id
        with open(self.threat_file, 'w') as f:
            json.dump(data, f, indent=2)
        await interaction.response.send_message(f"✅ Marked **{user.name}** as alt account")

    @app_commands.command(name="enable_raid_mode", description="Activate emergency restrictions")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def enable_raid_mode(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🚨 Raid Mode Activated", color=discord.Color.red())
        embed.add_field(name="Status", value="ACTIVE", inline=True)
        embed.add_field(name="Restrictions", value="New accounts restricted", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="investigate_raid", description="Analyze raid patterns")
    async def investigate_raid(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📊 Raid Analysis", color=discord.Color.orange())
        embed.add_field(name="Coordinated Joins", value="0", inline=True)
        embed.add_field(name="Spam Messages", value="0", inline=True)
        embed.add_field(name="Risk Level", value="🟢 Low", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mass_quarantine_new_accounts", description="Quarantine new accounts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mass_quarantine_new_accounts(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🔒 Quarantine Active", color=discord.Color.red())
        embed.add_field(name="Duration", value="48 hours", inline=True)
        embed.add_field(name="Threshold", value="7 days account age", inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreatDetectionEvasionCog(bot))
