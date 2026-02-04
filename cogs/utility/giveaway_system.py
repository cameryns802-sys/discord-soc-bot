"""
Giveaway System - Create and manage server giveaways
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

class GiveawaySystem(commands.Cog):
    """Create, manage, and run giveaways"""
    
    giveaway_group = app_commands.Group(name="giveaway", description="Giveaway management and creation")
    
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}
        self.data_file = 'data/giveaways.json'
        self.load_data()
    
    def load_data(self):
        """Load giveaway data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.giveaways = json.load(f)
            except:
                self.giveaways = {}
    
    def save_data(self):
        """Save giveaway data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.giveaways, f, indent=2)
    
    @giveaway_group.command(name="create", description="Create a giveaway")
    @app_commands.describe(
        duration="Duration (e.g., 1h, 30m, 1d)",
        winners="Number of winners (1-10)",
        prize="The prize to give away"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_giveaway(self, interaction: discord.Interaction, duration: str, winners: int = 1, prize: str = "Mystery Prize"):
        """
        Create a giveaway
        Durations: 10s, 1m, 1h, 1d
        """
        # Parse duration
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            amount = int(duration[:-1])
            unit = duration[-1].lower()
            if unit not in duration_map:
                raise ValueError
            seconds = amount * duration_map[unit]
        except:
            await interaction.response.send_message("❌ Invalid duration. Use format: 1h, 30m, 1d, etc.", ephemeral=True)
            return
        
        if winners < 1 or winners > 10:
            await interaction.response.send_message("❌ Winners must be between 1 and 10", ephemeral=True)
            return
        
        giveaway_id = f"{interaction.guild.id}_{interaction.id}"
        end_time = (get_now_pst() + timedelta(seconds=seconds)).isoformat()
        
        self.giveaways[giveaway_id] = {
            'guild_id': interaction.guild.id,
            'channel_id': interaction.channel.id,
            'message_id': None,
            'prize': prize,
            'winners': winners,
            'participants': [],
            'end_time': end_time,
            'ended': False
        }
        
        # Create giveaway embed
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Ends", value=f"<t:{int((datetime.fromisoformat(end_time)).timestamp())}:R>", inline=True)
        embed.add_field(name="React with 🎁 to enter!", value="Only one entry per person", inline=False)
        embed.set_footer(text=f"ID: {giveaway_id}")
        
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🎁")
        
        self.giveaways[giveaway_id]['message_id'] = msg.id
        self.save_data()
        
        await interaction.followup.send(f"✅ Giveaway created! Ends in {duration}", ephemeral=True)
    
    @giveaway_group.command(name="end", description="End a giveaway and pick winners")
    @app_commands.describe(giveaway_id="The ID of the giveaway to end")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_giveaway(self, interaction: discord.Interaction, giveaway_id: str):
        """End a giveaway and pick winners"""
        if giveaway_id not in self.giveaways:
            await interaction.response.send_message("❌ Giveaway not found", ephemeral=True)
            return
        
        giveaway = self.giveaways[giveaway_id]
        
        if not giveaway['participants']:
            await interaction.response.send_message("❌ No participants in this giveaway", ephemeral=True)
            return
        
        # Pick winners
        winners = random.sample(giveaway['participants'], min(giveaway['winners'], len(giveaway['participants'])))
        giveaway['ended'] = True
        self.save_data()
        
        # Announce winners
        winner_mentions = ", ".join([f"<@{w}>" for w in winners])
        embed = discord.Embed(
            title="🎉 GIVEAWAY ENDED 🎉",
            description=f"**Prize:** {giveaway['prize']}\n**Winner(s):** {winner_mentions}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Participants", value=str(len(giveaway['participants'])), inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # DM winners
        for winner_id in winners:
            try:
                user = await self.bot.fetch_user(winner_id)
                embed = discord.Embed(
                    title="🎉 You Won!",
                    description=f"Congratulations! You won **{giveaway['prize']}** in {interaction.guild.name}",
                    color=discord.Color.gold()
                )
                await user.send(embed=embed)
            except:
                pass
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle giveaway reactions"""
        if user.bot or reaction.emoji != "🎁":
            return
        
        # Find matching giveaway
        for giveaway_id, giveaway in self.giveaways.items():
            if (giveaway['message_id'] == reaction.message.id and 
                giveaway['channel_id'] == reaction.message.channel.id and
                not giveaway['ended']):
                
                if user.id not in giveaway['participants']:
                    giveaway['participants'].append(user.id)
                    self.save_data()
                break
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle reaction removal"""
        if user.bot or reaction.emoji != "🎁":
            return
        
        for giveaway_id, giveaway in self.giveaways.items():
            if (giveaway['message_id'] == reaction.message.id and 
                user.id in giveaway['participants']):
                giveaway['participants'].remove(user.id)
                self.save_data()
                break
    
    @giveaway_group.command(name="list", description="List active giveaways")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_giveaways(self, interaction: discord.Interaction):
        """List active giveaways"""
        active = [g for g in self.giveaways.values() 
                 if g['guild_id'] == interaction.guild.id and not g['ended']]
        
        if not active:
            await interaction.response.send_message("No active giveaways")
            return
        
        embed = discord.Embed(
            title="🎉 Active Giveaways",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        for g in active:
            end_time = datetime.fromisoformat(g['end_time'])
            time_left = (end_time - get_now_pst()).total_seconds()
            
            if time_left > 0:
                embed.add_field(
                    name=g['prize'],
                    value=f"👥 {len(g['participants'])} | ⏰ {int(time_left//3600)}h left",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
