"""
Kill Chain Analyzer: MITRE ATT&CK classification and kill-chain stage tracking.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class KillChainAnalyzerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/kill_chain.json"
        self.data = self.load_data()
        self.mitre_tactics = self.get_mitre_tactics()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "detections": [],
            "attack_chains": {},
            "tactic_coverage": {},
            "active_campaigns": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_mitre_tactics(self):
        """MITRE ATT&CK Tactics (Kill Chain Stages)."""
        return {
            "reconnaissance": {"name": "Reconnaissance", "color": 0x3498db, "stage": 1},
            "resource_development": {"name": "Resource Development", "color": 0x9b59b6, "stage": 2},
            "initial_access": {"name": "Initial Access", "color": 0xe74c3c, "stage": 3},
            "execution": {"name": "Execution", "color": 0xe67e22, "stage": 4},
            "persistence": {"name": "Persistence", "color": 0xf39c12, "stage": 5},
            "privilege_escalation": {"name": "Privilege Escalation", "color": 0xf1c40f, "stage": 6},
            "defense_evasion": {"name": "Defense Evasion", "color": 0x1abc9c, "stage": 7},
            "credential_access": {"name": "Credential Access", "color": 0x16a085, "stage": 8},
            "discovery": {"name": "Discovery", "color": 0x27ae60, "stage": 9},
            "lateral_movement": {"name": "Lateral Movement", "color": 0x2ecc71, "stage": 10},
            "collection": {"name": "Collection", "color": 0x3498db, "stage": 11},
            "command_and_control": {"name": "Command and Control", "color": 0x2980b9, "stage": 12},
            "exfiltration": {"name": "Exfiltration", "color": 0x8e44ad, "stage": 13},
            "impact": {"name": "Impact", "color": 0xc0392b, "stage": 14}
        }

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="classify_alert")
    async def classify_alert(self, ctx, tactic: str, *, technique: str):
        """Classify an alert by MITRE ATT&CK tactic/technique."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        tactic_lower = tactic.lower().replace(" ", "_")
        if tactic_lower not in self.mitre_tactics:
            await ctx.send(f"❌ Invalid tactic. Use !kill_chain_stages for valid tactics.")
            return
        
        detection = {
            "tactic": tactic_lower,
            "technique": technique,
            "detected_by": str(ctx.author.id),
            "detected_at": get_now_pst().isoformat(),
            "stage": self.mitre_tactics[tactic_lower]["stage"]
        }
        
        self.data["detections"].append(detection)
        
        # Update tactic coverage
        if tactic_lower not in self.data["tactic_coverage"]:
            self.data["tactic_coverage"][tactic_lower] = 0
        self.data["tactic_coverage"][tactic_lower] += 1
        
        self.save_data(self.data)
        
        tactic_info = self.mitre_tactics[tactic_lower]
        embed = discord.Embed(
            title=f"🎯 Alert Classified: {tactic_info['name']}",
            description=f"Technique: {technique}",
            color=discord.Color(tactic_info["color"])
        )
        embed.add_field(name="Kill Chain Stage", value=f"{tactic_info['stage']}/14", inline=True)
        embed.add_field(name="Total Detections (Tactic)", value=str(self.data["tactic_coverage"][tactic_lower]), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="kill_chain_stages")
    async def kill_chain_stages(self, ctx):
        """View all MITRE ATT&CK kill chain stages."""
        embed = discord.Embed(
            title="🎯 MITRE ATT&CK Kill Chain Stages",
            description="14 Tactics in the Attack Lifecycle",
            color=discord.Color.blue()
        )
        
        sorted_tactics = sorted(self.mitre_tactics.items(), key=lambda x: x[1]["stage"])
        
        for tactic_key, tactic_data in sorted_tactics:
            detection_count = self.data["tactic_coverage"].get(tactic_key, 0)
            embed.add_field(
                name=f"{tactic_data['stage']}. {tactic_data['name']}",
                value=f"Detections: {detection_count}",
                inline=True
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="kill_chain_analysis")
    async def kill_chain_analysis(self, ctx):
        """Analyze current attack chain progression."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if not self.data["detections"]:
            await ctx.send("❌ No detections recorded yet.")
            return
        
        # Analyze detected stages
        detected_stages = set(d["stage"] for d in self.data["detections"])
        max_stage = max(detected_stages) if detected_stages else 0
        
        embed = discord.Embed(
            title="📊 Kill Chain Progression Analysis",
            description=f"Highest detected stage: {max_stage}/14",
            color=discord.Color.red() if max_stage > 10 else discord.Color.orange()
        )
        
        # Show progression
        stages_detected = []
        for stage in range(1, 15):
            if stage in detected_stages:
                stages_detected.append(f"✅ Stage {stage}")
            elif stage <= max_stage:
                stages_detected.append(f"⚠️ Stage {stage}")
            else:
                stages_detected.append(f"⬜ Stage {stage}")
        
        embed.add_field(name="Progression", value="\n".join(stages_detected[:7]), inline=True)
        embed.add_field(name="", value="\n".join(stages_detected[7:]), inline=True)
        
        # Risk assessment
        if max_stage >= 13:
            risk = "🔴 CRITICAL - Exfiltration or Impact Detected"
        elif max_stage >= 10:
            risk = "🟠 HIGH - Lateral Movement Detected"
        elif max_stage >= 6:
            risk = "🟡 MEDIUM - Escalation or Persistence Detected"
        else:
            risk = "🟢 LOW - Early Stage Detection"
        
        embed.add_field(name="Risk Assessment", value=risk, inline=False)
        embed.set_footer(text=f"Total Detections: {len(self.data['detections'])}")
        
        await ctx.send(embed=embed)

    @commands.command(name="attack_chain_map")
    async def attack_chain_map(self, ctx, chain_id: str = None):
        """View attack chain visualization."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        embed = discord.Embed(
            title="🗺️ Attack Chain Map",
            description="Visual representation of attack progression",
            color=discord.Color.blue()
        )
        
        # Create visual map
        chain = "```\n"
        chain += "MITRE ATT&CK Kill Chain\n"
        chain += "═══════════════════════\n\n"
        
        for tactic_key, tactic_data in sorted(self.mitre_tactics.items(), key=lambda x: x[1]["stage"]):
            count = self.data["tactic_coverage"].get(tactic_key, 0)
            if count > 0:
                chain += f"[{tactic_data['stage']:2d}] {tactic_data['name']:<30} ({'█' * min(count, 10)})\n"
            else:
                chain += f"[{tactic_data['stage']:2d}] {tactic_data['name']:<30} ○\n"
        
        chain += "```"
        
        embed.description = chain
        
        await ctx.send(embed=embed)

    @commands.command(name="tactic_drilldown")
    async def tactic_drilldown(self, ctx, tactic: str):
        """View detailed detections for a specific tactic."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        tactic_lower = tactic.lower().replace(" ", "_")
        if tactic_lower not in self.mitre_tactics:
            await ctx.send(f"❌ Invalid tactic.")
            return
        
        detections = [d for d in self.data["detections"] if d["tactic"] == tactic_lower]
        
        tactic_info = self.mitre_tactics[tactic_lower]
        embed = discord.Embed(
            title=f"🔍 Tactic Drilldown: {tactic_info['name']}",
            description=f"Stage {tactic_info['stage']}/14",
            color=discord.Color(tactic_info["color"])
        )
        
        if detections:
            for detection in detections[-10:]:
                embed.add_field(
                    name=detection["technique"],
                    value=f"Detected: {detection['detected_at'][:19]}",
                    inline=False
                )
        else:
            embed.add_field(name="No Detections", value="No detections for this tactic yet", inline=False)
        
        embed.set_footer(text=f"Total: {len(detections)} detections")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(KillChainAnalyzerCog(bot))
