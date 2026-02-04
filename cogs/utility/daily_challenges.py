"""
Daily Challenges System - Complete daily tasks for bonus rewards
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import random
from cogs.core.pst_timezone import get_now_pst

class DailyChallenges(commands.Cog):
    """Daily challenges and tasks for bonus rewards"""
    
    challenge_group = app_commands.Group(name="challenge", description="Daily challenges and tasks")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/daily_challenges.json'
        self.load_data()
        self.define_challenges()
        self.check_daily_reset.start()
    
    def load_data(self):
        """Load challenge data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.active_challenges = data.get('active_challenges', {})
                self.user_progress = data.get('user_progress', {})
                self.last_reset = data.get('last_reset', get_now_pst().date().isoformat())
        else:
            self.active_challenges = {}  # guild_id: [challenge_ids]
            self.user_progress = {}  # user_id: {challenge_id: progress}
            self.last_reset = get_now_pst().date().isoformat()
    
    def save_data(self):
        """Save challenge data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'active_challenges': self.active_challenges,
                'user_progress': self.user_progress,
                'last_reset': self.last_reset
            }, f, indent=2)
    
    def define_challenges(self):
        """Define all possible challenges"""
        self.challenges = {
            'send_10_messages': {
                'name': 'Chatterbox',
                'description': 'Send 10 messages',
                'target': 10,
                'reward_coins': 100,
                'reward_xp': 50,
                'emoji': '💬'
            },
            'send_50_messages': {
                'name': 'Super Active',
                'description': 'Send 50 messages',
                'target': 50,
                'reward_coins': 500,
                'reward_xp': 200,
                'emoji': '🗣️'
            },
            'give_5_rep': {
                'name': 'Generous',
                'description': 'Give reputation 5 times',
                'target': 5,
                'reward_coins': 200,
                'reward_xp': 100,
                'emoji': '⭐'
            },
            'react_20_times': {
                'name': 'Reactor',
                'description': 'React to 20 messages',
                'target': 20,
                'reward_coins': 150,
                'reward_xp': 75,
                'emoji': '👍'
            },
            'spend_1000_coins': {
                'name': 'Big Spender',
                'description': 'Spend 1,000 coins',
                'target': 1000,
                'reward_coins': 500,
                'reward_xp': 150,
                'emoji': '💰'
            },
            'help_member': {
                'name': 'Helpful',
                'description': 'Help 3 members (react with ✅ to their questions)',
                'target': 3,
                'reward_coins': 300,
                'reward_xp': 100,
                'emoji': '🤝'
            }
        }
    
    @tasks.loop(hours=1)
    async def check_daily_reset(self):
        """Check if we need to reset daily challenges"""
        current_date = get_now_pst().date().isoformat()
        
        if current_date != self.last_reset:
            # Reset all challenges
            self.user_progress = {}
            self.last_reset = current_date
            
            # Generate new random challenges for each guild
            for guild_id in self.active_challenges.keys():
                self.active_challenges[guild_id] = self.generate_daily_challenges()
            
            self.save_data()
    
    def generate_daily_challenges(self):
        """Generate 3 random daily challenges"""
        return random.sample(list(self.challenges.keys()), min(3, len(self.challenges)))
    
    def get_user_progress(self, user_id):
        """Get user's challenge progress"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_progress:
            self.user_progress[user_id_str] = {}
        return self.user_progress[user_id_str]
    
    def update_progress(self, user_id, challenge_id, amount=1):
        """Update user progress on a challenge"""
        progress = self.get_user_progress(user_id)
        
        if challenge_id not in progress:
            progress[challenge_id] = 0
        
        progress[challenge_id] += amount
        self.save_data()
        
        return progress[challenge_id]
    
    async def check_completion(self, user_id, challenge_id, channel=None):
        """Check if challenge is completed and award rewards"""
        progress = self.get_user_progress(user_id)
        
        if challenge_id not in progress:
            return False
        
        challenge = self.challenges[challenge_id]
        
        if progress[challenge_id] >= challenge['target']:
            # Check if already rewarded
            if progress[challenge_id] == challenge['target']:
                # Award rewards
                currency_cog = self.bot.get_cog('CurrencySystem')
                rep_cog = self.bot.get_cog('ReputationSystem')
                
                if currency_cog:
                    currency_cog.add_balance(user_id, challenge['reward_coins'])
                
                if rep_cog:
                    rep_cog.add_xp(user_id, challenge['reward_xp'])
                
                # Mark as rewarded
                progress[challenge_id] = challenge['target'] + 1
                self.save_data()
                
                # Announce completion
                if channel:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        embed = discord.Embed(
                            title="✅ Challenge Complete!",
                            description=f"{user.mention} completed **{challenge['name']}**",
                            color=discord.Color.green(),
                            timestamp=get_now_pst()
                        )
                        
                        embed.add_field(
                            name="Rewards",
                            value=f"💰 {challenge['reward_coins']} coins\n⚡ {challenge['reward_xp']} XP",
                            inline=False
                        )
                        
                        await channel.send(embed=embed, delete_after=30)
                    except:
                        pass
                
                return True
        
        return False
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track message-based challenges"""
        if message.author.bot or not message.guild:
            return
        
        guild_id_str = str(message.guild.id)
        
        if guild_id_str not in self.active_challenges:
            self.active_challenges[guild_id_str] = self.generate_daily_challenges()
            self.save_data()
        
        active = self.active_challenges[guild_id_str]
        
        # Update message challenges
        if 'send_10_messages' in active:
            self.update_progress(message.author.id, 'send_10_messages')
            await self.check_completion(message.author.id, 'send_10_messages', message.channel)
        
        if 'send_50_messages' in active:
            self.update_progress(message.author.id, 'send_50_messages')
            await self.check_completion(message.author.id, 'send_50_messages', message.channel)
    
    @challenge_group.command(name="list", description="View today's daily challenges")
    async def challenges_cmd(self, interaction: discord.Interaction):
        """View today's daily challenges"""
        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.active_challenges:
            self.active_challenges[guild_id_str] = self.generate_daily_challenges()
            self.save_data()
        
        active_challenges = self.active_challenges[guild_id_str]
        user_progress = self.get_user_progress(interaction.user.id)
        
        embed = discord.Embed(
            title="📋 Today's Daily Challenges",
            description="Complete challenges for bonus rewards!",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for challenge_id in active_challenges:
            challenge = self.challenges[challenge_id]
            progress = user_progress.get(challenge_id, 0)
            
            # Cap progress display at target
            display_progress = min(progress, challenge['target'])
            
            status = "✅ COMPLETE" if progress >= challenge['target'] else f"{display_progress}/{challenge['target']}"
            
            embed.add_field(
                name=f"{challenge['emoji']} {challenge['name']}",
                value=f"**{challenge['description']}**\nProgress: {status}\nRewards: 💰 {challenge['reward_coins']} coins, ⚡ {challenge['reward_xp']} XP",
                inline=False
            )
        
        # Calculate time until reset
        now = get_now_pst()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_left = tomorrow - now
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        embed.set_footer(text=f"Resets in {hours}h {minutes}m")
        
        await interaction.response.send_message(embed=embed)
    
    @challenge_group.command(name="stats", description="View challenge completion statistics")
    @app_commands.describe(member="Member to view stats for")
    async def challengestats_cmd(self, interaction: discord.Interaction, member: discord.Member = None):
        """View challenge completion statistics"""
        if not member:
            member = interaction.user
        
        user_progress = self.get_user_progress(member.id)
        
        completed_today = sum(1 for chal_id, prog in user_progress.items() 
                             if chal_id in self.challenges and prog >= self.challenges[chal_id]['target'])
        
        embed = discord.Embed(
            title=f"📊 {member.name}'s Challenge Stats",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Today",
            value=f"✅ {completed_today}/3 challenges completed",
            inline=False
        )
        
        if user_progress:
            progress_text = []
            for chal_id, prog in user_progress.items():
                if chal_id in self.challenges:
                    challenge = self.challenges[chal_id]
                    display_prog = min(prog, challenge['target'])
                    progress_text.append(f"{challenge['emoji']} {challenge['name']}: {display_prog}/{challenge['target']}")
            
            if progress_text:
                embed.add_field(
                    name="Current Progress",
                    value="\n".join(progress_text[:5]),
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyChallenges(bot))
