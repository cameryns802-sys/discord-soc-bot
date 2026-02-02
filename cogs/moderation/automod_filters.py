"""
Auto-Moderation Filters: Advanced content filtering for links, invites, spam, and mentions
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import re
from collections import defaultdict
import asyncio

class AutoModFilters(commands.Cog):
    """Advanced auto-moderation filters"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = defaultdict(list)  # user_id: [timestamps]
        self.mention_tracker = defaultdict(list)  # user_id: [timestamps]
        self.link_whitelist = {}  # guild_id: [domains]
        self.filter_settings = {}  # guild_id: settings dict
    
    # ==================== FILTER CONFIGURATION ====================
    
    @commands.command(name='filterconfig')
    @commands.has_permissions(administrator=True)
    async def filterconfig(self, ctx, filter_type: str, action: str = "status"):
        """Configure automod filters (links, invites, spam, mentions, caps)"""
        await self._filterconfig_logic(ctx, filter_type, action)
    
    @app_commands.command(name="filterconfig", description="Configure automod filters")
    @app_commands.describe(
        filter_type="Filter type: links, invites, spam, mentions, caps",
        action="Action: enable, disable, or status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def filterconfig_slash(self, interaction: discord.Interaction, filter_type: str, action: str = "status"):
        """Configure filters using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._filterconfig_logic(ctx, filter_type, action)
    
    async def _filterconfig_logic(self, ctx, filter_type: str, action: str):
        filter_type = filter_type.lower()
        action = action.lower()
        
        if ctx.guild.id not in self.filter_settings:
            self.filter_settings[ctx.guild.id] = {
                'links': False,
                'invites': True,  # Default enabled
                'spam': True,     # Default enabled
                'mentions': True, # Default enabled
                'caps': False
            }
        
        settings = self.filter_settings[ctx.guild.id]
        
        if filter_type not in settings:
            await ctx.send(f"❌ Invalid filter type. Choose from: {', '.join(settings.keys())}")
            return
        
        if action == "enable":
            settings[filter_type] = True
            
            embed = discord.Embed(
                title=f"✅ {filter_type.title()} Filter Enabled",
                color=discord.Color.green(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Filter", value=filter_type.title(), inline=True)
            embed.add_field(name="Status", value="🟢 Enabled", inline=True)
            embed.add_field(name="Configured by", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
        elif action == "disable":
            settings[filter_type] = False
            
            embed = discord.Embed(
                title=f"❌ {filter_type.title()} Filter Disabled",
                color=discord.Color.red(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Filter", value=filter_type.title(), inline=True)
            embed.add_field(name="Status", value="🔴 Disabled", inline=True)
            embed.add_field(name="Configured by", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
        else:  # status
            embed = discord.Embed(
                title="🛡️ AutoMod Filter Configuration",
                color=discord.Color.blue(),
                timestamp=datetime.now(datetime.UTC)
            )
            
            for f_type, enabled in settings.items():
                status = "🟢 Enabled" if enabled else "🔴 Disabled"
                embed.add_field(name=f_type.title(), value=status, inline=True)
            
            embed.set_footer(text="Use /filterconfig <type> <enable/disable> to change")
            
            await ctx.send(embed=embed)
    
    # ==================== LINK WHITELIST ====================
    
    @commands.command(name='linkwhitelist')
    @commands.has_permissions(administrator=True)
    async def linkwhitelist(self, ctx, action: str, domain: str = None):
        """Manage link whitelist (add/remove/list)"""
        await self._linkwhitelist_logic(ctx, action, domain)
    
    @app_commands.command(name="linkwhitelist", description="Manage link whitelist")
    @app_commands.describe(
        action="Action: add, remove, or list",
        domain="Domain to whitelist (e.g., youtube.com)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def linkwhitelist_slash(self, interaction: discord.Interaction, action: str, domain: Optional[str] = None):
        """Manage whitelist using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._linkwhitelist_logic(ctx, action, domain)
    
    async def _linkwhitelist_logic(self, ctx, action: str, domain: Optional[str]):
        action = action.lower()
        
        if ctx.guild.id not in self.link_whitelist:
            self.link_whitelist[ctx.guild.id] = []
        
        whitelist = self.link_whitelist[ctx.guild.id]
        
        if action == "add":
            if not domain:
                await ctx.send("❌ Please provide a domain to whitelist")
                return
            
            domain = domain.lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
            
            if domain in whitelist:
                await ctx.send(f"❌ `{domain}` is already whitelisted")
                return
            
            whitelist.append(domain)
            
            embed = discord.Embed(
                title="✅ Domain Whitelisted",
                description=f"Links from `{domain}` will not be filtered",
                color=discord.Color.green(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Domain", value=domain, inline=True)
            embed.add_field(name="Added by", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        elif action == "remove":
            if not domain:
                await ctx.send("❌ Please provide a domain to remove")
                return
            
            domain = domain.lower()
            
            if domain not in whitelist:
                await ctx.send(f"❌ `{domain}` is not in the whitelist")
                return
            
            whitelist.remove(domain)
            
            embed = discord.Embed(
                title="❌ Domain Removed from Whitelist",
                description=f"Links from `{domain}` will now be filtered",
                color=discord.Color.orange(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Domain", value=domain, inline=True)
            embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        elif action == "list":
            if not whitelist:
                await ctx.send("📋 No domains are whitelisted")
                return
            
            embed = discord.Embed(
                title="📋 Link Whitelist",
                description=f"The following domains are allowed:",
                color=discord.Color.blue(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(
                name=f"Whitelisted Domains ({len(whitelist)})",
                value="\n".join([f"• `{d}`" for d in whitelist[:20]]) + (f"\n... and {len(whitelist) - 20} more" if len(whitelist) > 20 else ""),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("❌ Invalid action. Use: add, remove, or list")
    
    # ==================== AUTO-MODERATION LISTENERS ====================
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation message listener"""
        if message.author.bot or not message.guild:
            return
        
        # Check if user has mod permissions (bypass filters)
        if message.author.guild_permissions.manage_messages:
            return
        
        guild_id = message.guild.id
        
        if guild_id not in self.filter_settings:
            return
        
        settings = self.filter_settings[guild_id]
        
        # Spam detection
        if settings.get('spam', False):
            if await self._check_spam(message):
                return
        
        # Mention spam detection
        if settings.get('mentions', False):
            if await self._check_mention_spam(message):
                return
        
        # Invite link detection
        if settings.get('invites', False):
            if await self._check_invites(message):
                return
        
        # Link detection
        if settings.get('links', False):
            if await self._check_links(message):
                return
        
        # Caps detection
        if settings.get('caps', False):
            if await self._check_caps(message):
                return
    
    async def _check_spam(self, message):
        """Check for spam (5+ messages in 5 seconds)"""
        user_id = message.author.id
        now = datetime.now(datetime.UTC).timestamp()
        
        # Clean old timestamps
        self.spam_tracker[user_id] = [ts for ts in self.spam_tracker[user_id] if now - ts < 5]
        
        # Add current timestamp
        self.spam_tracker[user_id].append(now)
        
        # Check if spamming
        if len(self.spam_tracker[user_id]) >= 5:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} Slow down! Spam detected.",
                    delete_after=5
                )
                
                # Timeout for 60 seconds
                await message.author.timeout(
                    discord.utils.utcnow() + timedelta(seconds=60),
                    reason="Auto-mod: Spam detection"
                )
                
                return True
            except:
                pass
        
        return False
    
    async def _check_mention_spam(self, message):
        """Check for mention spam (5+ mentions)"""
        mention_count = len(message.mentions) + len(message.role_mentions)
        
        if mention_count >= 5:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} Too many mentions! Message deleted.",
                    delete_after=5
                )
                return True
            except:
                pass
        
        return False
    
    async def _check_invites(self, message):
        """Check for Discord invite links"""
        invite_pattern = r'(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)[a-zA-Z0-9]+'
        
        if re.search(invite_pattern, message.content, re.IGNORECASE):
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} Discord invites are not allowed!",
                    delete_after=5
                )
                return True
            except:
                pass
        
        return False
    
    async def _check_links(self, message):
        """Check for non-whitelisted links"""
        url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
        matches = re.findall(url_pattern, message.content, re.IGNORECASE)
        
        if not matches:
            return False
        
        whitelist = self.link_whitelist.get(message.guild.id, [])
        
        for domain in matches:
            if domain.lower() not in whitelist:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"⚠️ {message.author.mention} Links from `{domain}` are not allowed!",
                        delete_after=5
                    )
                    return True
                except:
                    pass
        
        return False
    
    async def _check_caps(self, message):
        """Check for excessive caps (70%+ uppercase)"""
        if len(message.content) < 10:
            return False
        
        letters = [c for c in message.content if c.isalpha()]
        if not letters:
            return False
        
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        
        if caps_ratio >= 0.7:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} Please don't use excessive caps!",
                    delete_after=5
                )
                return True
            except:
                pass
        
        return False

async def setup(bot):
    await bot.add_cog(AutoModFilters(bot))
