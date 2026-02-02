"""
Defense Efficacy Scorer
Tracks defense effectiveness metrics, response times, MTTD/MTTR
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

class DefenseEfficacyScorerCog(commands.Cog):
    """Defense Efficacy Scorer - Measures defense effectiveness and response metrics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/defense_efficacy"
        os.makedirs(self.data_dir, exist_ok=True)
        self.scores_file = os.path.join(self.data_dir, "efficacy_scores.json")
        self.metrics_file = os.path.join(self.data_dir, "response_metrics.json")
        self.scores = self.load_scores()
        self.metrics = self.load_metrics()
        
    def load_scores(self) -> List[Dict]:
        if os.path.exists(self.scores_file):
            with open(self.scores_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_scores(self):
        with open(self.scores_file, 'w') as f:
            json.dump(self.scores, f, indent=4)
    
    def load_metrics(self) -> Dict:
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {"mttd": [], "mttr": [], "mttr_target": 240, "mttd_target": 60}
    
    def save_metrics(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=4)
    
    @commands.command(name="defense_score")
    @commands.has_permissions(administrator=True)
    async def calculate_score(self, ctx, incident_id: int, detected_in_minutes: int, resolved_in_minutes: int):
        """Calculate defense efficacy score\nUsage: !defense_score <incident_id> <detected_in_min> <resolved_in_min>"""
        detection_score = max(0, 100 - (detected_in_minutes / self.metrics["mttd_target"] * 50))
        response_score = max(0, 100 - (resolved_in_minutes / self.metrics["mttr_target"] * 50))
        overall_score = (detection_score + response_score) / 2
        
        score = {
            "id": len(self.scores) + 1,
            "incident_id": incident_id,
            "detection_time": detected_in_minutes,
            "resolution_time": resolved_in_minutes,
            "detection_score": detection_score,
            "response_score": response_score,
            "overall_score": overall_score,
            "timestamp": datetime.utcnow().isoformat(),
            "scored_by": str(ctx.author.id)
        }
        
        self.scores.append(score)
        self.metrics["mttd"].append(detected_in_minutes)
        self.metrics["mttr"].append(resolved_in_minutes)
        self.save_scores()
        self.save_metrics()
        
        color = discord.Color.green() if overall_score >= 80 else discord.Color.gold() if overall_score >= 60 else discord.Color.red()
        embed = discord.Embed(title="✅ Defense Efficacy Score", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Incident ID", value=f"#{incident_id}", inline=True)
        embed.add_field(name="Overall Score", value=f"**{overall_score:.1f}/100**", inline=True)
        embed.add_field(name="Detection Score", value=f"{detection_score:.1f}/100", inline=True)
        embed.add_field(name="Response Score", value=f"{response_score:.1f}/100", inline=True)
        embed.add_field(name="MTTD", value=f"{detected_in_minutes} min", inline=True)
        embed.add_field(name="MTTR", value=f"{resolved_in_minutes} min", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="defense_metrics")
    @commands.has_permissions(administrator=True)
    async def view_metrics(self, ctx):
        """View defense metrics dashboard\nUsage: !defense_metrics"""
        if not self.metrics["mttd"] or not self.metrics["mttr"]:
            await ctx.send("📊 No metrics recorded yet")
            return
        
        avg_mttd = sum(self.metrics["mttd"]) / len(self.metrics["mttd"])
        avg_mttr = sum(self.metrics["mttr"]) / len(self.metrics["mttr"])
        avg_score = sum(s["overall_score"] for s in self.scores) / len(self.scores) if self.scores else 0
        
        embed = discord.Embed(title="📊 Defense Efficacy Metrics", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📈 Avg MTTD", value=f"{avg_mttd:.1f} min (Target: {self.metrics['mttd_target']} min)", inline=True)
        embed.add_field(name="⏱️ Avg MTTR", value=f"{avg_mttr:.1f} min (Target: {self.metrics['mttr_target']} min)", inline=True)
        embed.add_field(name="🎯 Avg Score", value=f"{avg_score:.1f}/100", inline=True)
        embed.add_field(name="📊 Total Incidents Scored", value=len(self.scores), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="defense_leaderboard")
    @commands.has_permissions(administrator=True)
    async def leaderboard(self, ctx):
        """View best defense scores\nUsage: !defense_leaderboard"""
        if not self.scores:
            await ctx.send("📋 No scores recorded yet")
            return
        
        top_scores = sorted(self.scores, key=lambda x: x["overall_score"], reverse=True)[:10]
        embed = discord.Embed(title="🏆 Defense Efficacy Leaderboard", color=discord.Color.gold(), timestamp=datetime.utcnow())
        
        for i, score in enumerate(top_scores[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(name=f"{medal} Incident #{score['incident_id']}", value=f"Score: {score['overall_score']:.1f}/100 | MTTD: {score['detection_time']}m | MTTR: {score['resolution_time']}m", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="defense_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View comprehensive defense dashboard\nUsage: !defense_dashboard"""
        total_scored = len(self.scores)
        if total_scored == 0:
            await ctx.send("📊 No data available")
            return
        
        excellent = len([s for s in self.scores if s["overall_score"] >= 90])
        good = len([s for s in self.scores if 70 <= s["overall_score"] < 90])
        needs_improvement = len([s for s in self.scores if s["overall_score"] < 70])
        avg_score = sum(s["overall_score"] for s in self.scores) / total_scored
        
        embed = discord.Embed(title="🛡️ Defense Efficacy Dashboard", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📊 Total Incidents", value=total_scored, inline=True)
        embed.add_field(name="📈 Average Score", value=f"{avg_score:.1f}/100", inline=True)
        embed.add_field(name="🟢 Excellent (90+)", value=excellent, inline=True)
        embed.add_field(name="🟡 Good (70-89)", value=good, inline=True)
        embed.add_field(name="🔴 Needs Improvement (<70)", value=needs_improvement, inline=True)
        
        status = "🟢 EXCELLENT" if avg_score >= 85 else "🟡 GOOD" if avg_score >= 70 else "🔴 NEEDS WORK"
        embed.add_field(name="Overall Defense Posture", value=status, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DefenseEfficacyScorerCog(bot))
