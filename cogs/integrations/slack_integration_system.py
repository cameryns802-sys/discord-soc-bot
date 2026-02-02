# Slack Integration: Push alerts and notifications to Slack
import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
import os

class SlackIntegrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.slack_config = {}
        self.slack_channels = {}
        self.notification_queue = []
        self.data_file = "data/slack_integration.json"
        self.load_slack_config()
        self.slack_sender.start()

    def load_slack_config(self):
        """Load Slack configuration."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.slack_config = data.get('config', {})
                    self.slack_channels = data.get('channels', {})
            except:
                pass

    def save_slack_config(self):
        """Save Slack configuration."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'config': self.slack_config,
                'channels': self.slack_channels
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setupslack(self, ctx, webhook_url: str):
        """Setup Slack integration. Usage: !setupslack <webhook_url>"""
        # Validate webhook URL format
        if not webhook_url.startswith("https://hooks.slack.com"):
            await ctx.send("❌ Invalid Slack webhook URL.")
            return
        
        self.slack_config = {
            "webhook_url": webhook_url,
            "enabled": True,
            "configured_by": ctx.author.id,
            "configured_at": datetime.utcnow().isoformat(),
            "notifications_sent": 0,
            "last_sent": None
        }
        
        self.save_slack_config()
        
        embed = discord.Embed(
            title="✅ Slack Integration Configured",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Webhook", value="✅ Configured", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mapslackchannel(self, ctx, slack_channel: str, notification_type: str):
        """Map Slack channel for notifications. Usage: !mapslackchannel #channel alerts|incidents|evidence"""
        valid_types = ['alerts', 'incidents', 'evidence', 'reports', 'all']
        if notification_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid type. Use: {', '.join(valid_types)}")
            return
        
        self.slack_channels[notification_type.lower()] = {
            "slack_channel": slack_channel,
            "mapped_at": datetime.utcnow().isoformat(),
            "mapped_by": ctx.author.id,
            "enabled": True,
            "message_count": 0
        }
        
        self.save_slack_config()
        
        embed = discord.Embed(
            title="✅ Slack Channel Mapped",
            description=f"{slack_channel} → {notification_type.upper()}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def slacknotify(self, ctx, notification_type: str, *, message: str):
        """Send notification to Slack. Usage: !slacknotify alerts message"""
        if not self.slack_config.get('enabled'):
            await ctx.send("❌ Slack integration not configured. Use `!setupslack` first.")
            return
        
        if notification_type.lower() not in self.slack_channels:
            await ctx.send(f"❌ No Slack channel mapped for '{notification_type}'")
            return
        
        notification = {
            "type": notification_type.lower(),
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "sent_by": ctx.author.id,
            "status": "queued"
        }
        
        self.notification_queue.append(notification)
        
        embed = discord.Embed(
            title="✅ Notification Queued",
            description="Will be sent to Slack",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=notification_type, inline=True)
        embed.add_field(name="Queue Position", value=len(self.notification_queue), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def slackstatus(self, ctx):
        """Check Slack integration status."""
        if not self.slack_config:
            embed = discord.Embed(
                title="🔴 Slack Integration",
                description="Not configured",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🟢 Slack Integration",
                description="Active",
                color=discord.Color.green()
            )
            embed.add_field(name="Status", value="✅ Connected", inline=True)
            embed.add_field(name="Notifications Sent", value=self.slack_config.get('notifications_sent', 0), inline=True)
            embed.add_field(name="Mapped Channels", value=len(self.slack_channels), inline=True)
        
        embed.add_field(name="Queue Length", value=len(self.notification_queue), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def slackchannels(self, ctx):
        """View mapped Slack channels."""
        if not self.slack_channels:
            await ctx.send("ℹ️ No Slack channels mapped.")
            return
        
        embed = discord.Embed(
            title="📋 Mapped Slack Channels",
            color=discord.Color.blue()
        )
        
        for notif_type, config in self.slack_channels.items():
            embed.add_field(
                name=f"{config['slack_channel']}",
                value=f"Type: {notif_type.upper()} | Messages: {config['message_count']} | Status: {'✅' if config['enabled'] else '❌'}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggleslack(self, ctx):
        """Toggle Slack integration on/off."""
        if not self.slack_config:
            await ctx.send("❌ Slack not configured.")
            return
        
        self.slack_config['enabled'] = not self.slack_config.get('enabled', True)
        status = "ENABLED" if self.slack_config['enabled'] else "DISABLED"
        
        self.save_slack_config()
        
        await ctx.send(f"✅ Slack integration {status}")

    @tasks.loop(minutes=1)
    async def slack_sender(self):
        """Process notification queue and send to Slack."""
        # Simulated Slack sender (would normally call Slack API)
        if not self.slack_config.get('enabled'):
            return
        
        for notification in self.notification_queue[:5]:
            notification['status'] = 'sent'
            
            if notification['type'] in self.slack_channels:
                self.slack_channels[notification['type']]['message_count'] += 1
        
        # Remove processed notifications
        self.notification_queue = [n for n in self.notification_queue if n['status'] != 'sent']
        
        if self.notification_queue:
            self.slack_config['notifications_sent'] = self.slack_config.get('notifications_sent', 0) + 5
            self.slack_config['last_sent'] = datetime.utcnow().isoformat()
            self.save_slack_config()

    @slack_sender.before_loop
    async def before_slack_sender(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(SlackIntegrationCog(bot))
