import discord
from discord.ext import commands, tasks
import aiohttp
import json
import psutil
import datetime
from pathlib import Path

class HealthCheckSystem(commands.Cog):
    """Bot health monitoring system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.health_file = self.data_dir / 'health_status.json'
        
        self.health_data = {
            'status': 'healthy',
            'last_check': None,
            'checks': {
                'discord_api': 'unknown',
                'database': 'unknown',
                'memory': 'unknown',
                'cpu': 'unknown'
            },
            'uptime_checks': 0,
            'failed_checks': 0
        }
        
        self.health_check_task.start()
    
    async def check_discord_api(self):
        """Check Discord API status"""
        try:
            # Simple latency check
            latency = self.bot.latency * 1000  # Convert to ms
            
            if latency < 100:
                return 'healthy', f'Latency: {latency:.0f}ms'
            elif latency < 300:
                return 'degraded', f'High latency: {latency:.0f}ms'
            else:
                return 'unhealthy', f'Very high latency: {latency:.0f}ms'
        except:
            return 'unhealthy', 'Cannot reach Discord API'
    
    async def check_database(self):
        """Check database connectivity (DataManager)"""
        try:
            data_manager = self.bot.get_cog('DataManager')
            if data_manager:
                # Simple check: can we access data?
                data_manager.data
                return 'healthy', 'DataManager accessible'
            else:
                return 'degraded', 'DataManager not loaded'
        except:
            return 'unhealthy', 'DataManager error'
    
    async def check_memory(self):
        """Check memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb < 500:
                return 'healthy', f'Memory: {memory_mb:.0f} MB'
            elif memory_mb < 1000:
                return 'degraded', f'High memory: {memory_mb:.0f} MB'
            else:
                return 'unhealthy', f'Critical memory: {memory_mb:.0f} MB'
        except:
            return 'unknown', 'Cannot check memory'
    
    async def check_cpu(self):
        """Check CPU usage"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            
            if cpu_percent < 50:
                return 'healthy', f'CPU: {cpu_percent:.1f}%'
            elif cpu_percent < 80:
                return 'degraded', f'High CPU: {cpu_percent:.1f}%'
            else:
                return 'unhealthy', f'Critical CPU: {cpu_percent:.1f}%'
        except:
            return 'unknown', 'Cannot check CPU'
    
    @tasks.loop(minutes=5)
    async def health_check_task(self):
        """Periodic health check"""
        self.health_data['last_check'] = datetime.datetime.now().isoformat()
        self.health_data['uptime_checks'] += 1
        
        # Run all checks
        checks = {
            'discord_api': await self.check_discord_api(),
            'database': await self.check_database(),
            'memory': await self.check_memory(),
            'cpu': await self.check_cpu()
        }
        
        # Update health data
        all_healthy = True
        for check_name, (status, message) in checks.items():
            self.health_data['checks'][check_name] = {
                'status': status,
                'message': message,
                'checked_at': datetime.datetime.now().isoformat()
            }
            
            if status == 'unhealthy':
                all_healthy = False
                self.health_data['failed_checks'] += 1
        
        # Update overall status
        if all_healthy:
            self.health_data['status'] = 'healthy'
        elif any(check[0] == 'unhealthy' for check in checks.values()):
            self.health_data['status'] = 'unhealthy'
        else:
            self.health_data['status'] = 'degraded'
        
        # Save health status
        with open(self.health_file, 'w') as f:
            json.dump(self.health_data, f, indent=2)
        
        # Notify owner if unhealthy
        if self.health_data['status'] == 'unhealthy':
            await self.notify_unhealthy(checks)
        
        print(f"[Health Check] Status: {self.health_data['status']}")
    
    async def notify_unhealthy(self, checks):
        """Notify owner of unhealthy status"""
        import os
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if not owner_id:
            return
        
        try:
            owner = await self.bot.fetch_user(owner_id)
            
            embed = discord.Embed(
                title="🚨 Health Check Failed",
                description="Bot health check detected issues",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            for check_name, (status, message) in checks.items():
                emoji = '✅' if status == 'healthy' else '⚠️' if status == 'degraded' else '❌'
                embed.add_field(
                    name=f"{emoji} {check_name.replace('_', ' ').title()}",
                    value=message,
                    inline=False
                )
            
            embed.add_field(name="Action Required", value="Use `!health` to investigate", inline=False)
            
            await owner.send(embed=embed)
        except:
            pass
    
    @health_check_task.before_loop
    async def before_health_check(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='health')
    async def health(self, ctx):
        """Check bot health status"""
        # Force immediate check
        await self.health_check_task()
        
        embed = discord.Embed(
            title="🏥 Bot Health Status",
            color=self.get_status_color(self.health_data['status']),
            timestamp=discord.utils.utcnow()
        )
        
        # Overall status
        status_emoji = '✅' if self.health_data['status'] == 'healthy' else '⚠️' if self.health_data['status'] == 'degraded' else '❌'
        embed.add_field(
            name="Overall Status",
            value=f"{status_emoji} {self.health_data['status'].upper()}",
            inline=True
        )
        
        # Uptime checks
        success_rate = ((self.health_data['uptime_checks'] - self.health_data['failed_checks']) / 
                       max(self.health_data['uptime_checks'], 1) * 100)
        embed.add_field(
            name="Uptime",
            value=f"{success_rate:.1f}%",
            inline=True
        )
        
        # Individual checks
        for check_name, check_data in self.health_data['checks'].items():
            if isinstance(check_data, dict):
                status = check_data['status']
                message = check_data['message']
                emoji = '✅' if status == 'healthy' else '⚠️' if status == 'degraded' else '❌'
                
                embed.add_field(
                    name=f"{emoji} {check_name.replace('_', ' ').title()}",
                    value=message,
                    inline=False
                )
        
        embed.add_field(
            name="Last Check",
            value=self.health_data.get('last_check', 'Never')[:19],
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    def get_status_color(self, status):
        """Get color for status"""
        if status == 'healthy':
            return discord.Color.green()
        elif status == 'degraded':
            return discord.Color.orange()
        else:
            return discord.Color.red()
    
    @commands.command(name='health_history')
    @commands.is_owner()
    async def health_history(self, ctx):
        """View health check history (owner only)"""
        embed = discord.Embed(
            title="📊 Health Check History",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Total Checks", value=str(self.health_data['uptime_checks']), inline=True)
        embed.add_field(name="Failed Checks", value=str(self.health_data['failed_checks']), inline=True)
        
        success_rate = ((self.health_data['uptime_checks'] - self.health_data['failed_checks']) / 
                       max(self.health_data['uptime_checks'], 1) * 100)
        embed.add_field(name="Success Rate", value=f"{success_rate:.2f}%", inline=True)
        
        await ctx.send(embed=embed)
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.health_check_task.cancel()

async def setup(bot):
    await bot.add_cog(HealthCheckSystem(bot))
