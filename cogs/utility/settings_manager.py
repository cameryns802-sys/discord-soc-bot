"""
Settings Manager - Manage server-specific settings
Configure bot behavior per server
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class SettingsManager(commands.Cog):
    """Manage server settings"""
    
    # Define command groups at class level
    settings_group = app_commands.Group(name="settings", description="Server settings management")
    
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'data/server_settings.json'
        self.load_settings()
    
    def load_settings(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, 'w') as f:
                json.dump({}, f)
    
    def get_settings(self, guild_id):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
            defaults = self.get_default_settings()
            saved = data.get(str(guild_id), {})
            defaults.update(saved)
            return defaults
        except:
            return self.get_default_settings()
    
    def get_default_settings(self):
        return {
            "prefix": "!",
            "mod_logs_enabled": True,
            "auto_mod_enabled": True,
            "verification_enabled": True,
            "welcome_messages": True,
            "farewell_messages": False,
            "anti_spam": True,
            "anti_raid": True,
            "anti_impersonation": True,
            "tickets_enabled": True,
            "welcome_channel_id": None,
            "farewell_channel_id": None,
            "log_channel_id": None,
            "modlog_channel_id": None,
            "transcript_channel_id": None,
            "auto_role_id": None,
            "dm_rules_enabled": False,
            "dm_rules_message": "Welcome to the server! Please read the rules in #rules and reach out to staff if you need help.",
            "welcome_message": "Hello {member}, welcome to **{server}**!",
            "farewell_message": "{member} has left **{server}**.",
            "welcome_use_embed": True,
            "farewell_use_embed": True
        }
    
    def save_settings(self, guild_id, settings):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        data[str(guild_id)] = settings
        with open(self.settings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @commands.command(name='settings', aliases=['config'])
    @commands.has_permissions(administrator=True)
    async def show_settings(self, ctx):
        """Show current server settings"""
        settings = self.get_settings(ctx.guild.id)

        embed = discord.Embed(
            title="Server Settings",
            description=f"{ctx.guild.name} - Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )

        embed.add_field(name="Core Settings", value="-" * 20, inline=False)
        embed.add_field(name="Prefix", value=settings.get("prefix", "!"), inline=True)

        embed.add_field(name="Features", value="-" * 20, inline=False)
        embed.add_field(name="Mod Logs", value="Enabled" if settings.get("mod_logs_enabled") else "Disabled", inline=True)
        embed.add_field(name="Auto-Mod", value="Enabled" if settings.get("auto_mod_enabled") else "Disabled", inline=True)
        embed.add_field(name="Verification", value="Enabled" if settings.get("verification_enabled") else "Disabled", inline=True)
        embed.add_field(name="Tickets", value="Enabled" if settings.get("tickets_enabled") else "Disabled", inline=True)

        embed.add_field(name="Messages", value="-" * 20, inline=False)
        embed.add_field(name="Welcome", value="Enabled" if settings.get("welcome_messages") else "Disabled", inline=True)
        embed.add_field(name="Farewell", value="Enabled" if settings.get("farewell_messages") else "Disabled", inline=True)
        embed.add_field(name="DM Rules", value="Enabled" if settings.get("dm_rules_enabled") else "Disabled", inline=True)
        embed.add_field(name="Welcome Embed", value="Enabled" if settings.get("welcome_use_embed") else "Disabled", inline=True)
        embed.add_field(name="Farewell Embed", value="Enabled" if settings.get("farewell_use_embed") else "Disabled", inline=True)

        embed.add_field(name="Security", value="-" * 20, inline=False)
        embed.add_field(name="Anti-Spam", value="Enabled" if settings.get("anti_spam") else "Disabled", inline=True)
        embed.add_field(name="Anti-Raid", value="Enabled" if settings.get("anti_raid") else "Disabled", inline=True)
        embed.add_field(name="Anti-Impersonation", value="Enabled" if settings.get("anti_impersonation") else "Disabled", inline=True)

        embed.add_field(name="Channels", value="-" * 20, inline=False)
        embed.add_field(name="Welcome Channel", value=self._format_channel(ctx.guild, settings.get("welcome_channel_id")), inline=True)
        embed.add_field(name="Farewell Channel", value=self._format_channel(ctx.guild, settings.get("farewell_channel_id")), inline=True)
        embed.add_field(name="Log Channel", value=self._format_channel(ctx.guild, settings.get("log_channel_id")), inline=True)
        embed.add_field(name="Mod-Log Channel", value=self._format_channel(ctx.guild, settings.get("modlog_channel_id")), inline=True)
        embed.add_field(name="Transcript Channel", value=self._format_channel(ctx.guild, settings.get("transcript_channel_id")), inline=True)
        embed.add_field(name="Auto Role", value=self._format_role(ctx.guild, settings.get("auto_role_id")), inline=True)

        embed.add_field(name="How to Change", value="Use `!set_setting <name> <true/false>` or `!setchannel <type> <#channel>`", inline=False)

        await ctx.send(embed=embed)

    @settings_group.command(name="view", description="View server configuration")
    async def show_settings_slash(self, interaction: discord.Interaction):
        settings = self.get_settings(interaction.guild.id)

        embed = discord.Embed(
            title="Server Settings",
            description=f"{interaction.guild.name} - Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )

        embed.add_field(name="Core Settings", value="-" * 20, inline=False)
        embed.add_field(name="Prefix", value=settings.get("prefix", "!"), inline=True)

        embed.add_field(name="Features", value="-" * 20, inline=False)
        embed.add_field(name="Mod Logs", value="Enabled" if settings.get("mod_logs_enabled") else "Disabled", inline=True)
        embed.add_field(name="Auto-Mod", value="Enabled" if settings.get("auto_mod_enabled") else "Disabled", inline=True)
        embed.add_field(name="Verification", value="Enabled" if settings.get("verification_enabled") else "Disabled", inline=True)
        embed.add_field(name="Tickets", value="Enabled" if settings.get("tickets_enabled") else "Disabled", inline=True)

        embed.add_field(name="Messages", value="-" * 20, inline=False)
        embed.add_field(name="Welcome", value="Enabled" if settings.get("welcome_messages") else "Disabled", inline=True)
        embed.add_field(name="Farewell", value="Enabled" if settings.get("farewell_messages") else "Disabled", inline=True)
        embed.add_field(name="DM Rules", value="Enabled" if settings.get("dm_rules_enabled") else "Disabled", inline=True)
        embed.add_field(name="Welcome Embed", value="Enabled" if settings.get("welcome_use_embed") else "Disabled", inline=True)
        embed.add_field(name="Farewell Embed", value="Enabled" if settings.get("farewell_use_embed") else "Disabled", inline=True)

        embed.add_field(name="Security", value="-" * 20, inline=False)
        embed.add_field(name="Anti-Spam", value="Enabled" if settings.get("anti_spam") else "Disabled", inline=True)
        embed.add_field(name="Anti-Raid", value="Enabled" if settings.get("anti_raid") else "Disabled", inline=True)
        embed.add_field(name="Anti-Impersonation", value="Enabled" if settings.get("anti_impersonation") else "Disabled", inline=True)

        embed.add_field(name="Channels", value="-" * 20, inline=False)
        embed.add_field(name="Welcome Channel", value=self._format_channel(interaction.guild, settings.get("welcome_channel_id")), inline=True)
        embed.add_field(name="Farewell Channel", value=self._format_channel(interaction.guild, settings.get("farewell_channel_id")), inline=True)
        embed.add_field(name="Log Channel", value=self._format_channel(interaction.guild, settings.get("log_channel_id")), inline=True)
        embed.add_field(name="Mod-Log Channel", value=self._format_channel(interaction.guild, settings.get("modlog_channel_id")), inline=True)
        embed.add_field(name="Transcript Channel", value=self._format_channel(interaction.guild, settings.get("transcript_channel_id")), inline=True)
        embed.add_field(name="Auto Role", value=self._format_role(interaction.guild, settings.get("auto_role_id")), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='set_setting')
    @commands.has_permissions(administrator=True)
    async def set_setting(self, ctx, setting_name: str, value: str):
        settings = self.get_settings(interaction.guild.id)

        if setting_name not in settings:
            await interaction.response.send_message(f"Unknown setting: {setting_name}", ephemeral=True)
            return

        bool_value = value.lower() in ["true", "yes", "enabled", "1", "on"]
        settings[setting_name] = bool_value
        self.save_settings(interaction.guild.id, settings)

        embed = discord.Embed(
            title="Setting Updated",
            description=f"{setting_name}: {'ENABLED' if bool_value else 'DISABLED'}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='setchannel', aliases=['set_channel'])
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel_type: str, channel: discord.TextChannel = None):
        """Set a channel for logs, welcome, mod-log, or transcripts"""
        settings = self.get_settings(ctx.guild.id)
        channel_type = channel_type.lower()

        channel_map = {
            "welcome": "welcome_channel_id",
            "farewell": "farewell_channel_id",
            "log": "log_channel_id",
            "logs": "log_channel_id",
            "modlog": "modlog_channel_id",
            "mod-log": "modlog_channel_id",
            "transcripts": "transcript_channel_id",
            "transcript": "transcript_channel_id"
        }

        if channel_type not in channel_map:
            await ctx.send("âŒ Invalid channel type. Use: welcome, farewell, log, modlog, transcripts")
            return

        key = channel_map[channel_type]
        settings[key] = channel.id if channel else None
        self.save_settings(ctx.guild.id, settings)

        embed = discord.Embed(
            title="âœ… Channel Updated",
            description=f"{channel_type} channel set to {channel.mention if channel else 'None'}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @settings_group.command(name="channel", description="Set a channel for welcome, farewell, logs, mod-log, transcripts")
    @app_commands.describe(channel_type="welcome|farewell|log|modlog|transcripts", channel="Target channel")
    async def set_channel_slash(self, interaction: discord.Interaction, channel_type: str, channel: discord.TextChannel = None):
        settings = self.get_settings(interaction.guild.id)
        channel_type = channel_type.lower()

        channel_map = {
            "welcome": "welcome_channel_id",
            "farewell": "farewell_channel_id",
            "log": "log_channel_id",
            "logs": "log_channel_id",
            "modlog": "modlog_channel_id",
            "mod-log": "modlog_channel_id",
            "transcripts": "transcript_channel_id",
            "transcript": "transcript_channel_id"
        }

        if channel_type not in channel_map:
            await interaction.response.send_message("Invalid channel type. Use: welcome, farewell, log, modlog, transcripts", ephemeral=True)
            return

        key = channel_map[channel_type]
        settings[key] = channel.id if channel else None
        self.save_settings(interaction.guild.id, settings)

        embed = discord.Embed(
            title="Channel Updated",
            description=f"{channel_type} channel set to {channel.mention if channel else 'None'}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='setmessage', aliases=['set_message'])
    @commands.has_permissions(administrator=True)
    async def set_message(self, ctx, message_type: str, *, message: str):
        """Set welcome, farewell, or DM rules message"""
        settings = self.get_settings(ctx.guild.id)
        message_type = message_type.lower()

        if message_type == "welcome":
            settings["welcome_message"] = message
        elif message_type == "farewell":
            settings["farewell_message"] = message
        elif message_type in ["dm", "dm_rules", "rules"]:
            settings["dm_rules_message"] = message
        else:
            await ctx.send("âŒ Invalid message type. Use: welcome, farewell, dm")
            return

        self.save_settings(ctx.guild.id, settings)
        await ctx.send("✅ Message updated.")

    @settings_group.command(name="message", description="Set welcome, farewell, or DM rules message")
    @app_commands.describe(message_type="welcome|farewell|dm", message="Message text")
    async def set_message_slash(self, interaction: discord.Interaction, message_type: str, message: str):
        settings = self.get_settings(interaction.guild.id)
        message_type = message_type.lower()

        if message_type == "welcome":
            settings["welcome_message"] = message
        elif message_type == "farewell":
            settings["farewell_message"] = message
        elif message_type in ["dm", "dm_rules", "rules"]:
            settings["dm_rules_message"] = message
        else:
            await interaction.response.send_message("Invalid message type. Use: welcome, farewell, dm", ephemeral=True)
            return

        self.save_settings(interaction.guild.id, settings)
        await interaction.response.send_message("Message updated.", ephemeral=True)

    @commands.command(name='setautorole', aliases=['set_auto_role'])
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx, role: discord.Role = None):
        """Set a role to auto-assign on join (use without role to clear)"""
        settings = self.get_settings(ctx.guild.id)
        settings["auto_role_id"] = role.id if role else None
        self.save_settings(ctx.guild.id, settings)

        embed = discord.Embed(
            title="âœ… Auto Role Updated",
            description=f"Auto-role set to {role.mention if role else 'None'}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @settings_group.command(name="autorole", description="Set an auto-role for new members")
    @app_commands.describe(role="Role to auto-assign")
    async def set_auto_role_slash(self, interaction: discord.Interaction, role: discord.Role = None):
        settings = self.get_settings(interaction.guild.id)
        settings["auto_role_id"] = role.id if role else None
        self.save_settings(interaction.guild.id, settings)

        embed = discord.Embed(
            title="Auto Role Updated",
            description=f"Auto-role set to {role.mention if role else 'None'}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='toggle_embed')
    @commands.has_permissions(administrator=True)
    async def toggle_embed(self, ctx, embed_type: str):
        """Toggle embed format for welcome/farewell messages"""
        settings = self.get_settings(ctx.guild.id)
        embed_type = embed_type.lower()

        if embed_type == "welcome":
            settings["welcome_use_embed"] = not settings.get("welcome_use_embed", True)
            status = settings["welcome_use_embed"]
            label = "Welcome"
        elif embed_type == "farewell":
            settings["farewell_use_embed"] = not settings.get("farewell_use_embed", True)
            status = settings["farewell_use_embed"]
            label = "Farewell"
        else:
            await ctx.send("âŒ Invalid type. Use: welcome or farewell")
            return

        self.save_settings(ctx.guild.id, settings)
        await ctx.send(f"✅ {label} embeds {'enabled' if status else 'disabled'}.")

    @settings_group.command(name="toggleembed", description="Toggle embed format for welcome/farewell messages")
    @app_commands.describe(embed_type="welcome or farewell")
    async def toggle_embed_slash(self, interaction: discord.Interaction, embed_type: str):
        settings = self.get_settings(interaction.guild.id)
        embed_type = embed_type.lower()

        if embed_type == "welcome":
            settings["welcome_use_embed"] = not settings.get("welcome_use_embed", True)
            status = settings["welcome_use_embed"]
            label = "Welcome"
        elif embed_type == "farewell":
            settings["farewell_use_embed"] = not settings.get("farewell_use_embed", True)
            status = settings["farewell_use_embed"]
            label = "Farewell"
        else:
            await interaction.response.send_message("Invalid type. Use: welcome or farewell", ephemeral=True)
            return

        self.save_settings(interaction.guild.id, settings)
        await interaction.response.send_message(f"{label} embeds {'enabled' if status else 'disabled'}.", ephemeral=True)

    def _format_channel(self, guild, channel_id):
        if not channel_id:
            return "Not set"
        channel = guild.get_channel(channel_id)
        return channel.mention if channel else "Not set"

    def _format_role(self, guild, role_id):
        if not role_id:
            return "Not set"
        role = guild.get_role(role_id)
        return role.mention if role else "Not set"
    
    @commands.command(name='reset_settings')
    @commands.has_permissions(administrator=True)
    async def reset_settings(self, ctx):
        """Reset settings to default"""
        default = self.get_default_settings()
        self.save_settings(ctx.guild.id, default)
        
        embed = discord.Embed(
            title="✅ Settings Reset",
            description="All settings reset to default values",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SettingsManager(bot))
