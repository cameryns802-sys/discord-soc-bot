"""
Security Control Framework - NIST/CIS control assessment and tracking
Assess and track security controls against industry frameworks (NIST, CIS, ISO)
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid

class SecurityControlFramework(commands.Cog):
    """Security control framework assessment and tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.controls_file = 'data/security_controls.json'
        self.assessments_file = 'data/control_assessments.json'
        self.load_data()
    
    def load_data(self):
        """Load control framework data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.controls_file):
            with open(self.controls_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.assessments_file):
            with open(self.assessments_file, 'w') as f:
                json.dump({}, f)
    
    def get_controls(self, guild_id):
        """Get security controls"""
        with open(self.controls_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_controls(self, guild_id, controls):
        """Save controls"""
        with open(self.controls_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = controls
        with open(self.controls_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_assessments(self, guild_id):
        """Get assessments"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_assessments(self, guild_id, assessments):
        """Save assessments"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = assessments
        with open(self.assessments_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # NIST Cybersecurity Framework controls
    NIST_CONTROLS = {
        'ID.AM-1': 'Inventory of Assets',
        'ID.AM-2': 'Software Inventory',
        'PR.AC-1': 'Access Control Policy',
        'PR.AC-2': 'Account Management',
        'PR.AC-3': 'MFA Implementation',
        'PR.AC-4': 'Access Rights',
        'PR.AC-5': 'Separation of Duties',
        'PR.DS-1': 'Data Security Policy',
        'PR.DS-2': 'Data in Transit Protection',
        'PR.DS-3': 'Data at Rest Protection',
        'PR.IP-1': 'Information Protection Process',
        'PR.MA-1': 'Maintenance Policy',
        'PR.MA-2': 'Remote Maintenance',
        'DE.AE-1': 'Anomalies Detected',
        'DE.AE-2': 'Events Analyzed',
        'RS.RP-1': 'Response Plans',
        'RS.CO-1': 'Personnel Coordination',
        'RC.RP-1': 'Recovery Plans',
        'RC.IM-1': 'Recovery Improvement'
    }
    
    # CIS Critical Security Controls
    CIS_CONTROLS = {
        'CSC-1': 'Inventory of Authorized Hardware',
        'CSC-2': 'Authorized Software Inventory',
        'CSC-3': 'Address Unauthorized Software',
        'CSC-4': 'Secure Configuration Management',
        'CSC-5': 'Access Control Lists (ACLs)',
        'CSC-6': 'Boundary Protection',
        'CSC-7': 'Email and Web Browser Protections',
        'CSC-8': 'Malware Defenses',
        'CSC-9': 'Limitation of Administrative Privileges',
        'CSC-10': 'Data Recovery Capability',
        'CSC-11': 'Secure Configuration Management',
        'CSC-12': 'Boundary Defense',
        'CSC-13': 'Implement an Incident Response Process',
        'CSC-14': 'Maintain an Incident Response Infrastructure',
        'CSC-15': 'Develop and Maintain Security Awareness Program',
        'CSC-16': 'Account Monitoring and Control',
        'CSC-17': 'Implement a Security Awareness Program',
        'CSC-18': 'Application Software Security',
        'CSC-19': 'Data Security and Privacy'
    }
    
    def calculate_framework_compliance(self, controls):
        """Calculate framework compliance percentage"""
        if not controls:
            return 0
        
        implemented = sum(1 for c in controls.values() if c.get('status') == 'implemented')
        total = len(controls)
        
        return int((implemented / total) * 100) if total > 0 else 0
    
    async def _addsecuritycontrol_logic(self, ctx, framework: str, control_id: str, status: str = 'planned'):
        """Add security control"""
        controls = self.get_controls(ctx.guild.id)
        
        framework_upper = framework.upper()
        
        if framework_upper == 'NIST' and control_id not in self.NIST_CONTROLS:
            await ctx.send(f"❌ Invalid NIST control ID. Use NIST CSF control IDs (e.g., ID.AM-1)")
            return
        
        if framework_upper == 'CIS' and control_id not in self.CIS_CONTROLS:
            await ctx.send(f"❌ Invalid CIS control ID. Use CIS CSC IDs (e.g., CSC-1)")
            return
        
        control_key = f"{framework_upper}-{control_id}"
        
        control = {
            'id': control_key,
            'framework': framework_upper,
            'control_id': control_id,
            'status': status.lower(),
            'added_at': datetime.utcnow().isoformat(),
            'implementation_date': None,
            'responsible_team': 'TBD',
            'last_assessed': None,
            'maturity_level': 0,
            'evidence': [],
            'findings': []
        }
        
        if framework_upper == 'NIST':
            control['description'] = self.NIST_CONTROLS.get(control_id, 'Unknown')
        elif framework_upper == 'CIS':
            control['description'] = self.CIS_CONTROLS.get(control_id, 'Unknown')
        
        controls[control_key] = control
        self.save_controls(ctx.guild.id, controls)
        
        embed = discord.Embed(
            title="✅ Security Control Added",
            description=f"**{framework_upper}** - {control_id}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Framework", value=framework_upper, inline=True)
        embed.add_field(name="Control ID", value=control_id, inline=True)
        embed.add_field(name="Status", value=status.title(), inline=True)
        embed.add_field(name="Description", value=control.get('description', 'N/A'), inline=False)
        embed.add_field(name="Maturity", value="0/5 (Not Started)", inline=True)
        embed.add_field(name="Responsible Team", value="TBD", inline=True)
        
        embed.set_footer(text="Use !controlassess to update control status")
        
        await ctx.send(embed=embed)
    
    async def _frameworkstatus_logic(self, ctx, framework: str = 'NIST'):
        """Show framework compliance status"""
        controls = self.get_controls(ctx.guild.id)
        
        framework_upper = framework.upper()
        
        if framework_upper == 'NIST':
            framework_controls = {k: v for k, v in controls.items() if v['framework'] == 'NIST'}
            total_controls = len(self.NIST_CONTROLS)
        elif framework_upper == 'CIS':
            framework_controls = {k: v for k, v in controls.items() if v['framework'] == 'CIS'}
            total_controls = len(self.CIS_CONTROLS)
        else:
            await ctx.send(f"❌ Unknown framework: {framework}")
            return
        
        compliance = self.calculate_framework_compliance(framework_controls)
        
        # Calculate by status
        planned = sum(1 for c in framework_controls.values() if c['status'] == 'planned')
        in_progress = sum(1 for c in framework_controls.values() if c['status'] == 'in_progress')
        implemented = sum(1 for c in framework_controls.values() if c['status'] == 'implemented')
        
        color = discord.Color.green() if compliance >= 80 else discord.Color.gold() if compliance >= 60 else discord.Color.orange() if compliance >= 40 else discord.Color.red()
        
        embed = discord.Embed(
            title=f"📊 {framework_upper} Cybersecurity Framework Status",
            description=f"Overall Compliance: **{compliance}%**",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Framework", value=framework_upper, inline=True)
        embed.add_field(name="Compliance Level", value=f"{compliance}%", inline=True)
        embed.add_field(name="Total Controls", value=str(len(framework_controls)), inline=True)
        
        embed.add_field(name="Control Status Distribution", value="━" * 25, inline=False)
        embed.add_field(name="🟢 Implemented", value=f"{implemented} controls", inline=True)
        embed.add_field(name="🟡 In Progress", value=f"{in_progress} controls", inline=True)
        embed.add_field(name="🔵 Planned", value=f"{planned} controls", inline=True)
        
        # Show top controls
        if framework_controls:
            embed.add_field(name="Sample Controls", value="━" * 25, inline=False)
            
            for control in list(framework_controls.values())[:5]:
                status_emoji = '🟢' if control['status'] == 'implemented' else '🟡' if control['status'] == 'in_progress' else '🔵'
                embed.add_field(
                    name=f"{status_emoji} {control['control_id']}",
                    value=control.get('description', 'Unknown')[:50],
                    inline=False
                )
        
        embed.set_footer(text="Use !controllist to see all controls")
        
        await ctx.send(embed=embed)
    
    async def _controllist_logic(self, ctx, framework: str = 'NIST'):
        """List all framework controls"""
        controls = self.get_controls(ctx.guild.id)
        
        framework_upper = framework.upper()
        
        if framework_upper == 'NIST':
            framework_controls = {k: v for k, v in controls.items() if v['framework'] == 'NIST'}
            all_controls = self.NIST_CONTROLS
        elif framework_upper == 'CIS':
            framework_controls = {k: v for k, v in controls.items() if v['framework'] == 'CIS'}
            all_controls = self.CIS_CONTROLS
        else:
            await ctx.send(f"❌ Unknown framework: {framework}")
            return
        
        embed = discord.Embed(
            title=f"📋 {framework_upper} Controls List",
            description=f"{len(framework_controls)}/{len(all_controls)} controls tracked",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Show status distribution
        status_dist = {}
        for control in framework_controls.values():
            status = control['status']
            status_dist[status] = status_dist.get(status, 0) + 1
        
        for status, count in status_dist.items():
            status_emoji = '🟢' if status == 'implemented' else '🟡' if status == 'in_progress' else '🔵'
            embed.add_field(name=f"{status_emoji} {status.title()}", value=f"{count} controls", inline=True)
        
        embed.add_field(name="Implementation Progress", value="━" * 25, inline=False)
        
        # Show recent controls
        for control in sorted(framework_controls.values(), key=lambda c: c['added_at'], reverse=True)[:8]:
            status_emoji = '🟢' if control['status'] == 'implemented' else '🟡' if control['status'] == 'in_progress' else '🔵'
            embed.add_field(
                name=f"{status_emoji} {control['control_id']}",
                value=control.get('description', 'Unknown'),
                inline=False
            )
        
        if len(framework_controls) > 8:
            embed.add_field(name="... and more", value=f"+{len(framework_controls) - 8} additional controls", inline=False)
        
        embed.set_footer(text=f"Use !addsecuritycontrol {framework} <control_id> to add controls")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='addsecuritycontrol')
    async def addsecuritycontrol_prefix(self, ctx, framework: str, control_id: str, status: str = 'planned'):
        """Add security control - Prefix command"""
        await self._addsecuritycontrol_logic(ctx, framework, control_id, status)
    
    @commands.command(name='frameworkstatus')
    async def frameworkstatus_prefix(self, ctx, framework: str = 'NIST'):
        """Show framework compliance - Prefix command"""
        await self._frameworkstatus_logic(ctx, framework)
    
    @commands.command(name='controllist')
    async def controllist_prefix(self, ctx, framework: str = 'NIST'):
        """List framework controls - Prefix command"""
        await self._controllist_logic(ctx, framework)

async def setup(bot):
    await bot.add_cog(SecurityControlFramework(bot))
