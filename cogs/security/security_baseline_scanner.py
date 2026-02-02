"""
Security Baseline Scanner - Automated security configuration assessment for Sentinel
Scans guild settings against industry security baselines and best practices
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

class SecurityBaselineScanner(commands.Cog):
    """Security configuration baseline scanning and assessment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scan_results_file = 'data/baseline_scans.json'
        self.load_scan_results()
    
    def load_scan_results(self):
        """Load scan results"""
        if not os.path.exists(self.scan_results_file):
            os.makedirs(os.path.dirname(self.scan_results_file), exist_ok=True)
            with open(self.scan_results_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_scans(self, guild_id):
        """Get scan history for guild"""
        with open(self.scan_results_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_scan(self, guild_id, scan_result):
        """Save scan result"""
        with open(self.scan_results_file, 'r') as f:
            data = json.load(f)
        
        if str(guild_id) not in data:
            data[str(guild_id)] = []
        
        data[str(guild_id)].append(scan_result)
        
        # Keep only last 20 scans
        data[str(guild_id)] = data[str(guild_id)][-20:]
        
        with open(self.scan_results_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def scan_guild_baseline(self, guild: discord.Guild) -> Dict:
        """Perform comprehensive security baseline scan"""
        checks = []
        score = 100
        
        # 1. Verification Level
        verification_level = guild.verification_level
        if verification_level == discord.VerificationLevel.none:
            checks.append({
                'category': 'Access Control',
                'check': 'Verification Level',
                'status': 'fail',
                'severity': 'high',
                'finding': 'No verification required for new members',
                'recommendation': 'Enable at least "Low" verification level',
                'impact': -10
            })
            score -= 10
        elif verification_level in [discord.VerificationLevel.low, discord.VerificationLevel.medium]:
            checks.append({
                'category': 'Access Control',
                'check': 'Verification Level',
                'status': 'warning',
                'severity': 'medium',
                'finding': f'Verification level: {verification_level.name}',
                'recommendation': 'Consider "High" or "Highest" for better security',
                'impact': -5
            })
            score -= 5
        else:
            checks.append({
                'category': 'Access Control',
                'check': 'Verification Level',
                'status': 'pass',
                'severity': 'info',
                'finding': f'Strong verification level: {verification_level.name}',
                'recommendation': 'Maintain current setting',
                'impact': 0
            })
        
        # 2. MFA Requirement
        if guild.mfa_level == discord.MFALevel.disabled:
            checks.append({
                'category': 'Authentication',
                'check': 'Multi-Factor Authentication',
                'status': 'fail',
                'severity': 'critical',
                'finding': 'MFA not required for moderation actions',
                'recommendation': 'Enable MFA requirement for all moderators',
                'impact': -15
            })
            score -= 15
        else:
            checks.append({
                'category': 'Authentication',
                'check': 'Multi-Factor Authentication',
                'status': 'pass',
                'severity': 'info',
                'finding': 'MFA required for moderation',
                'recommendation': 'Maintain MFA requirement',
                'impact': 0
            })
        
        # 3. Default Message Notifications
        if guild.default_notifications == discord.NotificationLevel.all_messages:
            checks.append({
                'category': 'Privacy',
                'check': 'Default Notifications',
                'status': 'warning',
                'severity': 'low',
                'finding': 'Default to all message notifications',
                'recommendation': 'Consider "Mentions Only" to reduce noise',
                'impact': -2
            })
            score -= 2
        else:
            checks.append({
                'category': 'Privacy',
                'check': 'Default Notifications',
                'status': 'pass',
                'severity': 'info',
                'finding': 'Notifications set to mentions only',
                'recommendation': 'Good privacy setting',
                'impact': 0
            })
        
        # 4. Explicit Content Filter
        if guild.explicit_content_filter == discord.ContentFilter.disabled:
            checks.append({
                'category': 'Content Safety',
                'check': 'Explicit Content Filter',
                'status': 'fail',
                'severity': 'high',
                'finding': 'No explicit content filtering',
                'recommendation': 'Enable content filtering for all members',
                'impact': -10
            })
            score -= 10
        elif guild.explicit_content_filter == discord.ContentFilter.no_role:
            checks.append({
                'category': 'Content Safety',
                'check': 'Explicit Content Filter',
                'status': 'warning',
                'severity': 'medium',
                'finding': 'Partial content filtering (members without roles)',
                'recommendation': 'Enable filtering for all members',
                'impact': -5
            })
            score -= 5
        else:
            checks.append({
                'category': 'Content Safety',
                'check': 'Explicit Content Filter',
                'status': 'pass',
                'severity': 'info',
                'finding': 'Full content filtering enabled',
                'recommendation': 'Maintain current setting',
                'impact': 0
            })
        
        # 5. System Channel Configuration
        if guild.system_channel is None:
            checks.append({
                'category': 'Monitoring',
                'check': 'System Channel',
                'status': 'warning',
                'severity': 'low',
                'finding': 'No system channel configured',
                'recommendation': 'Configure system channel for join/boost messages',
                'impact': -3
            })
            score -= 3
        else:
            checks.append({
                'category': 'Monitoring',
                'check': 'System Channel',
                'status': 'pass',
                'severity': 'info',
                'finding': 'System channel configured',
                'recommendation': 'Monitor system messages',
                'impact': 0
            })
        
        # 6. Administrator Role Count
        admin_roles = [role for role in guild.roles if role.permissions.administrator]
        admin_count = sum(1 for m in guild.members if m.guild_permissions.administrator and not m.bot)
        
        if admin_count > 5:
            checks.append({
                'category': 'Access Control',
                'check': 'Administrator Count',
                'status': 'fail',
                'severity': 'high',
                'finding': f'{admin_count} administrators (excessive)',
                'recommendation': 'Limit administrators to 3-5 trusted users',
                'impact': -10
            })
            score -= 10
        elif admin_count > 3:
            checks.append({
                'category': 'Access Control',
                'check': 'Administrator Count',
                'status': 'warning',
                'severity': 'medium',
                'finding': f'{admin_count} administrators',
                'recommendation': 'Review admin access necessity',
                'impact': -5
            })
            score -= 5
        else:
            checks.append({
                'category': 'Access Control',
                'check': 'Administrator Count',
                'status': 'pass',
                'severity': 'info',
                'finding': f'{admin_count} administrators (good)',
                'recommendation': 'Maintain minimal admin count',
                'impact': 0
            })
        
        # 7. @everyone Permissions
        everyone_role = guild.default_role
        dangerous_perms = [
            'administrator', 'manage_guild', 'manage_roles', 
            'manage_channels', 'manage_webhooks', 'mention_everyone'
        ]
        
        everyone_issues = []
        for perm_name in dangerous_perms:
            if getattr(everyone_role.permissions, perm_name, False):
                everyone_issues.append(perm_name)
        
        if everyone_issues:
            checks.append({
                'category': 'Access Control',
                'check': '@everyone Permissions',
                'status': 'fail',
                'severity': 'critical',
                'finding': f'@everyone has dangerous permissions: {", ".join(everyone_issues)}',
                'recommendation': 'Remove all elevated permissions from @everyone',
                'impact': -15
            })
            score -= 15
        else:
            checks.append({
                'category': 'Access Control',
                'check': '@everyone Permissions',
                'status': 'pass',
                'severity': 'info',
                'finding': '@everyone has no dangerous permissions',
                'recommendation': 'Maintain secure default role',
                'impact': 0
            })
        
        # 8. Public/Private Guild
        # Note: Cannot directly check if guild is public/discoverable via API
        # This is a placeholder check
        checks.append({
            'category': 'Exposure',
            'check': 'Guild Visibility',
            'status': 'info',
            'severity': 'info',
            'finding': 'Guild visibility setting cannot be verified via API',
            'recommendation': 'Manually verify guild is not publicly listed if private',
            'impact': 0
        })
        
        return {
            'scan_id': datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            'timestamp': datetime.utcnow().isoformat(),
            'score': max(0, min(100, score)),
            'total_checks': len(checks),
            'passed': sum(1 for c in checks if c['status'] == 'pass'),
            'warnings': sum(1 for c in checks if c['status'] == 'warning'),
            'failed': sum(1 for c in checks if c['status'] == 'fail'),
            'checks': checks
        }
    
    async def _baseline_logic(self, ctx):
        """Run security baseline scan"""
        await ctx.send("🔍 **Running security baseline scan...**")
        
        scan_result = await self.scan_guild_baseline(ctx.guild)
        self.save_scan(ctx.guild.id, scan_result)
        
        # Determine color based on score
        score = scan_result['score']
        if score >= 80:
            color = discord.Color.green()
            status = "🟢 EXCELLENT"
        elif score >= 60:
            color = discord.Color.yellow()
            status = "🟡 GOOD"
        elif score >= 40:
            color = discord.Color.orange()
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            color = discord.Color.red()
            status = "🔴 CRITICAL"
        
        embed = discord.Embed(
            title="🔒 Security Baseline Scan Results",
            description=f"Security Score: **{score}/100** - {status}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="✅ Passed", value=f"`{scan_result['passed']}`", inline=True)
        embed.add_field(name="⚠️ Warnings", value=f"`{scan_result['warnings']}`", inline=True)
        embed.add_field(name="❌ Failed", value=f"`{scan_result['failed']}`", inline=True)
        
        # Show critical/high severity findings
        critical_findings = [c for c in scan_result['checks'] if c['severity'] in ['critical', 'high'] and c['status'] != 'pass']
        
        if critical_findings:
            findings_str = ""
            for finding in critical_findings[:5]:
                severity_emoji = {'critical': '🔴', 'high': '🟠'}.get(finding['severity'], '❓')
                findings_str += f"{severity_emoji} **{finding['check']}**: {finding['finding']}\n"
            
            embed.add_field(name="⚠️ Priority Findings", value=findings_str, inline=False)
        
        embed.add_field(name="📊 Next Steps", value="• Review failed checks immediately\n• Address high-severity findings\n• Use `/baselinereport` for full details", inline=False)
        embed.set_footer(text=f"Scan ID: {scan_result['scan_id']} | Sentinel Baseline Scanner")
        
        await ctx.send(embed=embed)
    
    async def _baselinereport_logic(self, ctx):
        """Generate detailed baseline report"""
        scans = self.get_guild_scans(ctx.guild.id)
        
        if not scans:
            await ctx.send("❌ No baseline scans found. Run `/baseline` first.")
            return
        
        latest_scan = scans[-1]
        
        embed = discord.Embed(
            title="📋 Security Baseline Report",
            description=f"Scan ID: `{latest_scan['scan_id']}`",
            color=discord.Color.blurple(),
            timestamp=datetime.fromisoformat(latest_scan['timestamp'])
        )
        
        embed.add_field(name="Score", value=f"`{latest_scan['score']}/100`", inline=True)
        embed.add_field(name="Total Checks", value=f"`{latest_scan['total_checks']}`", inline=True)
        embed.add_field(name="Status", value=f"✅ {latest_scan['passed']} | ⚠️ {latest_scan['warnings']} | ❌ {latest_scan['failed']}", inline=True)
        
        # Group by category
        by_category = {}
        for check in latest_scan['checks']:
            cat = check['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(check)
        
        for category, checks in by_category.items():
            check_str = ""
            for check in checks:
                status_emoji = {'pass': '✅', 'warning': '⚠️', 'fail': '❌', 'info': 'ℹ️'}.get(check['status'], '❓')
                check_str += f"{status_emoji} {check['check']}: {check['finding']}\n"
            
            embed.add_field(name=f"📂 {category}", value=check_str, inline=False)
        
        embed.set_footer(text="Sentinel Security Baseline | Industry best practices")
        
        await ctx.send(embed=embed)
    
    async def _baselinehistory_logic(self, ctx):
        """Show scan history"""
        scans = self.get_guild_scans(ctx.guild.id)
        
        if not scans:
            await ctx.send("📋 No baseline scan history yet.")
            return
        
        embed = discord.Embed(
            title="📊 Baseline Scan History",
            description=f"{len(scans)} scan(s) recorded",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for scan in scans[-10:]:
            score = scan['score']
            status_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🟠" if score >= 40 else "🔴"
            
            embed.add_field(
                name=f"{status_emoji} Scan {scan['scan_id']}",
                value=f"Score: {score}/100 | Failed: {scan['failed']} | <t:{int(datetime.fromisoformat(scan['timestamp']).timestamp())}:R>",
                inline=False
            )
        
        embed.set_footer(text="Sentinel Baseline Scanner | Historical trends")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='baseline')
    async def baseline_prefix(self, ctx):
        """Run security baseline scan - Prefix command"""
        await self._baseline_logic(ctx)
    
    @commands.command(name='baselinereport')
    async def baselinereport_prefix(self, ctx):
        """Get detailed baseline report - Prefix command"""
        await self._baselinereport_logic(ctx)
    
    @commands.command(name='baselinehistory')
    async def baselinehistory_prefix(self, ctx):
        """Show scan history - Prefix command"""
        await self._baselinehistory_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityBaselineScanner(bot))
