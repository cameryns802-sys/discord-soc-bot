"""
Auto-Sync Control Cog - Commands for managing file/folder synchronization
Monitor auto-sync status, trigger manual syncs, view sync logs
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
import asyncio
from cogs.core.pst_timezone import get_now_pst

class AutoSyncControlCog(commands.Cog):
    """Auto-sync monitoring and control commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_auto_sync_manager(self):
        """Get AutoSyncManager instance"""
        if hasattr(self.bot, 'auto_sync_manager'):
            return self.bot.auto_sync_manager
        return None
    
    @commands.command(name='autosyncstatus')
    @commands.is_owner()
    async def autosync_status(self, ctx):
        """Show auto-sync status"""
        manager = self.get_auto_sync_manager()
        
        if not manager:
            await ctx.send("❌ Auto-sync manager not available")
            return
        
        stats = await manager.get_sync_stats()
        
        embed = discord.Embed(
            title="👁️ Auto-Sync Status",
            description="Real-time file monitoring and sync",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        watching_status = "🟢 ACTIVE" if stats['is_watching'] else "🔴 INACTIVE"
        embed.add_field(name="Watcher Status", value=watching_status, inline=True)
        embed.add_field(name="Tracked Files", value=f"📋 {stats['tracked_files']}", inline=True)
        embed.add_field(name="Loaded Cogs", value=f"⚙️ {stats['loaded_cogs']}", inline=True)
        
        embed.add_field(name="Watch Directories", value="━" * 25, inline=False)
        for dir_path in stats.get('watch_directories', []):
            embed.add_field(name="📁", value=dir_path, inline=False)
        
        embed.add_field(name="Recent Events", value="━" * 25, inline=False)
        
        recent_events = stats.get('recent_events', [])
        if recent_events:
            for event in recent_events[-5:]:
                timestamp = event.get('timestamp', '')[:10]
                event_type = event.get('type', 'UNKNOWN')
                status = event.get('status', 'unknown')
                
                emoji_map = {
                    'COG_LOAD': '⚙️',
                    'COG_RELOAD': '🔄',
                    'DATA_SYNC': '📊'
                }
                emoji = emoji_map.get(event_type, '📋')
                
                embed.add_field(
                    name=f"{emoji} {event_type}",
                    value=f"{status} - {timestamp}",
                    inline=False
                )
        else:
            embed.add_field(name="No Events", value="No recent sync events", inline=False)
        
        embed.add_field(name="Statistics", value="━" * 25, inline=False)
        embed.add_field(
            name="Total Events Logged",
            value=f"📊 {stats.get('total_events_logged', 0)}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='autosyncnow')
    @commands.is_owner()
    async def autosync_force(self, ctx):
        """Force immediate auto-sync check"""
        manager = self.get_auto_sync_manager()
        
        if not manager:
            await ctx.send("❌ Auto-sync manager not available")
            return
        
        async with ctx.typing():
            results = await manager.force_sync()
        
        embed = discord.Embed(
            title="✅ Manual Sync Complete",
            description="Files and folders have been synchronized",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="🆕 New Cogs Loaded",
            value=str(results['new_cogs']),
            inline=True
        )
        embed.add_field(
            name="🔄 Cogs Reloaded",
            value=str(results['reloaded_cogs']),
            inline=True
        )
        embed.add_field(
            name="📊 Data Files Synced",
            value=str(results['synced_data']),
            inline=True
        )
        
        embed.set_footer(text=f"Synced at: {results['timestamp']}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='autosynclog')
    @commands.is_owner()
    async def autosync_log(self, ctx, lines: int = 20):
        """Show auto-sync log"""
        log_file = 'data/autosync_log.json'
        
        if not os.path.exists(log_file):
            await ctx.send("📭 No sync log yet")
            return
        
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except:
            await ctx.send("❌ Error reading sync log")
            return
        
        if not logs:
            await ctx.send("📭 Sync log is empty")
            return
        
        # Get last N entries
        recent_logs = logs[-lines:]
        
        embed = discord.Embed(
            title="📋 Auto-Sync Log",
            description=f"Last {len(recent_logs)} events",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Group by type
        by_type = {}
        for log in recent_logs:
            log_type = log.get('type', 'UNKNOWN')
            by_type[log_type] = by_type.get(log_type, 0) + 1
        
        embed.add_field(name="Event Summary", value="━" * 25, inline=False)
        for log_type, count in by_type.items():
            embed.add_field(name=log_type, value=f"📊 {count}", inline=True)
        
        embed.add_field(name="Event Details", value="━" * 25, inline=False)
        
        # Show details
        for log in recent_logs[-10:]:
            timestamp = log.get('timestamp', '')[-8:]
            event_type = log.get('type', 'UNKNOWN')
            status = log.get('status', 'unknown')
            file_path = log.get('file', '')
            
            file_name = file_path.split('.')[-2].split('/')[-1] if '/' in file_path else file_path
            
            emoji_map = {
                'COG_LOAD': '⚙️',
                'COG_RELOAD': '🔄',
                'DATA_SYNC': '📊'
            }
            emoji = emoji_map.get(event_type, '📋')
            
            embed.add_field(
                name=f"{emoji} {file_name} - {timestamp}",
                value=f"{status}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='autosync')
    @commands.is_owner()
    async def autosync_control(self, ctx, action: str = 'status'):
        """Auto-sync control commands"""
        manager = self.get_auto_sync_manager()
        
        if not manager:
            await ctx.send("❌ Auto-sync manager not available")
            return
        
        action = action.lower()
        
        if action == 'start':
            if manager.is_watching:
                await ctx.send("✅ Auto-sync already running")
            else:
                manager.start_watching()
                await ctx.send("✅ Auto-sync started")
        
        elif action == 'stop':
            if not manager.is_watching:
                await ctx.send("⚠️ Auto-sync already stopped")
            else:
                manager.stop_watching()
                await ctx.send("✅ Auto-sync stopped")
        
        elif action == 'restart':
            manager.stop_watching()
            await asyncio.sleep(1)
            manager.start_watching()
            await ctx.send("✅ Auto-sync restarted")
        
        elif action == 'watch':
            watched = [str(d.relative_to(manager.watch_path)) for d in manager.watch_dirs]
            embed = discord.Embed(
                title="📁 Watched Directories",
                description=f"Monitoring {len(watched)} location(s)",
                color=discord.Color.blue()
            )
            for d in watched:
                embed.add_field(name="📁", value=d, inline=False)
            await ctx.send(embed=embed)
        
        else:
            embed = discord.Embed(
                title="❓ Auto-Sync Commands",
                color=discord.Color.blue()
            )
            embed.add_field(name="!autosync status", value="Show sync status", inline=False)
            embed.add_field(name="!autosync start", value="Start watcher", inline=False)
            embed.add_field(name="!autosync stop", value="Stop watcher", inline=False)
            embed.add_field(name="!autosync restart", value="Restart watcher", inline=False)
            embed.add_field(name="!autosync watch", value="Show watched directories", inline=False)
            embed.add_field(name="!autosyncnow", value="Force immediate sync", inline=False)
            embed.add_field(name="!autosyncstatus", value="Detailed status", inline=False)
            embed.add_field(name="!autosynclog [lines]", value="View sync log", inline=False)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoSyncControlCog(bot))
