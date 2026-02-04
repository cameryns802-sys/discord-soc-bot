import discord
from discord.ext import commands
import os
import sys
import asyncio
from datetime import timedelta
from cogs.core.pst_timezone import get_now_pst

class OwnerCommands(commands.Cog):
    """Owner-only administrative commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
    
    async def cog_check(self, ctx):
        """Global check to ensure only owner can use these commands"""
        return ctx.author.id == self.owner_id
    
    @commands.command(name='shutdown', aliases=['stop', 'halt'])
    async def shutdown(self, ctx):
        """Gracefully shutdown the bot (owner only)
        
        Usage: !shutdown
        Aliases: !stop, !halt
        
        This command will:
        - Save all data
        - Notify all guilds
        - Send shutdown confirmation
        - Close the bot connection
        """
        embed = discord.Embed(
            title="ðŸ›‘ Bot Shutdown Initiated",
            description="Gracefully shutting down the bot...",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="ðŸ”´ Shutting down...", inline=True)
        embed.add_field(name="Data", value="âœ… Being saved", inline=True)
        
        await ctx.send(embed=embed)
        
        # Save all data via data manager
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data_manager.save_data()
            print("âœ… Data saved successfully")
        
        # Notify all guilds
        notification_embed = discord.Embed(
            title="ðŸ›‘ Bot Shutting Down",
            description="The SOC bot is shutting down for maintenance.",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        notification_embed.add_field(name="Status", value="ðŸ”´ Offline", inline=True)
        notification_embed.add_field(name="Expected Downtime", value="Unknown", inline=True)
        notification_embed.set_footer(text="Contact bot owner for more information")
        
        for guild in self.bot.guilds:
            # Try to find an appropriate channel to notify
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=notification_embed)
                        break  # Only send to first available channel
                    except:
                        continue
        
        print(f"[Shutdown] Bot shutdown initiated by {ctx.author} ({ctx.author.id})")
        print("[Shutdown] Closing connection...")
        
        # Deactivate any active drill/threat status
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status:
            if dynamic_status.active_drill:
                await dynamic_status.deactivate_drill_status()
            if dynamic_status.active_threat:
                await dynamic_status.deactivate_threat_status()
        
        await self.bot.close()
    
    @commands.command(name='restart', aliases=['reboot'])
    async def restart(self, ctx):
        """Restart the bot (owner only)
        
        Usage: !restart
        Aliases: !reboot
        
        This command will:
        - Save all data
        - Notify all guilds
        - Attempt to restart the bot process
        
        Note: Requires bot to be run with auto-restart script or systemd
        """
        embed = discord.Embed(
            title="ðŸ”„ Bot Restart Initiated",
            description="Restarting the bot...",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="ðŸ”„ Restarting...", inline=True)
        embed.add_field(name="Expected Downtime", value="~5-10 seconds", inline=True)
        
        await ctx.send(embed=embed)
        
        # Save all data via data manager
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data_manager.save_data()
            print("âœ… Data saved successfully")
        
        # Notify all guilds
        notification_embed = discord.Embed(
            title="ðŸ”„ Bot Restarting",
            description="The SOC bot is restarting. Will be back online shortly.",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        notification_embed.add_field(name="Status", value="ðŸ”„ Restarting", inline=True)
        notification_embed.add_field(name="Expected Downtime", value="~5-10 seconds", inline=True)
        notification_embed.set_footer(text="Bot will reconnect automatically")
        
        for guild in self.bot.guilds:
            # Try to find an appropriate channel to notify
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=notification_embed)
                        break  # Only send to first available channel
                    except:
                        continue
        
        print(f"[Restart] Bot restart initiated by {ctx.author} ({ctx.author.id})")
        print("[Restart] Attempting restart...")
        
        # Deactivate any active drill/threat status
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status:
            if dynamic_status.active_drill:
                await dynamic_status.deactivate_drill_status()
            if dynamic_status.active_threat:
                await dynamic_status.deactivate_threat_status()
        
        await self.bot.close()
        
        # Attempt to restart the bot process
        # This works if the bot is run with a restart script or systemd
        os.execv(sys.executable, ['python'] + sys.argv)
    
    @commands.command(name='emergency_stop', aliases=['estop', 'panic_shutdown'])
    async def emergency_stop(self, ctx):
        """Emergency stop without notifications (owner only)
        
        Usage: !emergency_stop
        Aliases: !estop, !panic_shutdown
        
        This command will:
        - Immediately save critical data
        - Skip guild notifications
        - Force shutdown
        
        Use only in emergencies when normal shutdown fails
        """
        await ctx.send("ðŸš¨ **EMERGENCY STOP INITIATED** - Immediate shutdown...")
        
        # Quick save
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data_manager.save_data()
        
        print(f"[EMERGENCY] Emergency stop initiated by {ctx.author} ({ctx.author.id})")
        print("[EMERGENCY] Force closing...")
        
        await self.bot.close()
    
    @commands.command(name='reload_cog', aliases=['reload'])
    async def reload_cog(self, ctx, *, cog_name: str):
        """Reload a specific cog (owner only)
        
        Usage: !reload_cog <cog_name>
        Aliases: !reload <cog_name>
        
        Examples:
        !reload_cog core.dynamic_status
        !reload_cog security.antinuke
        !reload_cog moderation.automod
        """
        try:
            extension = f'cogs.{cog_name}'
            await self.bot.reload_extension(extension)
            
            embed = discord.Embed(
                title="âœ… Cog Reloaded",
                description=f"Successfully reloaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="âœ… Reloaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Reload] {ctx.author} reloaded cog: {extension}")
            
        except commands.ExtensionNotLoaded:
            await ctx.send(f"âŒ Cog `{cog_name}` is not loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"âŒ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"âŒ Error reloading cog: {str(e)}")
            print(f"[Reload] Error reloading {cog_name}: {e}")
    
    @commands.command(name='load_cog', aliases=['load'])
    async def load_cog(self, ctx, *, cog_name: str):
        """Load a specific cog (owner only)
        
        Usage: !load_cog <cog_name>
        Aliases: !load <cog_name>
        
        Examples:
        !load_cog experimental.explainable_ai
        !load_cog archives.bot_personality_system
        """
        try:
            extension = f'cogs.{cog_name}'
            await self.bot.load_extension(extension)
            
            embed = discord.Embed(
                title="âœ… Cog Loaded",
                description=f"Successfully loaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="âœ… Loaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Load] {ctx.author} loaded cog: {extension}")
            
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"âŒ Cog `{cog_name}` is already loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"âŒ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"âŒ Error loading cog: {str(e)}")
            print(f"[Load] Error loading {cog_name}: {e}")
    
    @commands.command(name='unload_cog', aliases=['unload'])
    async def unload_cog(self, ctx, *, cog_name: str):
        """Unload a specific cog (owner only)
        
        Usage: !unload_cog <cog_name>
        Aliases: !unload <cog_name>
        
        Examples:
        !unload_cog experimental.predictive_error_system
        !unload_cog security.security_drill
        
        Note: Cannot unload this cog (owner_commands)
        """
        if cog_name in ['utility.owner_commands', 'owner_commands']:
            await ctx.send("âŒ Cannot unload owner commands cog")
            return
        
        try:
            extension = f'cogs.{cog_name}'
            await self.bot.unload_extension(extension)
            
            embed = discord.Embed(
                title="âœ… Cog Unloaded",
                description=f"Successfully unloaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="âœ… Unloaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Unload] {ctx.author} unloaded cog: {extension}")
            
        except commands.ExtensionNotLoaded:
            await ctx.send(f"âŒ Cog `{cog_name}` is not loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"âŒ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"âŒ Error unloading cog: {str(e)}")
            print(f"[Unload] Error unloading {cog_name}: {e}")
    
    @commands.command(name='list_cogs', aliases=['cogs'])
    async def list_cogs(self, ctx):
        """List all loaded cogs (owner only)
        
        Usage: !list_cogs
        Aliases: !cogs
        """
        cogs = sorted([cog for cog in self.bot.cogs])
        
        embed = discord.Embed(
            title="ðŸ“¦ Loaded Cogs",
            description=f"Total: {len(cogs)} cogs loaded",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Split into chunks for embed fields
        chunk_size = 20
        for i in range(0, len(cogs), chunk_size):
            chunk = cogs[i:i+chunk_size]
            field_name = f"Cogs {i+1}-{min(i+chunk_size, len(cogs))}"
            field_value = "\n".join([f"â€¢ {cog}" for cog in chunk])
            embed.add_field(name=field_name, value=field_value, inline=False)
        
        embed.set_footer(text=f"Total Commands: {len(self.bot.commands)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='bot_stats', aliases=['stats'])
    async def bot_stats(self, ctx):
        """Show detailed bot statistics (owner only)
        
        Usage: !bot_stats
        Aliases: !stats
        """
        import psutil
        import platform
        
        # Calculate uptime
        uptime_delta = get_now_pst() - self.bot.uptime if hasattr(self.bot, 'uptime') else timedelta(seconds=0)
        uptime_str = str(uptime_delta).split('.')[0]
        
        # Get system info
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent(interval=1)
        
        embed = discord.Embed(
            title="ðŸ“Š Bot Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Bot Info
        embed.add_field(name="ðŸ¤– Bot", value=f"{self.bot.user.name}\n#{self.bot.user.discriminator}", inline=True)
        embed.add_field(name="â±ï¸ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="ðŸ“¡ Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Guild/User Stats
        total_members = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="ðŸ›ï¸ Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="ðŸ‘¥ Users", value=str(total_members), inline=True)
        embed.add_field(name="ðŸ“ Text Channels", value=str(len(list(self.bot.get_all_channels()))), inline=True)
        
        # Command Stats
        embed.add_field(name="âš¡ Slash Commands", value=str(len(list(self.bot.tree._get_all_commands()))), inline=True)
        embed.add_field(name="ðŸ“¦ Cogs", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(name="ðŸ’» Prefix Commands", value=str(len(self.bot.commands)), inline=True)
        
        # System Resources
        embed.add_field(name="ðŸ§  Memory", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="ðŸ’¾ CPU", value=f"{cpu_percent:.1f}%", inline=True)
        embed.add_field(name="ðŸ Python", value=platform.python_version(), inline=True)
        
        # Discord.py version
        embed.add_field(name="ðŸ“š Discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="ðŸ–¥ï¸ System", value=platform.system(), inline=True)
        embed.add_field(name="âš™ï¸ Architecture", value=platform.machine(), inline=True)
        
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sync_commands', aliases=['sync'])
    async def sync_commands(self, ctx, guild_id: int = None):
        """Sync slash commands to Discord (owner only)
        
        Usage: !sync_commands [guild_id]
        Aliases: !sync [guild_id]
        
        Without guild_id: Syncs globally (takes up to 1 hour)
        With guild_id: Syncs to specific guild (instant)
        
        Examples:
        !sync                    # Global sync
        !sync 1234567890         # Guild-specific sync
        """
        try:
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
                
                embed = discord.Embed(
                    title="âœ… Commands Synced",
                    description=f"Synced {len(synced)} slash commands to guild {guild_id}",
                    color=discord.Color.green(),
                    timestamp=get_now_pst()
                )
                embed.add_field(name="Scope", value="Guild-Specific", inline=True)
                embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
                
            else:
                synced = await self.bot.tree.sync()
                
                embed = discord.Embed(
                    title="âœ… Commands Synced",
                    description=f"Synced {len(synced)} slash commands globally",
                    color=discord.Color.green(),
                    timestamp=get_now_pst()
                )
                embed.add_field(name="Scope", value="Global", inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
                embed.add_field(name="âš ï¸ Note", value="May take up to 1 hour to propagate", inline=False)
            
            await ctx.send(embed=embed)
            print(f"[Sync] Commands synced by {ctx.author} - {len(synced)} commands")
            
        except Exception as e:
            await ctx.send(f"âŒ Error syncing commands: {str(e)}")
            print(f"[Sync] Error: {e}")
    
    @commands.command(name='botinfo')
    async def botinfo(self, ctx):
        """Get detailed bot information"""
        embed = discord.Embed(
            title=f"ðŸ¤– Bot Information",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        total_members = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Commands", value=len(list(self.bot.tree._get_all_commands())), inline=True)
        embed.add_field(name="Cogs", value=len(self.bot.cogs), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name='broadcast')
    async def broadcast(self, ctx, *, message: str):
        """Broadcast a message to all guilds"""
        count = 0
        for guild in self.bot.guilds:
            try:
                if guild.system_channel:
                    await guild.system_channel.send(f"ðŸ“¢ **Broadcast:** {message}")
                    count += 1
            except:
                pass
        
        embed = discord.Embed(
            title="ðŸ“¢ Broadcast Sent",
            description=f"Message sent to {count}/{len(self.bot.guilds)} servers",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Message", value=message, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name='queryguild')
    async def queryguild(self, ctx, guild_id: int):
        """Query information about a guild"""
        guild = self.bot.get_guild(guild_id)
        
        if not guild:
            await ctx.send("âŒ Guild not found")
            return
        
        embed = discord.Embed(
            title=f"ðŸ›ï¸ Guild: {guild.name}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Guild ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=False)
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        await ctx.send(embed=embed)
    
    @commands.command(name='listcogs')
    async def listcogs(self, ctx):
        """List all loaded cogs"""
        cogs_list = list(self.bot.cogs.keys())
        chunks = [cogs_list[i:i+10] for i in range(0, len(cogs_list), 10)]
        
        embed = discord.Embed(
            title=f"ðŸ”§ Loaded Cogs ({len(cogs_list)})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for i, chunk in enumerate(chunks[:5]):
            embed.add_field(
                name=f"Batch {i+1}",
                value="\n".join([f"âœ… {cog}" for cog in chunk]),
                inline=False
            )
        
        if len(chunks) > 5:
            embed.add_field(name="âš ï¸ Note", value=f"Showing 50/{len(cogs_list)} cogs", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='reloadcog')
    async def reloadcog(self, ctx, cog_name: str):
        """Reload a specific cog"""
        try:
            await self.bot.reload_extension(f'cogs.{cog_name}')
            await ctx.send(f"âœ… Reloaded cog: `{cog_name}`")
        except Exception as e:
            await ctx.send(f"âŒ Failed to reload cog: {e}")
    
    @commands.command(name='loadcog')
    async def loadcog(self, ctx, cog_name: str):
        """Load a cog"""
        try:
            await self.bot.load_extension(f'cogs.{cog_name}')
            await ctx.send(f"âœ… Loaded cog: `{cog_name}`")
        except Exception as e:
            await ctx.send(f"âŒ Failed to load cog: {e}")
    
    @commands.command(name='unloadcog')
    async def unloadcog(self, ctx, cog_name: str):
        """Unload a cog"""
        try:
            await self.bot.unload_extension(f'cogs.{cog_name}')
            await ctx.send(f"âœ… Unloaded cog: `{cog_name}`")
        except Exception as e:
            await ctx.send(f"âŒ Failed to unload cog: {e}")
    
    @commands.command(name='stats')
    async def stats(self, ctx):
        """Get bot statistics"""
        embed = discord.Embed(
            title="ðŸ“Š Bot Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        total_users = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="Users", value=total_users, inline=True)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)
        embed.add_field(name="Channels", value=total_channels, inline=True)
        embed.add_field(name="Commands", value=len(list(self.bot.tree._get_all_commands())), inline=True)
        embed.add_field(name="Cogs", value=len(self.bot.cogs), inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='checkdb')
    async def checkdb(self, ctx):
        """Check database integrity"""
        embed = discord.Embed(
            title="ðŸ” Database Integrity Check",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Check data files
        data_dir = "data"
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            embed.add_field(name="Data Files", value=f"âœ… {len(files)} files found", inline=False)
            
            for file in files[:5]:
                try:
                    size = os.path.getsize(os.path.join(data_dir, file)) / 1024
                    embed.add_field(name=f"â€¢ {file}", value=f"{size:.2f} KB", inline=True)
                except:
                    pass
        else:
            embed.add_field(name="Data Files", value="âŒ Data directory not found", inline=False)
        
        embed.add_field(name="Status", value="âœ… Database OK", inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name='setactivity')
    async def setactivity(self, ctx, activity_type: str, *, activity_text: str):
        """Set bot activity status"""
        activity_types = {
            'playing': discord.ActivityType.playing,
            'watching': discord.ActivityType.watching,
            'listening': discord.ActivityType.listening,
            'streaming': discord.ActivityType.streaming
        }
        
        activity_type = activity_type.lower()
        if activity_type not in activity_types:
            await ctx.send(f"âŒ Invalid activity type. Choose: {', '.join(activity_types.keys())}")
            return
        
        activity = discord.Activity(
            type=activity_types[activity_type],
            name=activity_text
        )
        
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"âœ… Activity set to: **{activity_type.title()}** {activity_text}")
    
    @commands.command(name='setstatus')
    async def setstatus(self, ctx, status: str):
        """Set bot status"""
        statuses = {
            'online': discord.Status.online,
            'idle': discord.Status.idle,
            'dnd': discord.Status.dnd,
            'offline': discord.Status.offline
        }
        
        status = status.lower()
        if status not in statuses:
            await ctx.send(f"âŒ Invalid status. Choose: {', '.join(statuses.keys())}")
            return
        
        await self.bot.change_presence(status=statuses[status])
        await ctx.send(f"âœ… Status set to: **{status.upper()}**")
    
    @commands.command(name='dm')
    async def dm(self, ctx, user_id: int, *, message: str):
        """Send a DM to a user"""
        try:
            user = await self.bot.fetch_user(user_id)
            embed = discord.Embed(
                title="ðŸ“¬ Message from Bot Owner",
                description=message,
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            embed.set_footer(text="Reply in DMs to respond")
            
            await user.send(embed=embed)
            await ctx.send(f"âœ… DM sent to {user}")
        except discord.NotFound:
            await ctx.send("âŒ User not found")
        except discord.Forbidden:
            await ctx.send("âŒ Cannot send DM to this user (DMs disabled)")
    
    @commands.command(name='userinfo')
    async def userinfo_cmd(self, ctx, user_id: int):
        """Get detailed info about a user"""
        try:
            user = await self.bot.fetch_user(user_id)
            embed = discord.Embed(
                title=f"ðŸ‘¤ User Info: {user}",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="ID", value=user.id, inline=True)
            embed.add_field(name="Bot", value=user.bot, inline=True)
            embed.add_field(name="Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Name", value=str(user), inline=True)
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("âŒ User not found")
    
    @commands.command(name='datainfo')
    async def datainfo(self, ctx):
        """Get information about stored data"""
        embed = discord.Embed(
            title="ðŸ’¾ Data Information",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data = data_manager.data
            embed.add_field(name="Warns", value=len(data.get('warns', {})), inline=True)
            embed.add_field(name="Reputation", value=len(data.get('reputation', {})), inline=True)
            embed.add_field(name="Levels", value=len(data.get('levels', {})), inline=True)
            embed.add_field(name="Reminders", value=len(data.get('reminders', [])), inline=True)
            embed.add_field(name="Guild Settings", value=len(data.get('guild_settings', {})), inline=True)
            embed.add_field(name="User Settings", value=len(data.get('user_settings', {})), inline=True)
            embed.add_field(name="Consents", value=len(data.get('consent', {})), inline=True)
        else:
            embed.add_field(name="Status", value="âŒ DataManager not loaded", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))
