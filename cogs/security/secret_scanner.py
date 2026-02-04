"""Secret Scanner & Verification: Consolidated command groups"""
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import re
import json
import os
from cogs.core.pst_timezone import get_now_pst

class SecretScanGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="secret", description="Secret scanner commands")
        self.cog = cog

    @app_commands.command(name="enable", description="Enable auto-delete for secret detection")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable(self, interaction: discord.Interaction):
        self.cog.auto_delete = True
        self.cog.save_data()
        await interaction.response.send_message("✅ Secret scanner auto-delete enabled")

    @app_commands.command(name="disable", description="Disable auto-delete for secret detection")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable(self, interaction: discord.Interaction):
        self.cog.auto_delete = False
        self.cog.save_data()
        await interaction.response.send_message("⚠️ Secret scanner auto-delete disabled - warnings only")

    @app_commands.command(name="whitelist", description="Add pattern to whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist(self, interaction: discord.Interaction, pattern: str):
        self.cog.whitelist.add(pattern)
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Added to whitelist")

    @app_commands.command(name="view", description="View detected secrets")
    @app_commands.checks.has_permissions(administrator=True)
    async def view(self, interaction: discord.Interaction):
        if not self.cog.detected_secrets:
            await interaction.response.send_message("ℹ️ No secrets detected", ephemeral=True)
            return
        embed = discord.Embed(title="🔍 Detected Secrets (Last 20)", color=discord.Color.red())
        for secret in self.cog.detected_secrets[-20:]:
            embed.add_field(name=f"{secret['type']}", value=f"Value: `{secret['value']}`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear", description="Clear secret detection log")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction):
        count = len(self.cog.detected_secrets)
        self.cog.detected_secrets = []
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Cleared {count} detections")

    @app_commands.command(name="stats", description="View secret scanner statistics")
    async def stats(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📊 Secret Scanner Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Detections", value=len(self.cog.detected_secrets), inline=True)
        embed.add_field(name="Auto-Delete", value="🟢 Enabled" if self.cog.auto_delete else "🔴 Disabled", inline=True)
        await interaction.response.send_message(embed=embed)

class VerifyGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="verify", description="Verification system commands")
        self.cog = cog

    @app_commands.command(name="setup", description="Setup verification channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, verified_role: discord.Role, method: str = "button"):
        if method.lower() not in ["button", "captcha", "reaction", "manual"]:
            await interaction.response.send_message("❌ Method must be: button, captcha, reaction, manual", ephemeral=True)
            return
        guild_id = interaction.guild.id
        self.cog.verify_channels[guild_id] = channel.id
        self.cog.verified_roles[guild_id] = verified_role.id
        self.cog.verification_methods[guild_id] = method.lower()
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Verification configured | Channel: {channel.mention} | Method: {method}")

    @app_commands.command(name="set_unverified_role", description="Set role for unverified members")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_unverified_role(self, interaction: discord.Interaction, role: discord.Role):
        self.cog.unverified_roles[interaction.guild.id] = role.id
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Unverified role set to {role.mention}")

    @app_commands.command(name="method", description="Change verification method")
    @app_commands.checks.has_permissions(administrator=True)
    async def method(self, interaction: discord.Interaction, method: str):
        if method.lower() not in ["button", "captcha", "reaction", "manual"]:
            await interaction.response.send_message("❌ Method must be: button, captcha, reaction, manual", ephemeral=True)
            return
        self.cog.verification_methods[interaction.guild.id] = method.lower()
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Method changed to: {method.capitalize()}")

    @app_commands.command(name="user", description="Manually verify a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def user(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = interaction.guild.id
        if guild_id not in self.cog.verified_roles:
            await interaction.response.send_message("❌ Verification not configured", ephemeral=True)
            return
        verified_role = interaction.guild.get_role(self.cog.verified_roles[guild_id])
        if verified_role:
            await member.add_roles(verified_role)
        self.cog.verification_log.append({"user_id": member.id, "verified_by": interaction.user.id, "timestamp": datetime.get_now_pst().isoformat(), "method": "manual"})
        self.cog.save_data()
        await interaction.response.send_message(f"✅ {member.mention} verified")

    @app_commands.command(name="unverify", description="Remove verification from user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unverify(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = interaction.guild.id
        if guild_id not in self.cog.verified_roles:
            await interaction.response.send_message("❌ Verification not configured", ephemeral=True)
            return
        verified_role = interaction.guild.get_role(self.cog.verified_roles[guild_id])
        if verified_role and verified_role in member.roles:
            await member.remove_roles(verified_role)
        await interaction.response.send_message(f"✅ Removed verification from {member.mention}")

    @app_commands.command(name="stats", description="View verification statistics")
    async def stats(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.cog.verified_roles:
            await interaction.response.send_message("❌ Verification not configured", ephemeral=True)
            return
        embed = discord.Embed(title="📊 Verification Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Verifications", value=len(self.cog.verification_log), inline=True)
        embed.add_field(name="Method", value=self.cog.verification_methods.get(str(guild_id), "button").capitalize(), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="log", description="View recent verifications")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def log(self, interaction: discord.Interaction):
        if not self.cog.verification_log:
            await interaction.response.send_message("ℹ️ No verification logs", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Recent Verifications", color=discord.Color.blue())
        for entry in self.cog.verification_log[-10:]:
            embed.add_field(name=f"<@{entry['user_id']}>", value=f"Method: {entry['method']}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="config", description="View verification configuration")
    async def config(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.cog.verify_channels:
            await interaction.response.send_message("❌ Verification not configured", ephemeral=True)
            return
        embed = discord.Embed(title="⚙️ Verification Configuration", color=discord.Color.blue())
        embed.add_field(name="Channel", value=f"<#{self.cog.verify_channels[guild_id]}>", inline=True)
        embed.add_field(name="Method", value=self.cog.verification_methods.get(str(guild_id), "button").capitalize(), inline=True)
        await interaction.response.send_message(embed=embed)

class SecretScannerVerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.detected_secrets = []
        self.patterns = {"discord_token": r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}", "github_token": r"ghp_[0-9a-zA-Z]{36}", "aws_key": r"AKIA[0-9A-Z]{16}", "slack_token": r"xox[baprs]-[0-9a-zA-Z]{10,48}", "api_key": r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[0-9a-zA-Z]{20,}", "private_key": r"-----BEGIN (RSA |DSA )?PRIVATE KEY-----", "jwt": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+"}
        self.whitelist = set()
        self.auto_delete = True
        self.verify_channels = {}
        self.verified_roles = {}
        self.unverified_roles = {}
        self.verification_methods = {}
        self.verification_log = []
        self.data_file_secrets = "data/secret_scanner.json"
        self.data_file_verify = "data/verification_system.json"
        self.load_data()
        self.secretscan_group = SecretScanGroup(self)
        self.verify_group = VerifyGroup(self)
        bot.tree.add_command(self.secretscan_group)
        bot.tree.add_command(self.verify_group)

    def load_data(self):
        if os.path.exists(self.data_file_secrets):
            try:
                with open(self.data_file_secrets, 'r') as f:
                    data = json.load(f)
                    self.detected_secrets = data.get('detected_secrets', [])
                    self.whitelist = set(data.get('whitelist', []))
                    self.auto_delete = data.get('auto_delete', True)
            except: pass
        if os.path.exists(self.data_file_verify):
            try:
                with open(self.data_file_verify, 'r') as f:
                    data = json.load(f)
                    self.verify_channels = {int(k): v for k, v in data.get('verify_channels', {}).items()}
                    self.verified_roles = {int(k): v for k, v in data.get('verified_roles', {}).items()}
                    self.unverified_roles = {int(k): v for k, v in data.get('unverified_roles', {}).items()}
                    self.verification_methods = data.get('verification_methods', {})
                    self.verification_log = data.get('verification_log', [])
            except: pass

    def save_data(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file_secrets, 'w') as f:
            json.dump({'detected_secrets': self.detected_secrets[-100:], 'whitelist': list(self.whitelist), 'auto_delete': self.auto_delete}, f, indent=2)
        with open(self.data_file_verify, 'w') as f:
            json.dump({'verify_channels': {str(k): v for k, v in self.verify_channels.items()}, 'verified_roles': {str(k): v for k, v in self.verified_roles.items()}, 'unverified_roles': {str(k): v for k, v in self.unverified_roles.items()}, 'verification_methods': self.verification_methods, 'verification_log': self.verification_log[-500:]}, f, indent=2)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content:
            return
        detected = []
        for secret_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, message.content, re.IGNORECASE)
            for match in matches:
                secret_value = match.group()
                if secret_value not in self.whitelist:
                    detected.append({"type": secret_type, "value": secret_value[:10] + "***", "timestamp": datetime.get_now_pst().isoformat()})
        if detected:
            for secret in detected:
                self.detected_secrets.append(secret)
            self.save_data()
            if self.auto_delete:
                try:
                    await message.delete()
                    await message.channel.send(f"🚨 {message.author.mention} - Your message contained potential secrets and was deleted.", delete_after=10)
                except: pass

    async def cog_unload(self):
        self.bot.tree.remove_command(self.secretscan_group.name)
        self.bot.tree.remove_command(self.verify_group.name)

async def setup(bot):
    await bot.add_cog(SecretScannerVerificationCog(bot))
