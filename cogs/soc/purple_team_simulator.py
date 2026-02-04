"""
Purple Team Simulator
Red/blue team adversarial simulations with attack vs defense scenarios
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import random
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class PurpleTeamSimulatorCog(commands.Cog):
    """
    Purple Team Simulator
    
    Runs adversarial simulations combining red team (attack) and blue team
    (defense) perspectives for comprehensive security testing.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/purple_team"
        os.makedirs(self.data_dir, exist_ok=True)
        self.simulations_file = os.path.join(self.data_dir, "simulations.json")
        self.scenarios_file = os.path.join(self.data_dir, "scenarios.json")
        self.simulations = self.load_simulations()
        self.scenarios = self.load_scenarios()
        
    def load_simulations(self) -> List[Dict]:
        """Load simulation results from JSON storage"""
        if os.path.exists(self.simulations_file):
            with open(self.simulations_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_simulations(self):
        """Save simulation results to JSON storage"""
        with open(self.simulations_file, 'w') as f:
            json.dump(self.simulations, f, indent=4)
    
    def load_scenarios(self) -> List[Dict]:
        """Load attack scenarios from JSON storage"""
        if os.path.exists(self.scenarios_file):
            with open(self.scenarios_file, 'r') as f:
                return json.load(f)
        return self.get_default_scenarios()
    
    def save_scenarios(self):
        """Save attack scenarios to JSON storage"""
        with open(self.scenarios_file, 'w') as f:
            json.dump(self.scenarios, f, indent=4)
    
    def get_default_scenarios(self) -> List[Dict]:
        """Get default attack scenarios"""
        return [
            {
                "id": 1,
                "name": "Phishing Campaign",
                "category": "social_engineering",
                "difficulty": "medium",
                "description": "Simulated phishing attack targeting user credentials"
            },
            {
                "id": 2,
                "name": "Privilege Escalation",
                "category": "exploitation",
                "difficulty": "hard",
                "description": "Attempt to gain elevated privileges on target systems"
            },
            {
                "id": 3,
                "name": "Data Exfiltration",
                "category": "data_theft",
                "difficulty": "medium",
                "description": "Simulate unauthorized data extraction"
            },
            {
                "id": 4,
                "name": "Lateral Movement",
                "category": "post_exploitation",
                "difficulty": "hard",
                "description": "Test detection of attacker movement within network"
            },
            {
                "id": 5,
                "name": "DDoS Attack",
                "category": "availability",
                "difficulty": "easy",
                "description": "Distributed denial of service simulation"
            }
        ]
    
    @commands.command(name="purple_simulate")
    @commands.has_permissions(administrator=True)
    async def run_simulation(self, ctx, scenario_id: int):
        """
        Run purple team simulation
        
        Usage: !purple_simulate <scenario_id>
        
        Example: !purple_simulate 1
        """
        scenario = next((s for s in self.scenarios if s["id"] == scenario_id), None)
        if not scenario:
            await ctx.send(f"❌ Scenario #{scenario_id} not found. Use `!purple_scenarios` to list available scenarios.")
            return
        
        await ctx.send(f"⏳ Starting purple team simulation: **{scenario['name']}**...")
        
        # Simulate red team attack
        red_team_results = self.simulate_red_team(scenario)
        
        # Simulate blue team defense
        blue_team_results = self.simulate_blue_team(scenario, red_team_results)
        
        # Calculate results
        simulation = {
            "id": len(self.simulations) + 1,
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "executed_at": get_now_pst().isoformat(),
            "executed_by": str(ctx.author.id),
            "red_team": red_team_results,
            "blue_team": blue_team_results,
            "detection_latency_seconds": blue_team_results["detection_time"],
            "defense_effectiveness": blue_team_results["effectiveness_score"]
        }
        
        self.simulations.append(simulation)
        self.save_simulations()
        
        # Determine outcome
        if blue_team_results["effectiveness_score"] >= 80:
            outcome = "🟢 DEFENSE SUCCESSFUL"
            color = discord.Color.green()
        elif blue_team_results["effectiveness_score"] >= 50:
            outcome = "🟡 PARTIAL DEFENSE"
            color = discord.Color.gold()
        else:
            outcome = "🔴 ATTACK SUCCESSFUL"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🎯 Purple Team Simulation Results",
            description=f"Scenario: **{scenario['name']}**",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Simulation ID", value=f"#{simulation['id']}", inline=True)
        embed.add_field(name="Difficulty", value=scenario["difficulty"].upper(), inline=True)
        embed.add_field(name="Outcome", value=outcome, inline=True)
        
        # Red Team Results
        red_text = f"Attack Vectors: {red_team_results['vectors_attempted']}\n"
        red_text += f"Successful: {red_team_results['vectors_successful']}\n"
        red_text += f"Attack Score: {red_team_results['attack_score']}/100"
        embed.add_field(name="⚔️ Red Team (Attack)", value=red_text, inline=True)
        
        # Blue Team Results
        blue_text = f"Detection Time: {blue_team_results['detection_time']}s\n"
        blue_text += f"Alerts Triggered: {blue_team_results['alerts_triggered']}\n"
        blue_text += f"Defense Score: {blue_team_results['effectiveness_score']}/100"
        embed.add_field(name="🛡️ Blue Team (Defense)", value=blue_text, inline=True)
        
        # Key Findings
        findings = []
        if blue_team_results["detection_time"] > 300:
            findings.append("• Detection latency exceeds 5 minutes")
        if blue_team_results["effectiveness_score"] < 70:
            findings.append("• Defense mechanisms need improvement")
        if red_team_results["vectors_successful"] > 2:
            findings.append("• Multiple attack vectors succeeded")
        
        if findings:
            embed.add_field(name="🔍 Key Findings", value="\n".join(findings), inline=False)
        
        # Recommendations
        recommendations = self.generate_recommendations(red_team_results, blue_team_results)
        if recommendations:
            embed.add_field(name="💡 Recommendations", value="\n".join(recommendations[:3]), inline=False)
        
        embed.set_footer(text=f"Executed by {ctx.author}")
        await ctx.send(embed=embed)
    
    def simulate_red_team(self, scenario: Dict) -> Dict:
        """Simulate red team attack"""
        difficulty_multipliers = {"easy": 0.7, "medium": 1.0, "hard": 1.3}
        multiplier = difficulty_multipliers.get(scenario["difficulty"], 1.0)
        
        vectors_attempted = random.randint(3, 7)
        vectors_successful = max(1, int(random.randint(1, vectors_attempted) * multiplier))
        attack_score = min(100, int((vectors_successful / vectors_attempted) * 100 * multiplier))
        
        return {
            "vectors_attempted": vectors_attempted,
            "vectors_successful": vectors_successful,
            "attack_score": attack_score,
            "techniques": ["T1078", "T1566", "T1059"]  # MITRE ATT&CK techniques
        }
    
    def simulate_blue_team(self, scenario: Dict, red_results: Dict) -> Dict:
        """Simulate blue team defense"""
        # Detection time based on attack success
        detection_time = random.randint(30, 600)
        
        # Alerts based on defense capability
        alerts_triggered = random.randint(1, red_results["vectors_attempted"])
        
        # Effectiveness inversely proportional to attack score
        base_effectiveness = 100 - red_results["attack_score"]
        effectiveness_score = max(20, min(100, base_effectiveness + random.randint(-10, 20)))
        
        return {
            "detection_time": detection_time,
            "alerts_triggered": alerts_triggered,
            "effectiveness_score": effectiveness_score,
            "blocked_vectors": alerts_triggered,
            "response_actions": ["Alert generated", "Threat hunted", "IOCs extracted"]
        }
    
    def generate_recommendations(self, red_results: Dict, blue_results: Dict) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []
        
        if blue_results["detection_time"] > 300:
            recommendations.append("• Improve detection capabilities with enhanced monitoring")
        
        if blue_results["effectiveness_score"] < 70:
            recommendations.append("• Review and update security controls")
        
        if red_results["vectors_successful"] > 3:
            recommendations.append("• Conduct focused training on identified weaknesses")
        
        if blue_results["alerts_triggered"] < red_results["vectors_attempted"] / 2:
            recommendations.append("• Enhance alert coverage for attack techniques")
        
        return recommendations
    
    @commands.command(name="purple_scenarios")
    @commands.has_permissions(administrator=True)
    async def list_scenarios(self, ctx):
        """
        List available simulation scenarios
        
        Usage: !purple_scenarios
        """
        embed = discord.Embed(
            title="🎯 Purple Team Scenarios",
            description=f"Available attack scenarios: {len(self.scenarios)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for scenario in self.scenarios:
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
            emoji = difficulty_emoji.get(scenario["difficulty"], "⚪")
            
            embed.add_field(
                name=f"{emoji} #{scenario['id']} - {scenario['name']}",
                value=f"Category: {scenario['category']}\nDifficulty: {scenario['difficulty'].upper()}\n{scenario['description']}",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="purple_history")
    @commands.has_permissions(administrator=True)
    async def simulation_history(self, ctx, limit: int = 10):
        """
        View simulation history
        
        Usage: !purple_history [limit]
        
        Example: !purple_history 20
        """
        if not self.simulations:
            await ctx.send("📋 No simulations recorded yet")
            return
        
        recent_sims = sorted(self.simulations, key=lambda x: x["executed_at"], reverse=True)[:limit]
        
        embed = discord.Embed(
            title="📋 Purple Team Simulation History",
            description=f"Showing {len(recent_sims)} most recent simulations",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for sim in recent_sims[:5]:
            effectiveness = sim["defense_effectiveness"]
            outcome_emoji = "🟢" if effectiveness >= 80 else "🟡" if effectiveness >= 50 else "🔴"
            
            embed.add_field(
                name=f"{outcome_emoji} Simulation #{sim['id']} - {sim['scenario_name']}",
                value=f"Defense: {effectiveness}/100 | Detection: {sim['detection_latency_seconds']}s",
                inline=False
            )
        
        embed.add_field(name="📊 Total Simulations", value=len(self.simulations), inline=True)
        
        # Average effectiveness
        if self.simulations:
            avg_effectiveness = sum(s["defense_effectiveness"] for s in self.simulations) / len(self.simulations)
            embed.add_field(name="📈 Average Defense Score", value=f"{avg_effectiveness:.1f}/100", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="purple_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """
        Display purple team dashboard
        
        Usage: !purple_dashboard
        """
        total_sims = len(self.simulations)
        
        if total_sims == 0:
            await ctx.send("📊 No simulations recorded yet. Run `!purple_simulate <scenario_id>` to start.")
            return
        
        # Calculate statistics
        successful_defenses = len([s for s in self.simulations if s["defense_effectiveness"] >= 80])
        partial_defenses = len([s for s in self.simulations if 50 <= s["defense_effectiveness"] < 80])
        failed_defenses = len([s for s in self.simulations if s["defense_effectiveness"] < 50])
        
        avg_effectiveness = sum(s["defense_effectiveness"] for s in self.simulations) / total_sims
        avg_detection_time = sum(s["detection_latency_seconds"] for s in self.simulations) / total_sims
        
        embed = discord.Embed(
            title="🎯 Purple Team Dashboard",
            description="Adversarial simulation metrics",
            color=discord.Color.purple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="📊 Total Simulations", value=total_sims, inline=True)
        embed.add_field(name="📈 Avg Defense Score", value=f"{avg_effectiveness:.1f}/100", inline=True)
        embed.add_field(name="⏱️ Avg Detection Time", value=f"{avg_detection_time:.1f}s", inline=True)
        embed.add_field(name="🟢 Successful Defenses", value=successful_defenses, inline=True)
        embed.add_field(name="🟡 Partial Defenses", value=partial_defenses, inline=True)
        embed.add_field(name="🔴 Failed Defenses", value=failed_defenses, inline=True)
        
        # System readiness
        if avg_effectiveness >= 80:
            readiness = "🟢 EXCELLENT"
            color = discord.Color.green()
        elif avg_effectiveness >= 60:
            readiness = "🟡 GOOD"
            color = discord.Color.gold()
        else:
            readiness = "🔴 NEEDS IMPROVEMENT"
            color = discord.Color.red()
        
        embed.add_field(name="Defense Readiness", value=readiness, inline=False)
        embed.color = color
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(PurpleTeamSimulatorCog(bot))
