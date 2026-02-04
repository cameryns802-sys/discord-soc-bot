"""
Chaos Injector - Simulate outages, latency, and dependency failures
Chaos engineering for Discord bot resilience testing
"""

import discord
from discord.ext import commands
from datetime import datetime
import random
import asyncio
from cogs.core.pst_timezone import get_now_pst

class ChaosInjector(commands.Cog):
    """Inject controlled failures to test system resilience"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_chaos = {}
        self.failure_types = [
            'database_latency',
            'api_timeout',
            'cache_miss',
            'dependency_error',
            'network_partition'
        ]
    
    async def inject_latency(self, component: str, latency_ms: int, duration_seconds: int):
        """Inject network latency into a component"""
        self.active_chaos[f"latency_{component}"] = {
            'type': 'latency',
            'component': component,
            'latency_ms': latency_ms,
            'start_time': get_now_pst(),
            'duration_seconds': duration_seconds
        }
        
        print(f"🔴 Injecting {latency_ms}ms latency to {component} for {duration_seconds}s")
        
        # Auto-cleanup after duration
        await asyncio.sleep(duration_seconds)
        del self.active_chaos[f"latency_{component}"]
        print(f"✅ Latency injection removed from {component}")
    
    async def inject_dependency_failure(self, dependency: str, duration_seconds: int):
        """Simulate a dependency becoming unavailable"""
        self.active_chaos[f"failure_{dependency}"] = {
            'type': 'failure',
            'dependency': dependency,
            'start_time': get_now_pst(),
            'duration_seconds': duration_seconds
        }
        
        print(f"🔴 Simulating {dependency} failure for {duration_seconds}s")
        
        await asyncio.sleep(duration_seconds)
        del self.active_chaos[f"failure_{dependency}"]
        print(f"✅ {dependency} restored")
    
    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is currently affected by chaos"""
        for chaos_id, chaos_state in self.active_chaos.items():
            if chaos_state.get('component') == component or chaos_state.get('dependency') == component:
                return False
        return True
    
    async def get_injection_latency(self, component: str) -> int:
        """Get injected latency for a component (0 if none)"""
        for chaos_state in self.active_chaos.values():
            if chaos_state.get('component') == component:
                return chaos_state.get('latency_ms', 0)
        return 0
    
    @commands.command(name='injectchaos')
    async def inject_chaos_cmd(self, ctx, component: str, failure_type: str, duration: int = 30):
        """Inject chaos into a component (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        if failure_type == 'latency':
            latency = 500  # 500ms default
            await self.inject_latency(component, latency, duration)
        
        elif failure_type == 'failure':
            await self.inject_dependency_failure(component, duration)
        
        embed = discord.Embed(
            title="🔴 Chaos Injected",
            description=f"Component: {component}\nType: {failure_type}\nDuration: {duration}s",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChaosInjector(bot))
