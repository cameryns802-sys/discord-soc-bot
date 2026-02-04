"""
Marketplace/Shop System - Buy items, roles, and perks with currency
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class MarketplaceSystem(commands.Cog):
    # Create shop command group
    shop_group = app_commands.Group(name="shop", description="Marketplace shopping and inventory")
    
    """Virtual shop for items, roles, and perks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.shop_file = 'data/shop.json'
        self.purchases_file = 'data/purchases.json'
        self.load_data()
    
    def load_data(self):
        """Load shop and purchase data"""
        os.makedirs('data', exist_ok=True)
        
        # Load shop items
        if os.path.exists(self.shop_file):
            with open(self.shop_file, 'r') as f:
                self.shop_items = json.load(f)
        else:
            # Default shop items
            self.shop_items = {
                'roles': [
                    {'id': 'vip', 'name': 'VIP', 'price': 5000, 'role_name': 'VIP', 'description': 'VIP role with special perks'},
                    {'id': 'supporter', 'name': 'Supporter', 'price': 2500, 'role_name': 'Supporter', 'description': 'Support the server!'},
                ],
                'items': [
                    {'id': 'boost', 'name': 'XP Boost', 'price': 1000, 'duration_hours': 24, 'description': '2x XP for 24 hours'},
                    {'id': 'badge', 'name': 'Custom Badge', 'price': 3000, 'description': 'Get a custom badge on your profile'},
                ],
                'perks': [
                    {'id': 'color', 'name': 'Custom Color', 'price': 1500, 'description': 'Custom role color'},
                    {'id': 'nickname', 'name': 'Custom Nickname', 'price': 500, 'description': 'Change your nickname anytime'},
                ]
            }
            self.save_shop()
        
        # Load purchases
        if os.path.exists(self.purchases_file):
            with open(self.purchases_file, 'r') as f:
                self.purchases = json.load(f)
        else:
            self.purchases = {}
    
    def save_shop(self):
        """Save shop items"""
        with open(self.shop_file, 'w') as f:
            json.dump(self.shop_items, f, indent=2)
    
    def save_purchases(self):
        """Save purchase history"""
        with open(self.purchases_file, 'w') as f:
            json.dump(self.purchases, f, indent=2)
    
    def get_currency_cog(self):
        """Get currency system cog"""
        return self.bot.get_cog('CurrencySystem')
    
    @shop_group.command(name="view", description="View the marketplace shop")
    @app_commands.describe(category="Category to view (roles, items, perks)")
    async def shop_cmd(self, interaction: discord.Interaction, category: str = None):
        """View the marketplace shop"""
        if not category:
            embed = discord.Embed(
                title="🛍️ Marketplace",
                description="Browse items available for purchase with coins",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(
                name="Categories",
                value="• `/shop roles` - Purchasable roles\n• `/shop items` - Consumable items\n• `/shop perks` - Special perks",
                inline=False
            )
            
            embed.add_field(
                name="How to Buy",
                value="Use `/buy <item_id>` to purchase",
                inline=False
            )
            
            embed.set_footer(text="Use /balance to check your coins")
            
            await interaction.response.send_message(embed=embed)
            return
        
        category = category.lower()
        
        if category not in self.shop_items:
            await interaction.response.send_message("❌ Invalid category. Use: roles, items, perks", ephemeral=True)
            return
        
        items = self.shop_items[category]
        
        embed = discord.Embed(
            title=f"🛍️ Shop - {category.title()}",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        if not items:
            embed.description = "No items available in this category"
        else:
            for item in items:
                value = f"**Price:** 💰 {item['price']} coins\n{item['description']}"
                if 'duration_hours' in item:
                    value += f"\n**Duration:** {item['duration_hours']}h"
                
                embed.add_field(
                    name=f"{item['name']} (`{item['id']}`)",
                    value=value,
                    inline=False
                )
        
        embed.set_footer(text="Use /buy <item_id> to purchase")
        
        await interaction.response.send_message(embed=embed)
    
    @shop_group.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item_id="The ID of the item to purchase")
    async def buy_cmd(self, interaction: discord.Interaction, item_id: str):
        """Buy an item from the shop"""
        currency_cog = self.get_currency_cog()
        
        if not currency_cog:
            await interaction.response.send_message("❌ Currency system not available", ephemeral=True)
            return
        
        # Find item
        item = None
        item_category = None
        
        for category, items in self.shop_items.items():
            for shop_item in items:
                if shop_item['id'] == item_id:
                    item = shop_item
                    item_category = category
                    break
            if item:
                break
        
        if not item:
            await interaction.response.send_message("❌ Item not found. Use `/shop` to see available items", ephemeral=True)
            return
        
        # Check balance
        balance = currency_cog.get_balance(interaction.user.id)
        
        if balance < item['price']:
            await interaction.response.send_message(f"❌ Not enough coins! You need 💰 {item['price']} coins but have 💰 {balance}", ephemeral=True)
            return
        
        # Process purchase based on category
        if item_category == 'roles':
            # Give role
            role = discord.utils.get(interaction.guild.roles, name=item['role_name'])
            
            if not role:
                await interaction.response.send_message(f"❌ Role `{item['role_name']}` not found. Contact an admin.", ephemeral=True)
                return
            
            if role in interaction.user.roles:
                await interaction.response.send_message(f"❌ You already have the {role.mention} role!", ephemeral=True)
                return
            
            try:
                await interaction.user.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to assign roles", ephemeral=True)
                return
        
        # Deduct coins
        currency_cog.remove_balance(interaction.user.id, item['price'])
        
        # Record purchase
        user_id_str = str(interaction.user.id)
        if user_id_str not in self.purchases:
            self.purchases[user_id_str] = []
        
        self.purchases[user_id_str].append({
            'item_id': item_id,
            'item_name': item['name'],
            'price': item['price'],
            'category': item_category,
            'timestamp': get_now_pst().isoformat()
        })
        
        self.save_purchases()
        
        # Success message
        embed = discord.Embed(
            title="✅ Purchase Complete!",
            description=f"You bought **{item['name']}**",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Price", value=f"💰 {item['price']} coins", inline=True)
        embed.add_field(name="New Balance", value=f"💰 {currency_cog.get_balance(interaction.user.id)} coins", inline=True)
        
        if item_category == 'roles':
            embed.add_field(name="Role Assigned", value=f"{role.mention}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @shop_group.command(name="inventory", description="View purchase history and inventory")
    @app_commands.describe(member="Member to view inventory for")
    async def inventory_cmd(self, interaction: discord.Interaction, member: discord.Member = None):
        """View purchase history / inventory"""
        if not member:
            member = interaction.user
        
        user_id_str = str(member.id)
        
        if user_id_str not in self.purchases or not self.purchases[user_id_str]:
            await interaction.response.send_message(f"📦 {member.mention} has no purchase history")
            return
        
        purchases = self.purchases[user_id_str]
        
        embed = discord.Embed(
            title=f"📦 {member.name}'s Inventory",
            description=f"Total purchases: {len(purchases)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Group by category
        by_category = {}
        for purchase in purchases:
            cat = purchase['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(purchase)
        
        for category, items in by_category.items():
            value = "\n".join([f"• {p['item_name']} (💰 {p['price']})" for p in items[:5]])
            if len(items) > 5:
                value += f"\n...and {len(items) - 5} more"
            
            embed.add_field(
                name=f"{category.title()} ({len(items)})",
                value=value,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @shop_group.command(name="additem", description="Add item to shop (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        category="Category (roles, items, perks)",
        item_id="Unique ID for the item",
        price="Price in coins",
        name="Display name for the item"
    )
    async def additem_cmd(self, interaction: discord.Interaction, category: str, item_id: str, price: int, name: str):
        """Add item to shop (Admin only)"""
        category = category.lower()
        
        if category not in self.shop_items:
            await interaction.response.send_message("❌ Invalid category. Use: roles, items, perks", ephemeral=True)
            return
        
        # Check if ID exists
        for item in self.shop_items[category]:
            if item['id'] == item_id:
                await interaction.response.send_message(f"❌ Item ID `{item_id}` already exists", ephemeral=True)
                return
        
        # Add item
        new_item = {
            'id': item_id,
            'name': name,
            'price': price,
            'description': 'No description'
        }
        
        self.shop_items[category].append(new_item)
        self.save_shop()
        
        await interaction.response.send_message(f"✅ Added **{name}** to {category} shop for 💰 {price} coins")

async def setup(bot):
    await bot.add_cog(MarketplaceSystem(bot))
