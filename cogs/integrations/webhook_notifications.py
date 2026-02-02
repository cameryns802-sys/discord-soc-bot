import discord
from discord.ext import commands
import aiohttp
import json
import datetime
from pathlib import Path

class WebhookNotifications(commands.Cog):
    """Webhook notification system for external integrations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.webhook_file = self.data_dir / 'webhooks.json'
        
        self.webhooks = {
            'endpoints': {},  # {name: {url, type, triggers}}
            'stats': {
                'total_sent': 0,
                'failed': 0,
                'last_sent': None
            }
        }
        
        self.load_webhooks()
    
    def load_webhooks(self):
        """Load webhooks from file"""
        if self.webhook_file.exists():
            with open(self.webhook_file, 'r') as f:
                self.webhooks = json.load(f)
    
    def save_webhooks(self):
        """Save webhooks to file"""
        with open(self.webhook_file, 'w') as f:
            json.dump(self.webhooks, f, indent=2)
    
    async def send_webhook(self, name: str, payload: dict):
        """Send webhook notification"""
        if name not in self.webhooks['endpoints']:
            return False
        
        webhook = self.webhooks['endpoints'][name]
        webhook_type = webhook.get('type', 'discord')
        
        try:
            if webhook_type == 'discord':
                await self.send_discord_webhook(webhook['url'], payload)
            elif webhook_type == 'slack':
                await self.send_slack_webhook(webhook['url'], payload)
            elif webhook_type == 'custom':
                await self.send_custom_webhook(webhook['url'], payload)
            
            self.webhooks['stats']['total_sent'] += 1
            self.webhooks['stats']['last_sent'] = datetime.datetime.now().isoformat()
            self.save_webhooks()
            return True
        except Exception as e:
            self.webhooks['stats']['failed'] += 1
            self.save_webhooks()
            print(f"[Webhook] Error sending to {name}: {e}")
            return False
    
    async def send_discord_webhook(self, url: str, payload: dict):
        """Send Discord webhook"""
        async with aiohttp.ClientSession() as session:
            # Discord webhook format
            data = {
                'content': payload.get('message', ''),
                'username': payload.get('username', 'SOC Bot'),
                'avatar_url': payload.get('avatar_url', '')
            }
            
            # Add embed if provided
            if 'embed' in payload:
                data['embeds'] = [payload['embed']]
            
            async with session.post(url, json=data) as resp:
                if resp.status not in [200, 204]:
                    raise Exception(f"Discord webhook failed: {resp.status}")
    
    async def send_slack_webhook(self, url: str, payload: dict):
        """Send Slack webhook"""
        async with aiohttp.ClientSession() as session:
            # Slack webhook format
            data = {
                'text': payload.get('message', ''),
                'username': payload.get('username', 'SOC Bot')
            }
            
            if 'color' in payload:
                data['attachments'] = [{
                    'color': payload['color'],
                    'text': payload.get('message', '')
                }]
            
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    raise Exception(f"Slack webhook failed: {resp.status}")
    
    async def send_custom_webhook(self, url: str, payload: dict):
        """Send custom webhook (raw JSON)"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status not in [200, 201, 204]:
                    raise Exception(f"Custom webhook failed: {resp.status}")
    
    async def notify_error(self, error_data: dict):
        """Send error notification to all webhooks with 'error' trigger"""
        for name, webhook in self.webhooks['endpoints'].items():
            if 'error' in webhook.get('triggers', []):
                payload = {
                    'message': f"🚨 **Error Detected**\n{error_data.get('message', 'Unknown error')}",
                    'username': 'SOC Bot - Errors',
                    'color': '#ff0000'
                }
                await self.send_webhook(name, payload)
    
    async def notify_alert(self, alert_data: dict):
        """Send security alert to all webhooks with 'alert' trigger"""
        for name, webhook in self.webhooks['endpoints'].items():
            if 'alert' in webhook.get('triggers', []):
                payload = {
                    'message': f"⚠️ **Security Alert**\n{alert_data.get('message', 'Unknown alert')}",
                    'username': 'SOC Bot - Alerts',
                    'color': '#ffa500'
                }
                await self.send_webhook(name, payload)
    
    @commands.command(name='add_webhook')
    @commands.is_owner()
    async def add_webhook(self, ctx, name: str, webhook_type: str, url: str, *triggers: str):
        """Add a webhook (owner only)
        
        Types: discord, slack, custom
        Triggers: error, alert, drill, incident
        
        Example: !add_webhook my_webhook discord https://discord.com/api/webhooks/... error alert
        """
        valid_types = ['discord', 'slack', 'custom']
        valid_triggers = ['error', 'alert', 'drill', 'incident', 'all']
        
        if webhook_type not in valid_types:
            await ctx.send(f"❌ Invalid type. Valid types: {', '.join(valid_types)}")
            return
        
        if not triggers:
            triggers = ['all']
        
        for trigger in triggers:
            if trigger not in valid_triggers:
                await ctx.send(f"❌ Invalid trigger `{trigger}`. Valid triggers: {', '.join(valid_triggers)}")
                return
        
        self.webhooks['endpoints'][name] = {
            'url': url,
            'type': webhook_type,
            'triggers': list(triggers),
            'created_at': datetime.datetime.now().isoformat(),
            'created_by': str(ctx.author)
        }
        
        self.save_webhooks()
        await ctx.send(f"✅ Webhook `{name}` added ({webhook_type})\nTriggers: {', '.join(triggers)}")
    
    @commands.command(name='list_webhooks')
    @commands.is_owner()
    async def list_webhooks(self, ctx):
        """List all webhooks (owner only)"""
        if not self.webhooks['endpoints']:
            await ctx.send("❌ No webhooks configured")
            return
        
        embed = discord.Embed(
            title="🔔 Configured Webhooks",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        for name, webhook in self.webhooks['endpoints'].items():
            triggers = ', '.join(webhook.get('triggers', []))
            webhook_type = webhook.get('type', 'unknown')
            
            embed.add_field(
                name=name,
                value=f"Type: `{webhook_type}`\nTriggers: `{triggers}`",
                inline=False
            )
        
        # Stats
        embed.add_field(
            name="📊 Statistics",
            value=f"Total Sent: {self.webhooks['stats']['total_sent']}\nFailed: {self.webhooks['stats']['failed']}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='remove_webhook')
    @commands.is_owner()
    async def remove_webhook(self, ctx, name: str):
        """Remove a webhook (owner only)"""
        if name not in self.webhooks['endpoints']:
            await ctx.send(f"❌ Webhook `{name}` not found")
            return
        
        del self.webhooks['endpoints'][name]
        self.save_webhooks()
        
        await ctx.send(f"✅ Webhook `{name}` removed")
    
    @commands.command(name='test_webhook')
    @commands.is_owner()
    async def test_webhook(self, ctx, name: str):
        """Test a webhook (owner only)"""
        if name not in self.webhooks['endpoints']:
            await ctx.send(f"❌ Webhook `{name}` not found")
            return
        
        payload = {
            'message': f"🧪 **Webhook Test**\nThis is a test notification from SOC Bot.\nTime: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'username': 'SOC Bot - Test',
            'color': '#00ff00'
        }
        
        success = await self.send_webhook(name, payload)
        
        if success:
            await ctx.send(f"✅ Test notification sent to `{name}`")
        else:
            await ctx.send(f"❌ Failed to send test notification to `{name}`")
    
    @commands.command(name='webhook_stats')
    @commands.is_owner()
    async def webhook_stats(self, ctx):
        """View webhook statistics (owner only)"""
        stats = self.webhooks['stats']
        
        embed = discord.Embed(
            title="📊 Webhook Statistics",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Total Sent", value=str(stats['total_sent']), inline=True)
        embed.add_field(name="Failed", value=str(stats['failed']), inline=True)
        
        if stats['total_sent'] > 0:
            success_rate = ((stats['total_sent'] - stats['failed']) / stats['total_sent']) * 100
            embed.add_field(name="Success Rate", value=f"{success_rate:.1f}%", inline=True)
        
        if stats.get('last_sent'):
            embed.add_field(name="Last Sent", value=stats['last_sent'][:19], inline=False)
        
        embed.add_field(name="Active Webhooks", value=str(len(self.webhooks['endpoints'])), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='webhook_info')
    @commands.is_owner()
    async def webhook_info(self, ctx, name: str):
        """View webhook details (owner only)"""
        if name not in self.webhooks['endpoints']:
            await ctx.send(f"❌ Webhook `{name}` not found")
            return
        
        webhook = self.webhooks['endpoints'][name]
        
        embed = discord.Embed(
            title=f"🔔 Webhook: {name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Type", value=webhook.get('type', 'unknown'), inline=True)
        embed.add_field(name="Triggers", value=', '.join(webhook.get('triggers', [])), inline=True)
        
        if webhook.get('created_at'):
            embed.add_field(name="Created", value=webhook['created_at'][:19], inline=False)
        
        if webhook.get('created_by'):
            embed.add_field(name="Created By", value=webhook['created_by'], inline=True)
        
        # Mask URL for security
        url = webhook.get('url', '')
        masked_url = url[:30] + '...' if len(url) > 30 else url
        embed.add_field(name="URL", value=f"`{masked_url}`", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WebhookNotifications(bot))
