"""
Reaction Roles System - Self-service role assignment via reactions
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ReactionRoles(commands.Cog):
    """Self-service role assignment with reactions"""
    
    # Define command group at class level
    reaction_group = app_commands.Group(name="reaction", description="Reaction role management")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/reaction_roles.json'
        self.load_data()
    
    def load_data(self):
        """Load reaction role data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.reaction_roles = json.load(f)
        else:
            self.reaction_roles = {}  # message_id: {emoji: role_id}
    
    def save_data(self):
        """Save reaction role data"""
        with open(self.data_file, 'w') as f:
            json.dump(self.reaction_roles, f, indent=2)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction added"""
        if payload.user_id == self.bot.user.id:
            return
        
        message_id = str(payload.message_id)
        
        if message_id not in self.reaction_roles:
            return
        
        emoji_str = str(payload.emoji)
        
        if emoji_str not in self.reaction_roles[message_id]:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role_id = self.reaction_roles[message_id][emoji_str]
        role = guild.get_role(role_id)
        
        if not role:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        try:
            await member.add_roles(role, reason="Reaction role")
        except discord.Forbidden:
            pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction removed"""
        if payload.user_id == self.bot.user.id:
            return
        
        message_id = str(payload.message_id)
        
        if message_id not in self.reaction_roles:
            return
        
        emoji_str = str(payload.emoji)
        
        if emoji_str not in self.reaction_roles[message_id]:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role_id = self.reaction_roles[message_id][emoji_str]
        role = guild.get_role(role_id)
        
        if not role:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        try:
            await member.remove_roles(role, reason="Reaction role removed")
        except discord.Forbidden:
            pass
    
    @reaction_group.command(name="set", description="Set up reaction role on a message")
    @app_commands.describe(
        message_id="The ID of the message to add reaction role to",
        emoji="The emoji to react with",
        role="The role to assign"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_cmd(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        """Set up reaction role on a message"""
        # Validate message exists
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except:
            await interaction.response.send_message("❌ Message not found in this channel", ephemeral=True)
            return
        
        # Add to database
        message_id_str = str(message_id)
        
        if message_id_str not in self.reaction_roles:
            self.reaction_roles[message_id_str] = {}
        
        self.reaction_roles[message_id_str][emoji] = role.id
        self.save_data()
        
        # Add reaction to message
        try:
            await message.add_reaction(emoji)
        except:
            await interaction.response.send_message("❌ Invalid emoji or can't add reaction", ephemeral=True)
            return
        
        await interaction.response.send_message(f"✅ Reaction role set! React with {emoji} to get {role.mention}")
    
    @reaction_group.command(name="panel", description="Create a reaction role panel")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def createreactionpanel_cmd(self, interaction: discord.Interaction):
        """Create a reaction role panel"""
        embed = discord.Embed(
            title="🎭 Role Selection",
            description="React to get roles!\n\nClick the reactions below to assign yourself roles.",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="How to use",
            value="• Click a reaction to get the role\n• Click again to remove the role\n• You can have multiple roles",
            inline=False
        )
        
        embed.set_footer(text="Use /reactionrole to configure roles")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        await interaction.followup.send(f"✅ Panel created! Message ID: `{message.id}`\nUse `/reaction set {message.id} <emoji> <@role>` to add roles", ephemeral=True)
    
    @reaction_group.command(name="remove", description="Remove a reaction role")
    @app_commands.describe(
        message_id="The message ID with the reaction role",
        emoji="The emoji to remove"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def removereactionrole_cmd(self, interaction: discord.Interaction, message_id: str, emoji: str):
        """Remove a reaction role"""
        message_id_str = str(message_id)
        
        if message_id_str not in self.reaction_roles:
            await interaction.response.send_message("❌ No reaction roles on that message", ephemeral=True)
            return
        
        if emoji not in self.reaction_roles[message_id_str]:
            await interaction.response.send_message("❌ That emoji is not set up on that message", ephemeral=True)
            return
        
        del self.reaction_roles[message_id_str][emoji]
        
        if not self.reaction_roles[message_id_str]:
            del self.reaction_roles[message_id_str]
        
        self.save_data()
        
        await interaction.response.send_message(f"✅ Removed reaction role for {emoji}")
    
    @reaction_group.command(name="list", description="List all reaction role setups")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def listreactionroles_cmd(self, interaction: discord.Interaction):
        """List all reaction role setups"""
        if not self.reaction_roles:
            await interaction.response.send_message("❌ No reaction roles configured")
            return
        
        embed = discord.Embed(
            title="🎭 Reaction Roles",
            description="All configured reaction roles",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for message_id, roles in self.reaction_roles.items():
            role_list = []
            for emoji, role_id in roles.items():
                role = interaction.guild.get_role(role_id)
                role_name = role.name if role else "Deleted Role"
                role_list.append(f"{emoji} → {role_name}")
            
            embed.add_field(
                name=f"Message ID: {message_id}",
                value="\n".join(role_list) if role_list else "No roles",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
