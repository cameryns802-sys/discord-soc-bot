import discord
from discord.ext import commands, tasks
import json
import datetime
from pathlib import Path

class ScheduledTasksDashboard(commands.Cog):
    """Dashboard for managing background tasks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.task_file = self.data_dir / 'task_metrics.json'
        
        self.task_metrics = {
            'tasks': {},  # {task_name: {runs, errors, last_run, avg_time}}
            'total_runs': 0,
            'total_errors': 0
        }
        
        self.load_metrics()
        self.monitor_tasks.start()
    
    def load_metrics(self):
        """Load task metrics"""
        if self.task_file.exists():
            with open(self.task_file, 'r') as f:
                self.task_metrics = json.load(f)
    
    def save_metrics(self):
        """Save task metrics"""
        with open(self.task_file, 'w') as f:
            json.dump(self.task_metrics, f, indent=2)
    
    @tasks.loop(minutes=10)
    async def monitor_tasks(self):
        """Monitor all background tasks"""
        # Get all tasks from all cogs
        for cog_name, cog in self.bot.cogs.items():
            # Find all tasks.Loop attributes
            for attr_name in dir(cog):
                attr = getattr(cog, attr_name)
                if isinstance(attr, tasks.Loop):
                    task_name = f"{cog_name}.{attr_name}"
                    
                    # Initialize metrics if needed
                    if task_name not in self.task_metrics['tasks']:
                        self.task_metrics['tasks'][task_name] = {
                            'runs': 0,
                            'errors': 0,
                            'last_run': None,
                            'status': 'unknown'
                        }
                    
                    # Update status
                    task_info = self.task_metrics['tasks'][task_name]
                    task_info['status'] = 'running' if attr.is_running() else 'stopped'
                    task_info['next_iteration'] = attr.next_iteration.isoformat() if attr.next_iteration else None
        
        self.save_metrics()
    
    @monitor_tasks.before_loop
    async def before_monitor_tasks(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='tasks')
    async def list_tasks(self, ctx):
        """List all background tasks"""
        tasks_list = []
        
        for cog_name, cog in self.bot.cogs.items():
            for attr_name in dir(cog):
                attr = getattr(cog, attr_name)
                if isinstance(attr, tasks.Loop):
                    task_name = f"{cog_name}.{attr_name}"
                    status = '🟢 Running' if attr.is_running() else '🔴 Stopped'
                    tasks_list.append(f"**{task_name}**\nStatus: {status}")
        
        if not tasks_list:
            await ctx.send("No background tasks found")
            return
        
        embed = discord.Embed(
            title="📋 Background Tasks",
            description=f"Total: {len(tasks_list)} tasks",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Split into chunks
        for i in range(0, len(tasks_list), 10):
            chunk = tasks_list[i:i+10]
            embed.add_field(
                name=f"Tasks {i+1}-{i+len(chunk)}",
                value="\n\n".join(chunk),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='task_info')
    async def task_info(self, ctx, cog_name: str, task_name: str):
        """View detailed task information"""
        full_task_name = f"{cog_name}.{task_name}"
        
        # Find task
        cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
            return
        
        if not hasattr(cog, task_name):
            await ctx.send(f"❌ Task `{task_name}` not found in {cog_name}")
            return
        
        task = getattr(cog, task_name)
        if not isinstance(task, tasks.Loop):
            await ctx.send(f"❌ `{task_name}` is not a background task")
            return
        
        # Get metrics
        metrics = self.task_metrics['tasks'].get(full_task_name, {})
        
        embed = discord.Embed(
            title=f"📊 Task Info: {full_task_name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Status
        status = '🟢 Running' if task.is_running() else '🔴 Stopped'
        embed.add_field(name="Status", value=status, inline=True)
        
        # Timing
        if task._task:
            embed.add_field(name="Currently Running", value="✅ Yes", inline=True)
        else:
            embed.add_field(name="Currently Running", value="❌ No", inline=True)
        
        if task.next_iteration:
            next_run = task.next_iteration.strftime('%Y-%m-%d %H:%M:%S')
            embed.add_field(name="Next Run", value=next_run, inline=True)
        
        # Metrics
        embed.add_field(name="Total Runs", value=str(metrics.get('runs', 0)), inline=True)
        embed.add_field(name="Errors", value=str(metrics.get('errors', 0)), inline=True)
        
        if metrics.get('last_run'):
            embed.add_field(name="Last Run", value=metrics['last_run'][:19], inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='stop_task')
    @commands.is_owner()
    async def stop_task(self, ctx, cog_name: str, task_name: str):
        """Stop a background task (owner only)"""
        cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
            return
        
        if not hasattr(cog, task_name):
            await ctx.send(f"❌ Task `{task_name}` not found")
            return
        
        task = getattr(cog, task_name)
        if not isinstance(task, tasks.Loop):
            await ctx.send(f"❌ `{task_name}` is not a background task")
            return
        
        if not task.is_running():
            await ctx.send(f"⚠️ Task `{cog_name}.{task_name}` is already stopped")
            return
        
        task.cancel()
        await ctx.send(f"✅ Stopped task `{cog_name}.{task_name}`")
        print(f"[Tasks] Stopped {cog_name}.{task_name}")
    
    @commands.command(name='start_task')
    @commands.is_owner()
    async def start_task(self, ctx, cog_name: str, task_name: str):
        """Start a background task (owner only)"""
        cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
            return
        
        if not hasattr(cog, task_name):
            await ctx.send(f"❌ Task `{task_name}` not found")
            return
        
        task = getattr(cog, task_name)
        if not isinstance(task, tasks.Loop):
            await ctx.send(f"❌ `{task_name}` is not a background task")
            return
        
        if task.is_running():
            await ctx.send(f"⚠️ Task `{cog_name}.{task_name}` is already running")
            return
        
        task.start()
        await ctx.send(f"✅ Started task `{cog_name}.{task_name}`")
        print(f"[Tasks] Started {cog_name}.{task_name}")
    
    @commands.command(name='restart_task')
    @commands.is_owner()
    async def restart_task(self, ctx, cog_name: str, task_name: str):
        """Restart a background task (owner only)"""
        cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.send(f"❌ Cog `{cog_name}` not found")
            return
        
        if not hasattr(cog, task_name):
            await ctx.send(f"❌ Task `{task_name}` not found")
            return
        
        task = getattr(cog, task_name)
        if not isinstance(task, tasks.Loop):
            await ctx.send(f"❌ `{task_name}` is not a background task")
            return
        
        task.restart()
        await ctx.send(f"✅ Restarted task `{cog_name}.{task_name}`")
        print(f"[Tasks] Restarted {cog_name}.{task_name}")
    
    @commands.command(name='task_stats')
    @commands.is_owner()
    async def task_stats(self, ctx):
        """View task statistics (owner only)"""
        total_tasks = len(self.task_metrics['tasks'])
        running_tasks = sum(
            1 for task in self.task_metrics['tasks'].values()
            if task.get('status') == 'running'
        )
        
        embed = discord.Embed(
            title="📊 Task Statistics",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Total Tasks", value=str(total_tasks), inline=True)
        embed.add_field(name="Running", value=str(running_tasks), inline=True)
        embed.add_field(name="Stopped", value=str(total_tasks - running_tasks), inline=True)
        
        embed.add_field(name="Total Runs", value=str(self.task_metrics.get('total_runs', 0)), inline=True)
        embed.add_field(name="Total Errors", value=str(self.task_metrics.get('total_errors', 0)), inline=True)
        
        await ctx.send(embed=embed)
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.monitor_tasks.cancel()
        self.save_metrics()

async def setup(bot):
    await bot.add_cog(ScheduledTasksDashboard(bot))
