"""
Graceful Degradation Engine - Maintain core functionality during failures
"""

import discord
from discord.ext import commands
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class GracefulDegradationEngine(commands.Cog):
    """Automatically degrade non-critical features when resources are constrained"""
    
    def __init__(self, bot):
        self.bot = bot
        self.degradation_level = 0  # 0=normal, 1=reduced, 2=critical
        self.disabled_features = []
    
    async def assess_system_health(self) -> int:
        """Assess overall system health and return degradation level"""
        # Check various metrics
        memory_health = await self.check_memory_health()
        dependency_health = await self.check_dependency_health()
        
        if memory_health < 0.2 or dependency_health < 0.5:
            return 2  # Critical
        elif memory_health < 0.5 or dependency_health < 0.7:
            return 1  # Reduced
        return 0  # Normal
    
    async def check_memory_health(self) -> float:
        """Check memory usage (0.0-1.0)"""
        # Simulate memory check
        return 0.7  # 70% memory used
    
    async def check_dependency_health(self) -> float:
        """Check external dependencies (0.0-1.0)"""
        # Simulate dependency check
        return 0.8  # 80% dependencies healthy
    
    async def enable_reduced_mode(self):
        """Disable non-critical features"""
        self.degradation_level = 1
        self.disabled_features = [
            'detailed_logging',
            'ml_anomaly_detection',
            'predictive_forecasting'
        ]
        print("⚠️ REDUCED MODE: Disabling non-critical features")
    
    async def enable_critical_mode(self):
        """Disable all but core functionality"""
        self.degradation_level = 2
        self.disabled_features = [
            'detailed_logging',
            'ml_anomaly_detection',
            'predictive_forecasting',
            'advanced_analytics',
            'compliance_reporting'
        ]
        print("🔴 CRITICAL MODE: Core security operations only")
    
    async def restore_normal_mode(self):
        """Restore all features"""
        self.degradation_level = 0
        self.disabled_features = []
        print("✅ NORMAL MODE: All features enabled")
    
    def is_feature_available(self, feature: str) -> bool:
        """Check if a feature is available given current degradation level"""
        return feature not in self.disabled_features
    
    @commands.command(name='degradationmode')
    async def set_mode_cmd(self, ctx, mode: str = 'status'):
        """Control degradation mode (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        if mode == 'reduced':
            await self.enable_reduced_mode()
        elif mode == 'critical':
            await self.enable_critical_mode()
        elif mode == 'normal':
            await self.restore_normal_mode()
        
        embed = discord.Embed(
            title="🎛️ Degradation Mode Status",
            color=discord.Color.orange() if self.degradation_level > 0 else discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        mode_names = {0: 'Normal', 1: 'Reduced', 2: 'Critical'}
        embed.add_field(name="Current Mode", value=mode_names.get(self.degradation_level), inline=True)
        embed.add_field(name="Disabled Features", value=str(len(self.disabled_features)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GracefulDegradationEngine(bot))
