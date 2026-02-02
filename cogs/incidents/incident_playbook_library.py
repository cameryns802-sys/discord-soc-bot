"""
Incident Playbook Library - Pre-built response playbooks for Sentinel
Standard operating procedures for common security incidents
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class IncidentPlaybookLibrary(commands.Cog):
    """Incident response playbook management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.playbooks_file = 'data/incident_playbooks.json'
        self.executions_file = 'data/playbook_executions.json'
        self.load_data()
        self.init_playbooks()
    
    def load_data(self):
        """Load playbook data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.playbooks_file):
            with open(self.playbooks_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.executions_file):
            with open(self.executions_file, 'w') as f:
                json.dump({}, f)
    
    def init_playbooks(self):
        """Initialize standard playbooks"""
        with open(self.playbooks_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            playbooks = {
                'phishing_response': {
                    'name': 'Phishing Email Response',
                    'category': 'email_security',
                    'severity': 'medium',
                    'description': 'Standard response to reported phishing emails',
                    'steps': [
                        {
                            'step': 1,
                            'action': 'Initial Assessment',
                            'description': 'Review reported email for indicators of phishing',
                            'checklist': [
                                'Verify sender address',
                                'Check for urgency/threats',
                                'Inspect links and attachments',
                                'Look for branding inconsistencies'
                            ],
                            'responsible': 'SOC Analyst',
                            'sla': 15  # minutes
                        },
                        {
                            'step': 2,
                            'action': 'Containment',
                            'description': 'Prevent further exposure to phishing email',
                            'checklist': [
                                'Block sender domain/email',
                                'Quarantine similar emails',
                                'Remove from all mailboxes',
                                'Update email filters'
                            ],
                            'responsible': 'Email Admin',
                            'sla': 30
                        },
                        {
                            'step': 3,
                            'action': 'Investigation',
                            'description': 'Determine scope and impact',
                            'checklist': [
                                'Identify recipients who opened email',
                                'Check if links were clicked',
                                'Review attachments if downloaded',
                                'Search for IOCs'
                            ],
                            'responsible': 'SOC Analyst',
                            'sla': 60
                        },
                        {
                            'step': 4,
                            'action': 'Communication',
                            'description': 'Notify affected users and stakeholders',
                            'checklist': [
                                'Alert affected users',
                                'Provide guidance on next steps',
                                'Update security team',
                                'Log incident details'
                            ],
                            'responsible': 'Communications Lead',
                            'sla': 30
                        },
                        {
                            'step': 5,
                            'action': 'Recovery',
                            'description': 'Restore normal operations',
                            'checklist': [
                                'Verify threat is eliminated',
                                'Monitor for recurrence',
                                'Update security awareness training',
                                'Document lessons learned'
                            ],
                            'responsible': 'SOC Manager',
                            'sla': 120
                        }
                    ]
                },
                'ransomware_response': {
                    'name': 'Ransomware Incident Response',
                    'category': 'malware',
                    'severity': 'critical',
                    'description': 'Critical response procedures for ransomware infections',
                    'steps': [
                        {
                            'step': 1,
                            'action': 'Immediate Isolation',
                            'description': 'Isolate infected systems immediately',
                            'checklist': [
                                'Disconnect from network',
                                'Disable wireless connections',
                                'Power off if actively encrypting',
                                'Preserve evidence'
                            ],
                            'responsible': 'Incident Commander',
                            'sla': 5
                        },
                        {
                            'step': 2,
                            'action': 'Scope Assessment',
                            'description': 'Determine extent of infection',
                            'checklist': [
                                'Identify patient zero',
                                'Map lateral movement',
                                'Check backup systems',
                                'Identify encrypted files'
                            ],
                            'responsible': 'Forensics Team',
                            'sla': 30
                        },
                        {
                            'step': 3,
                            'action': 'Executive Notification',
                            'description': 'Inform leadership and stakeholders',
                            'checklist': [
                                'Brief executive team',
                                'Notify legal counsel',
                                'Contact cyber insurance',
                                'Prepare public statement if needed'
                            ],
                            'responsible': 'CISO',
                            'sla': 60
                        },
                        {
                            'step': 4,
                            'action': 'Eradication',
                            'description': 'Remove malware from environment',
                            'checklist': [
                                'Identify malware variant',
                                'Deploy detection rules',
                                'Remove from all systems',
                                'Patch vulnerabilities'
                            ],
                            'responsible': 'Security Engineering',
                            'sla': 240
                        },
                        {
                            'step': 5,
                            'action': 'Recovery',
                            'description': 'Restore systems and data',
                            'checklist': [
                                'Restore from clean backups',
                                'Rebuild compromised systems',
                                'Verify integrity',
                                'Monitor for reinfection'
                            ],
                            'responsible': 'IT Operations',
                            'sla': 480
                        }
                    ]
                },
                'data_breach_response': {
                    'name': 'Data Breach Response',
                    'category': 'data_protection',
                    'severity': 'critical',
                    'description': 'Response to unauthorized data access or exfiltration',
                    'steps': [
                        {
                            'step': 1,
                            'action': 'Breach Confirmation',
                            'description': 'Verify and classify the breach',
                            'checklist': [
                                'Confirm unauthorized access',
                                'Identify data types affected',
                                'Determine sensitivity level',
                                'Assess regulatory implications'
                            ],
                            'responsible': 'SOC Lead',
                            'sla': 15
                        },
                        {
                            'step': 2,
                            'action': 'Containment',
                            'description': 'Stop ongoing data exposure',
                            'checklist': [
                                'Close access vectors',
                                'Revoke compromised credentials',
                                'Block attacker infrastructure',
                                'Secure affected systems'
                            ],
                            'responsible': 'Incident Response Team',
                            'sla': 30
                        },
                        {
                            'step': 3,
                            'action': 'Legal & Compliance',
                            'description': 'Assess legal obligations',
                            'checklist': [
                                'Notify legal team',
                                'Determine breach notification requirements',
                                'Document for regulatory compliance',
                                'Contact law enforcement if needed'
                            ],
                            'responsible': 'Legal Counsel',
                            'sla': 60
                        },
                        {
                            'step': 4,
                            'action': 'Notification',
                            'description': 'Notify affected parties',
                            'checklist': [
                                'Prepare notification letters',
                                'Notify affected individuals',
                                'Report to regulators (GDPR: 72hrs)',
                                'Offer credit monitoring if applicable'
                            ],
                            'responsible': 'Privacy Officer',
                            'sla': 2880  # 48 hours
                        },
                        {
                            'step': 5,
                            'action': 'Post-Incident',
                            'description': 'Review and improve',
                            'checklist': [
                                'Conduct post-mortem',
                                'Update security controls',
                                'Enhance monitoring',
                                'Train staff on lessons learned'
                            ],
                            'responsible': 'CISO',
                            'sla': 10080  # 1 week
                        }
                    ]
                },
                'account_compromise': {
                    'name': 'Account Compromise Response',
                    'category': 'access_control',
                    'severity': 'high',
                    'description': 'Response to compromised user accounts',
                    'steps': [
                        {
                            'step': 1,
                            'action': 'Account Lockout',
                            'description': 'Immediately secure compromised account',
                            'checklist': [
                                'Disable account access',
                                'Terminate active sessions',
                                'Revoke API tokens',
                                'Block password reset'
                            ],
                            'responsible': 'Identity Team',
                            'sla': 10
                        },
                        {
                            'step': 2,
                            'action': 'Scope Analysis',
                            'description': 'Determine what attacker accessed',
                            'checklist': [
                                'Review account activity logs',
                                'Check data access',
                                'Identify privilege usage',
                                'Look for persistence mechanisms'
                            ],
                            'responsible': 'SOC Analyst',
                            'sla': 30
                        },
                        {
                            'step': 3,
                            'action': 'Credential Reset',
                            'description': 'Reset credentials securely',
                            'checklist': [
                                'Force password change',
                                'Re-enroll MFA',
                                'Issue new API keys',
                                'Verify identity before restore'
                            ],
                            'responsible': 'Help Desk',
                            'sla': 60
                        },
                        {
                            'step': 4,
                            'action': 'Recovery',
                            'description': 'Restore account safely',
                            'checklist': [
                                'Verify no backdoors',
                                'Re-enable account',
                                'Monitor for anomalies',
                                'Brief user on incident'
                            ],
                            'responsible': 'Account Owner',
                            'sla': 120
                        }
                    ]
                },
                'ddos_mitigation': {
                    'name': 'DDoS Attack Mitigation',
                    'category': 'availability',
                    'severity': 'high',
                    'description': 'Response to distributed denial of service attacks',
                    'steps': [
                        {
                            'step': 1,
                            'action': 'Attack Detection',
                            'description': 'Confirm DDoS attack',
                            'checklist': [
                                'Verify abnormal traffic patterns',
                                'Identify attack vector (L3/L4/L7)',
                                'Determine attack source',
                                'Measure impact'
                            ],
                            'responsible': 'NOC Team',
                            'sla': 10
                        },
                        {
                            'step': 2,
                            'action': 'Mitigation Activation',
                            'description': 'Enable DDoS protection',
                            'checklist': [
                                'Activate DDoS protection service',
                                'Apply rate limiting',
                                'Enable geo-blocking if needed',
                                'Adjust firewall rules'
                            ],
                            'responsible': 'Network Security',
                            'sla': 15
                        },
                        {
                            'step': 3,
                            'action': 'Traffic Analysis',
                            'description': 'Analyze attack characteristics',
                            'checklist': [
                                'Capture traffic samples',
                                'Identify attack signatures',
                                'Tune mitigation rules',
                                'Block malicious IPs'
                            ],
                            'responsible': 'Security Analyst',
                            'sla': 30
                        },
                        {
                            'step': 4,
                            'action': 'Service Restoration',
                            'description': 'Restore normal operations',
                            'checklist': [
                                'Verify attack subsided',
                                'Gradually restore services',
                                'Monitor for resurgence',
                                'Document attack details'
                            ],
                            'responsible': 'Incident Commander',
                            'sla': 120
                        }
                    ]
                }
            }
            
            with open(self.playbooks_file, 'w') as f:
                json.dump(playbooks, f, indent=2)
    
    def get_playbooks(self):
        """Get all playbooks"""
        with open(self.playbooks_file, 'r') as f:
            return json.load(f)
    
    async def _playbooklist_logic(self, ctx, category: str = None):
        """List incident playbooks"""
        playbooks = self.get_playbooks()
        
        if category:
            playbooks = {k: v for k, v in playbooks.items() if v['category'] == category}
            if not playbooks:
                await ctx.send(f"📋 No playbooks found in category: {category}")
                return
        
        embed = discord.Embed(
            title="📚 Incident Response Playbook Library",
            description=f"{len(playbooks)} playbook(s) available",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for pb_id, pb in playbooks.items():
            by_severity[pb['severity']].append((pb_id, pb))
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if by_severity[severity]:
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[severity]
                pb_str = ""
                
                for pb_id, pb in by_severity[severity]:
                    pb_str += f"**{pb['name']}** (`{pb_id}`)\n{pb['description']}\n{len(pb['steps'])} steps\n\n"
                
                embed.add_field(
                    name=f"{severity_emoji} {severity.upper()} Priority",
                    value=pb_str,
                    inline=False
                )
        
        embed.set_footer(text="Use !playbookshow <playbook_id> to view playbook details")
        
        await ctx.send(embed=embed)
    
    async def _playbookshow_logic(self, ctx, playbook_id: str):
        """Show playbook details"""
        playbooks = self.get_playbooks()
        playbook = playbooks.get(playbook_id)
        
        if not playbook:
            await ctx.send(f"❌ Playbook not found: {playbook_id}\nUse `!playbooklist` to see available playbooks.")
            return
        
        severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[playbook['severity']]
        severity_color = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.green()
        }[playbook['severity']]
        
        embed = discord.Embed(
            title=f"{severity_emoji} {playbook['name']}",
            description=playbook['description'],
            color=severity_color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Category", value=playbook['category'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Severity", value=playbook['severity'].upper(), inline=True)
        embed.add_field(name="Total Steps", value=str(len(playbook['steps'])), inline=True)
        
        # Show steps
        for step in playbook['steps'][:3]:  # Show first 3 steps
            checklist_str = "\n".join([f"☐ {item}" for item in step['checklist'][:3]])
            if len(step['checklist']) > 3:
                checklist_str += f"\n... +{len(step['checklist']) - 3} more"
            
            embed.add_field(
                name=f"Step {step['step']}: {step['action']}",
                value=f"{step['description']}\n{checklist_str}\nResponsible: {step['responsible']}\nSLA: {step['sla']} min",
                inline=False
            )
        
        if len(playbook['steps']) > 3:
            embed.add_field(name="... and more", value=f"+{len(playbook['steps']) - 3} additional steps", inline=False)
        
        embed.add_field(
            name="🚀 Execute Playbook",
            value=f"Use `!playbookexecute {playbook_id}` to start guided execution",
            inline=False
        )
        
        embed.set_footer(text="Sentinel Incident Playbooks")
        
        await ctx.send(embed=embed)
    
    async def _playbookcategories_logic(self, ctx):
        """Show playbook categories"""
        playbooks = self.get_playbooks()
        
        # Count by category
        by_category = {}
        for pb in playbooks.values():
            category = pb['category']
            by_category[category] = by_category.get(category, 0) + 1
        
        embed = discord.Embed(
            title="📂 Playbook Categories",
            description=f"{len(by_category)} category(ies)",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for category, count in sorted(by_category.items()):
            embed.add_field(
                name=category.replace('_', ' ').title(),
                value=f"{count} playbook(s)",
                inline=True
            )
        
        embed.set_footer(text="Use !playbooklist <category> to filter by category")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='playbooklist')
    async def playbooklist_prefix(self, ctx, category: str = None):
        """List playbooks - Prefix command"""
        await self._playbooklist_logic(ctx, category)
    
    @commands.command(name='playbookshow')
    async def playbookshow_prefix(self, ctx, playbook_id: str):
        """Show playbook details - Prefix command"""
        await self._playbookshow_logic(ctx, playbook_id)
    
    @commands.command(name='playbookcategories')
    async def playbookcategories_prefix(self, ctx):
        """Show categories - Prefix command"""
        await self._playbookcategories_logic(ctx)

async def setup(bot):
    await bot.add_cog(IncidentPlaybookLibrary(bot))
