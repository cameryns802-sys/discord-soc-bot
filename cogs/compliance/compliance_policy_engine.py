"""
Compliance Policy Engine - Automated policy enforcement for Sentinel
Monitors and enforces security policies, regulatory compliance, and governance standards
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CompliancePolicyEngine(commands.Cog):
    """Automated compliance policy monitoring and enforcement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.policy_file = 'data/compliance_policies.json'
        self.violation_file = 'data/policy_violations.json'
        self.load_policies()
        self.load_violations()
    
    def load_policies(self):
        """Load compliance policies"""
        if not os.path.exists(self.policy_file):
            os.makedirs(os.path.dirname(self.policy_file), exist_ok=True)
            self.init_default_policies()
        else:
            with open(self.policy_file, 'r') as f:
                self.policies = json.load(f)
    
    def load_violations(self):
        """Load violation records"""
        if not os.path.exists(self.violation_file):
            os.makedirs(os.path.dirname(self.violation_file), exist_ok=True)
            with open(self.violation_file, 'w') as f:
                json.dump({}, f)
    
    def init_default_policies(self):
        """Initialize default compliance policies"""
        policies = {
            'gdpr_data_retention': {
                'name': 'GDPR Data Retention',
                'category': 'Data Privacy',
                'framework': 'GDPR',
                'description': 'Enforce 30-day data retention for user messages',
                'enabled': True,
                'severity': 'high',
                'auto_enforce': False,
                'parameters': {'max_retention_days': 30}
            },
            'admin_role_limit': {
                'name': 'Administrator Role Limit',
                'category': 'Access Control',
                'framework': 'Best Practice',
                'description': 'Limit administrator roles to max 3 users',
                'enabled': True,
                'severity': 'medium',
                'auto_enforce': False,
                'parameters': {'max_admins': 3}
            },
            'mfa_enforcement': {
                'name': 'Multi-Factor Authentication',
                'category': 'Authentication',
                'framework': 'SOC 2',
                'description': 'Require 2FA for all admin users',
                'enabled': True,
                'severity': 'high',
                'auto_enforce': False,
                'parameters': {'required_for_admins': True}
            },
            'audit_log_retention': {
                'name': 'Audit Log Retention',
                'category': 'Logging',
                'framework': 'SOC 2',
                'description': 'Retain audit logs for minimum 90 days',
                'enabled': True,
                'severity': 'high',
                'auto_enforce': True,
                'parameters': {'min_retention_days': 90}
            },
            'pii_detection': {
                'name': 'PII Exposure Prevention',
                'category': 'Data Privacy',
                'framework': 'GDPR/CCPA',
                'description': 'Detect and flag PII in public channels',
                'enabled': True,
                'severity': 'critical',
                'auto_enforce': False,
                'parameters': {'scan_public_channels': True}
            },
            'privileged_access_review': {
                'name': 'Privileged Access Review',
                'category': 'Access Control',
                'framework': 'ISO 27001',
                'description': 'Quarterly review of privileged access',
                'enabled': True,
                'severity': 'medium',
                'auto_enforce': False,
                'parameters': {'review_frequency_days': 90}
            }
        }
        
        with open(self.policy_file, 'w') as f:
            json.dump(policies, f, indent=2)
        self.policies = policies
    
    def get_guild_violations(self, guild_id):
        """Get violations for guild"""
        with open(self.violation_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_violation(self, guild_id, violation):
        """Save policy violation"""
        with open(self.violation_file, 'r') as f:
            data = json.load(f)
        
        if str(guild_id) not in data:
            data[str(guild_id)] = []
        
        data[str(guild_id)].append(violation)
        with open(self.violation_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def scan_guild_compliance(self, guild: discord.Guild) -> List[Dict[str, Any]]:
        """Scan guild for policy violations"""
        violations = []
        
        # Check admin role limit
        if 'admin_role_limit' in self.policies and self.policies['admin_role_limit']['enabled']:
            admin_count = sum(1 for m in guild.members if m.guild_permissions.administrator and not m.bot)
            max_admins = self.policies['admin_role_limit']['parameters']['max_admins']
            if admin_count > max_admins:
                violations.append({
                    'policy_id': 'admin_role_limit',
                    'policy_name': 'Administrator Role Limit',
                    'severity': 'medium',
                    'description': f'{admin_count} admins found (limit: {max_admins})',
                    'detected_at': datetime.utcnow().isoformat(),
                    'status': 'open'
                })
        
        # Check MFA enforcement
        if 'mfa_enforcement' in self.policies and self.policies['mfa_enforcement']['enabled']:
            if guild.mfa_level == discord.MFALevel.disabled:
                violations.append({
                    'policy_id': 'mfa_enforcement',
                    'policy_name': 'Multi-Factor Authentication',
                    'severity': 'high',
                    'description': 'Guild does not require 2FA for moderation',
                    'detected_at': datetime.utcnow().isoformat(),
                    'status': 'open'
                })
        
        return violations
    
    async def _policyscan_logic(self, ctx):
        """Run compliance policy scan"""
        await ctx.send("🔍 **Scanning guild for policy violations...**")
        
        violations = await self.scan_guild_compliance(ctx.guild)
        
        # Save violations
        for violation in violations:
            self.save_violation(ctx.guild.id, violation)
        
        if not violations:
            embed = discord.Embed(
                title="✅ Compliance Scan Complete",
                description="No policy violations detected",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Status", value="🟢 COMPLIANT", inline=True)
            embed.add_field(name="Policies Checked", value=str(len([p for p in self.policies.values() if p['enabled']])), inline=True)
            embed.set_footer(text="Sentinel Compliance Engine")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ Policy Violations Found",
            description=f"{len(violations)} violation(s) detected",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for violation in violations[:10]:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(violation['severity'], '❓')
            embed.add_field(
                name=f"{severity_emoji} {violation['policy_name']}",
                value=f"{violation['description']}\nSeverity: {violation['severity'].upper()}",
                inline=False
            )
        
        if len(violations) > 10:
            embed.add_field(name="... and more", value=f"+{len(violations) - 10} additional violations", inline=False)
        
        embed.set_footer(text="Use /policyviolations to view all violations")
        
        await ctx.send(embed=embed)
    
    async def _policylist_logic(self, ctx):
        """List all compliance policies"""
        enabled_count = sum(1 for p in self.policies.values() if p['enabled'])
        
        embed = discord.Embed(
            title="📋 Compliance Policies",
            description=f"{len(self.policies)} policies defined | {enabled_count} enabled",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        categories = {}
        for policy_id, policy in self.policies.items():
            cat = policy['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((policy_id, policy))
        
        for category, policies in categories.items():
            policy_str = ""
            for policy_id, policy in policies[:5]:
                status = "✅" if policy['enabled'] else "❌"
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(policy['severity'], '❓')
                policy_str += f"{status} {severity_emoji} **{policy['name']}** ({policy['framework']})\n"
            
            embed.add_field(name=f"📂 {category}", value=policy_str, inline=False)
        
        embed.set_footer(text="Use /policydetail <id> for details")
        
        await ctx.send(embed=embed)
    
    async def _policydetail_logic(self, ctx, policy_id: str):
        """Show policy details"""
        if policy_id not in self.policies:
            await ctx.send(f"❌ Policy `{policy_id}` not found.")
            return
        
        policy = self.policies[policy_id]
        
        embed = discord.Embed(
            title=f"📜 Policy: {policy['name']}",
            description=policy['description'],
            color=discord.Color.blue() if policy['enabled'] else discord.Color.greyple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Policy ID", value=f"`{policy_id}`", inline=True)
        embed.add_field(name="Status", value="✅ Enabled" if policy['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Severity", value=policy['severity'].upper(), inline=True)
        embed.add_field(name="Category", value=policy['category'], inline=True)
        embed.add_field(name="Framework", value=policy['framework'], inline=True)
        embed.add_field(name="Auto-Enforce", value="✅ Yes" if policy['auto_enforce'] else "❌ No", inline=True)
        
        # Parameters
        params_str = "\n".join([f"• {k}: `{v}`" for k, v in policy['parameters'].items()])
        embed.add_field(name="⚙️ Parameters", value=params_str or "None", inline=False)
        
        embed.set_footer(text="Sentinel Compliance Engine")
        
        await ctx.send(embed=embed)
    
    async def _policyviolations_logic(self, ctx):
        """Show policy violations"""
        violations = self.get_guild_violations(ctx.guild.id)
        
        if not violations:
            await ctx.send("✅ No policy violations recorded.")
            return
        
        open_violations = [v for v in violations if v['status'] == 'open']
        
        embed = discord.Embed(
            title="⚠️ Policy Violations",
            description=f"{len(open_violations)} open violation(s) | {len(violations)} total",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for violation in open_violations[:10]:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(violation['severity'], '❓')
            embed.add_field(
                name=f"{severity_emoji} {violation['policy_name']}",
                value=f"{violation['description']}\nDetected: <t:{int(datetime.fromisoformat(violation['detected_at']).timestamp())}:R>",
                inline=False
            )
        
        if len(open_violations) > 10:
            embed.add_field(name="... and more", value=f"+{len(open_violations) - 10} additional violations", inline=False)
        
        embed.set_footer(text="Sentinel Compliance Engine | Open violations")
        
        await ctx.send(embed=embed)
    
    async def _compliancereport_logic(self, ctx):
        """Generate compliance report"""
        violations = self.get_guild_violations(ctx.guild.id)
        enabled_policies = [p for p in self.policies.values() if p['enabled']]
        
        open_violations = [v for v in violations if v['status'] == 'open']
        critical = sum(1 for v in open_violations if v['severity'] == 'critical')
        high = sum(1 for v in open_violations if v['severity'] == 'high')
        
        # Calculate compliance score
        compliance_score = 100
        compliance_score -= (critical * 15)
        compliance_score -= (high * 10)
        compliance_score -= (len(open_violations) * 5)
        compliance_score = max(0, min(100, compliance_score))
        
        color = discord.Color.green() if compliance_score >= 80 else discord.Color.orange() if compliance_score >= 60 else discord.Color.red()
        
        embed = discord.Embed(
            title="📊 Compliance Report",
            description=f"Compliance Score: **{compliance_score}/100**",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📋 Active Policies", value=f"`{len(enabled_policies)}`", inline=True)
        embed.add_field(name="⚠️ Open Violations", value=f"`{len(open_violations)}`", inline=True)
        embed.add_field(name="🔴 Critical", value=f"`{critical}`", inline=True)
        
        # Framework breakdown
        frameworks = {}
        for policy in enabled_policies:
            fw = policy['framework']
            if fw not in frameworks:
                frameworks[fw] = {'total': 0, 'violations': 0}
            frameworks[fw]['total'] += 1
        
        for violation in open_violations:
            policy = self.policies.get(violation['policy_id'])
            if policy:
                fw = policy['framework']
                if fw in frameworks:
                    frameworks[fw]['violations'] += 1
        
        framework_str = ""
        for fw, data in frameworks.items():
            compliance_pct = ((data['total'] - data['violations']) / data['total'] * 100) if data['total'] > 0 else 100
            framework_str += f"• {fw}: {compliance_pct:.0f}% compliant ({data['violations']}/{data['total']} violations)\n"
        
        embed.add_field(name="🏛️ Framework Compliance", value=framework_str or "No frameworks configured", inline=False)
        
        # Recommendations
        if compliance_score < 60:
            embed.add_field(name="💡 Recommendations", value="• Address critical violations immediately\n• Review and remediate high-severity issues\n• Schedule compliance review meeting", inline=False)
        elif compliance_score < 80:
            embed.add_field(name="💡 Recommendations", value="• Continue monitoring open violations\n• Implement remediation plans\n• Update policies as needed", inline=False)
        
        embed.set_footer(text="Sentinel Compliance Engine | Generated report")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='policyscan')
    async def policyscan_prefix(self, ctx):
        """Run compliance policy scan - Prefix command"""
        await self._policyscan_logic(ctx)
    
    @commands.command(name='policylist')
    async def policylist_prefix(self, ctx):
        """List all policies - Prefix command"""
        await self._policylist_logic(ctx)
    
    @commands.command(name='policydetail')
    async def policydetail_prefix(self, ctx, policy_id: str):
        """Show policy details - Prefix command"""
        await self._policydetail_logic(ctx, policy_id)
    
    @commands.command(name='policyviolations')
    async def policyviolations_prefix(self, ctx):
        """Show policy violations - Prefix command"""
        await self._policyviolations_logic(ctx)
    
    @commands.command(name='compliancereport')
    async def compliancereport_prefix(self, ctx):
        """Generate compliance report - Prefix command"""
        await self._compliancereport_logic(ctx)

async def setup(bot):
    await bot.add_cog(CompliancePolicyEngine(bot))
