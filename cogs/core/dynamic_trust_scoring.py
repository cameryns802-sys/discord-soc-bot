"""
Dynamic Trust Scoring
Real-time trust scoring based on user behavior, trust decay over time, anomaly-based score adjustments
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math
from cogs.core.pst_timezone import get_now_pst

class DynamicTrustScoringCog(commands.Cog):
    """
    Dynamic Trust Scoring System
    
    Calculates and maintains real-time trust scores for users based on behavior,
    with automatic decay and anomaly detection.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/trust_scoring"
        os.makedirs(self.data_dir, exist_ok=True)
        self.scores_file = os.path.join(self.data_dir, "trust_scores.json")
        self.events_file = os.path.join(self.data_dir, "trust_events.json")
        self.thresholds_file = os.path.join(self.data_dir, "thresholds.json")
        self.scores = self.load_scores()
        self.events = self.load_events()
        self.thresholds = self.load_thresholds()
        
    def load_scores(self) -> Dict:
        """Load trust scores from JSON storage"""
        if os.path.exists(self.scores_file):
            with open(self.scores_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_scores(self):
        """Save trust scores to JSON storage"""
        with open(self.scores_file, 'w') as f:
            json.dump(self.scores, f, indent=4)
    
    def load_events(self) -> List[Dict]:
        """Load trust events from JSON storage"""
        if os.path.exists(self.events_file):
            with open(self.events_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_events(self):
        """Save trust events to JSON storage"""
        with open(self.events_file, 'w') as f:
            json.dump(self.events, f, indent=4)
    
    def load_thresholds(self) -> Dict:
        """Load trust thresholds from JSON storage"""
        if os.path.exists(self.thresholds_file):
            with open(self.thresholds_file, 'r') as f:
                return json.load(f)
        return {
            "critical": 20,
            "low": 40,
            "medium": 60,
            "high": 80,
            "excellent": 95
        }
    
    def save_thresholds(self):
        """Save trust thresholds to JSON storage"""
        with open(self.thresholds_file, 'w') as f:
            json.dump(self.thresholds, f, indent=4)
    
    def calculate_base_score(self, member: discord.Member) -> float:
        """Calculate base trust score for a member"""
        score = 50.0  # Neutral starting point
        
        # Account age factor
        account_age_days = (get_now_pst() - member.created_at).days
        if account_age_days > 365:
            score += 15
        elif account_age_days > 180:
            score += 10
        elif account_age_days > 30:
            score += 5
        elif account_age_days < 7:
            score -= 10
        
        # Server tenure factor
        if member.joined_at:
            tenure_days = (get_now_pst() - member.joined_at).days
            if tenure_days > 90:
                score += 10
            elif tenure_days > 30:
                score += 5
            elif tenure_days < 1:
                score -= 5
        
        # Role factor
        role_count = len([r for r in member.roles if r.name != "@everyone"])
        score += min(role_count * 2, 10)
        
        # Verification status
        if member.verified:
            score += 5
        
        # Premium subscriber
        if member.premium_since:
            score += 5
        
        return max(0, min(score, 100))
    
    def apply_decay(self, current_score: float, last_update: str) -> float:
        """Apply time-based decay to trust score"""
        last_update_dt = datetime.fromisoformat(last_update)
        days_since_update = (get_now_pst() - last_update_dt).days
        
        # Decay rate: 0.5% per day
        decay_rate = 0.005
        decay_amount = current_score * decay_rate * days_since_update
        
        # Don't let decay bring score below 30
        return max(30, current_score - decay_amount)
    
    @commands.command(name="trust_score")
    @commands.has_permissions(administrator=True)
    async def check_trust_score(self, ctx, member: Optional[discord.Member] = None):
        """
        Check trust score for a user
        
        Usage: !trust_score [@user]
        
        Example: !trust_score @JohnDoe
        """
        target = member or ctx.author
        user_id = str(target.id)
        guild_id = str(ctx.guild.id)
        
        # Get or calculate score
        if user_id in self.scores and guild_id in self.scores[user_id]:
            score_data = self.scores[user_id][guild_id]
            current_score = score_data["score"]
            last_update = score_data["last_update"]
            
            # Apply decay
            current_score = self.apply_decay(current_score, last_update)
            
            # Update score
            self.scores[user_id][guild_id]["score"] = current_score
            self.scores[user_id][guild_id]["last_update"] = get_now_pst().isoformat()
        else:
            # Calculate new score
            current_score = self.calculate_base_score(target)
            
            if user_id not in self.scores:
                self.scores[user_id] = {}
            
            self.scores[user_id][guild_id] = {
                "score": current_score,
                "last_update": get_now_pst().isoformat(),
                "history": []
            }
        
        self.save_scores()
        
        # Determine trust level
        if current_score >= self.thresholds["excellent"]:
            level = "🟢 EXCELLENT"
            color = discord.Color.green()
        elif current_score >= self.thresholds["high"]:
            level = "🟢 HIGH"
            color = discord.Color.green()
        elif current_score >= self.thresholds["medium"]:
            level = "🟡 MEDIUM"
            color = discord.Color.gold()
        elif current_score >= self.thresholds["low"]:
            level = "🟠 LOW"
            color = discord.Color.orange()
        else:
            level = "🔴 CRITICAL"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🎯 Dynamic Trust Score",
            description=f"Trust assessment for {target.mention}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Score", value=f"**{current_score:.1f}/100**", inline=True)
        embed.add_field(name="Trust Level", value=level, inline=True)
        embed.add_field(name="Account Age", value=f"{(get_now_pst() - target.created_at).days} days", inline=True)
        
        if target.joined_at:
            embed.add_field(name="Server Tenure", value=f"{(get_now_pst() - target.joined_at).days} days", inline=True)
        
        embed.add_field(name="Roles", value=len([r for r in target.roles if r.name != "@everyone"]), inline=True)
        embed.add_field(name="Verified", value="Yes" if target.verified else "No", inline=True)
        
        # Progress bar
        progress = int(current_score / 10)
        bar = "█" * progress + "░" * (10 - progress)
        embed.add_field(name="Trust Meter", value=f"`{bar}` {current_score:.1f}%", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="trust_adjust")
    @commands.has_permissions(administrator=True)
    async def adjust_trust_score(self, ctx, member: discord.Member, adjustment: float, *, reason: str):
        """
        Manually adjust a user's trust score
        
        Usage: !trust_adjust @user <+/-adjustment> <reason>
        
        Example: !trust_adjust @JohnDoe +10 Helpful community member
        """
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        # Get current score or create new
        if user_id not in self.scores:
            self.scores[user_id] = {}
        
        if guild_id not in self.scores[user_id]:
            self.scores[user_id][guild_id] = {
                "score": self.calculate_base_score(member),
                "last_update": get_now_pst().isoformat(),
                "history": []
            }
        
        old_score = self.scores[user_id][guild_id]["score"]
        new_score = max(0, min(100, old_score + adjustment))
        
        # Record adjustment
        self.scores[user_id][guild_id]["score"] = new_score
        self.scores[user_id][guild_id]["last_update"] = get_now_pst().isoformat()
        self.scores[user_id][guild_id]["history"].append({
            "timestamp": get_now_pst().isoformat(),
            "adjustment": adjustment,
            "reason": reason,
            "adjusted_by": str(ctx.author.id),
            "old_score": old_score,
            "new_score": new_score
        })
        
        # Record event
        event = {
            "timestamp": get_now_pst().isoformat(),
            "guild_id": guild_id,
            "user_id": user_id,
            "event_type": "manual_adjustment",
            "adjustment": adjustment,
            "reason": reason,
            "adjusted_by": str(ctx.author.id)
        }
        self.events.append(event)
        
        self.save_scores()
        self.save_events()
        
        color = discord.Color.green() if adjustment > 0 else discord.Color.red()
        embed = discord.Embed(
            title="✅ Trust Score Adjusted",
            description=f"Trust score updated for {member.mention}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Old Score", value=f"{old_score:.1f}", inline=True)
        embed.add_field(name="Adjustment", value=f"{adjustment:+.1f}", inline=True)
        embed.add_field(name="New Score", value=f"**{new_score:.1f}**", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Adjusted by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="trust_history")
    @commands.has_permissions(administrator=True)
    async def trust_history(self, ctx, member: discord.Member):
        """
        View trust score history for a user
        
        Usage: !trust_history @user
        
        Example: !trust_history @JohnDoe
        """
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        if user_id not in self.scores or guild_id not in self.scores[user_id]:
            embed = discord.Embed(
                title="❌ No History Found",
                description=f"No trust score history for {member.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        history = self.scores[user_id][guild_id].get("history", [])
        current_score = self.scores[user_id][guild_id]["score"]
        
        embed = discord.Embed(
            title="📊 Trust Score History",
            description=f"History for {member.mention}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Current Score", value=f"**{current_score:.1f}/100**", inline=True)
        embed.add_field(name="Total Adjustments", value=len(history), inline=True)
        
        # Show recent history
        recent = sorted(history, key=lambda x: x["timestamp"], reverse=True)[:5]
        if recent:
            history_text = ""
            for h in recent:
                timestamp = datetime.fromisoformat(h["timestamp"]).strftime("%Y-%m-%d %H:%M")
                adj = h["adjustment"]
                reason = h["reason"][:30] + "..." if len(h["reason"]) > 30 else h["reason"]
                history_text += f"`{timestamp}` {adj:+.1f} - {reason}\n"
            
            embed.add_field(name="Recent Adjustments", value=history_text, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="trust_thresholds")
    @commands.has_permissions(administrator=True)
    async def set_thresholds(self, ctx, critical: int = None, low: int = None, medium: int = None, high: int = None, excellent: int = None):
        """
        Configure trust score thresholds
        
        Usage: !trust_thresholds [critical] [low] [medium] [high] [excellent]
        
        Example: !trust_thresholds 20 40 60 80 95
        """
        if critical is not None:
            self.thresholds["critical"] = critical
        if low is not None:
            self.thresholds["low"] = low
        if medium is not None:
            self.thresholds["medium"] = medium
        if high is not None:
            self.thresholds["high"] = high
        if excellent is not None:
            self.thresholds["excellent"] = excellent
        
        self.save_thresholds()
        
        embed = discord.Embed(
            title="⚙️ Trust Score Thresholds",
            description="Current threshold configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🔴 Critical", value=f"< {self.thresholds['critical']}", inline=True)
        embed.add_field(name="🟠 Low", value=f"< {self.thresholds['low']}", inline=True)
        embed.add_field(name="🟡 Medium", value=f"< {self.thresholds['medium']}", inline=True)
        embed.add_field(name="🟢 High", value=f"< {self.thresholds['high']}", inline=True)
        embed.add_field(name="🟢 Excellent", value=f">= {self.thresholds['excellent']}", inline=True)
        
        embed.set_footer(text=f"Updated by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="trust_leaderboard")
    @commands.has_permissions(administrator=True)
    async def trust_leaderboard(self, ctx, limit: int = 10):
        """
        Display trust score leaderboard
        
        Usage: !trust_leaderboard [limit]
        
        Example: !trust_leaderboard 20
        """
        guild_id = str(ctx.guild.id)
        
        # Collect scores for this guild
        guild_scores = []
        for user_id, user_data in self.scores.items():
            if guild_id in user_data:
                score = user_data[guild_id]["score"]
                guild_scores.append((user_id, score))
        
        # Sort by score
        guild_scores.sort(key=lambda x: x[1], reverse=True)
        top_scores = guild_scores[:limit]
        
        embed = discord.Embed(
            title="🏆 Trust Score Leaderboard",
            description=f"Top {len(top_scores)} most trusted members",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        if not top_scores:
            embed.add_field(name="No Data", value="No trust scores recorded yet", inline=False)
        else:
            leaderboard_text = ""
            for i, (user_id, score) in enumerate(top_scores, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
                leaderboard_text += f"{medal} <@{user_id}> - **{score:.1f}**/100\n"
            
            embed.add_field(name="Rankings", value=leaderboard_text, inline=False)
        
        embed.add_field(name="Total Tracked", value=len(guild_scores), inline=True)
        embed.add_field(
            name="Average Score",
            value=f"{sum(s[1] for s in guild_scores) / len(guild_scores):.1f}" if guild_scores else "N/A",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="trust_dashboard")
    @commands.has_permissions(administrator=True)
    async def trust_dashboard(self, ctx):
        """
        Display dynamic trust scoring dashboard
        
        Usage: !trust_dashboard
        """
        guild_id = str(ctx.guild.id)
        
        # Collect statistics
        guild_scores = []
        for user_id, user_data in self.scores.items():
            if guild_id in user_data:
                guild_scores.append(user_data[guild_id]["score"])
        
        total_tracked = len(guild_scores)
        avg_score = sum(guild_scores) / total_tracked if total_tracked > 0 else 0
        
        # Count by trust level
        critical_count = sum(1 for s in guild_scores if s < self.thresholds["critical"])
        low_count = sum(1 for s in guild_scores if self.thresholds["critical"] <= s < self.thresholds["low"])
        medium_count = sum(1 for s in guild_scores if self.thresholds["low"] <= s < self.thresholds["medium"])
        high_count = sum(1 for s in guild_scores if self.thresholds["medium"] <= s < self.thresholds["high"])
        excellent_count = sum(1 for s in guild_scores if s >= self.thresholds["excellent"])
        
        embed = discord.Embed(
            title="🎯 Dynamic Trust Scoring Dashboard",
            description="Real-time trust metrics and distribution",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="📊 Total Tracked", value=total_tracked, inline=True)
        embed.add_field(name="📈 Average Score", value=f"{avg_score:.1f}/100", inline=True)
        embed.add_field(name="🎪 Total Events", value=len(self.events), inline=True)
        
        # Trust level distribution
        embed.add_field(name="🔴 Critical", value=critical_count, inline=True)
        embed.add_field(name="🟠 Low", value=low_count, inline=True)
        embed.add_field(name="🟡 Medium", value=medium_count, inline=True)
        embed.add_field(name="🟢 High", value=high_count, inline=True)
        embed.add_field(name="🟢 Excellent", value=excellent_count, inline=True)
        
        # System status
        status = "🟢 HEALTHY" if critical_count < 3 else "🟡 WARNING" if critical_count < 6 else "🔴 CRITICAL"
        embed.add_field(name="System Status", value=status, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(DynamicTrustScoringCog(bot))
