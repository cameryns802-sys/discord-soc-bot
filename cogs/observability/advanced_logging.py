import discord
from discord.ext import commands
import logging
import json
import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

class AdvancedLogging(commands.Cog):
    """Advanced logging system with rotation and filtering"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir = Path('./logs')
        self.logs_dir.mkdir(exist_ok=True)
        
        self.config_file = self.data_dir / 'logging_config.json'
        self.config = {
            'log_level': 'INFO',
            'max_size_mb': 10,
            'backup_count': 5,
            'enabled_cogs': []  # Empty = all cogs
        }
        
        self.load_config()
        self.setup_logging()
    
    def load_config(self):
        """Load logging configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config.update(json.load(f))
    
    def save_config(self):
        """Save logging configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_logging(self):
        """Setup rotating file handlers"""
        log_level = getattr(logging, self.config['log_level'])
        
        # Main bot log
        bot_logger = logging.getLogger('soc_bot')
        bot_logger.setLevel(log_level)
        
        # Remove old handlers
        bot_logger.handlers.clear()
        
        # Rotating file handler
        max_bytes = self.config['max_size_mb'] * 1024 * 1024
        file_handler = RotatingFileHandler(
            self.logs_dir / 'bot.log',
            maxBytes=max_bytes,
            backupCount=self.config['backup_count'],
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        bot_logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        bot_logger.addHandler(console_handler)
        
        print(f"[Logging] Configured: Level={self.config['log_level']}, MaxSize={self.config['max_size_mb']}MB")
    
    @commands.command(name='view_logs')
    @commands.is_owner()
    async def view_logs(self, ctx, lines: int = 50):
        """View recent log lines (owner only)"""
        log_file = self.logs_dir / 'bot.log'
        
        if not log_file.exists():
            await ctx.send("❌ No logs found")
            return
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        if not recent_lines:
            await ctx.send("❌ Log file is empty")
            return
        
        # Format for Discord
        log_text = ''.join(recent_lines)
        
        if len(log_text) > 4000:
            log_text = log_text[-4000:]
            log_text = "...(truncated)\n" + log_text
        
        embed = discord.Embed(
            title=f"📜 Recent Logs (Last {len(recent_lines)} lines)",
            description=f"```\n{log_text}\n```",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='log_level')
    @commands.is_owner()
    async def log_level(self, ctx, level: str = None):
        """View or set log level (owner only)"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if level is None:
            await ctx.send(f"Current log level: **{self.config['log_level']}**\nValid levels: {', '.join(valid_levels)}")
            return
        
        level = level.upper()
        if level not in valid_levels:
            await ctx.send(f"❌ Invalid level. Valid levels: {', '.join(valid_levels)}")
            return
        
        self.config['log_level'] = level
        self.save_config()
        self.setup_logging()
        
        await ctx.send(f"✅ Log level set to **{level}**")
        
        logger = logging.getLogger('soc_bot')
        logger.info(f"Log level changed to {level} by {ctx.author}")
    
    @commands.command(name='export_logs')
    @commands.is_owner()
    async def export_logs(self, ctx):
        """Export log file (owner only)"""
        log_file = self.logs_dir / 'bot.log'
        
        if not log_file.exists():
            await ctx.send("❌ No logs found")
            return
        
        # Check file size
        size_mb = log_file.stat().st_size / 1024 / 1024
        
        if size_mb > 8:
            await ctx.send(f"❌ Log file too large ({size_mb:.1f} MB). Discord limit is 8 MB.")
            return
        
        await ctx.send("📤 Exporting log file...", file=discord.File(log_file))
        
        logger = logging.getLogger('soc_bot')
        logger.info(f"Logs exported by {ctx.author}")
    
    @commands.command(name='search_logs')
    @commands.is_owner()
    async def search_logs(self, ctx, *, query: str):
        """Search logs for a pattern (owner only)"""
        log_file = self.logs_dir / 'bot.log'
        
        if not log_file.exists():
            await ctx.send("❌ No logs found")
            return
        
        # Search logs
        matches = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if query.lower() in line.lower():
                    matches.append(line.strip())
        
        if not matches:
            await ctx.send(f"❌ No matches found for: `{query}`")
            return
        
        # Take last 20 matches
        matches = matches[-20:]
        result = '\n'.join(matches)
        
        if len(result) > 4000:
            result = result[-4000:]
            result = "...(truncated)\n" + result
        
        embed = discord.Embed(
            title=f"🔍 Search Results: '{query}'",
            description=f"```\n{result}\n```",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{len(matches)} matches (showing last 20)")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clear_logs')
    @commands.is_owner()
    async def clear_logs(self, ctx):
        """Clear all log files (owner only)"""
        log_file = self.logs_dir / 'bot.log'
        
        # Backup before clearing
        if log_file.exists():
            backup_name = f"bot_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            backup_file = self.logs_dir / backup_name
            log_file.rename(backup_file)
            
            await ctx.send(f"✅ Logs cleared and backed up to `{backup_name}`")
        else:
            await ctx.send("❌ No logs to clear")
        
        logger = logging.getLogger('soc_bot')
        logger.info(f"Logs cleared by {ctx.author}")
    
    @commands.command(name='log_config')
    @commands.is_owner()
    async def log_config(self, ctx):
        """View logging configuration (owner only)"""
        embed = discord.Embed(
            title="⚙️ Logging Configuration",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Log Level", value=self.config['log_level'], inline=True)
        embed.add_field(name="Max Size (MB)", value=str(self.config['max_size_mb']), inline=True)
        embed.add_field(name="Backup Count", value=str(self.config['backup_count']), inline=True)
        
        # Log file info
        log_file = self.logs_dir / 'bot.log'
        if log_file.exists():
            size_mb = log_file.stat().st_size / 1024 / 1024
            embed.add_field(name="Current Size (MB)", value=f"{size_mb:.2f}", inline=True)
        
        # Backup files
        backup_files = list(self.logs_dir.glob('bot.log.*'))
        embed.add_field(name="Backup Files", value=str(len(backup_files)), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='set_log_size')
    @commands.is_owner()
    async def set_log_size(self, ctx, size_mb: int):
        """Set max log file size in MB (owner only)"""
        if size_mb < 1 or size_mb > 100:
            await ctx.send("❌ Size must be between 1 and 100 MB")
            return
        
        self.config['max_size_mb'] = size_mb
        self.save_config()
        self.setup_logging()
        
        await ctx.send(f"✅ Max log size set to {size_mb} MB")
    
    @commands.command(name='set_log_backups')
    @commands.is_owner()
    async def set_log_backups(self, ctx, count: int):
        """Set number of backup log files (owner only)"""
        if count < 1 or count > 20:
            await ctx.send("❌ Backup count must be between 1 and 20")
            return
        
        self.config['backup_count'] = count
        self.save_config()
        self.setup_logging()
        
        await ctx.send(f"✅ Backup count set to {count}")

async def setup(bot):
    await bot.add_cog(AdvancedLogging(bot))
