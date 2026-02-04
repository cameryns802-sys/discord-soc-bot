"""
User DM Notification System - Send direct messages to users
Notifications, alerts, and personal messages via DM
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class UserDMNotifier(commands.Cog):
    """Send DMs to users for notifications and alerts"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dm_queue_file = 'data/dm_queue.json'
        self.dm_log_file = 'data/dm_log.json'
        self.load_dm_data()
        self.process_dm_queue.start()
    
    def load_dm_data(self):
        """Load DM queue and log"""
        os.makedirs('data', exist_ok=True)
        for file in [self.dm_queue_file, self.dm_log_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def queue_dm(self, user_id, title, message, dm_type="info"):
        """Queue a DM to be sent to a user"""
        try:
            with open(self.dm_queue_file, 'r') as f:
                queue = json.load(f)
        except:
            queue = {}
        
        dm_id = f"{user_id}_{get_now_pst().timestamp()}"
        queue[dm_id] = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": dm_type,
            "timestamp": get_now_pst().isoformat(),
            "sent": False
        }
        
        with open(self.dm_queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
        
        return dm_id
    
    @tasks.loop(minutes=1)
    async def process_dm_queue(self):
        """Process DM queue every minute"""
        try:
            with open(self.dm_queue_file, 'r') as f:
                queue = json.load(f)
        except:
            return
        
        updated_queue = queue.copy()
        
        for dm_id, dm_data in queue.items():
            if dm_data.get("sent"):
                continue
            
            try:
                user = await self.bot.fetch_user(dm_data["user_id"])
                
                # Create embed based on type
                if dm_data["type"] == "alert":
                    color = discord.Color.red()
                    icon = "🚨"
                elif dm_data["type"] == "warning":
                    color = discord.Color.orange()
                    icon = "⚠️"
                elif dm_data["type"] == "success":
                    color = discord.Color.green()
                    icon = "✅"
                else:
                    color = discord.Color.blue()
                    icon = "ℹ️"
                
                embed = discord.Embed(
                    title=f"{icon} {dm_data['title']}",
                    description=dm_data['message'],
                    color=color,
                    timestamp=get_now_pst()
                )
                embed.set_footer(text="Sentinel SOC Bot")
                
                await user.send(embed=embed)
                
                # Mark as sent
                updated_queue[dm_id]["sent"] = True
                updated_queue[dm_id]["sent_at"] = get_now_pst().isoformat()
                
                # Log the DM
                self._log_dm(dm_data["user_id"], dm_data["title"], "sent")
                
            except discord.Forbidden:
                # User has DMs disabled
                updated_queue[dm_id]["sent"] = True
                updated_queue[dm_id]["error"] = "DMs disabled"
                self._log_dm(dm_data["user_id"], dm_data["title"], "failed_dms_disabled")
            except Exception as e:
                # Other error, retry later
                self._log_dm(dm_data["user_id"], dm_data["title"], f"failed_{str(e)}")
        
        # Save updated queue
        with open(self.dm_queue_file, 'w') as f:
            json.dump(updated_queue, f, indent=2)
    
    def _log_dm(self, user_id, title, status):
        """Log DM activity"""
        try:
            with open(self.dm_log_file, 'r') as f:
                log = json.load(f)
        except:
            log = {}
        
        log_entry = {
            "user_id": user_id,
            "title": title,
            "status": status,
            "timestamp": get_now_pst().isoformat()
        }
        
        log_id = f"{user_id}_{get_now_pst().timestamp()}"
        log[log_id] = log_entry
        
        with open(self.dm_log_file, 'w') as f:
            json.dump(log, f, indent=2)
    
    @commands.command(name='dm_user')
    @commands.has_permissions(administrator=True)
    async def dm_user(self, ctx, user_id: int, *, message: str):
        """Send a DM to a user"""
        try:
            user = await self.bot.fetch_user(user_id)
            
            embed = discord.Embed(
                title="📧 Message from Security Team",
                description=message,
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            embed.set_footer(text="Sentinel SOC Bot")
            
            await user.send(embed=embed)
            
            response_embed = discord.Embed(
                title="✅ DM Sent",
                description=f"Message sent to {user.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=response_embed)
            
        except discord.Forbidden:
            await ctx.send("❌ User has DMs disabled")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='alert_user')
    @commands.has_permissions(administrator=True)
    async def alert_user(self, ctx, user_id: int, *, message: str):
        """Send an alert DM to a user"""
        self.queue_dm(user_id, "Security Alert", message, "alert")
        
        embed = discord.Embed(
            title="📧 Alert Queued",
            description=f"Alert queued for user {user_id}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='notify_user')
    @commands.has_permissions(administrator=True)
    async def notify_user(self, ctx, user_id: int, *, message: str):
        """Send a notification DM to a user"""
        self.queue_dm(user_id, "Notification", message, "info")
        
        embed = discord.Embed(
            title="📧 Notification Queued",
            description=f"Notification queued for user {user_id}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='broadcast_dm')
    @commands.has_permissions(administrator=True)
    async def broadcast_dm(self, ctx, *, message: str):
        """Send DM to all server members"""
        guild = ctx.guild
        count = 0
        
        embed = discord.Embed(
            title="📢 Broadcasting DM",
            description=f"Sending DM to {len(guild.members)} members...",
            color=discord.Color.blue()
        )
        status_msg = await ctx.send(embed=embed)
        
        for member in guild.members:
            if not member.bot:
                try:
                    dm_embed = discord.Embed(
                        title="📢 Broadcast Message",
                        description=message,
                        color=discord.Color.blue(),
                        timestamp=get_now_pst()
                    )
                    dm_embed.add_field(name="From", value=f"{guild.name}", inline=False)
                    dm_embed.set_footer(text="Sentinel SOC Bot")
                    
                    await member.send(embed=dm_embed)
                    count += 1
                except:
                    pass
        
        result_embed = discord.Embed(
            title="✅ Broadcast Complete",
            description=f"DM sent to {count} members",
            color=discord.Color.green()
        )
        await status_msg.edit(embed=result_embed)
    
    @commands.command(name='welcome_dm')
    async def welcome_dm(self, ctx):
        """Send welcome DM to yourself"""
        embed = discord.Embed(
            title="👋 Welcome to Sentinel SOC",
            description="Security Operations Center Bot",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🤖 Bot Name", value="Sentinel", inline=True)
        embed.add_field(name="🎯 Purpose", value="Security Operations", inline=True)
        embed.add_field(name="🏢 Type", value="SOC Bot", inline=True)
        
        embed.add_field(name="📋 Quick Start", value="━" * 25, inline=False)
        embed.add_field(name="1️⃣", value="Join a server with Sentinel installed", inline=False)
        embed.add_field(name="2️⃣", value="Use `!setup_soc` to create SOC infrastructure", inline=False)
        embed.add_field(name="3️⃣", value="Assign roles to team members", inline=False)
        embed.add_field(name="4️⃣", value="Start running security commands!", inline=False)
        
        embed.add_field(name="🔗 Key Commands", value="━" * 25, inline=False)
        embed.add_field(name="`!helpme`", value="Full command documentation", inline=True)
        embed.add_field(name="`!botstatus`", value="Check bot health", inline=True)
        embed.add_field(name="`!setup_soc`", value="Setup infrastructure", inline=True)
        
        embed.add_field(name="💡 Need Help?", value="━" * 25, inline=False)
        embed.add_field(name="→", value="DM this bot for help commands", inline=False)
        embed.add_field(name="→", value="Use `!docs` for command documentation", inline=False)
        
        await ctx.author.send(embed=embed)
        
        response = discord.Embed(
            title="✅ Welcome DM Sent",
            color=discord.Color.green()
        )
        await ctx.send(embed=response)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome DM when member joins"""
        if member.bot:
            return
        
        embed = discord.Embed(
            title=f"👋 Welcome to {member.guild.name}!",
            description="You're now part of our security operations team",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🛡️ Sentinel SOC Bot", value="Security Operations Center", inline=False)
        embed.add_field(name="📊 Features", value="Threat detection, incident response, compliance tracking", inline=False)
        embed.add_field(name="🎯 Get Started", value="Check pinned messages for setup instructions", inline=False)
        
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(UserDMNotifier(bot))
