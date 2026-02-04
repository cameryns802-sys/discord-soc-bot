"""
Risk Register System - Enterprise risk management for Sentinel
Risk identification, assessment, tracking, and mitigation planning
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class RiskRegisterSystem(commands.Cog):
    """Enterprise risk tracking and mitigation management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.risk_file = 'data/risk_register.json'
        self.load_risks()
    
    def load_risks(self):
        """Load risk register"""
        if not os.path.exists(self.risk_file):
            os.makedirs(os.path.dirname(self.risk_file), exist_ok=True)
            with open(self.risk_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_risks(self, guild_id):
        """Get risks for guild"""
        with open(self.risk_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_risks(self, guild_id, risks):
        """Save risks"""
        with open(self.risk_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = risks
        with open(self.risk_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_risk_score(self, likelihood, impact):
        """Calculate risk score (1-25)"""
        likelihood_map = {'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5}
        impact_map = {'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5}
        
        l_score = likelihood_map.get(likelihood, 3)
        i_score = impact_map.get(impact, 3)
        
        return l_score * i_score
    
    def get_risk_level(self, score):
        """Get risk level from score"""
        if score >= 20:
            return ('critical', '🔴', discord.Color.red())
        elif score >= 15:
            return ('high', '🟠', discord.Color.orange())
        elif score >= 10:
            return ('medium', '🟡', discord.Color.gold())
        elif score >= 5:
            return ('low', '🟢', discord.Color.green())
        else:
            return ('very_low', '🟦', discord.Color.blue())
    
    async def _riskcreate_logic(self, ctx, category: str, likelihood: str, impact: str, *, description: str):
        """Create new risk"""
        valid_categories = ['security', 'compliance', 'operational', 'financial', 'reputational', 'technical']
        valid_ratings = ['very_low', 'low', 'medium', 'high', 'very_high']
        
        if category.lower() not in valid_categories:
            await ctx.send(f"❌ Invalid category. Use: {', '.join(valid_categories)}")
            return
        
        if likelihood.lower() not in valid_ratings:
            await ctx.send(f"❌ Invalid likelihood. Use: {', '.join(valid_ratings)}")
            return
        
        if impact.lower() not in valid_ratings:
            await ctx.send(f"❌ Invalid impact. Use: {', '.join(valid_ratings)}")
            return
        
        parts = description.split('|')
        if len(parts) < 2:
            await ctx.send("Usage: `!riskcreate <category> <likelihood> <impact> <title> | <description>`")
            return
        
        title = parts[0].strip()
        desc = parts[1].strip()
        
        risks = self.get_guild_risks(ctx.guild.id)
        risk_id = f"RISK-{str(uuid.uuid4())[:8].upper()}"
        
        risk_score = self.calculate_risk_score(likelihood.lower(), impact.lower())
        risk_level, risk_emoji, _ = self.get_risk_level(risk_score)
        
        risk = {
            'id': risk_id,
            'title': title,
            'description': desc,
            'category': category.lower(),
            'likelihood': likelihood.lower(),
            'impact': impact.lower(),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'status': 'open',
            'owner': ctx.author.id,
            'created_at': get_now_pst().isoformat(),
            'last_updated': get_now_pst().isoformat(),
            'mitigation_plan': None,
            'mitigation_status': 'not_started',
            'review_date': None,
            'notes': []
        }
        
        risks[risk_id] = risk
        self.save_risks(ctx.guild.id, risks)
        
        _, _, color = self.get_risk_level(risk_score)
        
        embed = discord.Embed(
            title=f"{risk_emoji} Risk Registered",
            description=f"**{title}**",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Risk ID", value=f"`{risk_id}`", inline=True)
        embed.add_field(name="Category", value=category.title(), inline=True)
        embed.add_field(name="Risk Level", value=f"{risk_level.upper()}", inline=True)
        embed.add_field(name="Likelihood", value=likelihood.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Impact", value=impact.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk_score}/25", inline=True)
        embed.add_field(name="Description", value=desc, inline=False)
        embed.add_field(name="Owner", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="🟢 OPEN", inline=True)
        embed.set_footer(text="Sentinel Risk Register | Use !riskmitigate to add mitigation plan")
        
        await ctx.send(embed=embed)
    
    async def _risklist_logic(self, ctx, category: str = None):
        """List risks"""
        risks = self.get_guild_risks(ctx.guild.id)
        
        if not risks:
            await ctx.send("📋 No risks registered yet.")
            return
        
        # Filter by category if specified
        if category:
            risks = {k: v for k, v in risks.items() if v['category'] == category.lower()}
            if not risks:
                await ctx.send(f"📋 No risks found in category: {category}")
                return
        
        # Sort by risk score (highest first)
        sorted_risks = sorted(risks.values(), key=lambda r: r['risk_score'], reverse=True)
        
        embed = discord.Embed(
            title="📊 Risk Register",
            description=f"{len(sorted_risks)} risk(s) tracked" + (f" in category: {category}" if category else ""),
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        for risk in sorted_risks[:10]:
            _, emoji, _ = self.get_risk_level(risk['risk_score'])
            status_emoji = {'open': '🟢', 'mitigating': '🟡', 'closed': '⚪', 'accepted': '🔵'}.get(risk['status'], '❓')
            
            embed.add_field(
                name=f"{emoji} {risk['title']} ({risk['id']})",
                value=f"Score: {risk['risk_score']}/25 | {risk['category'].title()} | {status_emoji} {risk['status'].title()}",
                inline=False
            )
        
        if len(sorted_risks) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_risks) - 10} additional risks", inline=False)
        
        embed.set_footer(text="Use !riskdetail <id> for full details")
        
        await ctx.send(embed=embed)
    
    async def _riskdetail_logic(self, ctx, risk_id: str):
        """Show risk details"""
        risks = self.get_guild_risks(ctx.guild.id)
        
        risk_id = risk_id.upper()
        if not risk_id.startswith('RISK-'):
            risk_id = f"RISK-{risk_id}"
        
        risk = risks.get(risk_id)
        if not risk:
            await ctx.send(f"❌ Risk not found: {risk_id}")
            return
        
        _, emoji, color = self.get_risk_level(risk['risk_score'])
        
        embed = discord.Embed(
            title=f"{emoji} Risk Details: {risk['title']}",
            description=risk['description'],
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Risk ID", value=f"`{risk['id']}`", inline=True)
        embed.add_field(name="Category", value=risk['category'].title(), inline=True)
        embed.add_field(name="Risk Level", value=risk['risk_level'].upper(), inline=True)
        embed.add_field(name="Likelihood", value=risk['likelihood'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Impact", value=risk['impact'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk['risk_score']}/25", inline=True)
        
        try:
            owner = await self.bot.fetch_user(risk['owner'])
            embed.add_field(name="Owner", value=owner.mention, inline=True)
        except:
            embed.add_field(name="Owner", value="Unknown", inline=True)
        
        status_emoji = {'open': '🟢', 'mitigating': '🟡', 'closed': '⚪', 'accepted': '🔵'}.get(risk['status'], '❓')
        embed.add_field(name="Status", value=f"{status_emoji} {risk['status'].title()}", inline=True)
        
        created = datetime.fromisoformat(risk['created_at'])
        embed.add_field(name="Created", value=created.strftime('%Y-%m-%d %H:%M UTC'), inline=True)
        
        if risk['mitigation_plan']:
            embed.add_field(name="🛡️ Mitigation Plan", value=risk['mitigation_plan'], inline=False)
            embed.add_field(name="Mitigation Status", value=risk['mitigation_status'].replace('_', ' ').title(), inline=True)
        
        if risk['review_date']:
            embed.add_field(name="Next Review", value=risk['review_date'], inline=True)
        
        if risk['notes']:
            notes_str = "\n".join([f"• {note}" for note in risk['notes'][-3:]])
            embed.add_field(name="Recent Notes", value=notes_str, inline=False)
        
        embed.set_footer(text="Sentinel Risk Register")
        
        await ctx.send(embed=embed)
    
    async def _riskstats_logic(self, ctx):
        """Show risk statistics"""
        risks = self.get_guild_risks(ctx.guild.id)
        
        if not risks:
            await ctx.send("📊 No risks tracked yet.")
            return
        
        # Calculate stats
        total = len(risks)
        by_level = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'very_low': 0}
        by_category = {}
        by_status = {'open': 0, 'mitigating': 0, 'closed': 0, 'accepted': 0}
        
        total_score = 0
        
        for risk in risks.values():
            by_level[risk['risk_level']] = by_level.get(risk['risk_level'], 0) + 1
            by_category[risk['category']] = by_category.get(risk['category'], 0) + 1
            by_status[risk['status']] = by_status.get(risk['status'], 0) + 1
            total_score += risk['risk_score']
        
        avg_score = total_score / total if total > 0 else 0
        
        embed = discord.Embed(
            title="📊 Risk Register Statistics",
            description=f"Total: {total} risks | Avg Score: {avg_score:.1f}/25",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        level_str = f"🔴 Critical: {by_level['critical']}\n🟠 High: {by_level['high']}\n🟡 Medium: {by_level['medium']}\n🟢 Low: {by_level['low']}\n🟦 Very Low: {by_level['very_low']}"
        embed.add_field(name="📈 By Risk Level", value=level_str, inline=True)
        
        status_str = f"🟢 Open: {by_status['open']}\n🟡 Mitigating: {by_status['mitigating']}\n🔵 Accepted: {by_status['accepted']}\n⚪ Closed: {by_status['closed']}"
        embed.add_field(name="📊 By Status", value=status_str, inline=True)
        
        cat_str = "\n".join([f"{cat.title()}: {count}" for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5]])
        embed.add_field(name="📂 By Category", value=cat_str, inline=True)
        
        embed.set_footer(text="Sentinel Risk Register | Current snapshot")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='riskcreate')
    async def riskcreate_prefix(self, ctx, category: str, likelihood: str, impact: str, *, description: str):
        """Create risk - Prefix command"""
        await self._riskcreate_logic(ctx, category, likelihood, impact, description=description)
    
    @commands.command(name='risklist')
    async def risklist_prefix(self, ctx, category: str = None):
        """List risks - Prefix command"""
        await self._risklist_logic(ctx, category)
    
    @commands.command(name='riskdetail')
    async def riskdetail_prefix(self, ctx, risk_id: str):
        """Show risk details - Prefix command"""
        await self._riskdetail_logic(ctx, risk_id)
    
    @commands.command(name='riskstats')
    async def riskstats_prefix(self, ctx):
        """Show risk statistics - Prefix command"""
        await self._riskstats_logic(ctx)

async def setup(bot):
    await bot.add_cog(RiskRegisterSystem(bot))
