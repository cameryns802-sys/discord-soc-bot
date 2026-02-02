import discord
from discord.ext import commands
import os
import sys
import asyncio
import datetime

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
            title="🛑 Bot Shutdown Initiated",
            description="Gracefully shutting down the bot...",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="🔴 Shutting down...", inline=True)
        embed.add_field(name="Data", value="✅ Being saved", inline=True)
        
        await ctx.send(embed=embed)
        
        # Save all data via data manager
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data_manager.save_data()
            print("✅ Data saved successfully")
        
        # Notify all guilds
        notification_embed = discord.Embed(
            title="🛑 Bot Shutting Down",
            description="The SOC bot is shutting down for maintenance.",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        notification_embed.add_field(name="Status", value="🔴 Offline", inline=True)
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
            title="🔄 Bot Restart Initiated",
            description="Restarting the bot...",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="🔄 Restarting...", inline=True)
        embed.add_field(name="Expected Downtime", value="~5-10 seconds", inline=True)
        
        await ctx.send(embed=embed)
        
        # Save all data via data manager
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            data_manager.save_data()
            print("✅ Data saved successfully")
        
        # Notify all guilds
        notification_embed = discord.Embed(
            title="🔄 Bot Restarting",
            description="The SOC bot is restarting. Will be back online shortly.",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        notification_embed.add_field(name="Status", value="🔄 Restarting", inline=True)
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
        await ctx.send("🚨 **EMERGENCY STOP INITIATED** - Immediate shutdown...")
        
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
                title="✅ Cog Reloaded",
                description=f"Successfully reloaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="✅ Reloaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Reload] {ctx.author} reloaded cog: {extension}")
            
        except commands.ExtensionNotLoaded:
            await ctx.send(f"❌ Cog `{cog_name}` is not loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"❌ Error reloading cog: {str(e)}")
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
                title="✅ Cog Loaded",
                description=f"Successfully loaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="✅ Loaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Load] {ctx.author} loaded cog: {extension}")
            
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"❌ Cog `{cog_name}` is already loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"❌ Error loading cog: {str(e)}")
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
            await ctx.send("❌ Cannot unload owner commands cog")
            return
        
        try:
            extension = f'cogs.{cog_name}'
            await self.bot.unload_extension(extension)
            
            embed = discord.Embed(
                title="✅ Cog Unloaded",
                description=f"Successfully unloaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Extension", value=extension, inline=True)
            embed.add_field(name="Status", value="✅ Unloaded", inline=True)
            
            await ctx.send(embed=embed)
            print(f"[Unload] {ctx.author} unloaded cog: {extension}")
            
        except commands.ExtensionNotLoaded:
            await ctx.send(f"❌ Cog `{cog_name}` is not loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
        except Exception as e:
            await ctx.send(f"❌ Error unloading cog: {str(e)}")
            print(f"[Unload] Error unloading {cog_name}: {e}")
    
    @commands.command(name='list_cogs', aliases=['cogs'])
    async def list_cogs(self, ctx):
        """List all loaded cogs (owner only)
        
        Usage: !list_cogs
        Aliases: !cogs
        """
        cogs = sorted([cog for cog in self.bot.cogs])
        
        embed = discord.Embed(
            title="📦 Loaded Cogs",
            description=f"Total: {len(cogs)} cogs loaded",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        # Split into chunks for embed fields
        chunk_size = 20
        for i in range(0, len(cogs), chunk_size):
            chunk = cogs[i:i+chunk_size]
            field_name = f"Cogs {i+1}-{min(i+chunk_size, len(cogs))}"
            field_value = "\n".join([f"• {cog}" for cog in chunk])
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
        uptime_delta = datetime.datetime.now(datetime.UTC) - self.bot.uptime if hasattr(self.bot, 'uptime') else datetime.timedelta(seconds=0)
        uptime_str = str(uptime_delta).split('.')[0]
        
        # Get system info
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent(interval=1)
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        # Bot Info
        embed.add_field(name="🤖 Bot", value=f"{self.bot.user.name}\n#{self.bot.user.discriminator}", inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="📡 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Guild/User Stats
        total_members = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="🏛️ Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(total_members), inline=True)
        embed.add_field(name="📝 Text Channels", value=str(len(list(self.bot.get_all_channels()))), inline=True)
        
        # Command Stats
        embed.add_field(name="⚡ Slash Commands", value=str(len(list(self.bot.tree._get_all_commands()))), inline=True)
        embed.add_field(name="📦 Cogs", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(name="💻 Prefix Commands", value=str(len(self.bot.commands)), inline=True)
        
        # System Resources
        embed.add_field(name="🧠 Memory", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="💾 CPU", value=f"{cpu_percent:.1f}%", inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        
        # Discord.py version
        embed.add_field(name="📚 Discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="🖥️ System", value=platform.system(), inline=True)
        embed.add_field(name="⚙️ Architecture", value=platform.machine(), inline=True)
        
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
                    title="✅ Commands Synced",
                    description=f"Synced {len(synced)} slash commands to guild {guild_id}",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.add_field(name="Scope", value="Guild-Specific", inline=True)
                embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
                
            else:
                synced = await self.bot.tree.sync()
                
                embed = discord.Embed(
                    title="✅ Commands Synced",
                    description=f"Synced {len(synced)} slash commands globally",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.add_field(name="Scope", value="Global", inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
                embed.add_field(name="⚠️ Note", value="May take up to 1 hour to propagate", inline=False)
            
            await ctx.send(embed=embed)
            print(f"[Sync] Commands synced by {ctx.author} - {len(synced)} commands")
            
        except Exception as e:
            await ctx.send(f"❌ Error syncing commands: {str(e)}")
            print(f"[Sync] Error: {e}")

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))
