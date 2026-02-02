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
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message to new members"""
        guild = member.guild
        config = self.get_welcome_config(guild.id)
        
        if not config.get("enabled"):
            return
        
        # Send welcome message
        embed = discord.Embed(
            title=f"👋 Welcome to {guild.name}!",
            description=f"Hello {member.mention}, welcome to our server!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="👤 Member #", value=str(len(guild.members)), inline=True)
        embed.add_field(name="📅 Join Date", value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="📋 Server Info", value=f"Members: {len(guild.members)}\nRoles: {len(guild.roles)}", inline=False)
        embed.add_field(name="📖 Guidelines", value="Please read server rules and verify yourself!", inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f"ID: {member.id}")
        
        # Send to general or first available channel
        general = discord.utils.get(guild.text_channels, name="general")
        if general and general.permissions_for(guild.me).send_messages:
            try:
                await general.send(embed=embed)
            except:
                pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send farewell message when member leaves"""
        guild = member.guild
        config = self.get_welcome_config(guild.id)
        
        if not config.get("farewell_enabled"):
            return
        
        # Send farewell message
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"{member.name} has left the server",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Member", value=str(member), inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime('%Y-%m-%d') if member.joined_at else "N/A", inline=True)
        embed.add_field(name="Remaining Members", value=str(len(guild.members)), inline=True)
        
        # Send to general or first available channel
        general = discord.utils.get(guild.text_channels, name="general")
        if general and general.permissions_for(guild.me).send_messages:
            try:
                await general.send(embed=embed)
            except:
                pass
    
    @commands.command(name='toggle_welcome')
    @commands.has_permissions(administrator=True)
    async def toggle_welcome(self, ctx):
        """Toggle welcome messages"""
        config = self.get_welcome_config(ctx.guild.id)
        config["enabled"] = not config.get("enabled", True)
        self.save_welcome_config(ctx.guild.id, config)
        
        embed = discord.Embed(
            title="✅ Welcome System Updated",
            description=f"Welcome messages: {'✅ ENABLED' if config['enabled'] else '❌ DISABLED'}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='toggle_farewell')
    @commands.has_permissions(administrator=True)
    async def toggle_farewell(self, ctx):
        """Toggle farewell messages"""
        config = self.get_welcome_config(ctx.guild.id)
        config["farewell_enabled"] = not config.get("farewell_enabled", False)
        self.save_welcome_config(ctx.guild.id, config)
        
        embed = discord.Embed(
            title="✅ Farewell System Updated",
            description=f"Farewell messages: {'✅ ENABLED' if config['farewell_enabled'] else '❌ DISABLED'}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeFarewellSystem(bot))
