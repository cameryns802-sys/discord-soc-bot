import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from typing import Dict, List

class MitreAttackMapper(commands.Cog):
    """
    MITRE ATT&CK Framework Mapper
    
    Maps security alerts and detections to MITRE ATT&CK tactics and techniques
    for standardized threat classification.
    
    Features:
    - Map alerts to ATT&CK techniques
    - Track technique coverage
    - Identify detection gaps
    - Executive-ready ATT&CK heatmaps
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/mitre_attack'
        os.makedirs(self.data_dir, exist_ok=True)
        self.mappings = self.load_mappings()
        
        # MITRE ATT&CK Tactics (14 tactics)
        self.tactics = [
            'TA0001',  # Initial Access
            'TA0002',  # Execution
            'TA0003',  # Persistence
            'TA0004',  # Privilege Escalation
            'TA0005',  # Defense Evasion
            'TA0006',  # Credential Access
            'TA0007',  # Discovery
            'TA0008',  # Lateral Movement
            'TA0009',  # Collection
            'TA0010',  # Exfiltration
            'TA0011',  # Command and Control
            'TA0040',  # Impact
            'TA0042',  # Resource Development
            'TA0043'   # Reconnaissance
        ]
        
        # Sample ATT&CK Techniques (subset for demonstration)
        self.techniques = {
            'T1078': {'name': 'Valid Accounts', 'tactic': 'TA0001'},
            'T1566': {'name': 'Phishing', 'tactic': 'TA0001'},
            'T1059': {'name': 'Command and Scripting Interpreter', 'tactic': 'TA0002'},
            'T1053': {'name': 'Scheduled Task/Job', 'tactic': 'TA0003'},
            'T1548': {'name': 'Abuse Elevation Control Mechanism', 'tactic': 'TA0004'},
            'T1027': {'name': 'Obfuscated Files or Information', 'tactic': 'TA0005'},
            'T1110': {'name': 'Brute Force', 'tactic': 'TA0006'},
            'T1087': {'name': 'Account Discovery', 'tactic': 'TA0007'},
            'T1021': {'name': 'Remote Services', 'tactic': 'TA0008'},
            'T1005': {'name': 'Data from Local System', 'tactic': 'TA0009'},
            'T1041': {'name': 'Exfiltration Over C2 Channel', 'tactic': 'TA0010'},
            'T1071': {'name': 'Application Layer Protocol', 'tactic': 'TA0011'},
            'T1486': {'name': 'Data Encrypted for Impact', 'tactic': 'TA0040'},
            'T1583': {'name': 'Acquire Infrastructure', 'tactic': 'TA0042'},
            'T1595': {'name': 'Active Scanning', 'tactic': 'TA0043'}
        }
        
        self.tactic_names = {
            'TA0001': 'Initial Access',
            'TA0002': 'Execution',
            'TA0003': 'Persistence',
            'TA0004': 'Privilege Escalation',
            'TA0005': 'Defense Evasion',
            'TA0006': 'Credential Access',
            'TA0007': 'Discovery',
            'TA0008': 'Lateral Movement',
            'TA0009': 'Collection',
            'TA0010': 'Exfiltration',
            'TA0011': 'Command and Control',
            'TA0040': 'Impact',
            'TA0042': 'Resource Development',
            'TA0043': 'Reconnaissance'
        }
    
    def load_mappings(self) -> Dict:
        """Load ATT&CK mappings from JSON storage"""
        try:
            with open(f'{self.data_dir}/mappings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_mappings(self):
        """Save ATT&CK mappings to JSON storage"""
        with open(f'{self.data_dir}/mappings.json', 'w') as f:
            json.dump(self.mappings, f, indent=2)
    
    def map_alert_to_technique(self, guild_id: str, alert_id: str, technique_id: str, confidence: str = 'high'):
        """
        Map a security alert to a MITRE ATT&CK technique
        
        Args:
            guild_id: Guild ID
            alert_id: Alert identifier
            technique_id: MITRE ATT&CK technique ID (e.g., T1078)
            confidence: Confidence level (high, medium, low)
        """
        if str(guild_id) not in self.mappings:
            self.mappings[str(guild_id)] = []
        
        mapping = {
            'alert_id': alert_id,
            'technique_id': technique_id,
            'technique_name': self.techniques.get(technique_id, {}).get('name', 'Unknown'),
            'tactic_id': self.techniques.get(technique_id, {}).get('tactic', 'Unknown'),
            'tactic_name': self.tactic_names.get(self.techniques.get(technique_id, {}).get('tactic', ''), 'Unknown'),
            'confidence': confidence,
            'mapped_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.mappings[str(guild_id)].append(mapping)
        self.save_mappings()
        
        return mapping
    
    def get_coverage_by_tactic(self, guild_id: str) -> Dict:
        """
        Calculate ATT&CK coverage grouped by tactic
        
        Returns:
            Dict of tactic_id -> count of mapped techniques
        """
        if str(guild_id) not in self.mappings:
            return {}
        
        coverage = {}
        
        for mapping in self.mappings[str(guild_id)]:
            tactic_id = mapping.get('tactic_id', 'Unknown')
            coverage[tactic_id] = coverage.get(tactic_id, 0) + 1
        
        return coverage
    
    def get_technique_frequency(self, guild_id: str) -> Dict:
        """Get frequency of each technique detection"""
        if str(guild_id) not in self.mappings:
            return {}
        
        frequency = {}
        
        for mapping in self.mappings[str(guild_id)]:
            tech_id = mapping.get('technique_id', 'Unknown')
            frequency[tech_id] = frequency.get(tech_id, 0) + 1
        
        return frequency
    
    @commands.command(name='map_attack')
    @commands.has_permissions(administrator=True)
    async def map_attack_cmd(self, ctx, alert_id: str, technique_id: str, confidence: str = 'high'):
        """
        Map a security alert to MITRE ATT&CK technique
        
        Usage: !map_attack ALERT-001 T1078 high
        """
        if technique_id not in self.techniques:
            await ctx.send(f"❌ Unknown technique ID: `{technique_id}`")
            return
        
        mapping = self.map_alert_to_technique(ctx.guild.id, alert_id, technique_id, confidence)
        
        embed = discord.Embed(
            title="✅ ATT&CK Mapping Created",
            description=f"Alert `{alert_id}` mapped to MITRE ATT&CK technique",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🎯 Technique", value=f"**{technique_id}**: {mapping['technique_name']}", inline=False)
        embed.add_field(name="📊 Tactic", value=f"**{mapping['tactic_id']}**: {mapping['tactic_name']}", inline=False)
        embed.add_field(name="⚡ Confidence", value=confidence.upper(), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='attack_coverage')
    @commands.has_permissions(administrator=True)
    async def attack_coverage_cmd(self, ctx):
        """Show MITRE ATT&CK coverage by tactic"""
        coverage = self.get_coverage_by_tactic(ctx.guild.id)
        
        if not coverage:
            await ctx.send("📊 No ATT&CK mappings found for this guild.")
            return
        
        embed = discord.Embed(
            title="📊 MITRE ATT&CK Coverage",
            description="Detection coverage across ATT&CK tactics",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        total = sum(coverage.values())
        
        for tactic_id, count in sorted(coverage.items(), key=lambda x: x[1], reverse=True):
            tactic_name = self.tactic_names.get(tactic_id, 'Unknown')
            percentage = (count / total * 100) if total > 0 else 0
            
            embed.add_field(
                name=f"**{tactic_id}**: {tactic_name}",
                value=f"**{count}** detections ({percentage:.1f}%)",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {total} ATT&CK technique mappings")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='attack_techniques')
    @commands.has_permissions(administrator=True)
    async def attack_techniques_cmd(self, ctx):
        """List all available ATT&CK techniques"""
        embed = discord.Embed(
            title="🎯 MITRE ATT&CK Techniques",
            description="Available techniques for mapping",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Group by tactic
        by_tactic = {}
        for tech_id, tech_data in self.techniques.items():
            tactic = tech_data['tactic']
            if tactic not in by_tactic:
                by_tactic[tactic] = []
            by_tactic[tactic].append(f"**{tech_id}**: {tech_data['name']}")
        
        for tactic_id, techniques in sorted(by_tactic.items())[:5]:  # Show first 5 tactics
            tactic_name = self.tactic_names.get(tactic_id, 'Unknown')
            embed.add_field(
                name=f"📂 {tactic_name}",
                value='\n'.join(techniques[:3]),  # Show first 3 techniques
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(self.techniques)} techniques available")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='attack_heatmap')
    @commands.has_permissions(administrator=True)
    async def attack_heatmap_cmd(self, ctx):
        """Generate ATT&CK heatmap showing detection frequency"""
        frequency = self.get_technique_frequency(ctx.guild.id)
        
        if not frequency:
            await ctx.send("📊 No ATT&CK mappings found for this guild.")
            return
        
        embed = discord.Embed(
            title="🔥 ATT&CK Heatmap",
            description="Most frequently detected techniques",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Top 10 techniques
        sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for tech_id, count in sorted_freq:
            tech_name = self.techniques.get(tech_id, {}).get('name', 'Unknown')
            tactic_id = self.techniques.get(tech_id, {}).get('tactic', 'Unknown')
            tactic_name = self.tactic_names.get(tactic_id, 'Unknown')
            
            # Heat indicator
            heat = '🔴' if count >= 10 else '🟠' if count >= 5 else '🟡'
            
            embed.add_field(
                name=f"{heat} {tech_id}: {tech_name}",
                value=f"**{count}** detections | Tactic: {tactic_name}",
                inline=False
            )
        
        embed.set_footer(text="Techniques with most detections")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MitreAttackMapper(bot))
