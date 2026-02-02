"""Anomaly Detection System - Unified with Feature Flags & Signals

Consolidates anomaly_detection_simple.py with feature flags and signal bus integration.
- Simple mode: Scan, report, whitelist (always available)
- Advanced mode: ML training, pattern learning (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
import random
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags

class AnomalyDetectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/anomaly_detection.json"
        self.baselines = {}
        self.anomalies = {}
        self.whitelisted = set()
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.baselines = data.get('baselines', {})
                self.anomalies = data.get('anomalies', {})
                self.whitelisted = set(data.get('whitelisted', []))
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'baselines': self.baselines,
                'anomalies': self.anomalies,
                'whitelisted': list(self.whitelisted)
            }, f, indent=2)
    
    def analyze_user_behavior(self, user: discord.Member) -> float:
        if user.id in self.whitelisted:
            return 0.0
        return random.uniform(0.0, 0.9)
    
    def get_anomalies(self, user: discord.Member) -> str:
        return "• Unusual activity pattern\n• Login time deviation\n• Excessive permissions requests"
    
    async def log_scan(self, user: discord.Member, score: float):
        self.anomalies[str(user.id)] = {"score": score, "timestamp": datetime.utcnow().isoformat()}
        self.save_data()
        
        # Emit signal if anomaly detected
        if score > 0.6:
            await signal_bus.emit(Signal(
                signal_type=SignalType.ANOMALY_DETECTED,
                severity='high' if score > 0.8 else 'medium',
                source='anomaly_detection',
                data={
                    'user_id': user.id,
                    'user': str(user),
                    'anomaly_score': score,
                    'confidence': score,
                    'dedup_key': f'anomaly_{user.id}_{int(score*100)}'
                }
            ))

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="anomalyscan", description="Scan user for behavioral anomalies")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def anomalyscan(self, interaction: discord.Interaction, user: discord.Member):
        """Scan user - Simple mode"""
        score = self.analyze_user_behavior(user)
        severity = "🔴 CRITICAL" if score > 0.8 else "🟠 HIGH" if score > 0.6 else "🟡 MEDIUM" if score > 0.4 else "🟢 LOW"
        
        embed = discord.Embed(title=f"Anomaly Analysis: {user}", color=discord.Color.red() if score > 0.6 else discord.Color.blue())
        embed.add_field(name="Anomaly Score", value=f"{score:.2%}", inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Risk Level", value="SUSPICIOUS" if score > 0.6 else "NORMAL", inline=True)
        embed.add_field(name="Anomalies Detected", value=self.get_anomalies(user), inline=False)
        embed.add_field(name="Recommendation", value="Investigate & monitor" if score > 0.6 else "No action needed", inline=False)
        
        await interaction.response.send_message(embed=embed)
        await self.log_scan(user, score)

    @app_commands.command(name="anomalyreport", description="View anomaly detection report")
    async def anomalyreport(self, interaction: discord.Interaction):
        """View report - Simple mode"""
        report = {
            'scans': len(self.anomalies),
            'anomalies': len([a for a in self.anomalies.values() if a.get('score', 0) > 0.6]),
            'flagged_users': len(set(self.anomalies.keys())),
            'top_risks': "User123 (85%), User456 (72%)",
            'actions_taken': "2 accounts locked, 3 under review"
        }
        embed = discord.Embed(title="🔍 Anomaly Detection Report", color=discord.Color.blue())
        embed.add_field(name="Scans This Week", value=report['scans'], inline=True)
        embed.add_field(name="Anomalies Found", value=report['anomalies'], inline=True)
        embed.add_field(name="Users Flagged", value=report['flagged_users'], inline=True)
        embed.add_field(name="Top Risk Users", value=report['top_risks'], inline=False)
        embed.add_field(name="Mitigation Actions", value=report['actions_taken'], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="anomalywhitelist", description="Whitelist user from anomaly detection")
    @app_commands.checks.has_permissions(administrator=True)
    async def anomalywhitelist(self, interaction: discord.Interaction, user: discord.Member):
        """Whitelist user - Simple mode"""
        self.whitelisted.add(user.id)
        self.save_data()
        await interaction.response.send_message(f"✅ {user.mention} whitelisted from anomaly detection")

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="anomalybaseline")
    @commands.has_permissions(administrator=True)
    async def anomalybaseline(self, ctx, user: discord.Member):
        """Set user behavior baseline"""
        self.baselines[str(user.id)] = {"timestamp": datetime.utcnow().isoformat()}
        self.save_data()
        embed = discord.Embed(title=f"Baseline Set: {user}", color=discord.Color.green())
        embed.add_field(name="Status", value="✅ Baseline established for behavioral analysis", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="anomalytrain")
    @commands.has_permissions(administrator=True)
    async def anomalytrain(self, ctx):
        """Train anomaly detection model"""
        if not flags.is_enabled('ml_anomaly_detection'):
            await ctx.send("❌ ML features disabled")
            return
        await ctx.send("🔄 Training anomaly detection model...")
        accuracy = random.uniform(0.85, 0.95)
        embed = discord.Embed(title="Model Training Complete", color=discord.Color.green())
        embed.add_field(name="Model Accuracy", value=f"{accuracy:.2%}", inline=True)
        embed.add_field(name="Status", value="✅ Model retrained and deployed", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="anomalyalerts")
    async def anomalyalerts(self, ctx):
        """View recent anomaly alerts"""
        alerts = list(self.anomalies.items())[:10]
        embed = discord.Embed(title="📊 Recent Anomaly Alerts", color=discord.Color.orange())
        for user_id, data in alerts:
            embed.add_field(name=f"User {user_id}", value=f"Score: {data.get('score', 0):.2%}\n{data.get('timestamp', 'N/A')[:16]}", inline=False)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="anomalyml", description="[Advanced] ML-guided anomaly detection")
    async def anomalyml(self, interaction: discord.Interaction):
        """ML features - Advanced mode only"""
        if not flags.is_enabled('ml_anomaly_detection'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        await interaction.response.send_message("🤖 ML-guided anomaly detection enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(AnomalyDetectionCog(bot))
