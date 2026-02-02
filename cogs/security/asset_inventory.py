"""Asset Inventory System: Consolidated command group"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os

class AssetGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="asset", description="Asset inventory commands")
        self.cog = cog

    @app_commands.command(name="add", description="Add asset to inventory")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def add(self, interaction: discord.Interaction, asset_type: str, name: str, owner: discord.Member = None):
        self.cog.asset_counter += 1
        asset_id = str(self.cog.asset_counter)
        self.cog.assets[asset_id] = {"id": asset_id, "type": asset_type, "name": name, "owner": owner.id if owner else interaction.user.id, "status": "active", "added_by": interaction.user.id, "added_at": datetime.utcnow().isoformat(), "last_audit": None}
        self.cog.save_data()
        embed = discord.Embed(title=f"📦 Asset #{asset_id} Added", description=name, color=discord.Color.green())
        embed.add_field(name="Type", value=asset_type, inline=True)
        embed.add_field(name="Owner", value=f"<@{owner.id if owner else interaction.user.id}>", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="List all assets")
    async def list(self, interaction: discord.Interaction, asset_type: str = None):
        if asset_type:
            assets = [a for a in self.cog.assets.values() if a['type'].lower() == asset_type.lower() and a['status'] == 'active']
        else:
            assets = [a for a in self.cog.assets.values() if a['status'] == 'active']
        
        if not assets:
            await interaction.response.send_message("ℹ️ No assets found", ephemeral=True)
            return
        
        embed = discord.Embed(title="📦 Asset Inventory", color=discord.Color.blue())
        for asset in assets[:20]:
            embed.add_field(name=f"#{asset['id']} - {asset['name']}", value=f"Type: {asset['type']}\nOwner: <@{asset['owner']}>", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="detail", description="View asset details")
    async def detail(self, interaction: discord.Interaction, asset_id: str):
        if asset_id not in self.cog.assets:
            await interaction.response.send_message("❌ Asset not found", ephemeral=True)
            return
        asset = self.cog.assets[asset_id]
        embed = discord.Embed(title=f"Asset #{asset['id']}: {asset['name']}", color=discord.Color.blue())
        embed.add_field(name="Type", value=asset['type'], inline=True)
        embed.add_field(name="Status", value=asset['status'].upper(), inline=True)
        embed.add_field(name="Owner", value=f"<@{asset['owner']}>", inline=True)
        embed.add_field(name="Added", value=asset['added_at'][:16], inline=True)
        if asset['last_audit']:
            embed.add_field(name="Last Audit", value=asset['last_audit'][:16], inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="audit", description="Mark asset as audited")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def audit(self, interaction: discord.Interaction, asset_id: str):
        if asset_id not in self.cog.assets:
            await interaction.response.send_message("❌ Asset not found", ephemeral=True)
            return
        self.cog.assets[asset_id]['last_audit'] = datetime.utcnow().isoformat()
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Asset #{asset_id} audited by {interaction.user.mention}")

    @app_commands.command(name="decommission", description="Decommission asset")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def decommission(self, interaction: discord.Interaction, asset_id: str):
        if asset_id not in self.cog.assets:
            await interaction.response.send_message("❌ Asset not found", ephemeral=True)
            return
        self.cog.assets[asset_id]['status'] = 'decommissioned'
        self.cog.assets[asset_id]['decommissioned_at'] = datetime.utcnow().isoformat()
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Asset #{asset_id} decommissioned")

    @app_commands.command(name="stats", description="View inventory statistics")
    async def stats(self, interaction: discord.Interaction):
        active = len([a for a in self.cog.assets.values() if a['status'] == 'active'])
        decom = len([a for a in self.cog.assets.values() if a['status'] == 'decommissioned'])
        types = {}
        for asset in self.cog.assets.values():
            if asset['status'] == 'active':
                types[asset['type']] = types.get(asset['type'], 0) + 1
        embed = discord.Embed(title="📊 Asset Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Assets", value=len(self.cog.assets), inline=True)
        embed.add_field(name="Active", value=active, inline=True)
        embed.add_field(name="Decommissioned", value=decom, inline=True)
        if types:
            types_str = "\n".join([f"{k}: {v}" for k, v in sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]])
            embed.add_field(name="Top Asset Types", value=types_str, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="transfer", description="Transfer asset ownership")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def transfer(self, interaction: discord.Interaction, asset_id: str, new_owner: discord.Member):
        if asset_id not in self.cog.assets:
            await interaction.response.send_message("❌ Asset not found", ephemeral=True)
            return
        old_owner = self.cog.assets[asset_id]['owner']
        self.cog.assets[asset_id]['owner'] = new_owner.id
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Asset #{asset_id} transferred from <@{old_owner}> to {new_owner.mention}")

class AssetInventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assets = {}
        self.asset_counter = 0
        self.data_file = "data/asset_inventory.json"
        self.load_data()
        self.asset_group = AssetGroup(self)
        bot.tree.add_command(self.asset_group)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.assets = data.get('assets', {})
                    self.asset_counter = data.get('counter', 0)
            except: pass

    def save_data(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'assets': self.assets, 'counter': self.asset_counter}, f, indent=2)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.asset_group.name)

async def setup(bot):
    await bot.add_cog(AssetInventoryCog(bot))
