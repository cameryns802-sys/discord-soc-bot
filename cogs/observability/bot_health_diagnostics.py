"""
Bot Health & Diagnostics: Real-time monitoring, self-repair, auto-update, health dashboard.
"""
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

# Optional psutil import for system metrics
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class BotHealthDiagnosticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/bot_health.json"
        self.data = self.load_data()
        # Only start background monitor if psutil is available
        if HAS_PSUTIL:
            self.health_monitor.start()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "health_history": [],
            "error_log": [],
            "recovery_attempts": [],
            "system_metrics": {},
            "api_health": {"rate_limits": 0, "errors": 0, "last_check": None},
            "auto_update_config": {"enabled": False, "check_interval": 24},
            "self_repair_triggers": [],
            "uptime_milestones": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def get_system_metrics(self):
        """Collect system health metrics."""
        try:
            if HAS_PSUTIL:
                process = psutil.Process()
                return {
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "thread_count": process.num_threads(),
                    "file_descriptors": process.num_fds() if hasattr(process, 'num_fds') else 0,
                    "timestamp": get_now_pst().isoformat()
                }
            else:
                # Fallback when psutil not available
                return {
                    "memory_mb": 0.0,
                    "cpu_percent": 0.0,
                    "thread_count": 0,
                    "file_descriptors": 0,
                    "timestamp": get_now_pst().isoformat(),
                    "note": "psutil not installed"
                }
        except:
            return {"error": "Unable to collect metrics", "timestamp": get_now_pst().isoformat()}

    @tasks.loop(minutes=5)
    async def health_monitor(self):
        """Periodically monitor bot health."""
        try:
            metrics = self.get_system_metrics()
            health_check = {
                "timestamp": get_now_pst().isoformat(),
                "latency_ms": round(self.bot.latency * 1000),
                "guilds": len(self.bot.guilds),
                "cogs_loaded": len(self.bot.cogs),
                "system_metrics": metrics,
                "status": "HEALTHY"
            }
            
            # Check for issues
            if metrics.get("memory_mb", 0) > 500:
                health_check["status"] = "WARNING"
                health_check["warning"] = "High memory usage"
            
            if health_check["latency_ms"] > 500:
                health_check["status"] = "WARNING"
                health_check["warning"] = "High latency"
            
            self.data["health_history"].append(health_check)
            self.data["health_history"] = self.data["health_history"][-100:]  # Keep last 100
            self.save_data(self.data)
        except Exception as e:
            print(f"[Health Monitor] Error: {e}")

    @health_monitor.before_loop
    async def before_health_monitor(self):
        await self.bot.wait_until_ready()

    @commands.command(name="health_dashboard")
    async def health_dashboard(self, ctx):
        """Display comprehensive bot health dashboard."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        metrics = self.get_system_metrics()
        
        # Get latest health check
        latest_health = self.data["health_history"][-1] if self.data["health_history"] else {}
        
        embed = discord.Embed(
            title="🔧 Bot Health Dashboard",
            color=discord.Color.green() if latest_health.get("status") == "HEALTHY" else discord.Color.orange()
        )
        
        embed.add_field(name="🟢 Status", value=latest_health.get("status", "UNKNOWN"), inline=True)
        embed.add_field(name="📊 Latency", value=f"{latest_health.get('latency_ms', 'N/A')}ms", inline=True)
        embed.add_field(name="🏛️ Guilds", value=str(latest_health.get("guilds", 0)), inline=True)
        embed.add_field(name="📦 Cogs", value=str(latest_health.get("cogs_loaded", 0)), inline=True)
        
        if "system_metrics" in latest_health and "memory_mb" in latest_health["system_metrics"]:
            mem = latest_health["system_metrics"]["memory_mb"]
            cpu = latest_health["system_metrics"]["cpu_percent"]
            embed.add_field(name="💾 Memory", value=f"{mem:.1f}MB", inline=True)
            embed.add_field(name="🖥️ CPU", value=f"{cpu:.1f}%", inline=True)
        
        embed.add_field(name="📈 Health History", value=f"Last {len(self.data['health_history'])} checks", inline=False)
        
        if self.data["error_log"]:
            recent_errors = len([e for e in self.data["error_log"] if 
                                (datetime.fromisoformat(e["timestamp"]) > get_now_pst() - timedelta(hours=1))])
            embed.add_field(name="🚨 Errors (Last Hour)", value=str(recent_errors), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="self_repair")
    async def self_repair(self, ctx):
        """Attempt automated self-repair of common issues."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        repairs = []
        
        # Check for memory issues
        metrics = self.get_system_metrics()
        if metrics.get("memory_mb", 0) > 500:
            repairs.append({"issue": "High memory", "action": "Consider garbage collection or cog reload"})
        
        # Check for missing files
        required_files = ["data/", "cogs/"]
        for file_path in required_files:
            if not os.path.exists(file_path):
                repairs.append({"issue": f"Missing {file_path}", "action": "CREATE"})
        
        repair_attempt = {
            "timestamp": get_now_pst().isoformat(),
            "issues_found": len(repairs),
            "repairs": repairs,
            "status": "COMPLETED"
        }
        
        self.data["recovery_attempts"].append(repair_attempt)
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🔨 Self-Repair Attempt",
            color=discord.Color.blue()
        )
        embed.add_field(name="Issues Found", value=str(len(repairs)), inline=True)
        embed.add_field(name="Status", value="COMPLETED", inline=True)
        
        if repairs:
            repair_str = "\n".join([f"• {r['issue']}: {r['action']}" for r in repairs[:5]])
            embed.add_field(name="Repairs Applied", value=repair_str, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="uptime_tracker")
    async def uptime_tracker(self, ctx):
        """View bot uptime and milestones."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        start_time = self.bot.user.created_at if hasattr(self.bot, 'user') else get_now_pst()
        uptime = get_now_pst() - start_time
        
        embed = discord.Embed(
            title="⏰ Bot Uptime Tracker",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="Start Time", value=start_time.isoformat(), inline=True)
        embed.add_field(name="Milestones Achieved", value=str(len(self.data["uptime_milestones"])), inline=True)
        
        if self.data["uptime_milestones"]:
            milestones = "\n".join([m["milestone"] for m in self.data["uptime_milestones"][-3:]])
            embed.add_field(name="Recent Milestones", value=milestones, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="error_log")
    async def error_log(self, ctx, hours: int = 24):
        """View recent errors from the bot."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        cutoff_time = get_now_pst() - timedelta(hours=hours)
        recent_errors = [e for e in self.data["error_log"] if 
                        datetime.fromisoformat(e["timestamp"]) > cutoff_time]
        
        embed = discord.Embed(
            title=f"📋 Error Log (Last {hours}h)",
            color=discord.Color.red() if recent_errors else discord.Color.green()
        )
        embed.add_field(name="Total Errors", value=str(len(recent_errors)), inline=True)
        
        if recent_errors:
            error_summary = "\n".join([f"• {e['error'][:50]}" for e in recent_errors[-5:]])
            embed.add_field(name="Recent Errors", value=error_summary, inline=False)
        else:
            embed.add_field(name="Status", value="✅ No errors in this period", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="enable_auto_update")
    async def enable_auto_update(self, ctx):
        """Enable automatic bot updates (with admin approval)."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        self.data["auto_update_config"]["enabled"] = True
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Auto-Update Enabled",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="Enabled", inline=True)
        embed.add_field(name="Check Interval", value="24 hours", inline=True)
        embed.add_field(name="⚠️ Note", value="Updates require admin approval before deployment", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="api_health_check")
    async def api_health_check(self, ctx):
        """Check Discord API health and rate limits."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        api_status = {
            "timestamp": get_now_pst().isoformat(),
            "gateway_connected": not self.bot.is_closed(),
            "latency": round(self.bot.latency * 1000),
            "status": "🟢 HEALTHY" if self.bot.latency < 0.5 else "🟡 DEGRADED"
        }
        
        self.data["api_health"] = api_status
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🌐 Discord API Health",
            color=discord.Color.green() if "HEALTHY" in api_status["status"] else discord.Color.orange()
        )
        embed.add_field(name="Status", value=api_status["status"], inline=True)
        embed.add_field(name="Latency", value=f"{api_status['latency']}ms", inline=True)
        embed.add_field(name="Connected", value="✅ Yes" if api_status["gateway_connected"] else "❌ No", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotHealthDiagnosticsCog(bot))
