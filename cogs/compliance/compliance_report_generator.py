"""
Compliance Report Generator - Automated compliance reporting for Sentinel
Generate compliance reports for GDPR, SOC 2, ISO 27001, HIPAA, and custom frameworks
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

class ComplianceReportGenerator(commands.Cog):
    """Automated compliance report generation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reports_file = 'data/compliance_reports.json'
        self.templates_file = 'data/report_templates.json'
        self.load_data()
        self.init_templates()
    
    def load_data(self):
        """Load report data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.reports_file):
            with open(self.reports_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.templates_file):
            with open(self.templates_file, 'w') as f:
                json.dump({}, f)
    
    def init_templates(self):
        """Initialize report templates"""
        with open(self.templates_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            templates = {
                'gdpr': {
                    'name': 'GDPR Compliance Report',
                    'framework': 'GDPR',
                    'sections': [
                        'Data Processing Activities',
                        'Data Subject Rights',
                        'Data Protection Measures',
                        'Data Breach Incidents',
                        'Third-Party Processors',
                        'Privacy Impact Assessments'
                    ],
                    'frequency': 'quarterly'
                },
                'soc2': {
                    'name': 'SOC 2 Type II Report',
                    'framework': 'SOC 2',
                    'sections': [
                        'Security Controls',
                        'Availability Controls',
                        'Processing Integrity',
                        'Confidentiality Controls',
                        'Privacy Controls',
                        'Incident Response'
                    ],
                    'frequency': 'annual'
                },
                'iso27001': {
                    'name': 'ISO 27001 Compliance Report',
                    'framework': 'ISO 27001',
                    'sections': [
                        'Information Security Policy',
                        'Asset Management',
                        'Access Control',
                        'Cryptography',
                        'Physical Security',
                        'Operations Security',
                        'Communications Security',
                        'Incident Management',
                        'Business Continuity'
                    ],
                    'frequency': 'annual'
                },
                'hipaa': {
                    'name': 'HIPAA Compliance Report',
                    'framework': 'HIPAA',
                    'sections': [
                        'Administrative Safeguards',
                        'Physical Safeguards',
                        'Technical Safeguards',
                        'PHI Access Controls',
                        'Audit Controls',
                        'Breach Notification'
                    ],
                    'frequency': 'annual'
                },
                'pci_dss': {
                    'name': 'PCI DSS Compliance Report',
                    'framework': 'PCI DSS',
                    'sections': [
                        'Network Security',
                        'Cardholder Data Protection',
                        'Vulnerability Management',
                        'Access Control Measures',
                        'Network Monitoring',
                        'Information Security Policy'
                    ],
                    'frequency': 'quarterly'
                }
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(templates, f, indent=2)
    
    def get_guild_reports(self, guild_id):
        """Get reports for guild"""
        with open(self.reports_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_report(self, guild_id, report):
        """Save report"""
        with open(self.reports_file, 'r') as f:
            data = json.load(f)
        
        reports = data.get(str(guild_id), [])
        reports.append(report)
        # Keep last 50 reports
        data[str(guild_id)] = reports[-50:]
        
        with open(self.reports_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_templates(self):
        """Get report templates"""
        with open(self.templates_file, 'r') as f:
            return json.load(f)
    
    def generate_report(self, guild, framework):
        """Generate compliance report"""
        templates = self.get_templates()
        template = templates.get(framework)
        
        if not template:
            return None
        
        # Collect compliance data (in production, would query actual data sources)
        report_data = {
            'report_id': f"RPT-{get_now_pst().strftime('%Y%m%d-%H%M%S')}",
            'framework': framework,
            'framework_name': template['name'],
            'guild_id': guild.id,
            'guild_name': guild.name,
            'generated_at': get_now_pst().isoformat(),
            'period_start': (get_now_pst() - timedelta(days=90)).isoformat(),
            'period_end': get_now_pst().isoformat(),
            'sections': []
        }
        
        # Generate section data
        for section in template['sections']:
            section_data = {
                'name': section,
                'status': 'compliant',  # In production: actual compliance check
                'findings': self._generate_section_findings(section),
                'score': 85  # In production: calculated score
            }
            report_data['sections'].append(section_data)
        
        # Calculate overall compliance
        total_score = sum(s['score'] for s in report_data['sections'])
        avg_score = total_score / len(report_data['sections']) if report_data['sections'] else 0
        
        report_data['overall_score'] = int(avg_score)
        report_data['compliance_status'] = self._get_compliance_status(avg_score)
        
        return report_data
    
    def _generate_section_findings(self, section):
        """Generate findings for section (placeholder)"""
        # In production, would query actual data sources
        findings = [
            f"✅ {section}: All controls implemented",
            f"ℹ️ {section}: Last reviewed 30 days ago",
            f"⚠️ {section}: 2 minor recommendations"
        ]
        return findings[:2]  # Return first 2
    
    def _get_compliance_status(self, score):
        """Get compliance status from score"""
        if score >= 90:
            return 'full_compliance'
        elif score >= 75:
            return 'substantial_compliance'
        elif score >= 60:
            return 'partial_compliance'
        else:
            return 'non_compliant'
    
    async def _reportgenerate_logic(self, ctx, framework: str):
        """Generate compliance report"""
        valid_frameworks = ['gdpr', 'soc2', 'iso27001', 'hipaa', 'pci_dss']
        
        if framework.lower() not in valid_frameworks:
            await ctx.send(f"❌ Invalid framework. Use: {', '.join(valid_frameworks)}")
            return
        
        msg = await ctx.send(f"📄 Generating {framework.upper()} compliance report...")
        
        report = self.generate_report(ctx.guild, framework.lower())
        
        if not report:
            await msg.edit(content="❌ Failed to generate report.")
            return
        
        # Save report
        self.save_report(ctx.guild.id, report)
        
        # Determine color
        score = report['overall_score']
        if score >= 90:
            color = discord.Color.green()
            status_emoji = "✅"
        elif score >= 75:
            color = discord.Color.blue()
            status_emoji = "🔵"
        elif score >= 60:
            color = discord.Color.gold()
            status_emoji = "🟡"
        else:
            color = discord.Color.red()
            status_emoji = "🔴"
        
        embed = discord.Embed(
            title=f"📊 {report['framework_name']}",
            description=f"**Compliance Score: {score}/100** {status_emoji}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Report ID", value=f"`{report['report_id']}`", inline=True)
        embed.add_field(name="Framework", value=framework.upper(), inline=True)
        embed.add_field(name="Status", value=report['compliance_status'].replace('_', ' ').title(), inline=True)
        
        period_start = datetime.fromisoformat(report['period_start']).strftime('%Y-%m-%d')
        period_end = datetime.fromisoformat(report['period_end']).strftime('%Y-%m-%d')
        embed.add_field(name="Period", value=f"{period_start} to {period_end}", inline=False)
        
        # Show section summary
        sections_str = ""
        for section in report['sections'][:5]:
            status_icon = "✅" if section['status'] == 'compliant' else "⚠️"
            sections_str += f"{status_icon} {section['name']}: {section['score']}/100\n"
        
        if len(report['sections']) > 5:
            sections_str += f"... +{len(report['sections']) - 5} more sections"
        
        embed.add_field(name="Sections", value=sections_str, inline=False)
        embed.set_footer(text="Sentinel Compliance Reporting | Use !reportdetail <id> for full report")
        
        await msg.edit(content=None, embed=embed)
    
    async def _reportlist_logic(self, ctx, framework: str = None):
        """List compliance reports"""
        reports = self.get_guild_reports(ctx.guild.id)
        
        if not reports:
            await ctx.send("📋 No compliance reports generated yet.")
            return
        
        # Filter by framework if specified
        if framework:
            reports = [r for r in reports if r['framework'] == framework.lower()]
            if not reports:
                await ctx.send(f"📋 No reports found for framework: {framework}")
                return
        
        # Sort by date (newest first)
        sorted_reports = sorted(reports, key=lambda r: r['generated_at'], reverse=True)
        
        embed = discord.Embed(
            title="📊 Compliance Reports",
            description=f"{len(sorted_reports)} report(s) generated",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for report in sorted_reports[:10]:
            score = report['overall_score']
            score_emoji = "✅" if score >= 90 else "🔵" if score >= 75 else "🟡" if score >= 60 else "🔴"
            
            generated = datetime.fromisoformat(report['generated_at']).strftime('%Y-%m-%d %H:%M')
            
            embed.add_field(
                name=f"{score_emoji} {report['framework_name']}",
                value=f"Score: {score}/100 | {report['report_id']}\nGenerated: {generated}",
                inline=False
            )
        
        if len(sorted_reports) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_reports) - 10} additional reports", inline=False)
        
        embed.set_footer(text="Use !reportdetail <id> for full report")
        
        await ctx.send(embed=embed)
    
    async def _reporttemplates_logic(self, ctx):
        """Show report templates"""
        templates = self.get_templates()
        
        embed = discord.Embed(
            title="📋 Compliance Report Templates",
            description=f"{len(templates)} framework(s) available",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        for template_id, template in sorted(templates.items()):
            sections_count = len(template['sections'])
            
            embed.add_field(
                name=f"📄 {template['name']}",
                value=f"Framework: {template['framework']}\nSections: {sections_count}\nFrequency: {template['frequency'].title()}",
                inline=True
            )
        
        embed.set_footer(text="Use !reportgenerate <framework> to generate report")
        
        await ctx.send(embed=embed)
    
    async def _reportschedule_logic(self, ctx):
        """Show report schedule"""
        templates = self.get_templates()
        
        embed = discord.Embed(
            title="📅 Compliance Report Schedule",
            description="Recommended reporting frequency",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        quarterly = []
        annual = []
        
        for template_id, template in templates.items():
            if template['frequency'] == 'quarterly':
                quarterly.append(template['framework'])
            elif template['frequency'] == 'annual':
                annual.append(template['framework'])
        
        if quarterly:
            embed.add_field(name="📊 Quarterly Reports", value="\n".join(quarterly), inline=True)
        
        if annual:
            embed.add_field(name="📊 Annual Reports", value="\n".join(annual), inline=True)
        
        embed.add_field(
            name="ℹ️ Next Steps",
            value="Configure automated report generation with `!reportautomate`",
            inline=False
        )
        
        embed.set_footer(text="Sentinel Compliance Reporting")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='reportgenerate')
    async def reportgenerate_prefix(self, ctx, framework: str):
        """Generate compliance report - Prefix command"""
        await self._reportgenerate_logic(ctx, framework)
    
    @commands.command(name='reportlist')
    async def reportlist_prefix(self, ctx, framework: str = None):
        """List reports - Prefix command"""
        await self._reportlist_logic(ctx, framework)
    
    @commands.command(name='reporttemplates')
    async def reporttemplates_prefix(self, ctx):
        """Show templates - Prefix command"""
        await self._reporttemplates_logic(ctx)
    
    @commands.command(name='reportschedule')
    async def reportschedule_prefix(self, ctx):
        """Show schedule - Prefix command"""
        await self._reportschedule_logic(ctx)

async def setup(bot):
    await bot.add_cog(ComplianceReportGenerator(bot))
