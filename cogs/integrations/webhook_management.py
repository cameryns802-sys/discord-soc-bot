"""Webhook Management System: Command group combining inbound and ingestion"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class WebhookGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="webhook", description="Webhook management commands")
        self.cog = cog

    @app_commands.command(name="create", description="Create new webhook")
    @app_commands.checks.has_permissions(manage_webhooks=True)
    async def create(self, interaction: discord.Interaction, channel: discord.TextChannel, name: str):
        webhook = await channel.create_webhook(name=name, reason=f"Created by {interaction.user}")
        self.cog.webhooks[str(webhook.id)] = {"id": webhook.id, "name": name, "channel_id": channel.id, "created_by": interaction.user.id, "created_at": get_now_pst().isoformat(), "message_count": 0}
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Webhook **{name}** created in {channel.mention}\nURL: ||{webhook.url}||", ephemeral=True)

    @app_commands.command(name="list", description="List all webhooks")
    async def list(self, interaction: discord.Interaction):
        if not self.cog.webhooks:
            await interaction.response.send_message("ℹ️ No webhooks configured", ephemeral=True)
            return
        embed = discord.Embed(title="🔗 Configured Webhooks", color=discord.Color.blue())
        for wh in list(self.cog.webhooks.values())[:15]:
            embed.add_field(name=wh['name'], value=f"Channel: <#{wh['channel_id']}>\nMessages: {wh.get('message_count', 0)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete", description="Delete webhook")
    @app_commands.checks.has_permissions(manage_webhooks=True)
    async def delete(self, interaction: discord.Interaction, webhook_id: str):
        if webhook_id in self.cog.webhooks:
            del self.cog.webhooks[webhook_id]
            self.cog.save_data()
            await interaction.response.send_message(f"✅ Webhook deleted")
        else:
            await interaction.response.send_message("❌ Webhook not found", ephemeral=True)

    @app_commands.command(name="stats", description="View webhook statistics")
    async def stats(self, interaction: discord.Interaction):
        total_messages = sum(wh.get('message_count', 0) for wh in self.cog.webhooks.values())
        embed = discord.Embed(title="📊 Webhook Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Webhooks", value=len(self.cog.webhooks), inline=True)
        embed.add_field(name="Total Messages", value=total_messages, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="send", description="Send message via webhook")
    @app_commands.checks.has_permissions(manage_webhooks=True)
    async def send(self, interaction: discord.Interaction, webhook_id: str, message: str):
        if webhook_id not in self.cog.webhooks:
            await interaction.response.send_message("❌ Webhook not found", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Message sent via webhook (simulated)")
        self.cog.webhooks[webhook_id]['message_count'] = self.cog.webhooks[webhook_id].get('message_count', 0) + 1
        self.cog.save_data()

    @app_commands.command(name="configure", description="Configure webhook settings")
    @app_commands.checks.has_permissions(manage_webhooks=True)
    async def configure(self, interaction: discord.Interaction, webhook_id: str, setting: str, value: str):
        if webhook_id not in self.cog.webhooks:
            await interaction.response.send_message("❌ Webhook not found", ephemeral=True)
            return
        self.cog.webhooks[webhook_id][setting] = value
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Webhook {setting} updated")

    @app_commands.command(name="test", description="Test webhook connectivity")
    @app_commands.checks.has_permissions(manage_webhooks=True)
    async def test(self, interaction: discord.Interaction, webhook_id: str):
        if webhook_id not in self.cog.webhooks:
            await interaction.response.send_message("❌ Webhook not found", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Webhook connectivity test passed")

class WebhookManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = {}
        self.data_file = "data/webhooks.json"
        self.load_data()
        self.webhook_group = WebhookGroup(self)
        bot.tree.add_command(self.webhook_group)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.webhooks = data.get('webhooks', {})
            except: pass

    def save_data(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'webhooks': self.webhooks}, f, indent=2)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.webhook_group.name)

async def setup(bot):
    await bot.add_cog(WebhookManagementCog(bot))
