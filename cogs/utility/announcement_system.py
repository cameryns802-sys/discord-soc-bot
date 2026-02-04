"""
Announcement System - Server announcements and scheduled messages
Create polls, broadcasts, reminders, and scheduled announcements
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from cogs.core.pst_timezone import get_now_pst

class AnnouncementSystem(commands.Cog):
    """Create and manage server announcements"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/announcements.json"
        self.announcements = []
        self.scheduled = []
        self.polls = []
        self.load_data()
        self.process_scheduled.start()
    
    def load_data(self):
        """Load announcement data"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.announcements = data.get('announcements', [])
                    self.scheduled = data.get('scheduled', [])
                    self.polls = data.get('polls', [])
            except:
                self.init_defaults()
        else:
            self.init_defaults()
    
    def init_defaults(self):
        """Initialize defaults"""
        self.announcements = []
        self.scheduled = []
        self.polls = []
    
    def save_data(self):
        """Save announcement data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'announcements': self.announcements[-500:],  # Keep last 500
                'scheduled': self.scheduled,
                'polls': self.polls
            }, f, indent=2)
    
    @tasks.loop(minutes=1)
    async def process_scheduled(self):
        """Process scheduled announcements"""
        now = get_now_pst()
        
        for announcement in self.scheduled[:]:
            sched_time = datetime.fromisoformat(announcement['scheduled_time'])
            
            if sched_time <= now and not announcement.get('sent'):
                # Send announcement
                try:
                    channel = self.bot.get_channel(announcement['channel_id'])
                    
                    if channel:
                        # Mention roles if specified
                        mention_text = ""
                        if announcement.get('role_ids'):
                            roles = [f"<@&{rid}>" for rid in announcement['role_ids']]
                            mention_text = " ".join(roles) + "\n"
                        
                        embed = discord.Embed(
                            title=announcement['title'],
                            description=announcement['message'],
                            color=discord.Color.blue(),
                            timestamp=now
                        )
                        
                        await channel.send(mention_text, embed=embed)
                        
                        announcement['sent'] = True
                        announcement['sent_at'] = now.isoformat()
                        self.save_data()
                except Exception as e:
                    print(f"Failed to send scheduled announcement: {e}")
    
    @process_scheduled.before_loop
    async def before_process_scheduled(self):
        """Wait for bot to be ready"""
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        """Cleanup"""
        self.process_scheduled.cancel()
    
    @commands.command(name='announce')
    @commands.has_permissions(manage_guild=True)
    async def announce(self, ctx, *, message: str):
        """Send announcement to channel"""
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.set_footer(text=f"By {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        # Log announcement
        self.announcements.append({
            'timestamp': get_now_pst().isoformat(),
            'channel_id': ctx.channel.id,
            'guild_id': ctx.guild.id,
            'author_id': ctx.author.id,
            'message': message
        })
        
        self.save_data()
    
    @commands.command(name='broadcast')
    @commands.has_permissions(manage_guild=True)
    async def broadcast(self, ctx, channel: Optional[discord.TextChannel] = None, *, message: str):
        """Broadcast announcement to specific channel"""
        target_channel = channel or ctx.channel
        
        embed = discord.Embed(
            title="📢 Broadcast",
            description=message,
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.set_footer(text=f"From {ctx.author.name}")
        
        try:
            await target_channel.send(embed=embed)
            await ctx.send(f"✅ Broadcast sent to {target_channel.mention}")
        except discord.Forbidden:
            await ctx.send(f"❌ Cannot send message to {target_channel.mention}")
    
    @commands.command(name='dmrole')
    @commands.has_permissions(manage_guild=True)
    async def dm_role(self, ctx, role: discord.Role, *, message: str):
        """Send DM announcement to role members"""
        count = 0
        failed = 0
        
        for member in role.members:
            if not member.bot:
                try:
                    embed = discord.Embed(
                        title=f"Message from {ctx.guild.name}",
                        description=message,
                        color=discord.Color.blue(),
                        timestamp=get_now_pst()
                    )
                    
                    await member.send(embed=embed)
                    count += 1
                except:
                    failed += 1
        
        embed = discord.Embed(
            title="📧 DM Campaign Sent",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Sent", value=str(count), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)
        embed.add_field(name="Target Role", value=role.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='schedule')
    @commands.has_permissions(manage_guild=True)
    async def schedule_announcement(self, ctx, channel: discord.TextChannel, 
                                   title: str, hours_from_now: int, *, message: str):
        """Schedule announcement for future time"""
        scheduled_time = get_now_pst() + timedelta(hours=hours_from_now)
        
        announcement = {
            'id': f"ANN-{get_now_pst().strftime('%Y%m%d%H%M%S')}",
            'channel_id': channel.id,
            'guild_id': ctx.guild.id,
            'author_id': ctx.author.id,
            'title': title,
            'message': message,
            'scheduled_time': scheduled_time.isoformat(),
            'sent': False,
            'sent_at': None,
            'role_ids': []
        }
        
        self.scheduled.append(announcement)
        self.save_data()
        
        embed = discord.Embed(
            title="⏰ Announcement Scheduled",
            description=title,
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Scheduled For", value=f"<t:{int(scheduled_time.timestamp())}:F>", inline=True)
        embed.add_field(name="Message", value=message[:200], inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='poll')
    @commands.has_permissions(manage_guild=True)
    async def create_poll(self, ctx, question: str, *options: str):
        """Create a poll"""
        if len(options) < 2:
            await ctx.send("❌ Poll needs at least 2 options")
            return
        
        if len(options) > 10:
            await ctx.send("❌ Poll can have max 10 options")
            return
        
        # Create embed
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.purple(),
            timestamp=get_now_pst()
        )
        
        # Add options
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{emojis[i]} Option {i+1}",
                value=option,
                inline=False
            )
        
        embed.set_footer(text="React to vote!")
        
        poll_msg = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await poll_msg.add_reaction(emojis[i])
        
        # Log poll
        self.polls.append({
            'id': f"POLL-{get_now_pst().strftime('%Y%m%d%H%M%S')}",
            'message_id': poll_msg.id,
            'channel_id': ctx.channel.id,
            'guild_id': ctx.guild.id,
            'question': question,
            'options': list(options),
            'created_at': get_now_pst().isoformat()
        })
        
        self.save_data()
    
    @commands.command(name='scheduled')
    @commands.has_permissions(manage_guild=True)
    async def view_scheduled(self, ctx):
        """View scheduled announcements"""
        guild_scheduled = [
            a for a in self.scheduled 
            if a['guild_id'] == ctx.guild.id and not a.get('sent')
        ]
        
        if not guild_scheduled:
            await ctx.send("No scheduled announcements")
            return
        
        embed = discord.Embed(
            title="⏰ Scheduled Announcements",
            description=f"{len(guild_scheduled)} pending",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for ann in guild_scheduled:
            sched_time = datetime.fromisoformat(ann['scheduled_time'])
            channel = self.bot.get_channel(ann['channel_id'])
            channel_name = channel.mention if channel else f"Channel {ann['channel_id']}"
            
            embed.add_field(
                name=ann['title'],
                value=f"**Channel:** {channel_name}\n**Time:** <t:{int(sched_time.timestamp())}:R>",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='announcehistory')
    @commands.has_permissions(manage_guild=True)
    async def announcement_history(self, ctx, limit: int = 10):
        """View announcement history"""
        guild_announcements = [
            a for a in self.announcements 
            if a['guild_id'] == ctx.guild.id
        ]
        
        if not guild_announcements:
            await ctx.send("No announcement history")
            return
        
        embed = discord.Embed(
            title="📜 Announcement History",
            description=f"Last {min(limit, len(guild_announcements))} announcements",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for ann in guild_announcements[-limit:]:
            author = self.bot.get_user(ann['author_id'])
            author_name = author.name if author else f"User {ann['author_id']}"
            
            embed.add_field(
                name=datetime.fromisoformat(ann['timestamp']).strftime('%Y-%m-%d %H:%M'),
                value=f"**Author:** {author_name}\n**Message:** {ann['message'][:100]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AnnouncementSystem(bot))
