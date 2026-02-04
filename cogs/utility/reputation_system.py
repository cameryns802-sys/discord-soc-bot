"""
Reputation & XP System - Gamification through leveling and badges
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

class ReputationSystem(commands.Cog):
    """Member reputation, XP, levels, and leaderboards"""
    
    # Define command groups at class level
    rep_group = app_commands.Group(name="rep", description="Reputation management")
    profile_group = app_commands.Group(name="profile", description="Profile management")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/reputation.json'
        self.load_data()
    
    def load_data(self):
        """Load reputation data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}
    
    def save_data(self):
        """Save reputation data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_member_data(self, user_id: int):
        """Get or create member data"""
        user_key = str(user_id)
        if user_key not in self.data:
            self.data[user_key] = {
                'xp': 0,
                'level': 1,
                'rep': 0,
                'badges': [],
                'messages': 0,
                'last_xp_time': None
            }
        return self.data[user_key]
    
    def add_xp(self, user_id: int, amount: int = 5):
        """Add XP to member (triggered by messages)"""
        member = self.get_member_data(user_id)
        
        # Cooldown: only get XP every 5 seconds
        if member['last_xp_time']:
            last_time = datetime.fromisoformat(member['last_xp_time'])
            if (get_now_pst() - last_time).seconds < 5:
                return False
        
        member['xp'] += amount
        member['messages'] += 1
        member['last_xp_time'] = get_now_pst().isoformat()
        
        # Level up calculation
        xp_needed = 100 + (member['level'] * 50)
        if member['xp'] >= xp_needed:
            member['level'] += 1
            member['xp'] = 0
            self.save_data()
            return True  # Leveled up
        
        self.save_data()
        return False
    
    def give_rep(self, giver_id: int, receiver_id: int, amount: int = 1):
        """Give reputation points"""
        receiver = self.get_member_data(receiver_id)
        receiver['rep'] += amount
        
        # Award badge if rep hits milestone
        if receiver['rep'] == 10:
            receiver['badges'].append('🌟 Reputable')
        elif receiver['rep'] == 50:
            receiver['badges'].append('⭐ Celebrity')
        elif receiver['rep'] == 100:
            receiver['badges'].append('👑 Legendary')
        
        self.save_data()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP on messages"""
        if message.author.bot or not message.guild:
            return
        
        leveled_up = self.add_xp(message.author.id)
        
        # Notify on level up
        if leveled_up:
            member = self.get_member_data(message.author.id)
            embed = discord.Embed(
                title=f"🎉 Level Up!",
                description=f"{message.author.mention} reached **Level {member['level']}**",
                color=discord.Color.gold(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Total XP", value=str(member['xp']), inline=True)
            embed.add_field(name="Reputation", value=f"⭐ {member['rep']}", inline=True)
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
    
    @rep_group.command(name="give", description="Give reputation to a member")
    @app_commands.describe(
        member="The member to give reputation to",
        amount="Amount of rep to give (1-10)"
    )
    async def give_rep_cmd(self, interaction: discord.Interaction, member: discord.Member, amount: int = 1):
        """Give reputation to a member"""
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't rep yourself!", ephemeral=True)
            return
        
        if amount < 1 or amount > 10:
            await interaction.response.send_message("❌ Rep amount must be between 1 and 10", ephemeral=True)
            return
        
        self.give_rep(interaction.user.id, member.id, amount)
        
        embed = discord.Embed(
            title="⭐ Reputation Given",
            description=f"{interaction.user.mention} gave {amount} rep to {member.mention}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        await interaction.response.send_message(embed=embed)
    
    @profile_group.command(name="view", description="View member profile with level and reputation")
    @app_commands.describe(member="Member to view profile for")
    async def profile_cmd(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """View member profile"""
        member = member or interaction.user
        data = self.get_member_data(member.id)
        
        embed = discord.Embed(
            title=f"📊 {member.name}'s Profile",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=f"**{data['level']}**", inline=True)
        embed.add_field(name="XP", value=f"{data['xp']} XP", inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {data['rep']}", inline=True)
        embed.add_field(name="Messages", value=str(data['messages']), inline=True)
        
        if data['badges']:
            embed.add_field(name="Badges", value=" ".join(data['badges']), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @profile_group.command(name="leaderboard", description="View server leaderboard")
    @app_commands.describe(sort_by="Sort by: level, rep, or messages")
    async def leaderboard_cmd(self, interaction: discord.Interaction, sort_by: str = 'level'):
        """View leaderboard"""
        if sort_by.lower() not in ['level', 'rep', 'messages']:
            await interaction.response.send_message("❌ Sort by: level, rep, or messages", ephemeral=True)
            return
        
        # Sort by chosen metric
        sorted_members = sorted(
            self.data.items(),
            key=lambda x: x[1].get(sort_by.lower(), 0),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title=f"🏆 Leaderboard (by {sort_by.title()})",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        leaderboard_text = ""
        for idx, (user_id, data) in enumerate(sorted_members, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                if sort_by.lower() == 'level':
                    value = f"Level {data['level']} ({data['xp']} XP)"
                elif sort_by.lower() == 'rep':
                    value = f"⭐ {data['rep']} Rep"
                else:
                    value = f"💬 {data['messages']} Messages"
                
                leaderboard_text += f"{idx}. **{user.name}** - {value}\n"
            except:
                pass
        
        embed.description = leaderboard_text or "No data yet"
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ReputationSystem(bot))
