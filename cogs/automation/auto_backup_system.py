import discord
from discord.ext import commands, tasks
import os
import json
import shutil
import datetime
import hashlib
from pathlib import Path

class AutoBackupSystem(commands.Cog):
    """Automated backup system with retention policies"""
    
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = Path('./backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.config_file = self.backup_dir / 'backup_config.json'
        self.config = self.load_config()
        self.hourly_backup.start()
    
    def load_config(self):
        """Load backup configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            'enabled': True,
            'hourly_enabled': True,
            'daily_enabled': True,
            'weekly_enabled': True,
            'retention_hourly': 24,  # Keep last 24 hourly backups
            'retention_daily': 7,    # Keep last 7 daily backups
            'retention_weekly': 4,   # Keep last 4 weekly backups
            'paths': ['data/', 'transcripts/', 'cogs/data_manager.py'],
            'last_hourly': None,
            'last_daily': None,
            'last_weekly': None
        }
    
    def save_config(self):
        """Save backup configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def calculate_checksum(self, file_path):
        """Calculate SHA-256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def create_backup(self, backup_type='manual'):
        """Create a backup"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{backup_type}_{timestamp}'
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        backed_up = []
        checksums = {}
        
        for path in self.config['paths']:
            src = Path(path)
            if src.exists():
                if src.is_file():
                    dest = backup_path / src.name
                    shutil.copy2(src, dest)
                    checksums[str(src)] = self.calculate_checksum(dest)
                    backed_up.append(str(src))
                elif src.is_dir():
                    dest = backup_path / src.name
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                    backed_up.append(str(src))
        
        # Save backup manifest
        manifest = {
            'timestamp': timestamp,
            'type': backup_type,
            'files': backed_up,
            'checksums': checksums,
            'bot_version': 'Phase 11',
            'created_at': datetime.datetime.now().isoformat()
        }
        
        with open(backup_path / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return backup_name, len(backed_up)
    
    def cleanup_old_backups(self, backup_type):
        """Remove old backups based on retention policy"""
        retention_key = f'retention_{backup_type}'
        retention_count = self.config.get(retention_key, 10)
        
        # Get all backups of this type
        backups = sorted([
            d for d in self.backup_dir.iterdir() 
            if d.is_dir() and d.name.startswith(f'backup_{backup_type}')
        ], key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old backups
        removed = 0
        for backup in backups[retention_count:]:
            shutil.rmtree(backup)
            removed += 1
        
        return removed
    
    @tasks.loop(hours=1)
    async def hourly_backup(self):
        """Hourly backup task"""
        if not self.config['enabled'] or not self.config['hourly_enabled']:
            return
        
        try:
            backup_name, file_count = self.create_backup('hourly')
            self.config['last_hourly'] = datetime.datetime.now().isoformat()
            self.save_config()
            
            # Cleanup old backups
            removed = self.cleanup_old_backups('hourly')
            
            print(f"[Auto-Backup] Hourly backup complete: {backup_name} ({file_count} items, {removed} old backups removed)")
            
            # Check if daily backup needed (once per day)
            if self.config['daily_enabled']:
                last_daily = self.config.get('last_daily')
                if not last_daily or (datetime.datetime.now() - datetime.datetime.fromisoformat(last_daily)).days >= 1:
                    backup_name, file_count = self.create_backup('daily')
                    self.config['last_daily'] = datetime.datetime.now().isoformat()
                    self.save_config()
                    self.cleanup_old_backups('daily')
                    print(f"[Auto-Backup] Daily backup complete: {backup_name}")
            
            # Check if weekly backup needed (once per week)
            if self.config['weekly_enabled']:
                last_weekly = self.config.get('last_weekly')
                if not last_weekly or (datetime.datetime.now() - datetime.datetime.fromisoformat(last_weekly)).days >= 7:
                    backup_name, file_count = self.create_backup('weekly')
                    self.config['last_weekly'] = datetime.datetime.now().isoformat()
                    self.save_config()
                    self.cleanup_old_backups('weekly')
                    print(f"[Auto-Backup] Weekly backup complete: {backup_name}")
        
        except Exception as e:
            print(f"[Auto-Backup] Error: {e}")
    
    @hourly_backup.before_loop
    async def before_hourly_backup(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='backup_now')
    @commands.is_owner()
    async def backup_now(self, ctx):
        """Create an immediate backup (owner only)"""
        embed = discord.Embed(
            title="💾 Creating Backup...",
            description="Creating manual backup of all data",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        msg = await ctx.send(embed=embed)
        
        try:
            backup_name, file_count = self.create_backup('manual')
            
            embed = discord.Embed(
                title="✅ Backup Complete",
                description=f"Backup created successfully: `{backup_name}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Files Backed Up", value=str(file_count), inline=True)
            embed.add_field(name="Type", value="Manual", inline=True)
            embed.add_field(name="Location", value=f"`{self.backup_dir / backup_name}`", inline=False)
            
            await msg.edit(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Backup Failed",
                description=f"Error creating backup: {str(e)}",
                color=discord.Color.red()
            )
            await msg.edit(embed=embed)
    
    @commands.command(name='list_backups')
    @commands.is_owner()
    async def list_backups(self, ctx, backup_type: str = None):
        """List all available backups (owner only)"""
        backups = sorted([
            d for d in self.backup_dir.iterdir() 
            if d.is_dir() and (not backup_type or backup_type in d.name)
        ], key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backups:
            await ctx.send("📦 No backups found")
            return
        
        embed = discord.Embed(
            title="📦 Available Backups",
            description=f"Total: {len(backups)} backups",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        for i, backup in enumerate(backups[:15], 1):  # Show last 15
            manifest_file = backup / 'manifest.json'
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                size = sum(f.stat().st_size for f in backup.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                
                embed.add_field(
                    name=f"{i}. {backup.name}",
                    value=f"Files: {len(manifest['files'])} | Size: {size_mb:.2f} MB\nCreated: {manifest['created_at'][:19]}",
                    inline=False
                )
        
        if len(backups) > 15:
            embed.set_footer(text=f"Showing 15 of {len(backups)} backups. Use !backup_config to view all")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='restore_backup')
    @commands.is_owner()
    async def restore_backup(self, ctx, backup_name: str):
        """Restore from a backup (owner only)"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            await ctx.send(f"❌ Backup `{backup_name}` not found")
            return
        
        # Confirm restoration
        embed = discord.Embed(
            title="⚠️ Confirm Backup Restoration",
            description=f"Are you sure you want to restore from `{backup_name}`?\n\n**This will overwrite current data!**",
            color=discord.Color.orange()
        )
        embed.add_field(name="⚠️ Warning", value="Current data will be backed up first", inline=False)
        embed.add_field(name="To Proceed", value="React with ✅ within 30 seconds", inline=False)
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '❌':
                await ctx.send("❌ Restoration cancelled")
                return
            
            # Create backup of current state first
            current_backup, _ = self.create_backup('pre_restore')
            
            # Restore from backup
            manifest_file = backup_path / 'manifest.json'
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            restored = []
            for item in manifest['files']:
                src = backup_path / Path(item).name
                dest = Path(item)
                
                if src.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    restored.append(item)
                elif src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                    restored.append(item)
            
            embed = discord.Embed(
                title="✅ Backup Restored",
                description=f"Successfully restored from `{backup_name}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Files Restored", value=str(len(restored)), inline=True)
            embed.add_field(name="Current State Backup", value=f"`{current_backup}`", inline=True)
            embed.add_field(name="⚠️ Restart Required", value="Use `!restart` to apply changes", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Restoration failed: {str(e)}")
    
    @commands.command(name='verify_backup')
    @commands.is_owner()
    async def verify_backup(self, ctx, backup_name: str):
        """Verify backup integrity (owner only)"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            await ctx.send(f"❌ Backup `{backup_name}` not found")
            return
        
        manifest_file = backup_path / 'manifest.json'
        if not manifest_file.exists():
            await ctx.send(f"❌ Backup manifest not found")
            return
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        verified = 0
        failed = []
        
        for file_path, expected_checksum in manifest.get('checksums', {}).items():
            backup_file = backup_path / Path(file_path).name
            if backup_file.exists():
                actual_checksum = self.calculate_checksum(backup_file)
                if actual_checksum == expected_checksum:
                    verified += 1
                else:
                    failed.append(file_path)
            else:
                failed.append(file_path)
        
        embed = discord.Embed(
            title="🔍 Backup Verification",
            description=f"Backup: `{backup_name}`",
            color=discord.Color.green() if not failed else discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="✅ Verified", value=str(verified), inline=True)
        embed.add_field(name="❌ Failed", value=str(len(failed)), inline=True)
        embed.add_field(name="Status", value="✅ Intact" if not failed else "⚠️ Corrupted", inline=True)
        
        if failed:
            embed.add_field(name="Failed Files", value="\n".join(failed[:10]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='backup_config')
    @commands.is_owner()
    async def backup_config_cmd(self, ctx, setting: str = None, value: str = None):
        """Configure backup settings (owner only)"""
        if not setting:
            embed = discord.Embed(
                title="⚙️ Backup Configuration",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            embed.add_field(name="Enabled", value="✅" if self.config['enabled'] else "❌", inline=True)
            embed.add_field(name="Hourly", value="✅" if self.config['hourly_enabled'] else "❌", inline=True)
            embed.add_field(name="Daily", value="✅" if self.config['daily_enabled'] else "❌", inline=True)
            embed.add_field(name="Retention (Hourly)", value=str(self.config['retention_hourly']), inline=True)
            embed.add_field(name="Retention (Daily)", value=str(self.config['retention_daily']), inline=True)
            embed.add_field(name="Retention (Weekly)", value=str(self.config['retention_weekly']), inline=True)
            embed.add_field(name="Last Hourly", value=self.config.get('last_hourly', 'Never')[:19], inline=False)
            embed.add_field(name="Last Daily", value=self.config.get('last_daily', 'Never')[:19], inline=False)
            
            await ctx.send(embed=embed)
            return
        
        # Update setting
        if setting == 'enabled':
            self.config['enabled'] = value.lower() in ['true', '1', 'yes', 'on']
        elif setting in ['hourly_enabled', 'daily_enabled', 'weekly_enabled']:
            self.config[setting] = value.lower() in ['true', '1', 'yes', 'on']
        elif setting in ['retention_hourly', 'retention_daily', 'retention_weekly']:
            self.config[setting] = int(value)
        else:
            await ctx.send(f"❌ Unknown setting: {setting}")
            return
        
        self.save_config()
        await ctx.send(f"✅ Updated {setting} to {value}")
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.hourly_backup.cancel()

async def setup(bot):
    await bot.add_cog(AutoBackupSystem(bot))
