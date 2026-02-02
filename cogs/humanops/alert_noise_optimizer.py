"""
Alert Noise Optimizer
Reduces alert noise with intelligent suppression and signal-to-noise optimization
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class AlertNoiseOptimizerCog(commands.Cog):
    """Alert Noise Optimizer - Reduces false positive alerts and improves signal quality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/alert_noise"
        os.makedirs(self.data_dir, exist_ok=True)
        self.alerts_file = os.path.join(self.data_dir, "alerts.json")
        self.suppressions_file = os.path.join(self.data_dir, "suppressions.json")
        self.alerts = self.load_alerts()
        self.suppressions = self.load_suppressions()
        
    def load_alerts(self):
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_alerts(self):
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=4)
    
    def load_suppressions(self):
        if os.path.exists(self.suppressions_file):
            with open(self.suppressions_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_suppressions(self):
        with open(self.suppressions_file, 'w') as f:
            json.dump(self.suppressions, f, indent=4)
    
    def calculate_signal_to_noise(self) -> float:
        if not self.alerts:
            return 100.0
        
        true_positives = len([a for a in self.alerts if a.get("disposition") == "true_positive"])
        false_positives = len([a for a in self.alerts if a.get("disposition") == "false_positive"])
        
        if true_positives + false_positives == 0:
            return 100.0
        
        return (true_positives / (true_positives + false_positives)) * 100
    
    @commands.command(name="noise_log_alert")
    @commands.has_permissions(administrator=True)
    async def log_alert(self, ctx, alert_type: str, disposition: str, *, description: str):
        """Log alert for noise analysis\nUsage: !noise_log_alert <type> <true_positive|false_positive> <description>"""
        alert = {
            "id": len(self.alerts) + 1,
            "type": alert_type,
            "disposition": disposition.lower(),
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
            "logged_by": str(ctx.author.id)
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        
        color = discord.Color.green() if disposition.lower() == "true_positive" else discord.Color.orange()
        embed = discord.Embed(title="✅ Alert Logged", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Alert ID", value=f"#{alert['id']}", inline=True)
        embed.add_field(name="Type", value=alert_type, inline=True)
        embed.add_field(name="Disposition", value=disposition.upper(), inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="noise_suppress")
    @commands.has_permissions(administrator=True)
    async def suppress_alert(self, ctx, alert_type: str, duration_hours: int, *, reason: str):
        """Suppress noisy alert type\nUsage: !noise_suppress <alert_type> <hours> <reason>"""
        suppression = {
            "id": len(self.suppressions) + 1,
            "alert_type": alert_type,
            "duration_hours": duration_hours,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + datetime.timedelta(hours=duration_hours)).isoformat(),
            "created_by": str(ctx.author.id),
            "active": True
        }
        
        self.suppressions.append(suppression)
        self.save_suppressions()
        
        embed = discord.Embed(title="🔇 Alert Suppression Created", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Suppression ID", value=f"#{suppression['id']}", inline=True)
        embed.add_field(name="Alert Type", value=alert_type, inline=True)
        embed.add_field(name="Duration", value=f"{duration_hours}h", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Expires", value=suppression["expires_at"][:19], inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="noise_analyze")
    @commands.has_permissions(administrator=True)
    async def analyze_noise(self, ctx):
        """Analyze alert noise and signal quality\nUsage: !noise_analyze"""
        if not self.alerts:
            await ctx.send("📊 No alert data available")
            return
        
        signal_to_noise = self.calculate_signal_to_noise()
        total_alerts = len(self.alerts)
        true_positives = len([a for a in self.alerts if a.get("disposition") == "true_positive"])
        false_positives = len([a for a in self.alerts if a.get("disposition") == "false_positive"])
        
        # Count by type
        alert_types = {}
        for alert in self.alerts:
            atype = alert.get("type", "unknown")
            alert_types[atype] = alert_types.get(atype, 0) + 1
        
        top_noisy_types = sorted(alert_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        color = discord.Color.green() if signal_to_noise >= 70 else discord.Color.gold() if signal_to_noise >= 50 else discord.Color.red()
        embed = discord.Embed(title="📊 Alert Noise Analysis", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Signal-to-Noise Ratio", value=f"**{signal_to_noise:.1f}%**", inline=True)
        embed.add_field(name="Total Alerts", value=total_alerts, inline=True)
        embed.add_field(name="✅ True Positives", value=true_positives, inline=True)
        embed.add_field(name="❌ False Positives", value=false_positives, inline=True)
        
        if top_noisy_types:
            noisy_text = "\n".join([f"• {atype}: {count} alerts" for atype, count in top_noisy_types])
            embed.add_field(name="Top Alert Types", value=noisy_text, inline=False)
        
        if signal_to_noise < 50:
            embed.add_field(name="⚠️ Recommendation", value="High noise level - review and suppress false positive sources", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="noise_suppressions")
    @commands.has_permissions(administrator=True)
    async def list_suppressions(self, ctx):
        """List active alert suppressions\nUsage: !noise_suppressions"""
        active_suppressions = [s for s in self.suppressions if s.get("active", False)]
        
        if not active_suppressions:
            await ctx.send("📋 No active suppressions")
            return
        
        embed = discord.Embed(title="🔇 Active Alert Suppressions", color=discord.Color.blue(), timestamp=datetime.utcnow())
        
        for suppression in active_suppressions[:10]:
            embed.add_field(
                name=f"#{suppression['id']} - {suppression['alert_type']}",
                value=f"Expires: {suppression['expires_at'][:19]}\nReason: {suppression['reason'][:50]}",
                inline=False
            )
        
        embed.add_field(name="Total Active", value=len(active_suppressions), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="noise_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View alert noise optimization dashboard\nUsage: !noise_dashboard"""
        total_alerts = len(self.alerts)
        signal_to_noise = self.calculate_signal_to_noise()
        active_suppressions = len([s for s in self.suppressions if s.get("active", False)])
        
        embed = discord.Embed(title="🔇 Alert Noise Optimizer Dashboard", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📊 Total Alerts", value=total_alerts, inline=True)
        embed.add_field(name="📈 Signal-to-Noise", value=f"{signal_to_noise:.1f}%", inline=True)
        embed.add_field(name="🔇 Active Suppressions", value=active_suppressions, inline=True)
        
        status = "🟢 EXCELLENT" if signal_to_noise >= 80 else "🟡 GOOD" if signal_to_noise >= 60 else "🔴 NOISY"
        embed.add_field(name="Alert Quality", value=status, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AlertNoiseOptimizerCog(bot))
