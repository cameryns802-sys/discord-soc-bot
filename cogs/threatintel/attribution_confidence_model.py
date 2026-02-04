"""
Attribution Confidence Model
Threat attribution with confidence scoring, alternative hypothesis modeling, evidence tracking
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class AttributionConfidenceModelCog(commands.Cog):
    """
    Attribution Confidence Model
    
    Tracks threat actor attribution with evidence-based confidence scoring
    and alternative hypothesis analysis.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/attribution"
        os.makedirs(self.data_dir, exist_ok=True)
        self.attributions_file = os.path.join(self.data_dir, "attributions.json")
        self.evidence_file = os.path.join(self.data_dir, "evidence.json")
        self.hypotheses_file = os.path.join(self.data_dir, "hypotheses.json")
        self.attributions = self.load_attributions()
        self.evidence = self.load_evidence()
        self.hypotheses = self.load_hypotheses()
        
    def load_attributions(self) -> List[Dict]:
        """Load threat attributions from JSON storage"""
        if os.path.exists(self.attributions_file):
            with open(self.attributions_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_attributions(self):
        """Save threat attributions to JSON storage"""
        with open(self.attributions_file, 'w') as f:
            json.dump(self.attributions, f, indent=4)
    
    def load_evidence(self) -> List[Dict]:
        """Load attribution evidence from JSON storage"""
        if os.path.exists(self.evidence_file):
            with open(self.evidence_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_evidence(self):
        """Save attribution evidence to JSON storage"""
        with open(self.evidence_file, 'w') as f:
            json.dump(self.evidence, f, indent=4)
    
    def load_hypotheses(self) -> List[Dict]:
        """Load alternative hypotheses from JSON storage"""
        if os.path.exists(self.hypotheses_file):
            with open(self.hypotheses_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_hypotheses(self):
        """Save alternative hypotheses to JSON storage"""
        with open(self.hypotheses_file, 'w') as f:
            json.dump(self.hypotheses, f, indent=4)
    
    def calculate_confidence(self, attribution_id: int) -> float:
        """Calculate confidence score based on evidence weight"""
        # Get all evidence for this attribution
        attribution_evidence = [e for e in self.evidence if e.get("attribution_id") == attribution_id]
        
        if not attribution_evidence:
            return 0.0
        
        # Weight evidence by type and quality
        evidence_weights = {
            "ttps": 25,      # Tactics, Techniques, Procedures
            "infrastructure": 20,  # Infrastructure overlap
            "malware": 20,   # Malware signatures
            "linguistic": 10, # Language/cultural indicators
            "timing": 10,    # Attack timing patterns
            "targets": 15    # Target selection patterns
        }
        
        total_score = 0
        for evidence in attribution_evidence:
            evidence_type = evidence.get("type", "unknown")
            quality = evidence.get("quality", 50)  # 0-100
            
            base_weight = evidence_weights.get(evidence_type, 5)
            weighted_score = (base_weight * quality) / 100
            total_score += weighted_score
        
        # Normalize to 0-100
        return min(100, total_score)
    
    @commands.command(name="attr_create")
    @commands.has_permissions(administrator=True)
    async def create_attribution(self, ctx, actor_name: str, *, description: str):
        """
        Create new threat actor attribution
        
        Usage: !attr_create <actor_name> <description>
        
        Example: !attr_create "APT29" Advanced persistent threat targeting government entities
        """
        attribution = {
            "id": len(self.attributions) + 1,
            "actor_name": actor_name,
            "description": description,
            "confidence_score": 0,
            "created_at": get_now_pst().isoformat(),
            "created_by": str(ctx.author.id),
            "status": "investigating"
        }
        
        self.attributions.append(attribution)
        self.save_attributions()
        
        embed = discord.Embed(
            title="✅ Attribution Created",
            description=f"New threat actor attribution: **{actor_name}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Attribution ID", value=f"#{attribution['id']}", inline=True)
        embed.add_field(name="Confidence", value=f"{attribution['confidence_score']}/100", inline=True)
        embed.add_field(name="Status", value=attribution["status"].upper(), inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.set_footer(text=f"Created by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="attr_add_evidence")
    @commands.has_permissions(administrator=True)
    async def add_evidence(self, ctx, attribution_id: int, evidence_type: str, quality: int, *, description: str):
        """
        Add evidence to attribution
        
        Usage: !attr_add_evidence <attribution_id> <ttps|infrastructure|malware|linguistic|timing|targets> <quality_0-100> <description>
        
        Example: !attr_add_evidence 1 ttps 85 Uses credential dumping technique matching known actor profile
        """
        # Validate attribution exists
        attribution = next((a for a in self.attributions if a["id"] == attribution_id), None)
        if not attribution:
            await ctx.send(f"❌ Attribution #{attribution_id} not found")
            return
        
        # Validate evidence type
        valid_types = ["ttps", "infrastructure", "malware", "linguistic", "timing", "targets"]
        if evidence_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid evidence type. Use: {', '.join(valid_types)}")
            return
        
        # Add evidence
        evidence = {
            "id": len(self.evidence) + 1,
            "attribution_id": attribution_id,
            "type": evidence_type.lower(),
            "quality": max(0, min(100, quality)),
            "description": description,
            "added_at": get_now_pst().isoformat(),
            "added_by": str(ctx.author.id)
        }
        
        self.evidence.append(evidence)
        self.save_evidence()
        
        # Recalculate confidence
        new_confidence = self.calculate_confidence(attribution_id)
        attribution["confidence_score"] = new_confidence
        self.save_attributions()
        
        embed = discord.Embed(
            title="✅ Evidence Added",
            description=f"Evidence added to attribution **{attribution['actor_name']}**",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Evidence ID", value=f"#{evidence['id']}", inline=True)
        embed.add_field(name="Type", value=evidence_type.upper(), inline=True)
        embed.add_field(name="Quality", value=f"{quality}/100", inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Updated Confidence", value=f"**{new_confidence:.1f}/100**", inline=True)
        embed.set_footer(text=f"Added by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="attr_hypothesis")
    @commands.has_permissions(administrator=True)
    async def add_hypothesis(self, ctx, attribution_id: int, *, hypothesis: str):
        """
        Add alternative hypothesis to attribution
        
        Usage: !attr_hypothesis <attribution_id> <hypothesis>
        
        Example: !attr_hypothesis 1 Could be false flag operation by different actor group
        """
        attribution = next((a for a in self.attributions if a["id"] == attribution_id), None)
        if not attribution:
            await ctx.send(f"❌ Attribution #{attribution_id} not found")
            return
        
        alt_hypothesis = {
            "id": len(self.hypotheses) + 1,
            "attribution_id": attribution_id,
            "hypothesis": hypothesis,
            "likelihood": "possible",
            "created_at": get_now_pst().isoformat(),
            "created_by": str(ctx.author.id)
        }
        
        self.hypotheses.append(alt_hypothesis)
        self.save_hypotheses()
        
        embed = discord.Embed(
            title="💡 Alternative Hypothesis Added",
            description=f"New hypothesis for **{attribution['actor_name']}**",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Hypothesis ID", value=f"#{alt_hypothesis['id']}", inline=True)
        embed.add_field(name="Likelihood", value=alt_hypothesis["likelihood"].upper(), inline=True)
        embed.add_field(name="Hypothesis", value=hypothesis, inline=False)
        embed.set_footer(text=f"Added by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="attr_view")
    @commands.has_permissions(administrator=True)
    async def view_attribution(self, ctx, attribution_id: int):
        """
        View detailed attribution analysis
        
        Usage: !attr_view <attribution_id>
        
        Example: !attr_view 1
        """
        attribution = next((a for a in self.attributions if a["id"] == attribution_id), None)
        if not attribution:
            await ctx.send(f"❌ Attribution #{attribution_id} not found")
            return
        
        # Get evidence and hypotheses
        attribution_evidence = [e for e in self.evidence if e.get("attribution_id") == attribution_id]
        attribution_hypotheses = [h for h in self.hypotheses if h.get("attribution_id") == attribution_id]
        
        # Determine confidence level
        confidence = attribution["confidence_score"]
        if confidence >= 85:
            confidence_level = "🟢 HIGH"
            color = discord.Color.green()
        elif confidence >= 60:
            confidence_level = "🟡 MEDIUM"
            color = discord.Color.gold()
        elif confidence >= 30:
            confidence_level = "🟠 LOW"
            color = discord.Color.orange()
        else:
            confidence_level = "🔴 VERY LOW"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title=f"🎯 Attribution Analysis: {attribution['actor_name']}",
            description=attribution["description"],
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Attribution ID", value=f"#{attribution['id']}", inline=True)
        embed.add_field(name="Confidence Score", value=f"**{confidence:.1f}/100**", inline=True)
        embed.add_field(name="Confidence Level", value=confidence_level, inline=True)
        embed.add_field(name="Status", value=attribution["status"].upper(), inline=True)
        embed.add_field(name="Evidence Count", value=len(attribution_evidence), inline=True)
        embed.add_field(name="Alt. Hypotheses", value=len(attribution_hypotheses), inline=True)
        
        # Show evidence summary
        if attribution_evidence:
            evidence_summary = {}
            for e in attribution_evidence:
                etype = e["type"]
                evidence_summary[etype] = evidence_summary.get(etype, 0) + 1
            
            evidence_text = "\n".join([f"• {etype.upper()}: {count}" for etype, count in evidence_summary.items()])
            embed.add_field(name="📊 Evidence Breakdown", value=evidence_text, inline=False)
        
        # Show alternative hypotheses
        if attribution_hypotheses:
            hypotheses_text = "\n".join([f"• {h['hypothesis'][:60]}..." if len(h['hypothesis']) > 60 else f"• {h['hypothesis']}" for h in attribution_hypotheses[:3]])
            embed.add_field(name="💡 Alternative Hypotheses", value=hypotheses_text, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="attr_list")
    @commands.has_permissions(administrator=True)
    async def list_attributions(self, ctx):
        """
        List all threat actor attributions
        
        Usage: !attr_list
        """
        if not self.attributions:
            embed = discord.Embed(
                title="📋 Threat Actor Attributions",
                description="No attributions tracked",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Sort by confidence score
        sorted_attributions = sorted(self.attributions, key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        embed = discord.Embed(
            title="📋 Threat Actor Attributions",
            description=f"Tracking {len(self.attributions)} threat actor attributions",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for i, attr in enumerate(sorted_attributions[:10], 1):
            confidence = attr["confidence_score"]
            
            if confidence >= 85:
                indicator = "🟢"
            elif confidence >= 60:
                indicator = "🟡"
            elif confidence >= 30:
                indicator = "🟠"
            else:
                indicator = "🔴"
            
            embed.add_field(
                name=f"{indicator} #{attr['id']} - {attr['actor_name']}",
                value=f"Confidence: {confidence:.1f}/100 | Status: {attr['status']}",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="attr_dashboard")
    @commands.has_permissions(administrator=True)
    async def attribution_dashboard(self, ctx):
        """
        Display attribution analysis dashboard
        
        Usage: !attr_dashboard
        """
        # Calculate statistics
        total_attributions = len(self.attributions)
        high_confidence = len([a for a in self.attributions if a.get("confidence_score", 0) >= 85])
        medium_confidence = len([a for a in self.attributions if 60 <= a.get("confidence_score", 0) < 85])
        low_confidence = len([a for a in self.attributions if a.get("confidence_score", 0) < 60])
        
        total_evidence = len(self.evidence)
        total_hypotheses = len(self.hypotheses)
        
        embed = discord.Embed(
            title="🎯 Attribution Analysis Dashboard",
            description="Threat actor attribution tracking",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="📊 Total Attributions", value=total_attributions, inline=True)
        embed.add_field(name="📝 Evidence Items", value=total_evidence, inline=True)
        embed.add_field(name="💡 Alt. Hypotheses", value=total_hypotheses, inline=True)
        embed.add_field(name="🟢 High Confidence", value=high_confidence, inline=True)
        embed.add_field(name="🟡 Medium Confidence", value=medium_confidence, inline=True)
        embed.add_field(name="🔴 Low Confidence", value=low_confidence, inline=True)
        
        # Average confidence
        if self.attributions:
            avg_confidence = sum(a.get("confidence_score", 0) for a in self.attributions) / len(self.attributions)
            embed.add_field(name="📈 Average Confidence", value=f"{avg_confidence:.1f}/100", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(AttributionConfidenceModelCog(bot))
