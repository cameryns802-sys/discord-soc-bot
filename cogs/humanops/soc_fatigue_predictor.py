"""
SOC Fatigue Predictor
Predicts SOC analyst burnout with alert overload detection and shift risk forecasting
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

class SOCFatiguePredictorCog(commands.Cog):
    """SOC Fatigue Predictor - Monitors analyst workload and predicts burnout"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/soc_fatigue"
        os.makedirs(self.data_dir, exist_ok=True)
        self.workload_file = os.path.join(self.data_dir, "analyst_workload.json")
        self.predictions_file = os.path.join(self.data_dir, "fatigue_predictions.json")
        self.workload = self.load_workload()
        self.predictions = self.load_predictions()
        
    def load_workload(self):
        if os.path.exists(self.workload_file):
            with open(self.workload_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_workload(self):
        with open(self.workload_file, 'w') as f:
            json.dump(self.workload, f, indent=4)
    
    def load_predictions(self):
        if os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_predictions(self):
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=4)
    
    def calculate_fatigue_risk(self, user_id: str) -> float:
        if user_id not in self.workload:
            return 0.0
        
        user_data = self.workload[user_id]
        alerts_handled = user_data.get("alerts_handled_24h", 0)
        incidents_worked = user_data.get("incidents_worked_week", 0)
        consecutive_shifts = user_data.get("consecutive_shifts", 0)
        avg_response_time = user_data.get("avg_response_time_min", 30)
        
        risk = 0.0
        risk += min(40, alerts_handled * 2)
        risk += min(30, incidents_worked * 5)
        risk += min(20, consecutive_shifts * 4)
        if avg_response_time > 60:
            risk += 10
        
        return min(100, risk)
    
    @commands.command(name="fatigue_log_shift")
    @commands.has_permissions(administrator=True)
    async def log_shift(self, ctx, member: discord.Member, alerts_handled: int, incidents: int):
        """Log analyst shift workload\nUsage: !fatigue_log_shift @analyst <alerts> <incidents>"""
        user_id = str(member.id)
        
        if user_id not in self.workload:
            self.workload[user_id] = {
                "alerts_handled_24h": 0,
                "incidents_worked_week": 0,
                "consecutive_shifts": 0,
                "avg_response_time_min": 30,
                "last_shift": None
            }
        
        self.workload[user_id]["alerts_handled_24h"] = alerts_handled
        self.workload[user_id]["incidents_worked_week"] += incidents
        self.workload[user_id]["consecutive_shifts"] += 1
        self.workload[user_id]["last_shift"] = get_now_pst().isoformat()
        self.save_workload()
        
        fatigue_risk = self.calculate_fatigue_risk(user_id)
        
        color = discord.Color.green() if fatigue_risk < 40 else discord.Color.gold() if fatigue_risk < 70 else discord.Color.red()
        embed = discord.Embed(title="✅ Shift Logged", color=color, timestamp=get_now_pst())
        embed.add_field(name="Analyst", value=member.mention, inline=True)
        embed.add_field(name="Alerts Handled", value=alerts_handled, inline=True)
        embed.add_field(name="Incidents", value=incidents, inline=True)
        embed.add_field(name="Fatigue Risk", value=f"**{fatigue_risk:.1f}%**", inline=True)
        
        if fatigue_risk >= 70:
            embed.add_field(name="⚠️ Warning", value="High burnout risk detected - consider rotation", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="fatigue_predict")
    @commands.has_permissions(administrator=True)
    async def predict_fatigue(self, ctx, member: discord.Member):
        """Predict analyst burnout risk\nUsage: !fatigue_predict @analyst"""
        user_id = str(member.id)
        fatigue_risk = self.calculate_fatigue_risk(user_id)
        
        if fatigue_risk >= 70:
            risk_level = "🔴 HIGH RISK"
            recommendation = "Immediate rotation recommended"
            color = discord.Color.red()
        elif fatigue_risk >= 40:
            risk_level = "🟡 MODERATE RISK"
            recommendation = "Monitor closely, plan rotation"
            color = discord.Color.gold()
        else:
            risk_level = "🟢 LOW RISK"
            recommendation = "Normal operations"
            color = discord.Color.green()
        
        prediction = {
            "id": len(self.predictions) + 1,
            "user_id": user_id,
            "fatigue_risk": fatigue_risk,
            "risk_level": risk_level,
            "prediction_time": get_now_pst().isoformat(),
            "predicted_by": str(ctx.author.id)
        }
        
        self.predictions.append(prediction)
        self.save_predictions()
        
        embed = discord.Embed(title="🔮 Fatigue Risk Prediction", color=color, timestamp=get_now_pst())
        embed.add_field(name="Analyst", value=member.mention, inline=True)
        embed.add_field(name="Risk Score", value=f"**{fatigue_risk:.1f}%**", inline=True)
        embed.add_field(name="Risk Level", value=risk_level, inline=True)
        embed.add_field(name="Recommendation", value=recommendation, inline=False)
        
        if user_id in self.workload:
            workload = self.workload[user_id]
            embed.add_field(name="Alerts (24h)", value=workload.get("alerts_handled_24h", 0), inline=True)
            embed.add_field(name="Incidents (Week)", value=workload.get("incidents_worked_week", 0), inline=True)
            embed.add_field(name="Consecutive Shifts", value=workload.get("consecutive_shifts", 0), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="fatigue_team_status")
    @commands.has_permissions(administrator=True)
    async def team_status(self, ctx):
        """View team fatigue status\nUsage: !fatigue_team_status"""
        if not self.workload:
            await ctx.send("📊 No analyst data recorded")
            return
        
        embed = discord.Embed(title="👥 SOC Team Fatigue Status", color=discord.Color.blue(), timestamp=get_now_pst())
        
        high_risk = []
        moderate_risk = []
        low_risk = []
        
        for user_id in self.workload.keys():
            risk = self.calculate_fatigue_risk(user_id)
            if risk >= 70:
                high_risk.append((user_id, risk))
            elif risk >= 40:
                moderate_risk.append((user_id, risk))
            else:
                low_risk.append((user_id, risk))
        
        embed.add_field(name="🔴 High Risk", value=len(high_risk), inline=True)
        embed.add_field(name="🟡 Moderate Risk", value=len(moderate_risk), inline=True)
        embed.add_field(name="🟢 Low Risk", value=len(low_risk), inline=True)
        
        if high_risk:
            high_risk_text = "\n".join([f"<@{uid}> - {risk:.1f}%" for uid, risk in sorted(high_risk, key=lambda x: x[1], reverse=True)[:5]])
            embed.add_field(name="⚠️ Requires Attention", value=high_risk_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="fatigue_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View SOC fatigue dashboard\nUsage: !fatigue_dashboard"""
        total_analysts = len(self.workload)
        total_predictions = len(self.predictions)
        
        high_risk_count = sum(1 for uid in self.workload if self.calculate_fatigue_risk(uid) >= 70)
        
        embed = discord.Embed(title="📊 SOC Fatigue Dashboard", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="👥 Tracked Analysts", value=total_analysts, inline=True)
        embed.add_field(name="🔮 Total Predictions", value=total_predictions, inline=True)
        embed.add_field(name="🔴 High Risk", value=high_risk_count, inline=True)
        
        status = "🟢 HEALTHY" if high_risk_count == 0 else "🟡 MONITOR" if high_risk_count < 2 else "🔴 CRITICAL"
        embed.add_field(name="Team Health", value=status, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SOCFatiguePredictorCog(bot))
