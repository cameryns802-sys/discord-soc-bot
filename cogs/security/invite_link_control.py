"""
Invite Link Control - Detect and manage Discord invite links
Auto-delete or whitelist invites, track sharing
"""

import discord
from discord.ext import commands
import json
import os
import re
from datetime import datetime
from typing import Optional, List, Dict
from cogs.core.pst_timezone import get_now_pst

class InviteLinkControl(commands.Cog):
    """Control Discord invite links in server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/invite_links.json"
        self.config = {}  # guild_id -> config
        self.whitelisted = {}  # guild_id -> [invite codes]
        self.invite_log = []  # Track all invites
        self.load_data()
        
        # Discord invite regex
        self.invite_regex = re.compile(
            r'(?:https?://)?(?:www\.)?discord(?:\.gg|\.com/invite)/([a-zA-Z0-9\-]+)'
        )
    
    def load_data(self):
        """Load config and whitelist"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.config = data.get('config', {})
                    self.whitelisted = data.get('whitelisted', {})
                    self.invite_log = data.get('invite_log', [])
            except:
                self.init_defaults()
        else:
            self.init_defaults()
    
    def init_defaults(self):
        """Initialize default config"""
        self.config = {}
        self.whitelisted = {}
        self.invite_log = []
    
    def save_data(self):
        """Save config and whitelist"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'config': self.config,
                'whitelisted': self.whitelisted,
                'invite_log': self.invite_log[-5000:]  # Keep last 5000
            }, f, indent=2)
    
    def get_config(self, guild_id: int) -> Dict:
        """Get guild config"""
        guild_key = str(guild_id)
        
        if guild_key not in self.config:
            self.config[guild_key] = {
                'enabled': True,
                'action': 'delete',  # delete or warn
                'notify_user': True,
                'notify_mods': True,
                'whitelist_enabled': False
            }
            self.save_data()
        
        return self.config[guild_key]
    
    def is_invite_whitelisted(self, guild_id: int, invite_code: str) -> bool:
        """Check if invite is whitelisted"""
        guild_key = str(guild_id)
        config = self.get_config(guild_id)
        
        if not config['whitelist_enabled']:
            return False
        
        if guild_key not in self.whitelisted:
            return False
        
        return invite_code in self.whitelisted[guild_key]
    
    def add_whitelist(self, guild_id: int, invite_code: str):
        """Add invite to whitelist"""
        guild_key = str(guild_id)
        
        if guild_key not in self.whitelisted:
            self.whitelisted[guild_key] = []
        
        if invite_code not in self.whitelisted[guild_key]:
            self.whitelisted[guild_key].append(invite_code)
            self.save_data()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for invite links"""
        if message.author.bot or not message.guild:
            return
        
        config = self.get_config(message.guild.id)
        
        if not config['enabled']:
            return
        
        # Find invites
        invites = self.invite_regex.findall(message.content)
        
        if not invites:
            return
        
        # Check each invite
        for invite_code in invites:
            # Check whitelist
            if self.is_invite_whitelisted(message.guild.id, invite_code):
                continue
            
            # Log the invite
            self.invite_log.append({
                'timestamp': get_now_pst().isoformat(),
                'guild_id': message.guild.id,
                'user_id': message.author.id,
                'user_name': message.author.name,
                'invite_code': invite_code,
                'action_taken': config['action']
            })
            
            # Take action
            if config['action'] == 'delete':
                try:
                    await message.delete()
                    
                    # Notify user
                    if config['notify_user']:
                        try:
                            await message.author.send(
                                f"🚫 Your message in {message.guild.name} was deleted for containing an invite link.\n"
                                f"If you think this was a mistake, contact server moderators."
                            )
                        except:
                            pass
                    
                    # Notify mods
                    if config['notify_mods']:
                        embed = discord.Embed(
                            title="🚫 Invite Link Detected",
                            description=f"Deleted invite link from {message.author.mention}",
                            color=discord.Color.red(),
                            timestamp=get_now_pst()
                        )
                        embed.add_field(name="Invite Code", value=invite_code, inline=True)
                        embed.add_field(name="Message Content", value=message.content[:100], inline=False)
                        
                        mod_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                        if mod_channel:
                            await mod_channel.send(embed=embed, delete_after=60)
                except:
                    pass
            
            self.save_data()
    
    @commands.command(name='inviteconfig')
    @commands.has_permissions(manage_guild=True)
    async def invite_config(self, ctx):
        """View invite link configuration"""
        config = self.get_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="🔗 Invite Link Control Settings",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Enabled", value="✅ Yes" if config['enabled'] else "❌ No", inline=True)
        embed.add_field(name="Action", value=config['action'].upper(), inline=True)
        embed.add_field(name="Notify User", value="✅ Yes" if config['notify_user'] else "❌ No", inline=True)
        embed.add_field(name="Notify Mods", value="✅ Yes" if config['notify_mods'] else "❌ No", inline=True)
        embed.add_field(name="Whitelist Enabled", value="✅ Yes" if config['whitelist_enabled'] else "❌ No", inline=True)
        
        guild_key = str(ctx.guild.id)
        whitelist_count = len(self.whitelisted.get(guild_key, []))
        embed.add_field(name="Whitelisted Invites", value=str(whitelist_count), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='setinviteaction')
    @commands.has_permissions(manage_guild=True)
    async def set_invite_action(self, ctx, action: str):
        """Set action for invite links (delete or warn)"""
        if action not in ['delete', 'warn']:
            await ctx.send("❌ Action must be 'delete' or 'warn'")
            return
        
        config = self.get_config(ctx.guild.id)
        config['action'] = action
        self.save_data()
        
        await ctx.send(f"✅ Invite action set to: **{action.upper()}**")
    
    @commands.command(name='toggleinvitecontrol')
    @commands.has_permissions(manage_guild=True)
    async def toggle_invite_control(self, ctx):
        """Enable/disable invite link control"""
        config = self.get_config(ctx.guild.id)
        config['enabled'] = not config['enabled']
        self.save_data()
        
        status = "✅ Enabled" if config['enabled'] else "❌ Disabled"
        await ctx.send(f"Invite link control: {status}")
    
    @commands.command(name='whitelist')
    @commands.has_permissions(manage_guild=True)
    async def whitelist_invite(self, ctx, invite_code: str):
        """Whitelist an invite code"""
        config = self.get_config(ctx.guild.id)
        config['whitelist_enabled'] = True
        
        self.add_whitelist(ctx.guild.id, invite_code)
        
        embed = discord.Embed(
            title="✅ Invite Whitelisted",
            description=f"Code: `{invite_code}`",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='whitelistshow')
    @commands.has_permissions(manage_guild=True)
    async def show_whitelist(self, ctx):
        """Show whitelisted invites"""
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.whitelisted or not self.whitelisted[guild_key]:
            await ctx.send("No whitelisted invites")
            return
        
        embed = discord.Embed(
            title="📋 Whitelisted Invite Codes",
            description=f"{len(self.whitelisted[guild_key])} code(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        codes = self.whitelisted[guild_key]
        embed.add_field(name="Codes", value="\n".join([f"`{code}`" for code in codes]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='invitehistory')
    @commands.has_permissions(manage_guild=True)
    async def invite_history(self, ctx, limit: int = 20):
        """View invite sharing history"""
        guild_invites = [
            i for i in self.invite_log 
            if i['guild_id'] == ctx.guild.id
        ]
        
        if not guild_invites:
            await ctx.send("No invite sharing history")
            return
        
        embed = discord.Embed(
            title="📊 Invite Sharing History",
            description=f"Last {min(limit, len(guild_invites))} events",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for invite in guild_invites[-limit:]:
            field_value = f"**User:** {invite['user_name']}\n"
            field_value += f"**Code:** `{invite['invite_code']}`\n"
            field_value += f"**Action:** {invite['action_taken'].upper()}"
            
            embed.add_field(
                name=datetime.fromisoformat(invite['timestamp']).strftime('%Y-%m-%d %H:%M'),
                value=field_value,
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteLinkControl(bot))
