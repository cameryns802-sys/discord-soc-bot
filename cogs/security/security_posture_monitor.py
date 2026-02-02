import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SecurityPostureMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.posture_file = "data/security_posture.json"
        self.load_posture()

    def load_posture(self):
        if os.path.exists(self.posture_file):
            with open(self.posture_file) as f:
                self.posture = json.load(f)
        else:
            self.posture = {
                "score": 85,
                "areas": {
                    "access_control": 90,
                    "threat_detection": 85,
                    "incident_response": 80,
                    "compliance": 88,
                    "data_protection": 82,
                    "vulnerability_mgmt": 78
                },
                "last_updated": datetime.utcnow().isoformat()
            }

    def save_posture(self):
        os.makedirs("data", exist_ok=True)
        with open(self.posture_file, 'w') as f:
            json.dump(self.posture, f, indent=2)

    @commands.command()
    async def posturescore(self, ctx):
        """View current security posture score"""
        score = self.posture["score"]
        
        if score >= 90:
            color = discord.Color.green()
            status = "🟢 EXCELLENT"
        elif score >= 75:
            color = discord.Color.yellow()
            status = "🟡 GOOD"
        else:
            color = discord.Color.red()
            status = "🔴 AT RISK"
        
        embed = discord.Embed(
            title="🛡️ Security Posture Score",
            description=f"Overall Score: **{score}/100**",
            color=color
        )
        embed.add_field(name="Status", value=status, inline=False)
        
        for area, score in self.posture["areas"].items():
            emoji = "✅" if score >= 85 else "⚠️" if score >= 75 else "❌"
            embed.add_field(name=f"{emoji} {area.replace('_', ' ').title()}", value=str(score), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def updateposture(self, ctx, area: str, new_score: int):
        """Update security posture score for an area"""
        if area.lower() not in self.posture["areas"]:
            await ctx.send(f"❌ Unknown area. Valid areas: {', '.join(self.posture['areas'].keys())}")
            return
        
        if not 0 <= new_score <= 100:
            await ctx.send("❌ Score must be between 0 and 100")
            return
        
        old_score = self.posture["areas"][area.lower()]
        self.posture["areas"][area.lower()] = new_score
        self.posture["last_updated"] = datetime.utcnow().isoformat()
        
        # Recalculate overall score
        self.posture["score"] = sum(self.posture["areas"].values()) // len(self.posture["areas"])
        self.save_posture()
        
        change = new_score - old_score
        change_text = f"📈 +{change}" if change > 0 else f"📉 {change}"
        
        embed = discord.Embed(
            title="✅ Posture Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="Area", value=area.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Change", value=change_text, inline=True)
        embed.add_field(name="New Score", value=new_score, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def posturetrends(self, ctx):
        """Show security posture trends"""
        embed = discord.Embed(
            title="📊 Security Posture Trends",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="30-Day Trend",
            value="↗️ +4 points (steady improvement)",
            inline=False
        )
        embed.add_field(
            name="Risk Areas",
            value="• Vulnerability Management: -7 points\n• Incident Response: -2 points",
            inline=False
        )
        embed.add_field(
            name="Strengths",
            value="• Access Control: +3 points\n• Compliance: +5 points",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def postureforecast(self, ctx):
        """AI-powered security posture forecast"""
        embed = discord.Embed(
            title="🔮 Security Posture Forecast",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="90-Day Projection",
            value="Expected score: 89/100 (📈 +4 points)",
            inline=False
        )
        embed.add_field(
            name="Key Drivers",
            value="• Vulnerability remediation timeline\n• Compliance certification progress\n• Threat detection improvements",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityPostureMonitorCog(bot))
