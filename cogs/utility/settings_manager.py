"""
Settings Manager - Manage server-specific settings
Configure bot behavior per server
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SettingsManager(commands.Cog):
    """Manage server settings"""
    
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
            return data.get(str(guild_id), self.get_default_settings())
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
            "anti_impersonation": True
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
    
    @commands.command(name='settings')
    @commands.has_permissions(administrator=True)
    async def show_settings(self, ctx):
        """Show current server settings"""
        settings = self.get_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Server Settings",
            description=f"{ctx.guild.name} - Configuration",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🔧 Core Settings", value="━" * 20, inline=False)
        embed.add_field(name="Prefix", value=settings.get("prefix", "!"), inline=True)
        
        embed.add_field(name="📋 Features", value="━" * 20, inline=False)
        embed.add_field(name="Mod Logs", value="✅" if settings.get("mod_logs_enabled") else "❌", inline=True)
        embed.add_field(name="Auto-Mod", value="✅" if settings.get("auto_mod_enabled") else "❌", inline=True)
        embed.add_field(name="Verification", value="✅" if settings.get("verification_enabled") else "❌", inline=True)
        
        embed.add_field(name="👋 Messages", value="━" * 20, inline=False)
        embed.add_field(name="Welcome", value="✅" if settings.get("welcome_messages") else "❌", inline=True)
        embed.add_field(name="Farewell", value="✅" if settings.get("farewell_messages") else "❌", inline=True)
        
        embed.add_field(name="🛡️ Security", value="━" * 20, inline=False)
        embed.add_field(name="Anti-Spam", value="✅" if settings.get("anti_spam") else "❌", inline=True)
        embed.add_field(name="Anti-Raid", value="✅" if settings.get("anti_raid") else "❌", inline=True)
        embed.add_field(name="Anti-Impersonation", value="✅" if settings.get("anti_impersonation") else "❌", inline=True)
        
        embed.add_field(name="💡 How to Change", value="Use `!set_setting <name> <true/false>`", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='set_setting')
    @commands.has_permissions(administrator=True)
    async def set_setting(self, ctx, setting_name: str, value: str):
        """Change a server setting"""
        settings = self.get_settings(ctx.guild.id)
        
        if setting_name not in settings:
            await ctx.send(f"❌ Unknown setting: {setting_name}")
            return
        
        bool_value = value.lower() in ["true", "yes", "enabled", "1", "on"]
        settings[setting_name] = bool_value
        self.save_settings(ctx.guild.id, settings)
        
        embed = discord.Embed(
            title="✅ Setting Updated",
            description=f"{setting_name}: {'✅ ENABLED' if bool_value else '❌ DISABLED'}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
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
