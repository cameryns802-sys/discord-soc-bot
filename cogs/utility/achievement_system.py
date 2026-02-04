"""
Achievement System - Unlock achievements for milestones and actions
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class AchievementSystem(commands.Cog):
    """Track and award achievements for member activities"""
    
    achievement_group = app_commands.Group(name="achievement", description="Achievement tracking and viewing")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/achievements.json'
        self.load_data()
        self.define_achievements()
    
    def load_data(self):
        """Load achievement data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.user_achievements = json.load(f)
        else:
            self.user_achievements = {}
    
    def save_data(self):
        """Save achievement data"""
        with open(self.data_file, 'w') as f:
            json.dump(self.user_achievements, f, indent=2)
    
    def define_achievements(self):
        """Define all available achievements"""
        self.achievements = {
            # Social achievements
            'first_message': {'name': 'First Steps', 'description': 'Send your first message', 'emoji': '👋', 'reward_coins': 50},
            'messages_100': {'name': 'Chatterbox', 'description': 'Send 100 messages', 'emoji': '💬', 'reward_coins': 100},
            'messages_1000': {'name': 'Conversation Master', 'description': 'Send 1,000 messages', 'emoji': '🗣️', 'reward_coins': 500},
            
            # Level achievements
            'level_5': {'name': 'Rising Star', 'description': 'Reach level 5', 'emoji': '⭐', 'reward_coins': 100},
            'level_10': {'name': 'Dedicated Member', 'description': 'Reach level 10', 'emoji': '🌟', 'reward_coins': 250},
            'level_25': {'name': 'Veteran', 'description': 'Reach level 25', 'emoji': '👑', 'reward_coins': 1000},
            
            # Reputation achievements
            'rep_10': {'name': 'Helpful', 'description': 'Earn 10 reputation', 'emoji': '🤝', 'reward_coins': 100},
            'rep_50': {'name': 'Community Hero', 'description': 'Earn 50 reputation', 'emoji': '🦸', 'reward_coins': 500},
            'rep_100': {'name': 'Legend', 'description': 'Earn 100 reputation', 'emoji': '🏆', 'reward_coins': 1500},
            
            # Currency achievements
            'coins_1000': {'name': 'Penny Saver', 'description': 'Accumulate 1,000 coins', 'emoji': '💰', 'reward_coins': 200},
            'coins_10000': {'name': 'Wealthy', 'description': 'Accumulate 10,000 coins', 'emoji': '💎', 'reward_coins': 1000},
            
            # Special achievements
            'early_bird': {'name': 'Early Bird', 'description': 'Be one of the first 100 members', 'emoji': '🐦', 'reward_coins': 500},
            'giveaway_winner': {'name': 'Lucky Winner', 'description': 'Win a giveaway', 'emoji': '🎁', 'reward_coins': 100},
            'daily_streak_7': {'name': 'Consistent', 'description': 'Claim daily reward 7 days in a row', 'emoji': '📅', 'reward_coins': 300},
            'daily_streak_30': {'name': 'Dedicated', 'description': 'Claim daily reward 30 days in a row', 'emoji': '🔥', 'reward_coins': 2000},
        }
    
    def get_user_achievements(self, user_id):
        """Get user's unlocked achievements"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_achievements:
            self.user_achievements[user_id_str] = {
                'unlocked': [],
                'progress': {}
            }
        return self.user_achievements[user_id_str]
    
    async def unlock_achievement(self, user_id, achievement_id, channel=None):
        """Unlock achievement for user"""
        user_data = self.get_user_achievements(user_id)
        
        # Check if already unlocked
        if achievement_id in user_data['unlocked']:
            return False
        
        # Unlock achievement
        user_data['unlocked'].append(achievement_id)
        self.save_data()
        
        achievement = self.achievements[achievement_id]
        
        # Award coins
        currency_cog = self.bot.get_cog('CurrencySystem')
        if currency_cog and achievement['reward_coins'] > 0:
            currency_cog.add_balance(user_id, achievement['reward_coins'])
        
        # Announce in channel
        if channel:
            try:
                user = await self.bot.fetch_user(user_id)
                embed = discord.Embed(
                    title="🏆 Achievement Unlocked!",
                    description=f"{user.mention} unlocked **{achievement['name']}**",
                    color=discord.Color.gold(),
                    timestamp=get_now_pst()
                )
                
                embed.add_field(name="Description", value=achievement['description'], inline=False)
                embed.add_field(name="Reward", value=f"💰 {achievement['reward_coins']} coins", inline=False)
                embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
                
                await channel.send(embed=embed, delete_after=30)
            except:
                pass
        
        return True
    
    async def check_achievements(self, user_id, channel=None):
        """Check and unlock eligible achievements"""
        # Get user data from other cogs
        rep_cog = self.bot.get_cog('ReputationSystem')
        currency_cog = self.bot.get_cog('CurrencySystem')
        
        if not rep_cog:
            return
        
        member_data = rep_cog.get_member_data(user_id)
        
        # Check message achievements
        messages = member_data.get('messages', 0)
        if messages >= 1:
            await self.unlock_achievement(user_id, 'first_message', channel)
        if messages >= 100:
            await self.unlock_achievement(user_id, 'messages_100', channel)
        if messages >= 1000:
            await self.unlock_achievement(user_id, 'messages_1000', channel)
        
        # Check level achievements
        level = member_data.get('level', 1)
        if level >= 5:
            await self.unlock_achievement(user_id, 'level_5', channel)
        if level >= 10:
            await self.unlock_achievement(user_id, 'level_10', channel)
        if level >= 25:
            await self.unlock_achievement(user_id, 'level_25', channel)
        
        # Check reputation achievements
        reputation = member_data.get('reputation', 0)
        if reputation >= 10:
            await self.unlock_achievement(user_id, 'rep_10', channel)
        if reputation >= 50:
            await self.unlock_achievement(user_id, 'rep_50', channel)
        if reputation >= 100:
            await self.unlock_achievement(user_id, 'rep_100', channel)
        
        # Check currency achievements
        if currency_cog:
            balance = currency_cog.get_balance(user_id)
            if balance >= 1000:
                await self.unlock_achievement(user_id, 'coins_1000', channel)
            if balance >= 10000:
                await self.unlock_achievement(user_id, 'coins_10000', channel)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check achievements on message"""
        if message.author.bot or not message.guild:
            return
        
        await self.check_achievements(message.author.id, message.channel)
    
    @achievement_group.command(name="view", description="View unlocked achievements")
    @app_commands.describe(member="Member to view achievements for")
    async def achievements_cmd(self, interaction: discord.Interaction, member: discord.Member = None):
        """View unlocked achievements"""
        if not member:
            member = interaction.user
        
        user_data = self.get_user_achievements(member.id)
        unlocked = user_data['unlocked']
        
        total_achievements = len(self.achievements)
        unlocked_count = len(unlocked)
        
        embed = discord.Embed(
            title=f"🏆 {member.name}'s Achievements",
            description=f"Unlocked {unlocked_count}/{total_achievements} achievements",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        # Show unlocked achievements
        if unlocked:
            unlocked_text = []
            for ach_id in unlocked[:10]:
                ach = self.achievements[ach_id]
                unlocked_text.append(f"{ach['emoji']} **{ach['name']}** - {ach['description']}")
            
            embed.add_field(
                name="✅ Unlocked",
                value="\n".join(unlocked_text) if unlocked_text else "None yet",
                inline=False
            )
        
        # Show locked achievements (next 5)
        locked = [aid for aid in self.achievements.keys() if aid not in unlocked]
        if locked:
            locked_text = []
            for ach_id in locked[:5]:
                ach = self.achievements[ach_id]
                locked_text.append(f"🔒 **{ach['name']}** - {ach['description']}")
            
            embed.add_field(
                name="🔒 Locked (Next 5)",
                value="\n".join(locked_text),
                inline=False
            )
        
        # Progress bar
        progress_percent = (unlocked_count / total_achievements) * 100
        progress_bar = '█' * int(progress_percent / 10) + '░' * (10 - int(progress_percent / 10))
        embed.add_field(
            name="Progress",
            value=f"`{progress_bar}` {progress_percent:.1f}%",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @achievement_group.command(name="list", description="View all available achievements")
    async def achievementlist_cmd(self, interaction: discord.Interaction):
        """View all available achievements"""
        embed = discord.Embed(
            title="🏆 All Achievements",
            description=f"Total: {len(self.achievements)} achievements",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        # Group by category
        categories = {
            'Social': ['first_message', 'messages_100', 'messages_1000'],
            'Leveling': ['level_5', 'level_10', 'level_25'],
            'Reputation': ['rep_10', 'rep_50', 'rep_100'],
            'Wealth': ['coins_1000', 'coins_10000'],
            'Special': ['early_bird', 'giveaway_winner', 'daily_streak_7', 'daily_streak_30']
        }
        
        for category, ach_ids in categories.items():
            text = []
            for ach_id in ach_ids:
                if ach_id in self.achievements:
                    ach = self.achievements[ach_id]
                    text.append(f"{ach['emoji']} **{ach['name']}** - {ach['description']} (💰 {ach['reward_coins']})")
            
            if text:
                embed.add_field(
                    name=category,
                    value="\n".join(text),
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AchievementSystem(bot))
