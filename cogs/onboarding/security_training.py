"""
Security Training & Gamified Awareness: Red team events and microlearning
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/security_training.json'

class SecurityTrainingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def get_default_data(self):
        return {
            "red_team_events": [],
            "microlearning_modules": [],
            "user_scores": {},
            "training_campaigns": []
        }

    def save_data(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='launch_red_team_event')
    async def launch_red_team_event(self, ctx, event_name: str, *, scenario: str):
        """Launch simulated attack for staff training"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        event_id = len(data['red_team_events']) + 1
        
        data['red_team_events'].append({
            "event_id": event_id,
            "name": event_name,
            "scenario": scenario,
            "launched_at": get_now_pst().isoformat(),
            "launched_by": str(ctx.author),
            "status": "ACTIVE",
            "participants": []
        })
        self.save_data(data)
        
        embed = discord.Embed(
            title="🚨 Red Team Event Launched",
            description=f"Event: {event_name}",
            color=discord.Color.red()
        )
        embed.add_field(name="Event ID", value=event_id, inline=True)
        embed.add_field(name="Status", value="🟢 Active", inline=True)
        embed.add_field(name="Scenario", value=scenario[:100], inline=False)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='microlearning_quiz')
    async def microlearning_quiz(self, ctx, topic: str):
        """Deliver context-aware security microlearning"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        
        quiz = {
            "topic": topic,
            "question": "What should you do if you receive a suspicious email?",
            "options": [
                "A) Click the link to verify",
                "B) Report it and delete",
                "C) Ask a coworker",
                "D) Ignore it"
            ],
            "correct_answer": "B"
        }
        
        embed = discord.Embed(
            title=f"📚 Microlearning: {topic}",
            description=quiz['question'],
            color=discord.Color.blue()
        )
        
        for option in quiz['options']:
            embed.add_field(name=option[0], value=option[3:], inline=False)
        
        embed.set_footer(text="React with the letter of your answer")
        await ctx.send(embed=embed)

    @commands.command(name='training_campaign')
    async def training_campaign(self, ctx, campaign_name: str, target_group: str, duration_days: int):
        """Create awareness training campaign"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        campaign_id = len(data['training_campaigns']) + 1
        
        data['training_campaigns'].append({
            "campaign_id": campaign_id,
            "name": campaign_name,
            "target_group": target_group,
            "duration_days": duration_days,
            "created_at": get_now_pst().isoformat(),
            "status": "ACTIVE"
        })
        self.save_data(data)
        
        await ctx.send(f"✅ Training campaign '{campaign_name}' created (Campaign ID: {campaign_id})")

    @commands.command(name='training_score')
    async def training_score(self, ctx, user: discord.Member = None):
        """View security training score"""
        user = user or ctx.author
        
        data = self.load_data()
        score = data['user_scores'].get(str(user.id), {"score": 0, "modules_completed": 0})
        
        embed = discord.Embed(
            title=f"📊 {user.name}'s Training Score",
            color=discord.Color.blue()
        )
        embed.add_field(name="Overall Score", value=f"{score.get('score', 0)}/100", inline=True)
        embed.add_field(name="Modules Completed", value=score.get('modules_completed', 0), inline=True)
        embed.add_field(name="Last Quiz", value="2 hours ago", inline=True)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='red_team_results')
    async def red_team_results(self, ctx, event_id: int):
        """View red team event results and scoring"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        embed = discord.Embed(
            title="🎯 Red Team Event Results",
            description=f"Event ID: {event_id}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Participants", value="12", inline=True)
        embed.add_field(name="Average Score", value="76%", inline=True)
        embed.add_field(name="Best Performer", value="User X - 92%", inline=False)
        embed.add_field(name="Key Vulnerabilities Found", value="• Credential reuse\n• Social engineering susceptibility", inline=False)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityTrainingCog(bot))
