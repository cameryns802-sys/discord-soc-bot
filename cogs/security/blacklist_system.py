import discord
from discord.ext import commands
import json
import datetime
from pathlib import Path

class BlacklistSystem(commands.Cog):
    """User and guild blacklist system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.blacklist_file = self.data_dir / 'blacklist.json'
        self.blacklist = self.load_blacklist()
        
        # Register check
        self.bot.add_check(self.blacklist_check)
    
    def load_blacklist(self):
        """Load blacklist data"""
        if self.blacklist_file.exists():
            with open(self.blacklist_file, 'r') as f:
                return json.load(f)
        return {
            'users': {},  # user_id: {reason, added_by, added_at, expires_at}
            'guilds': {}, # guild_id: {reason, added_by, added_at, expires_at}
            'total_users': 0,
            'total_guilds': 0
        }
    
    def save_blacklist(self):
        """Save blacklist data"""
        with open(self.blacklist_file, 'w') as f:
            json.dump(self.blacklist, f, indent=2)
    
    async def blacklist_check(self, ctx):
        """Global check for blacklisted users/guilds"""
        # Check if user is blacklisted
        user_id = str(ctx.author.id)
        if user_id in self.blacklist['users']:
            entry = self.blacklist['users'][user_id]
            
            # Check if blacklist expired
            if entry.get('expires_at'):
                expires = datetime.datetime.fromisoformat(entry['expires_at'])
                if datetime.datetime.now() > expires:
                    # Remove expired blacklist
                    del self.blacklist['users'][user_id]
                    self.save_blacklist()
                    return True
            
            # User is blacklisted
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="You are blacklisted from using this bot",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=entry['reason'], inline=False)
            
            if entry.get('expires_at'):
                embed.add_field(name="Expires", value=entry['expires_at'][:19], inline=True)
            else:
                embed.add_field(name="Duration", value="Permanent", inline=True)
            
            embed.set_footer(text="Contact bot owner for appeals")
            
            await ctx.send(embed=embed, delete_after=15)
            return False
        
        # Check if guild is blacklisted
        if ctx.guild:
            guild_id = str(ctx.guild.id)
            if guild_id in self.blacklist['guilds']:
                entry = self.blacklist['guilds'][guild_id]
                
                # Check if blacklist expired
                if entry.get('expires_at'):
                    expires = datetime.datetime.fromisoformat(entry['expires_at'])
                    if datetime.datetime.now() > expires:
                        del self.blacklist['guilds'][guild_id]
                        self.save_blacklist()
                        return True
                
                # Guild is blacklisted
                embed = discord.Embed(
                    title="🚫 Guild Blacklisted",
                    description="This server is blacklisted from using this bot",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value=entry['reason'], inline=False)
                
                await ctx.send(embed=embed)
                return False
        
        return True
    
    async def add_to_blacklist(self, target_id: int, target_type: str, reason: str, duration: int = None):
        """Add user or guild to blacklist (can be called by other cogs)"""
        target_id = str(target_id)
        now = datetime.datetime.now()
        
        entry = {
            'reason': reason,
            'added_at': now.isoformat(),
            'expires_at': (now + datetime.timedelta(seconds=duration)).isoformat() if duration else None
        }
        
        if target_type == 'user':
            self.blacklist['users'][target_id] = entry
            self.blacklist['total_users'] += 1
        elif target_type == 'guild':
            self.blacklist['guilds'][target_id] = entry
            self.blacklist['total_guilds'] += 1
        
        self.save_blacklist()
    
    @commands.command(name='blacklist_add')
    @commands.is_owner()
    async def blacklist_add(self, ctx, target_type: str, target_id: str, *, reason: str):
        """Add user or guild to blacklist (owner only)
        
        Usage:
        !blacklist_add user 123456789 Spamming commands
        !blacklist_add guild 987654321 Terms of service violation
        """
        if target_type not in ['user', 'guild']:
            await ctx.send("❌ Invalid type. Use 'user' or 'guild'")
            return
        
        await self.add_to_blacklist(int(target_id), target_type, reason)
        
        embed = discord.Embed(
            title="✅ Added to Blacklist",
            description=f"{target_type.capitalize()} {target_id} has been blacklisted",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Type", value=target_type.capitalize(), inline=True)
        embed.add_field(name="ID", value=target_id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Duration", value="Permanent", inline=True)
        
        await ctx.send(embed=embed)
        print(f"[Blacklist] Added {target_type} {target_id}: {reason}")
    
    @commands.command(name='blacklist_temp')
    @commands.is_owner()
    async def blacklist_temp(self, ctx, target_type: str, target_id: str, hours: int, *, reason: str):
        """Temporarily blacklist user or guild (owner only)
        
        Usage:
        !blacklist_temp user 123456789 24 Temporary ban for spam
        !blacklist_temp guild 987654321 72 Cooling off period
        """
        if target_type not in ['user', 'guild']:
            await ctx.send("❌ Invalid type. Use 'user' or 'guild'")
            return
        
        duration = hours * 3600  # Convert to seconds
        await self.add_to_blacklist(int(target_id), target_type, reason, duration)
        
        embed = discord.Embed(
            title="✅ Temporarily Blacklisted",
            description=f"{target_type.capitalize()} {target_id} has been temporarily blacklisted",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Type", value=target_type.capitalize(), inline=True)
        embed.add_field(name="ID", value=target_id, inline=True)
        embed.add_field(name="Duration", value=f"{hours} hours", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        expires = datetime.datetime.now() + datetime.timedelta(hours=hours)
        embed.add_field(name="Expires", value=expires.strftime('%Y-%m-%d %H:%M:%S'), inline=True)
        
        await ctx.send(embed=embed)
        print(f"[Blacklist] Temp blacklisted {target_type} {target_id} for {hours}h: {reason}")
    
    @commands.command(name='blacklist_remove')
    @commands.is_owner()
    async def blacklist_remove(self, ctx, target_type: str, target_id: str):
        """Remove user or guild from blacklist (owner only)"""
        if target_type not in ['user', 'guild']:
            await ctx.send("❌ Invalid type. Use 'user' or 'guild'")
            return
        
        target_dict = self.blacklist['users'] if target_type == 'user' else self.blacklist['guilds']
        
        if target_id not in target_dict:
            await ctx.send(f"❌ {target_type.capitalize()} {target_id} is not blacklisted")
            return
        
        del target_dict[target_id]
        self.save_blacklist()
        
        await ctx.send(f"✅ Removed {target_type} {target_id} from blacklist")
        print(f"[Blacklist] Removed {target_type} {target_id} from blacklist")
    
    @commands.command(name='blacklist')
    @commands.is_owner()
    async def list_blacklist(self, ctx, target_type: str = None):
        """List all blacklisted users/guilds (owner only)"""
        embed = discord.Embed(
            title="🚫 Blacklist",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        if not target_type or target_type == 'user':
            users_text = []
            for user_id, entry in list(self.blacklist['users'].items())[:10]:
                expires = entry.get('expires_at', 'Never')[:19] if entry.get('expires_at') else 'Permanent'
                users_text.append(f"<@{user_id}>: {entry['reason'][:30]}...\nExpires: {expires}")
            
            embed.add_field(
                name=f"👥 Users ({len(self.blacklist['users'])})",
                value="\n\n".join(users_text) if users_text else "No users blacklisted",
                inline=False
            )
        
        if not target_type or target_type == 'guild':
            guilds_text = []
            for guild_id, entry in list(self.blacklist['guilds'].items())[:10]:
                expires = entry.get('expires_at', 'Never')[:19] if entry.get('expires_at') else 'Permanent'
                guilds_text.append(f"Guild {guild_id}: {entry['reason'][:30]}...\nExpires: {expires}")
            
            embed.add_field(
                name=f"🏛️ Guilds ({len(self.blacklist['guilds'])})",
                value="\n\n".join(guilds_text) if guilds_text else "No guilds blacklisted",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(self.blacklist['users'])} users, {len(self.blacklist['guilds'])} guilds")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='blacklist_check')
    async def check_blacklist(self, ctx, target_type: str, target_id: str):
        """Check if user or guild is blacklisted"""
        target_dict = self.blacklist['users'] if target_type == 'user' else self.blacklist['guilds']
        
        if target_id not in target_dict:
            await ctx.send(f"✅ {target_type.capitalize()} {target_id} is not blacklisted")
            return
        
        entry = target_dict[target_id]
        
        embed = discord.Embed(
            title=f"🚫 Blacklist Entry",
            description=f"{target_type.capitalize()} {target_id}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=entry['reason'], inline=False)
        embed.add_field(name="Added", value=entry['added_at'][:19], inline=True)
        
        if entry.get('expires_at'):
            embed.add_field(name="Expires", value=entry['expires_at'][:19], inline=True)
            
            expires = datetime.datetime.fromisoformat(entry['expires_at'])
            remaining = expires - datetime.datetime.now()
            embed.add_field(name="Remaining", value=str(remaining).split('.')[0], inline=True)
        else:
            embed.add_field(name="Duration", value="Permanent", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='blacklist_stats')
    @commands.is_owner()
    async def blacklist_stats(self, ctx):
        """View blacklist statistics (owner only)"""
        # Count active vs expired
        now = datetime.datetime.now()
        active_users = sum(
            1 for entry in self.blacklist['users'].values()
            if not entry.get('expires_at') or datetime.datetime.fromisoformat(entry['expires_at']) > now
        )
        active_guilds = sum(
            1 for entry in self.blacklist['guilds'].values()
            if not entry.get('expires_at') or datetime.datetime.fromisoformat(entry['expires_at']) > now
        )
        
        embed = discord.Embed(
            title="📊 Blacklist Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        embed.add_field(name="Active Users", value=str(active_users), inline=True)
        embed.add_field(name="Active Guilds", value=str(active_guilds), inline=True)
        embed.add_field(name="Total Entries", value=str(active_users + active_guilds), inline=True)
        
        embed.add_field(name="All-Time Users", value=str(self.blacklist['total_users']), inline=True)
        embed.add_field(name="All-Time Guilds", value=str(self.blacklist['total_guilds']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BlacklistSystem(bot))
