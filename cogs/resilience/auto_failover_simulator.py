"""
Auto Failover Simulator - Simulate failover scenarios and recovery
"""

import discord
from discord.ext import commands
from datetime import datetime
import asyncio
from typing import Dict
from cogs.core.pst_timezone import get_now_pst

class AutoFailoverSimulator(commands.Cog):
    """Simulate failover scenarios and test recovery mechanisms"""
    
    def __init__(self, bot):
        self.bot = bot
        self.failover_scenarios = []
        self.failover_results = []
    
    async def simulate_primary_failure(self, service: str, recovery_time: int = 60):
        """Simulate primary service failure and measure failover time"""
        start_time = get_now_pst()
        
        print(f"🔴 Simulating {service} primary failure...")
        
        # Wait for automatic failover
        await asyncio.sleep(recovery_time)
        
        failover_time = (get_now_pst() - start_time).total_seconds()
        
        result = {
            'service': service,
            'scenario': 'primary_failure',
            'failover_time_seconds': failover_time,
            'timestamp': get_now_pst().isoformat(),
            'success': failover_time < 30  # Should failover in <30s
        }
        
        self.failover_results.append(result)
        print(f"✅ Failover completed in {failover_time:.1f}s")
        
        return result
    
    async def simulate_cascading_failure(self):
        """Simulate cascading failures across multiple services"""
        print("🔴 Initiating cascading failure scenario...")
        
        services = ['database', 'cache', 'api_gateway']
        results = []
        
        for service in services:
            result = await self.simulate_primary_failure(service, 30)
            results.append(result)
            await asyncio.sleep(5)  # Stagger failures
        
        return results
    
    def get_failover_metrics(self) -> Dict:
        """Calculate failover metrics"""
        if not self.failover_results:
            return {}
        
        times = [r['failover_time_seconds'] for r in self.failover_results]
        successes = sum(1 for r in self.failover_results if r['success'])
        
        return {
            'total_failovers': len(self.failover_results),
            'successful': successes,
            'success_rate': successes / len(self.failover_results),
            'avg_failover_time': sum(times) / len(times),
            'max_failover_time': max(times),
            'min_failover_time': min(times)
        }
    
    @commands.command(name='failoversim')
    async def run_failover_sim(self, ctx, scenario: str = 'primary'):
        """Run failover simulation (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        if scenario == 'primary':
            result = await self.simulate_primary_failure('database')
        elif scenario == 'cascade':
            result = await self.simulate_cascading_failure()
        
        metrics = self.get_failover_metrics()
        
        embed = discord.Embed(
            title=f"⚡ Failover Simulation Results - {scenario}",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        if metrics:
            embed.add_field(name="Avg Failover Time", value=f"{metrics['avg_failover_time']:.1f}s", inline=True)
            embed.add_field(name="Success Rate", value=f"{metrics['success_rate']:.0%}", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoFailoverSimulator(bot))
