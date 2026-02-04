"""
Virtual Currency System - In-game economy, wallet management, transactions
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

class CurrencySystem(commands.Cog):
    """Virtual currency, wallets, and economy"""
    
    # Create currency command group
    currency_group = app_commands.Group(name="currency", description="Wallet and currency management")
    
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = "💰 Coins"
        self.data_file = 'data/currency.json'
        self.load_data()
    
    def load_data(self):
        """Load currency data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}
    
    def save_data(self):
        """Save currency data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_balance(self, user_id: int) -> int:
        """Get user balance"""
        user_key = str(user_id)
        if user_key not in self.data:
            self.data[user_key] = {'balance': 100, 'daily_claimed': None}
        return self.data[user_key]['balance']
    
    def add_balance(self, user_id: int, amount: int):
        """Add coins to user"""
        user_key = str(user_id)
        if user_key not in self.data:
            self.data[user_key] = {'balance': 0, 'daily_claimed': None}
        self.data[user_key]['balance'] += amount
        self.save_data()
    
    def remove_balance(self, user_id: int, amount: int) -> bool:
        """Remove coins (check balance first)"""
        if self.get_balance(user_id) < amount:
            return False
        user_key = str(user_id)
        self.data[user_key]['balance'] -= amount
        self.save_data()
        return True
    
    @currency_group.command(name="balance", description="Check coin balance")
    @app_commands.describe(member="Member to check balance for")
    async def balance(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Check coin balance"""
        member = member or interaction.user
        balance = self.get_balance(member.id)
        
        embed = discord.Embed(
            title=f"💰 {member.name}'s Wallet",
            description=f"**Balance:** {balance:,} Coins",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    
    @currency_group.command(name="daily", description="Claim daily coins")
    async def daily_coins(self, interaction: discord.Interaction):
        """Claim daily coins"""
        user_key = str(interaction.user.id)
        if user_key not in self.data:
            self.data[user_key] = {'balance': 100, 'daily_claimed': None}
        
        user_data = self.data[user_key]
        last_claim = user_data.get('daily_claimed')
        
        # Check if already claimed today
        if last_claim:
            last_claim_dt = datetime.fromisoformat(last_claim)
            if (get_now_pst() - last_claim_dt).days < 1:
                time_left = timedelta(days=1) - (get_now_pst() - last_claim_dt)
                hours = int(time_left.total_seconds() // 3600)
                await interaction.response.send_message(f"❌ Already claimed! Come back in {hours}h", ephemeral=True)
                return
        
        # Award daily coins
        daily_amount = 100
        self.add_balance(interaction.user.id, daily_amount)
        user_data['daily_claimed'] = get_now_pst().isoformat()
        self.save_data()
        
        embed = discord.Embed(
            title="💰 Daily Coins Claimed!",
            description=f"You got **+{daily_amount}** coins!",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="New Balance", value=f"{self.get_balance(interaction.user.id):,} coins", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @currency_group.command(name="pay", description="Send coins to another member")
    @app_commands.describe(
        member="Member to send coins to",
        amount="Amount of coins to send"
    )
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Send coins to another member"""
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't send coins to yourself", ephemeral=True)
            return
        
        if amount < 1:
            await interaction.response.send_message("❌ Amount must be at least 1 coin", ephemeral=True)
            return
        
        if not self.remove_balance(interaction.user.id, amount):
            await interaction.response.send_message(f"❌ Insufficient balance! You only have {self.get_balance(interaction.user.id):,} coins", ephemeral=True)
            return
        
        self.add_balance(member.id, amount)
        
        embed = discord.Embed(
            title="💸 Coins Transferred",
            description=f"{interaction.user.mention} sent {amount:,} coins to {member.mention}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name=f"{interaction.user.name}'s Balance", value=f"{self.get_balance(interaction.user.id):,}", inline=True)
        embed.add_field(name=f"{member.name}'s Balance", value=f"{self.get_balance(member.id):,}", inline=True)
        await interaction.response.send_message(embed=embed)
    
    @currency_group.command(name="richlist", description="Top richest members")
    async def richlist(self, interaction: discord.Interaction):
        """Top richest members"""
        sorted_users = sorted(
            self.data.items(),
            key=lambda x: x[1].get('balance', 0),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="💰 Richest Members",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        richlist_text = ""
        for idx, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                balance = data.get('balance', 0)
                richlist_text += f"{idx}. **{user.name}** - {balance:,} coins\n"
            except:
                pass
        
        embed.description = richlist_text or "No data yet"
        await interaction.response.send_message(embed=embed)
    
    @currency_group.command(name="give", description="[Admin] Give coins to a member")
    @app_commands.describe(
        member="Member to give coins to",
        amount="Amount of coins to give"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """[Admin] Give coins to a member"""
        if amount < 0:
            await interaction.response.send_message("❌ Amount must be positive", ephemeral=True)
            return
        
        self.add_balance(member.id, amount)
        
        embed = discord.Embed(
            title="💰 Coins Awarded",
            description=f"{interaction.user.mention} gave {amount:,} coins to {member.mention}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CurrencySystem(bot))
