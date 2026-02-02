import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List

class LogRetentionTiers(commands.Cog):
    """
    Log Retention Tier Management System
    
    Implements tiered log retention policies (hot/warm/cold storage)
    for compliance and cost optimization.
    
    Features:
    - Hot tier: Recent logs (7 days) - fast access
    - Warm tier: Medium-age logs (30 days) - slower access
    - Cold tier: Archived logs (90+ days) - archival only
    - Automatic tier transitions
    - Compliance-aware retention
    - Storage quota management
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/log_retention'
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f'{self.data_dir}/hot', exist_ok=True)
        os.makedirs(f'{self.data_dir}/warm', exist_ok=True)
        os.makedirs(f'{self.data_dir}/cold', exist_ok=True)
        
        self.retention_policies = self.load_retention_policies()
        self.tier_stats = self.load_tier_stats()
        
        # Default retention tiers (days)
        self.tiers = {
            'hot': 7,      # 0-7 days: Fast access
            'warm': 30,    # 8-30 days: Medium access
            'cold': 90     # 31-90 days: Archival
        }
        
        # Start background task
        self.tier_transition_task.start()
    
    def cog_unload(self):
        self.tier_transition_task.cancel()
    
    def load_retention_policies(self) -> Dict:
        """Load retention policies from JSON storage"""
        try:
            with open(f'{self.data_dir}/retention_policies.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_retention_policies(self):
        """Save retention policies to JSON storage"""
        with open(f'{self.data_dir}/retention_policies.json', 'w') as f:
            json.dump(self.retention_policies, f, indent=2)
    
    def load_tier_stats(self) -> Dict:
        """Load tier statistics from JSON storage"""
        try:
            with open(f'{self.data_dir}/tier_stats.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'hot': 0, 'warm': 0, 'cold': 0}
    
    def save_tier_stats(self):
        """Save tier statistics to JSON storage"""
        with open(f'{self.data_dir}/tier_stats.json', 'w') as f:
            json.dump(self.tier_stats, f, indent=2)
    
    def get_log_tier(self, log_timestamp: str) -> str:
        """
        Determine which tier a log belongs to based on age
        
        Args:
            log_timestamp: ISO 8601 timestamp
        
        Returns:
            Tier name ('hot', 'warm', 'cold')
        """
        try:
            log_time = datetime.fromisoformat(log_timestamp)
            age_days = (datetime.now(timezone.utc) - log_time).days
            
            if age_days <= self.tiers['hot']:
                return 'hot'
            elif age_days <= self.tiers['warm']:
                return 'warm'
            elif age_days <= self.tiers['cold']:
                return 'cold'
            else:
                return 'expired'  # Beyond retention period
        except:
            return 'hot'  # Default to hot if parsing fails
    
    def store_log_in_tier(self, guild_id: str, log_event: Dict, tier: str):
        """Store a log event in the appropriate tier"""
        tier_file = f'{self.data_dir}/{tier}/{guild_id}.json'
        
        # Load existing tier data
        try:
            with open(tier_file, 'r') as f:
                tier_data = json.load(f)
        except FileNotFoundError:
            tier_data = []
        
        tier_data.append(log_event)
        
        # Save to tier
        with open(tier_file, 'w') as f:
            json.dump(tier_data, f, indent=2)
        
        # Update stats
        self.tier_stats[tier] = self.tier_stats.get(tier, 0) + 1
        self.save_tier_stats()
    
    def transition_logs_between_tiers(self):
        """
        Transition logs between tiers based on age
        (hot → warm → cold → expired)
        """
        transitioned = {'hot_to_warm': 0, 'warm_to_cold': 0, 'expired': 0}
        
        # Process hot tier
        for tier in ['hot', 'warm']:
            tier_path = f'{self.data_dir}/{tier}'
            
            for filename in os.listdir(tier_path):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(tier_path, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        logs = json.load(f)
                except:
                    continue
                
                # Separate logs by new tier
                new_tier_logs = {'hot': [], 'warm': [], 'cold': [], 'expired': []}
                
                for log in logs:
                    timestamp = log.get('event.timestamp', '')
                    new_tier = self.get_log_tier(timestamp)
                    
                    if new_tier != 'expired':
                        new_tier_logs[new_tier].append(log)
                    else:
                        transitioned['expired'] += 1
                
                # Move logs to new tiers
                guild_id = filename.replace('.json', '')
                
                for new_tier, new_logs in new_tier_logs.items():
                    if new_tier == 'expired' or not new_logs:
                        continue
                    
                    if new_tier != tier:
                        # Write to new tier
                        new_tier_file = f'{self.data_dir}/{new_tier}/{guild_id}.json'
                        
                        try:
                            with open(new_tier_file, 'r') as f:
                                existing = json.load(f)
                        except FileNotFoundError:
                            existing = []
                        
                        existing.extend(new_logs)
                        
                        with open(new_tier_file, 'w') as f:
                            json.dump(existing, f, indent=2)
                        
                        if tier == 'hot' and new_tier == 'warm':
                            transitioned['hot_to_warm'] += len(new_logs)
                        elif tier == 'warm' and new_tier == 'cold':
                            transitioned['warm_to_cold'] += len(new_logs)
                
                # Overwrite original tier file with remaining logs
                remaining = new_tier_logs[tier]
                with open(filepath, 'w') as f:
                    json.dump(remaining, f, indent=2)
        
        return transitioned
    
    @tasks.loop(hours=24)
    async def tier_transition_task(self):
        """Background task to transition logs between tiers daily"""
        print("[Log Retention] Running tier transition...")
        transitioned = self.transition_logs_between_tiers()
        print(f"[Log Retention] Transitioned {transitioned['hot_to_warm']} hot→warm, "
              f"{transitioned['warm_to_cold']} warm→cold, "
              f"{transitioned['expired']} expired")
    
    @tier_transition_task.before_loop
    async def before_tier_transition(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='retention_policy')
    @commands.has_permissions(administrator=True)
    async def retention_policy_cmd(self, ctx, action: str = None, *, args: str = None):
        """
        Configure log retention policies
        
        Usage:
        !retention_policy set hot=14 warm=60 cold=365
        !retention_policy show
        """
        if action == 'set' and args:
            # Parse tier settings
            for pair in args.split():
                if '=' in pair:
                    tier, days = pair.split('=')
                    if tier in self.tiers:
                        self.tiers[tier] = int(days)
            
            if str(ctx.guild.id) not in self.retention_policies:
                self.retention_policies[str(ctx.guild.id)] = {}
            
            self.retention_policies[str(ctx.guild.id)] = self.tiers.copy()
            self.save_retention_policies()
            
            embed = discord.Embed(
                title="✅ Retention Policy Updated",
                description="Log retention tiers have been configured.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="🔥 Hot Tier", value=f"{self.tiers['hot']} days", inline=True)
            embed.add_field(name="🟠 Warm Tier", value=f"{self.tiers['warm']} days", inline=True)
            embed.add_field(name="❄️ Cold Tier", value=f"{self.tiers['cold']} days", inline=True)
            
            await ctx.send(embed=embed)
        
        else:
            # Show current policy
            embed = discord.Embed(
                title="📋 Log Retention Policy",
                description="Current retention tier configuration",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="🔥 Hot Tier (Fast Access)",
                value=f"**{self.tiers['hot']} days**\nRecent logs with immediate access",
                inline=False
            )
            embed.add_field(
                name="🟠 Warm Tier (Medium Access)",
                value=f"**{self.tiers['warm']} days**\nMedium-age logs with slower retrieval",
                inline=False
            )
            embed.add_field(
                name="❄️ Cold Tier (Archival)",
                value=f"**{self.tiers['cold']} days**\nArchived logs for compliance",
                inline=False
            )
            
            embed.set_footer(text="Use !retention_policy set hot=X warm=Y cold=Z to configure")
            await ctx.send(embed=embed)
    
    @commands.command(name='tier_stats')
    @commands.has_permissions(administrator=True)
    async def tier_stats_cmd(self, ctx):
        """Show log tier statistics"""
        embed = discord.Embed(
            title="📊 Log Tier Statistics",
            description="Current log distribution across tiers",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        total = sum(self.tier_stats.values())
        
        for tier in ['hot', 'warm', 'cold']:
            count = self.tier_stats.get(tier, 0)
            percentage = (count / total * 100) if total > 0 else 0
            
            tier_icons = {'hot': '🔥', 'warm': '🟠', 'cold': '❄️'}
            tier_names = {'hot': 'Hot (0-7d)', 'warm': 'Warm (8-30d)', 'cold': 'Cold (31-90d)'}
            
            embed.add_field(
                name=f"{tier_icons[tier]} {tier_names[tier]}",
                value=f"**{count:,}** logs ({percentage:.1f}%)",
                inline=True
            )
        
        embed.add_field(name="📈 Total Logs", value=f"**{total:,}**", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='transition_logs')
    @commands.has_permissions(administrator=True)
    async def transition_logs_cmd(self, ctx):
        """Manually trigger log tier transitions"""
        await ctx.send("⏳ Transitioning logs between tiers...")
        
        transitioned = self.transition_logs_between_tiers()
        
        embed = discord.Embed(
            title="✅ Log Tier Transition Complete",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🔥→🟠 Hot to Warm", value=str(transitioned['hot_to_warm']), inline=True)
        embed.add_field(name="🟠→❄️ Warm to Cold", value=str(transitioned['warm_to_cold']), inline=True)
        embed.add_field(name="🗑️ Expired", value=str(transitioned['expired']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LogRetentionTiers(bot))
