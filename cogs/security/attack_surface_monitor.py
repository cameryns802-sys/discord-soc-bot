"""
Attack Surface Monitor - Real-time attack surface tracking for Sentinel
Monitor exposed services, permissions, webhooks, invites, and attack vectors
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class AttackSurfaceMonitor(commands.Cog):
    """Attack surface monitoring and exposure tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.surface_file = 'data/attack_surface.json'
        self.load_surface_data()
    
    def load_surface_data(self):
        """Load attack surface data"""
        if not os.path.exists(self.surface_file):
            os.makedirs(os.path.dirname(self.surface_file), exist_ok=True)
            with open(self.surface_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_surface(self, guild_id):
        """Get attack surface for guild"""
        with open(self.surface_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {'scans': [], 'findings': []})
    
    def save_surface(self, guild_id, surface):
        """Save attack surface"""
        with open(self.surface_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = surface
        with open(self.surface_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def scan_attack_surface(self, guild):
        """Comprehensive attack surface scan"""
        findings = []
        exposure_score = 0
        
        # 1. Webhook Exposure
        webhooks = await guild.webhooks()
        if webhooks:
            exposure_score += len(webhooks) * 2
            findings.append({
                'category': 'webhooks',
                'severity': 'medium',
                'finding': f"{len(webhooks)} webhook(s) active",
                'risk': 'Webhooks can be abused for spam, phishing, or data exfiltration',
                'recommendation': 'Review webhook usage and implement monitoring',
                'exposure': len(webhooks) * 2
            })
        
        # 2. Invite Link Exposure
        invites = await guild.invites()
        permanent_invites = [i for i in invites if i.max_age == 0]
        if permanent_invites:
            exposure_score += len(permanent_invites) * 5
            findings.append({
                'category': 'invites',
                'severity': 'high' if len(permanent_invites) > 3 else 'medium',
                'finding': f"{len(permanent_invites)} permanent invite(s)",
                'risk': 'Permanent invites can be shared publicly, enabling unauthorized access',
                'recommendation': 'Use temporary invites with expiration and usage limits',
                'exposure': len(permanent_invites) * 5
            })
        
        # 3. Public Channel Exposure
        public_channels = [c for c in guild.text_channels if c.permissions_for(guild.default_role).read_messages]
        if public_channels:
            exposure_score += len(public_channels)
            findings.append({
                'category': 'channels',
                'severity': 'low',
                'finding': f"{len(public_channels)} public channel(s)",
                'risk': 'Public channels expose information to all members',
                'recommendation': 'Review channel permissions and restrict sensitive channels',
                'exposure': len(public_channels)
            })
        
        # 4. Overprivileged Roles
        dangerous_perms = [
            discord.Permissions.administrator,
            discord.Permissions.manage_guild,
            discord.Permissions.manage_roles,
            discord.Permissions.manage_webhooks,
            discord.Permissions.manage_channels
        ]
        
        overprivileged_roles = []
        for role in guild.roles:
            if role == guild.default_role:
                continue
            dangerous_found = [p for p in dangerous_perms if getattr(role.permissions, p.name)]
            if dangerous_found and len(role.members) > 10:
                overprivileged_roles.append(role)
        
        if overprivileged_roles:
            exposure_score += len(overprivileged_roles) * 10
            findings.append({
                'category': 'permissions',
                'severity': 'critical' if len(overprivileged_roles) > 2 else 'high',
                'finding': f"{len(overprivileged_roles)} overprivileged role(s) with >10 members",
                'risk': 'Large roles with dangerous permissions increase insider threat risk',
                'recommendation': 'Limit dangerous permissions to small, trusted groups',
                'exposure': len(overprivileged_roles) * 10
            })
        
        # 5. Bot Account Exposure
        bot_count = sum(1 for m in guild.members if m.bot)
        if bot_count > 5:
            exposure_score += (bot_count - 5) * 3
            findings.append({
                'category': 'bots',
                'severity': 'medium',
                'finding': f"{bot_count} bot account(s)",
                'risk': 'Each bot represents a potential attack vector if compromised',
                'recommendation': 'Audit bot permissions and remove unused bots',
                'exposure': (bot_count - 5) * 3
            })
        
        # 6. @everyone Mention Exposure
        if guild.default_role.permissions.mention_everyone:
            exposure_score += 15
            findings.append({
                'category': 'permissions',
                'severity': 'critical',
                'finding': '@everyone can mention @everyone',
                'risk': 'Enables mass spam and harassment attacks',
                'recommendation': 'Disable mention_everyone permission for @everyone role',
                'exposure': 15
            })
        
        # 7. External Emoji Usage
        external_emoji_allowed = guild.default_role.permissions.use_external_emojis
        if external_emoji_allowed:
            findings.append({
                'category': 'permissions',
                'severity': 'low',
                'finding': '@everyone can use external emojis',
                'risk': 'Minor risk - can be used for phishing or impersonation',
                'recommendation': 'Consider restricting to trusted roles',
                'exposure': 1
            })
            exposure_score += 1
        
        # 8. Verification Level
        if guild.verification_level == discord.VerificationLevel.none:
            exposure_score += 20
            findings.append({
                'category': 'access_control',
                'severity': 'critical',
                'finding': 'No verification required',
                'risk': 'Bots and throwaway accounts can join instantly',
                'recommendation': 'Enable at least medium verification level',
                'exposure': 20
            })
        
        # 9. Vanity URL (info only - increases discoverability)
        if guild.vanity_url_code:
            findings.append({
                'category': 'exposure',
                'severity': 'info',
                'finding': f'Vanity URL: {guild.vanity_url_code}',
                'risk': 'Increases server discoverability',
                'recommendation': 'Monitor for unauthorized sharing of invite link',
                'exposure': 0
            })
        
        # 10. Widget Enabled
        if guild.widget_enabled:
            exposure_score += 5
            findings.append({
                'category': 'exposure',
                'severity': 'medium',
                'finding': 'Server widget enabled',
                'risk': 'Exposes member list and invite link publicly',
                'recommendation': 'Disable widget if not needed for community growth',
                'exposure': 5
            })
        
        return {
            'exposure_score': exposure_score,
            'findings': findings,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _surfacescan_logic(self, ctx):
        """Scan attack surface"""
        msg = await ctx.send("🔍 Scanning attack surface...")
        
        result = await self.scan_attack_surface(ctx.guild)
        
        # Save scan
        surface = self.get_guild_surface(ctx.guild.id)
        scans = surface.get('scans', [])
        scans.append({
            'score': result['exposure_score'],
            'timestamp': result['timestamp'],
            'findings_count': len(result['findings'])
        })
        surface['scans'] = scans[-20:]  # Keep last 20
        surface['last_scan'] = result
        self.save_surface(ctx.guild.id, surface)
        
        # Determine color
        score = result['exposure_score']
        if score >= 100:
            color = discord.Color.red()
            status = "🔴 CRITICAL EXPOSURE"
        elif score >= 50:
            color = discord.Color.orange()
            status = "🟠 HIGH EXPOSURE"
        elif score >= 25:
            color = discord.Color.gold()
            status = "🟡 MODERATE EXPOSURE"
        else:
            color = discord.Color.green()
            status = "🟢 LOW EXPOSURE"
        
        embed = discord.Embed(
            title="🛡️ Attack Surface Analysis",
            description=f"**Exposure Score: {score}** - {status}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Group findings by severity
        critical = [f for f in result['findings'] if f['severity'] == 'critical']
        high = [f for f in result['findings'] if f['severity'] == 'high']
        medium = [f for f in result['findings'] if f['severity'] == 'medium']
        low = [f for f in result['findings'] if f['severity'] == 'low']
        
        summary_str = f"🔴 Critical: {len(critical)}\n🟠 High: {len(high)}\n🟡 Medium: {len(medium)}\n🟢 Low: {len(low)}"
        embed.add_field(name="📊 Findings Summary", value=summary_str, inline=True)
        
        # Top findings
        top_findings = sorted(result['findings'], key=lambda f: f['exposure'], reverse=True)[:3]
        for finding in top_findings:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}.get(finding['severity'], '❓')
            embed.add_field(
                name=f"{severity_emoji} {finding['finding']}",
                value=f"**Risk:** {finding['risk']}\n**Action:** {finding['recommendation']}",
                inline=False
            )
        
        if len(result['findings']) > 3:
            embed.add_field(name="... and more", value=f"+{len(result['findings']) - 3} additional findings. Use `!surfacereport` for full report.", inline=False)
        
        embed.set_footer(text="Sentinel Attack Surface Monitor")
        
        await msg.edit(content=None, embed=embed)
    
    async def _surfacereport_logic(self, ctx):
        """Full attack surface report"""
        surface = self.get_guild_surface(ctx.guild.id)
        
        if 'last_scan' not in surface:
            await ctx.send("❌ No scan data available. Run `!surfacescan` first.")
            return
        
        last_scan = surface['last_scan']
        
        embed = discord.Embed(
            title="📋 Attack Surface Report",
            description=f"Exposure Score: {last_scan['exposure_score']}",
            color=discord.Color.orange(),
            timestamp=datetime.fromisoformat(last_scan['timestamp'])
        )
        
        # Group by category
        by_category = {}
        for finding in last_scan['findings']:
            cat = finding['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)
        
        # Show all findings by category
        for category, findings in sorted(by_category.items()):
            category_display = category.replace('_', ' ').title()
            findings_str = ""
            for f in findings:
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}.get(f['severity'], '❓')
                findings_str += f"{severity_emoji} {f['finding']}\n"
            
            embed.add_field(name=category_display, value=findings_str, inline=False)
        
        embed.set_footer(text="Sentinel Attack Surface Monitor | Full report")
        
        await ctx.send(embed=embed)
    
    async def _surfacehistory_logic(self, ctx):
        """Show attack surface history"""
        surface = self.get_guild_surface(ctx.guild.id)
        scans = surface.get('scans', [])
        
        if len(scans) < 2:
            await ctx.send("📊 Not enough scan history. Run `!surfacescan` multiple times.")
            return
        
        embed = discord.Embed(
            title="📈 Attack Surface History",
            description=f"{len(scans)} scan(s) recorded",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Show last 5 scans
        for scan in reversed(scans[-5:]):
            ts = datetime.fromisoformat(scan['timestamp'])
            relative = self._relative_time(ts)
            embed.add_field(
                name=f"Score: {scan['score']} ({scan['findings_count']} findings)",
                value=relative,
                inline=False
            )
        
        # Calculate trend
        scores = [s['score'] for s in scans]
        if len(scores) >= 3:
            recent_avg = sum(scores[-3:]) / 3
            older_avg = sum(scores[:-3]) / len(scores[:-3]) if len(scores) > 3 else scores[0]
            
            if recent_avg > older_avg + 10:
                trend = "📈 INCREASING EXPOSURE"
                trend_color = "🔴"
            elif recent_avg < older_avg - 10:
                trend = "📉 DECREASING EXPOSURE"
                trend_color = "🟢"
            else:
                trend = "➡️ STABLE"
                trend_color = "🔵"
            
            embed.add_field(name="Trend", value=f"{trend_color} {trend}", inline=False)
        
        embed.set_footer(text="Sentinel Attack Surface Monitor")
        
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
    
    @commands.command(name='surfacescan')
    async def surfacescan_prefix(self, ctx):
        """Scan attack surface - Prefix command"""
        await self._surfacescan_logic(ctx)
    
    @commands.command(name='surfacereport')
    async def surfacereport_prefix(self, ctx):
        """Full attack surface report - Prefix command"""
        await self._surfacereport_logic(ctx)
    
    @commands.command(name='surfacehistory')
    async def surfacehistory_prefix(self, ctx):
        """Attack surface history - Prefix command"""
        await self._surfacehistory_logic(ctx)

async def setup(bot):
    await bot.add_cog(AttackSurfaceMonitor(bot))
