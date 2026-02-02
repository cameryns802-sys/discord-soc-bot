"""
False Flag Detection
Detects false flag operations with deception analysis and attribution confidence adjustments
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class FalseFlagDetectionCog(commands.Cog):
    """
    False Flag Detection System
    
    Analyzes threat actors for false flag indicators and adjusts attribution
    confidence based on deception analysis.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/false_flags"
        os.makedirs(self.data_dir, exist_ok=True)
        self.detections_file = os.path.join(self.data_dir, "false_flag_detections.json")
        self.indicators_file = os.path.join(self.data_dir, "deception_indicators.json")
        self.detections = self.load_detections()
        self.indicators = self.load_indicators()
        
    def load_detections(self) -> List[Dict]:
        """Load false flag detections from JSON storage"""
        if os.path.exists(self.detections_file):
            with open(self.detections_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_detections(self):
        """Save false flag detections to JSON storage"""
        with open(self.detections_file, 'w') as f:
            json.dump(self.detections, f, indent=4)
    
    def load_indicators(self) -> List[Dict]:
        """Load deception indicators from JSON storage"""
        if os.path.exists(self.indicators_file):
            with open(self.indicators_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_indicators(self):
        """Save deception indicators to JSON storage"""
        with open(self.indicators_file, 'w') as f:
            json.dump(self.indicators, f, indent=4)
    
    def calculate_false_flag_probability(self, attribution_id: int) -> float:
        """Calculate probability this is a false flag operation"""
        # Get indicators for this attribution
        attr_indicators = [i for i in self.indicators if i.get("attribution_id") == attribution_id]
        
        if not attr_indicators:
            return 0.0
        
        # Weight indicators
        indicator_weights = {
            "inconsistent_ttps": 20,      # TTPs don't match known actor
            "obvious_attribution": 15,    # Attribution too obvious/planted
            "misdirection": 15,            # Deliberate misdirection attempts
            "capability_mismatch": 20,    # Operation beyond actor's known capability
            "linguistic_errors": 10,      # Intentional linguistic mistakes
            "timing_suspicious": 10,      # Suspicious timing of attack
            "geopolitical_benefit": 10    # Who benefits analysis
        }
        
        total_score = 0
        for indicator in attr_indicators:
            indicator_type = indicator.get("type", "unknown")
            strength = indicator.get("strength", 50)  # 0-100
            
            base_weight = indicator_weights.get(indicator_type, 5)
            weighted_score = (base_weight * strength) / 100
            total_score += weighted_score
        
        return min(100, total_score)
    
    @commands.command(name="falseflag_analyze")
    @commands.has_permissions(administrator=True)
    async def analyze_attribution(self, ctx, attribution_id: int):
        """
        Analyze attribution for false flag indicators
        
        Usage: !falseflag_analyze <attribution_id>
        
        Example: !falseflag_analyze 1
        """
        # Check if attribution exists
        attr_cog = self.bot.get_cog('AttributionConfidenceModelCog')
        if not attr_cog or not hasattr(attr_cog, 'attributions'):
            await ctx.send("❌ Attribution system not available")
            return
        
        attribution = next((a for a in attr_cog.attributions if a["id"] == attribution_id), None)
        if not attribution:
            await ctx.send(f"❌ Attribution #{attribution_id} not found")
            return
        
        # Calculate false flag probability
        false_flag_prob = self.calculate_false_flag_probability(attribution_id)
        
        # Get indicators
        attr_indicators = [i for i in self.indicators if i.get("attribution_id") == attribution_id]
        
        # Determine risk level
        if false_flag_prob >= 70:
            risk_level = "🔴 HIGH RISK"
            color = discord.Color.red()
            assessment = "Strong indicators of false flag operation"
        elif false_flag_prob >= 40:
            risk_level = "🟡 MODERATE RISK"
            color = discord.Color.gold()
            assessment = "Some concerning indicators present"
        else:
            risk_level = "🟢 LOW RISK"
            color = discord.Color.green()
            assessment = "Attribution appears genuine"
        
        embed = discord.Embed(
            title=f"🎭 False Flag Analysis: {attribution['actor_name']}",
            description=f"Deception analysis for attribution #{attribution_id}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="False Flag Probability", value=f"**{false_flag_prob:.1f}%**", inline=True)
        embed.add_field(name="Risk Level", value=risk_level, inline=True)
        embed.add_field(name="Indicators Found", value=len(attr_indicators), inline=True)
        embed.add_field(name="Assessment", value=assessment, inline=False)
        
        # Show indicators if present
        if attr_indicators:
            indicator_summary = {}
            for ind in attr_indicators:
                itype = ind["type"]
                indicator_summary[itype] = indicator_summary.get(itype, 0) + 1
            
            indicator_text = "\n".join([f"• {itype.replace('_', ' ').title()}: {count}" for itype, count in indicator_summary.items()])
            embed.add_field(name="🚩 Deception Indicators", value=indicator_text, inline=False)
        
        # Recommendation
        if false_flag_prob >= 40:
            recommendation = "⚠️ Recommend additional analysis before finalizing attribution"
        else:
            recommendation = "✅ Attribution confidence justified"
        
        embed.add_field(name="Recommendation", value=recommendation, inline=False)
        embed.set_footer(text=f"Analyzed by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="falseflag_add_indicator")
    @commands.has_permissions(administrator=True)
    async def add_indicator(self, ctx, attribution_id: int, indicator_type: str, strength: int, *, description: str):
        """
        Add false flag indicator to attribution
        
        Usage: !falseflag_add_indicator <attribution_id> <type> <strength_0-100> <description>
        Types: inconsistent_ttps, obvious_attribution, misdirection, capability_mismatch, linguistic_errors, timing_suspicious, geopolitical_benefit
        
        Example: !falseflag_add_indicator 1 obvious_attribution 75 Attribution artifacts appear deliberately planted
        """
        valid_types = [
            "inconsistent_ttps", "obvious_attribution", "misdirection",
            "capability_mismatch", "linguistic_errors", "timing_suspicious",
            "geopolitical_benefit"
        ]
        
        if indicator_type not in valid_types:
            await ctx.send(f"❌ Invalid indicator type. Use: {', '.join(valid_types)}")
            return
        
        indicator = {
            "id": len(self.indicators) + 1,
            "attribution_id": attribution_id,
            "type": indicator_type,
            "strength": max(0, min(100, strength)),
            "description": description,
            "added_at": datetime.utcnow().isoformat(),
            "added_by": str(ctx.author.id)
        }
        
        self.indicators.append(indicator)
        self.save_indicators()
        
        # Recalculate false flag probability
        new_prob = self.calculate_false_flag_probability(attribution_id)
        
        embed = discord.Embed(
            title="🚩 False Flag Indicator Added",
            description=f"New deception indicator for attribution #{attribution_id}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Indicator ID", value=f"#{indicator['id']}", inline=True)
        embed.add_field(name="Type", value=indicator_type.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Strength", value=f"{strength}/100", inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Updated False Flag Probability", value=f"**{new_prob:.1f}%**", inline=True)
        embed.set_footer(text=f"Added by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="falseflag_create_detection")
    @commands.has_permissions(administrator=True)
    async def create_detection(self, ctx, attribution_id: int, confidence: str, *, analysis: str):
        """
        Create false flag detection report
        
        Usage: !falseflag_create_detection <attribution_id> <confirmed|suspected|unlikely> <analysis>
        
        Example: !falseflag_create_detection 1 suspected Multiple indicators suggest this may be misdirection
        """
        detection = {
            "id": len(self.detections) + 1,
            "attribution_id": attribution_id,
            "confidence": confidence.lower(),
            "analysis": analysis,
            "false_flag_probability": self.calculate_false_flag_probability(attribution_id),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": str(ctx.author.id),
            "status": "active"
        }
        
        self.detections.append(detection)
        self.save_detections()
        
        color_map = {
            "confirmed": discord.Color.red(),
            "suspected": discord.Color.gold(),
            "unlikely": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="🎭 False Flag Detection Created",
            description=f"New detection for attribution #{attribution_id}",
            color=color_map.get(confidence.lower(), discord.Color.blue()),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Detection ID", value=f"#{detection['id']}", inline=True)
        embed.add_field(name="Confidence", value=confidence.upper(), inline=True)
        embed.add_field(name="Probability", value=f"{detection['false_flag_probability']:.1f}%", inline=True)
        embed.add_field(name="Analysis", value=analysis, inline=False)
        embed.set_footer(text=f"Created by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="falseflag_list")
    @commands.has_permissions(administrator=True)
    async def list_detections(self, ctx):
        """
        List all false flag detections
        
        Usage: !falseflag_list
        """
        if not self.detections:
            embed = discord.Embed(
                title="🎭 False Flag Detections",
                description="No false flag detections recorded",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Sort by false flag probability
        sorted_detections = sorted(self.detections, key=lambda x: x.get("false_flag_probability", 0), reverse=True)
        
        embed = discord.Embed(
            title="🎭 False Flag Detections",
            description=f"Tracking {len(self.detections)} potential false flag operations",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for i, detection in enumerate(sorted_detections[:10], 1):
            prob = detection["false_flag_probability"]
            confidence = detection["confidence"]
            
            if prob >= 70:
                indicator = "🔴"
            elif prob >= 40:
                indicator = "🟡"
            else:
                indicator = "🟢"
            
            embed.add_field(
                name=f"{indicator} Detection #{detection['id']} - Attribution #{detection['attribution_id']}",
                value=f"Probability: {prob:.1f}% | Confidence: {confidence.upper()}",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="falseflag_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """
        Display false flag detection dashboard
        
        Usage: !falseflag_dashboard
        """
        # Calculate statistics
        total_detections = len(self.detections)
        confirmed = len([d for d in self.detections if d.get("confidence") == "confirmed"])
        suspected = len([d for d in self.detections if d.get("confidence") == "suspected"])
        unlikely = len([d for d in self.detections if d.get("confidence") == "unlikely"])
        
        total_indicators = len(self.indicators)
        
        # High risk detections
        high_risk = len([d for d in self.detections if d.get("false_flag_probability", 0) >= 70])
        
        embed = discord.Embed(
            title="🎭 False Flag Detection Dashboard",
            description="Deception analysis and false flag tracking",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📊 Total Detections", value=total_detections, inline=True)
        embed.add_field(name="🚩 Total Indicators", value=total_indicators, inline=True)
        embed.add_field(name="🔴 High Risk", value=high_risk, inline=True)
        embed.add_field(name="✅ Confirmed", value=confirmed, inline=True)
        embed.add_field(name="🟡 Suspected", value=suspected, inline=True)
        embed.add_field(name="🟢 Unlikely", value=unlikely, inline=True)
        
        # Average false flag probability
        if self.detections:
            avg_prob = sum(d.get("false_flag_probability", 0) for d in self.detections) / len(self.detections)
            embed.add_field(name="📈 Average Probability", value=f"{avg_prob:.1f}%", inline=True)
        
        # System status
        status = "🟢 NORMAL" if high_risk == 0 else "🟡 ELEVATED" if high_risk < 3 else "🔴 CRITICAL"
        embed.add_field(name="System Status", value=status, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(FalseFlagDetectionCog(bot))
