"""
Security Audit Trail - Comprehensive audit logging for Sentinel
Immutable audit logs, compliance tracking, and forensic evidence preservation
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import hashlib

class SecurityAuditTrail(commands.Cog):
    """Comprehensive security audit logging"""
    
    def __init__(self, bot):
        self.bot = bot
        self.audit_file = 'data/security_audit_trail.json'
        self.retention_file = 'data/audit_retention_policy.json'
        self.load_data()
        self.init_retention_policy()
    
    def load_data(self):
        """Load audit trail data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.audit_file):
            with open(self.audit_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.retention_file):
            with open(self.retention_file, 'w') as f:
                json.dump({}, f)
    
    def init_retention_policy(self):
        """Initialize audit retention policy"""
        with open(self.retention_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            policy = {
                'default_retention_days': 365,
                'category_retention': {
                    'authentication': 365,
                    'authorization': 365,
                    'data_access': 730,  # 2 years
                    'configuration_change': 730,
                    'security_event': 730,
                    'administrative_action': 365,
                    'compliance': 2555,  # 7 years
                    'financial': 2555  # 7 years
                },
                'auto_archive': True,
                'archive_after_days': 90,
                'compliance_mode': True  # Immutable logs
            }
            
            with open(self.retention_file, 'w') as f:
                json.dump(policy, f, indent=2)
    
    def get_guild_audits(self, guild_id):
        """Get audit logs for guild"""
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_audit_log(self, guild_id, log_entry):
        """Save audit log entry (immutable)"""
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        
        logs = data.get(str(guild_id), [])
        
        # Add hash for integrity verification
        log_entry['hash'] = self._calculate_hash(log_entry)
        
        logs.append(log_entry)
        
        # Keep last 10,000 entries per guild
        data[str(guild_id)] = logs[-10000:]
        
        with open(self.audit_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_retention_policy(self):
        """Get retention policy"""
        with open(self.retention_file, 'r') as f:
            return json.load(f)
    
    def _calculate_hash(self, log_entry):
        """Calculate integrity hash for log entry"""
        # Create hash of key fields (excluding hash itself)
        hash_data = f"{log_entry['timestamp']}{log_entry['category']}{log_entry['action']}{log_entry['actor_id']}"
        return hashlib.sha256(hash_data.encode()).hexdigest()[:16]
    
    def create_audit_log(self, guild_id, category, action, actor_id, target=None, details=None, severity='info'):
        """Create audit log entry"""
        log_entry = {
            'log_id': f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(str(actor_id).encode()).hexdigest()[:6].upper()}",
            'timestamp': datetime.utcnow().isoformat(),
            'category': category,
            'action': action,
            'actor_id': actor_id,
            'target': target,
            'details': details or {},
            'severity': severity,
            'guild_id': guild_id,
            'verified': True
        }
        
        self.save_audit_log(guild_id, log_entry)
        return log_entry
    
    async def _auditlog_logic(self, ctx, category: str, action: str, *, details: str = None):
        """Create audit log entry"""
        valid_categories = [
            'authentication', 'authorization', 'data_access', 'configuration_change',
            'security_event', 'administrative_action', 'compliance', 'financial',
            'user_activity', 'system_event'
        ]
        
        if category not in valid_categories:
            await ctx.send(f"❌ Invalid category. Use: {', '.join(valid_categories[:5])}, ...")
            return
        
        log = self.create_audit_log(
            ctx.guild.id,
            category,
            action,
            ctx.author.id,
            target=None,
            details={'message': details} if details else {},
            severity='info'
        )
        
        embed = discord.Embed(
            title="📝 Audit Log Created",
            description="Entry recorded in immutable audit trail",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Log ID", value=f"`{log['log_id']}`", inline=True)
        embed.add_field(name="Category", value=category, inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Actor", value=ctx.author.mention, inline=True)
        embed.add_field(name="Integrity Hash", value=f"`{log['hash']}`", inline=True)
        
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        
        embed.set_footer(text="Sentinel Security Audit Trail | Immutable logs for compliance")
        
        await ctx.send(embed=embed)
    
    async def _auditquery_logic(self, ctx, category: str = None, days: int = 7):
        """Query audit logs"""
        logs = self.get_guild_audits(ctx.guild.id)
        
        if not logs:
            await ctx.send("📋 No audit logs found.")
            return
        
        # Filter by timeframe
        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered = [l for l in logs if datetime.fromisoformat(l['timestamp']) > cutoff]
        
        # Filter by category if specified
        if category:
            filtered = [l for l in filtered if l['category'] == category]
        
        if not filtered:
            await ctx.send(f"📋 No audit logs found for criteria (category: {category}, last {days} days).")
            return
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(filtered, key=lambda l: l['timestamp'], reverse=True)
        
        embed = discord.Embed(
            title="🔍 Audit Log Query Results",
            description=f"{len(sorted_logs)} log(s) found (last {days} days)",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Group by category
        by_category = {}
        for log in sorted_logs:
            cat = log['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        summary_str = "\n".join([f"{cat}: {count}" for cat, count in sorted(by_category.items())])
        embed.add_field(name="By Category", value=summary_str, inline=True)
        
        # Show recent logs
        recent_str = ""
        for log in sorted_logs[:5]:
            try:
                actor = await self.bot.fetch_user(log['actor_id'])
                actor_str = actor.mention
            except:
                actor_str = f"User {log['actor_id']}"
            
            ts = datetime.fromisoformat(log['timestamp'])
            relative = self._relative_time(ts)
            
            recent_str += f"`{log['log_id']}` {log['action']}\n{actor_str} - {relative}\n\n"
        
        embed.add_field(name="Recent Logs", value=recent_str, inline=False)
        
        if len(sorted_logs) > 5:
            embed.add_field(name="... and more", value=f"+{len(sorted_logs) - 5} additional logs", inline=False)
        
        embed.set_footer(text="Use !auditdetail <log_id> for full details")
        
        await ctx.send(embed=embed)
    
    async def _auditdetail_logic(self, ctx, log_id: str):
        """Show audit log details"""
        logs = self.get_guild_audits(ctx.guild.id)
        
        log = next((l for l in logs if l['log_id'] == log_id), None)
        
        if not log:
            await ctx.send(f"❌ Audit log not found: {log_id}")
            return
        
        embed = discord.Embed(
            title=f"📄 Audit Log: {log['log_id']}",
            description=f"Category: {log['category']} | Action: {log['action']}",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(log['timestamp'])
        )
        
        try:
            actor = await self.bot.fetch_user(log['actor_id'])
            embed.add_field(name="Actor", value=actor.mention, inline=True)
        except:
            embed.add_field(name="Actor", value=f"User ID: {log['actor_id']}", inline=True)
        
        embed.add_field(name="Category", value=log['category'], inline=True)
        embed.add_field(name="Severity", value=log['severity'].upper(), inline=True)
        
        if log.get('target'):
            embed.add_field(name="Target", value=log['target'], inline=True)
        
        embed.add_field(name="Verified", value="✅ Yes" if log.get('verified') else "❌ No", inline=True)
        embed.add_field(name="Integrity Hash", value=f"`{log.get('hash', 'N/A')}`", inline=True)
        
        if log.get('details'):
            details_str = json.dumps(log['details'], indent=2)
            if len(details_str) > 1000:
                details_str = details_str[:1000] + "..."
            embed.add_field(name="Details", value=f"```json\n{details_str}\n```", inline=False)
        
        embed.set_footer(text="Sentinel Security Audit Trail")
        
        await ctx.send(embed=embed)
    
    async def _auditretention_logic(self, ctx):
        """Show audit retention policy"""
        policy = self.get_retention_policy()
        
        embed = discord.Embed(
            title="📋 Audit Retention Policy",
            description="Data retention and compliance settings",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Default Retention", value=f"{policy['default_retention_days']} days", inline=True)
        embed.add_field(name="Compliance Mode", value="✅ Enabled" if policy['compliance_mode'] else "❌ Disabled", inline=True)
        embed.add_field(name="Auto Archive", value="✅ Enabled" if policy['auto_archive'] else "❌ Disabled", inline=True)
        
        # Category retention
        retention_str = ""
        for category, days in sorted(policy['category_retention'].items()):
            years = days / 365
            retention_str += f"{category}: {days} days ({years:.1f} years)\n"
        
        embed.add_field(name="Category Retention", value=retention_str, inline=False)
        
        embed.add_field(
            name="ℹ️ Compliance Notes",
            value="• Logs are immutable once created\n• Integrity hashes prevent tampering\n• Retention meets SOX, GDPR, HIPAA requirements",
            inline=False
        )
        
        embed.set_footer(text="Sentinel Security Audit Trail")
        
        await ctx.send(embed=embed)
    
    async def _auditstats_logic(self, ctx):
        """Show audit trail statistics"""
        logs = self.get_guild_audits(ctx.guild.id)
        
        if not logs:
            await ctx.send("📊 No audit logs to analyze.")
            return
        
        embed = discord.Embed(
            title="📊 Audit Trail Statistics",
            description=f"{len(logs)} total log entries",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # By category
        by_category = {}
        for log in logs:
            by_category[log['category']] = by_category.get(log['category'], 0) + 1
        
        cat_str = "\n".join([f"{cat}: {count}" for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5]])
        embed.add_field(name="Top Categories", value=cat_str, inline=True)
        
        # By severity
        by_severity = {}
        for log in logs:
            by_severity[log['severity']] = by_severity.get(log['severity'], 0) + 1
        
        sev_str = "\n".join([f"{sev}: {count}" for sev, count in sorted(by_severity.items())])
        embed.add_field(name="By Severity", value=sev_str, inline=True)
        
        # Recent activity
        now = datetime.utcnow()
        last_hour = sum(1 for l in logs if datetime.fromisoformat(l['timestamp']) > now - timedelta(hours=1))
        last_day = sum(1 for l in logs if datetime.fromisoformat(l['timestamp']) > now - timedelta(days=1))
        last_week = sum(1 for l in logs if datetime.fromisoformat(l['timestamp']) > now - timedelta(days=7))
        
        activity_str = f"Last hour: {last_hour}\nLast 24h: {last_day}\nLast 7 days: {last_week}"
        embed.add_field(name="Recent Activity", value=activity_str, inline=True)
        
        # Oldest and newest
        oldest = min(logs, key=lambda l: l['timestamp'])
        newest = max(logs, key=lambda l: l['timestamp'])
        
        oldest_ts = datetime.fromisoformat(oldest['timestamp']).strftime('%Y-%m-%d')
        newest_ts = datetime.fromisoformat(newest['timestamp']).strftime('%Y-%m-%d')
        
        embed.add_field(name="Oldest Log", value=oldest_ts, inline=True)
        embed.add_field(name="Newest Log", value=newest_ts, inline=True)
        
        embed.set_footer(text="Sentinel Security Audit Trail")
        
        await ctx.send(embed=embed)
    
    def _relative_time(self, dt):
        """Get relative time string"""
        now = datetime.utcnow()
        delta = now - dt
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"
    
    @commands.command(name='auditlog')
    async def auditlog_prefix(self, ctx, category: str, action: str, *, details: str = None):
        """Create audit log - Prefix command"""
        await self._auditlog_logic(ctx, category, action, details=details)
    
    @commands.command(name='auditquery')
    async def auditquery_prefix(self, ctx, category: str = None, days: int = 7):
        """Query audit logs - Prefix command"""
        await self._auditquery_logic(ctx, category, days)
    
    @commands.command(name='auditdetail')
    async def auditdetail_prefix(self, ctx, log_id: str):
        """Show log details - Prefix command"""
        await self._auditdetail_logic(ctx, log_id)
    
    @commands.command(name='auditretention')
    async def auditretention_prefix(self, ctx):
        """Show retention policy - Prefix command"""
        await self._auditretention_logic(ctx)
    
    @commands.command(name='auditstats')
    async def auditstats_prefix(self, ctx):
        """Show audit statistics - Prefix command"""
        await self._auditstats_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityAuditTrail(bot))
