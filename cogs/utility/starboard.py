"""
Starboard System - Highlight popular messages with star reactions
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class Starboard(commands.Cog):
    """Highlight popular community messages"""
    
    # Define command group at class level
    starboard_group = app_commands.Group(name="starboard", description="Starboard management")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/starboard.json'
        self.load_data()
    
    def load_data(self):
        """Load starboard data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.config = data.get('config', {})
                self.starred_messages = data.get('starred_messages', {})
        else:
            self.config = {}  # guild_id: {channel_id, threshold}
            self.starred_messages = {}  # message_id: starboard_message_id
    
    def save_data(self):
        """Save starboard data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'config': self.config,
                'starred_messages': self.starred_messages
            }, f, indent=2)
    
    def get_config(self, guild_id):
        """Get starboard config for guild"""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.config:
            self.config[guild_id_str] = {
                'channel_id': None,
                'threshold': 3,
                'emoji': '⭐'
            }
        return self.config[guild_id_str]
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle star reactions"""
        await self.handle_star_reaction(payload)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle star removal"""
        await self.handle_star_reaction(payload)
    
    async def handle_star_reaction(self, payload):
        """Process star reactions"""
        if payload.user_id == self.bot.user.id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        config = self.get_config(payload.guild_id)
        
        if not config['channel_id']:
            return
        
        # Check if reaction is star emoji
        if str(payload.emoji) != config['emoji']:
            return
        
        # Get channel and message
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except:
            return
        
        # Don't star bot messages or messages in starboard
        if message.author.bot or message.channel.id == config['channel_id']:
            return
        
        # Count stars
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == config['emoji']:
                star_count = reaction.count
                break
        
        message_id_str = str(message.id)
        
        # Check if message should be on starboard
        if star_count >= config['threshold']:
            await self.add_to_starboard(message, star_count, config)
        elif message_id_str in self.starred_messages:
            await self.update_starboard(message, star_count, config)
    
    async def add_to_starboard(self, message, star_count, config):
        """Add message to starboard"""
        message_id_str = str(message.id)
        
        # Check if already on starboard
        if message_id_str in self.starred_messages:
            await self.update_starboard(message, star_count, config)
            return
        
        starboard_channel = self.bot.get_channel(config['channel_id'])
        if not starboard_channel:
            return
        
        # Create embed
        embed = discord.Embed(
            description=message.content[:2000] if message.content else "*No text content*",
            color=discord.Color.gold(),
            timestamp=message.created_at
        )
        
        embed.set_author(
            name=message.author.name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )
        
        # Add image if present
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        embed.add_field(
            name="Source",
            value=f"[Jump to message]({message.jump_url})",
            inline=False
        )
        
        embed.set_footer(text=f"#{message.channel.name}")
        
        # Send to starboard
        try:
            starboard_msg = await starboard_channel.send(
                content=f"{config['emoji']} **{star_count}** | {message.channel.mention}",
                embed=embed
            )
            
            # Save mapping
            self.starred_messages[message_id_str] = starboard_msg.id
            self.save_data()
        except:
            pass
    
    async def update_starboard(self, message, star_count, config):
        """Update existing starboard entry"""
        message_id_str = str(message.id)
        
        if message_id_str not in self.starred_messages:
            return
        
        starboard_channel = self.bot.get_channel(config['channel_id'])
        if not starboard_channel:
            return
        
        starboard_msg_id = self.starred_messages[message_id_str]
        
        try:
            starboard_msg = await starboard_channel.fetch_message(starboard_msg_id)
            
            # Update star count
            await starboard_msg.edit(
                content=f"{config['emoji']} **{star_count}** | {message.channel.mention}"
            )
        except:
            # Message deleted, remove from tracking
            del self.starred_messages[message_id_str]
            self.save_data()
    
    @starboard_group.command(name="setup", description="Set up starboard channel and threshold")
    @app_commands.describe(
        channel="The channel to send starred messages to",
        threshold="Number of star reactions required (default: 3)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setstarboard_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel, threshold: int = 3):
        """Set up starboard channel and threshold"""
        guild_id_str = str(interaction.guild.id)
        
        self.config[guild_id_str] = {
            'channel_id': channel.id,
            'threshold': threshold,
            'emoji': '⭐'
        }
        
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Starboard Configured",
            description=f"Messages with {threshold}+ ⭐ reactions will appear in {channel.mention}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @starboard_group.command(name="stats", description="View starboard statistics")
    async def starboardstats_cmd(self, interaction: discord.Interaction):
        """View starboard statistics"""
        config = self.get_config(interaction.guild.id)
        
        if not config['channel_id']:
            await interaction.response.send_message("❌ Starboard not configured. Use `/setstarboard #channel`", ephemeral=True)
            return
        
        # Count starred messages
        starred_count = len([msg_id for msg_id in self.starred_messages.keys() 
                            if msg_id.startswith(str(interaction.guild.id))])
        
        embed = discord.Embed(
            title="⭐ Starboard Statistics",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        starboard_channel = interaction.guild.get_channel(config['channel_id'])
        
        embed.add_field(
            name="Channel",
            value=starboard_channel.mention if starboard_channel else "Not found",
            inline=True
        )
        
        embed.add_field(
            name="Threshold",
            value=f"{config['threshold']} {config['emoji']}",
            inline=True
        )
        
        embed.add_field(
            name="Starred Messages",
            value=str(starred_count),
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
