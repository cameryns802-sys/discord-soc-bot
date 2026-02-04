"""
Welcome/Farewell System - Greet members and log departures
Send welcome messages to new members
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class WelcomeFarewellSystem(commands.Cog):
    """Welcome and farewell message system"""

    def __init__(self, bot):
        self.bot = bot
        self.welcome_file = 'data/welcome_farewell.json'
        self.load_welcome_data()

    def load_welcome_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.welcome_file):
            with open(self.welcome_file, 'w') as f:
                json.dump({}, f)

    def get_welcome_config(self, guild_id):
        try:
            with open(self.welcome_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {"enabled": True})
        except:
            return {"enabled": True}

    def save_welcome_config(self, guild_id, config):
        try:
            with open(self.welcome_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}

        data[str(guild_id)] = config
        with open(self.welcome_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_settings(self, guild_id):
        settings_cog = self.bot.get_cog('SettingsManager')
        if settings_cog:
            return settings_cog.get_settings(guild_id)
        return None

    def _format_message(self, template: str, member: discord.Member):
        if not template:
            return ""
        return (
            template
            .replace("{member}", member.mention)
            .replace("{user}", member.mention)
            .replace("{server}", member.guild.name)
        )

    async def _send_message(self, channel, use_embed: bool, title: str, description: str, color: discord.Color, member: discord.Member):
        if not channel or not channel.permissions_for(member.guild.me).send_messages:
            return

        if use_embed:
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=get_now_pst()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            try:
                await channel.send(embed=embed)
            except:
                pass
        else:
            try:
                await channel.send(description)
            except:
                pass

    def _get_channel(self, guild: discord.Guild, channel_id):
        if channel_id:
            return guild.get_channel(channel_id)
        general = discord.utils.get(guild.text_channels, name="general")
        if general and general.permissions_for(guild.me).send_messages:
            return general
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message to new members"""
        settings = self._get_settings(member.guild.id)

        if settings:
            if not settings.get("welcome_messages", True):
                return
            welcome_channel = self._get_channel(member.guild, settings.get("welcome_channel_id"))
            message = self._format_message(settings.get("welcome_message", ""), member)
            if not message:
                message = f"Hello {member.mention}, welcome to {member.guild.name}!"
            use_embed = settings.get("welcome_use_embed", True)
        else:
            config = self.get_welcome_config(member.guild.id)
            if not config.get("enabled"):
                return
            welcome_channel = self._get_channel(member.guild, None)
            message = f"Hello {member.mention}, welcome to {member.guild.name}!"
            use_embed = True

        await self._send_message(
            welcome_channel,
            use_embed,
            title=f"Welcome to {member.guild.name}!",
            description=message,
            color=discord.Color.green(),
            member=member
        )

        if settings:
            auto_role_id = settings.get("auto_role_id")
            if auto_role_id:
                role = member.guild.get_role(auto_role_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Auto role assignment")
                    except:
                        pass

            if settings.get("dm_rules_enabled"):
                dm_message = self._format_message(settings.get("dm_rules_message", ""), member)
                if dm_message:
                    try:
                        await member.send(dm_message)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send farewell message when member leaves"""
        settings = self._get_settings(member.guild.id)

        if settings:
            if not settings.get("farewell_messages", False):
                return
            farewell_channel = self._get_channel(member.guild, settings.get("farewell_channel_id"))
            message = self._format_message(settings.get("farewell_message", ""), member)
            if not message:
                message = f"{member.name} has left {member.guild.name}."
            use_embed = settings.get("farewell_use_embed", True)
        else:
            config = self.get_welcome_config(member.guild.id)
            if not config.get("farewell_enabled"):
                return
            farewell_channel = self._get_channel(member.guild, None)
            message = f"{member.name} has left {member.guild.name}."
            use_embed = True

        await self._send_message(
            farewell_channel,
            use_embed,
            title="Member Left",
            description=message,
            color=discord.Color.red(),
            member=member
        )

    @commands.command(name='toggle_welcome')
    @commands.has_permissions(administrator=True)
    async def toggle_welcome(self, ctx):
        """Toggle welcome messages"""
        settings = self._get_settings(ctx.guild.id)
        if settings is not None:
            settings["welcome_messages"] = not settings.get("welcome_messages", True)
            settings_cog = self.bot.get_cog('SettingsManager')
            settings_cog.save_settings(ctx.guild.id, settings)
            enabled = settings["welcome_messages"]
        else:
            config = self.get_welcome_config(ctx.guild.id)
            config["enabled"] = not config.get("enabled", True)
            self.save_welcome_config(ctx.guild.id, config)
            enabled = config["enabled"]

        embed = discord.Embed(
            title="Welcome System Updated",
            description=f"Welcome messages: {'ENABLED' if enabled else 'DISABLED'}",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

    @commands.command(name='toggle_farewell')
    @commands.has_permissions(administrator=True)
    async def toggle_farewell(self, ctx):
        """Toggle farewell messages"""
        settings = self._get_settings(ctx.guild.id)
        if settings is not None:
            settings["farewell_messages"] = not settings.get("farewell_messages", False)
            settings_cog = self.bot.get_cog('SettingsManager')
            settings_cog.save_settings(ctx.guild.id, settings)
            enabled = settings["farewell_messages"]
        else:
            config = self.get_welcome_config(ctx.guild.id)
            config["farewell_enabled"] = not config.get("farewell_enabled", False)
            self.save_welcome_config(ctx.guild.id, config)
            enabled = config["farewell_enabled"]

        embed = discord.Embed(
            title="Farewell System Updated",
            description=f"Farewell messages: {'ENABLED' if enabled else 'DISABLED'}",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeFarewellSystem(bot))
