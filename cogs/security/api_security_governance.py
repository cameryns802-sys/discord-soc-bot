"""
API Security & Governance - API inventory and security controls
Track, monitor, and secure APIs across the organization
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
from cogs.core.pst_timezone import get_now_pst

class APISecurityGovernance(commands.Cog):
    """API security management and governance"""
    
    def __init__(self, bot):
        self.bot = bot
        self.apis_file = 'data/api_inventory.json'
        self.endpoints_file = 'data/api_endpoints.json'
        self.load_data()
    
    def load_data(self):
        """Load API data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.apis_file):
            with open(self.apis_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.endpoints_file):
            with open(self.endpoints_file, 'w') as f:
                json.dump({}, f)
    
    def get_apis(self, guild_id):
        """Get APIs for guild"""
        with open(self.apis_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_apis(self, guild_id, apis):
        """Save APIs"""
        with open(self.apis_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = apis
        with open(self.apis_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_api_risk_score(self, api):
        """Calculate API security risk score (0-100)"""
        score = 50
        
        # Authentication method
        auth = api.get('authentication', 'none')
        if auth == 'oauth2':
            score -= 20
        elif auth == 'api_key':
            score -= 5
        elif auth == 'none':
            score += 40
        
        # Rate limiting
        if api.get('rate_limiting_enabled', False):
            score -= 10
        
        # HTTPS/TLS
        if api.get('uses_https', False):
            score -= 15
        
        # API versioning
        if api.get('versioned', False):
            score -= 5
        
        # Access logging
        if api.get('access_logging_enabled', False):
            score -= 5
        
        # Exposure
        if api.get('public_access', False):
            score += 20
        
        # Last security audit
        if api.get('last_security_audit'):
            last = datetime.fromisoformat(api['last_security_audit'])
            days_since = (get_now_pst() - last).days
            if days_since > 180:
                score += 25
        else:
            score += 30
        
        # Known vulnerabilities
        if api.get('vulnerabilities', []):
            score += len(api['vulnerabilities']) * 5
        
        return max(0, min(100, score))
    
    async def _apiadd_logic(self, ctx, api_name: str, endpoint: str, auth_type: str = 'api_key'):
        """Add API to inventory"""
        apis = self.get_apis(ctx.guild.id)
        
        api_id = f"API-{str(uuid.uuid4())[:8].upper()}"
        
        api = {
            'id': api_id,
            'name': api_name,
            'endpoint': endpoint,
            'added_at': get_now_pst().isoformat(),
            'authentication': auth_type.lower(),
            'rate_limiting_enabled': True,
            'uses_https': True,
            'versioned': True,
            'access_logging_enabled': True,
            'public_access': False,
            'last_security_audit': None,
            'vulnerabilities': [],
            'risk_score': 0,
            'status': 'active',
            'owner': 'Unknown',
            'endpoints': [],
            'deprecation_date': None
        }
        
        api['risk_score'] = self.calculate_api_risk_score(api)
        apis[api_id] = api
        self.save_apis(ctx.guild.id, apis)
        
        embed = discord.Embed(
            title="🔌 API Registered",
            description=f"**{api_name}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="API ID", value=f"`{api_id}`", inline=True)
        embed.add_field(name="Endpoint", value=f"`{endpoint}`", inline=True)
        embed.add_field(name="Authentication", value=auth_type, inline=True)
        embed.add_field(name="Security Score", value=f"{api['risk_score']}/100", inline=True)
        embed.add_field(name="Rate Limiting", value="✅ Enabled", inline=True)
        embed.add_field(name="HTTPS", value="✅ Enabled", inline=True)
        
        embed.set_footer(text="Use !apiscan to assess API security")
        
        await ctx.send(embed=embed)
    
    async def _apiinventory_logic(self, ctx):
        """List all APIs"""
        apis = self.get_apis(ctx.guild.id)
        
        if not apis:
            await ctx.send("🔌 No APIs registered yet.")
            return
        
        # Sort by risk score
        sorted_apis = sorted(apis.values(), key=lambda a: a['risk_score'], reverse=True)
        
        embed = discord.Embed(
            title="🔌 API Inventory",
            description=f"{len(sorted_apis)} API(s) tracked",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        public_apis = sum(1 for a in apis.values() if a['public_access'])
        high_risk = sum(1 for a in apis.values() if a['risk_score'] >= 70)
        
        embed.add_field(name="Status Summary", value=f"🔴 {high_risk} high-risk | 🟠 {public_apis} public", inline=False)
        
        for api in sorted_apis[:10]:
            risk_emoji = '🔴' if api['risk_score'] >= 70 else '🟠' if api['risk_score'] >= 50 else '🟡' if api['risk_score'] >= 30 else '🟢'
            public_badge = ' (🌐 PUBLIC)' if api['public_access'] else ''
            
            embed.add_field(
                name=f"{risk_emoji} {api['name']} ({api['id']}){public_badge}",
                value=f"Auth: {api['authentication'].upper()} | Risk: {api['risk_score']}/100 | {api['endpoint']}",
                inline=False
            )
        
        if len(sorted_apis) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_apis) - 10} additional APIs", inline=False)
        
        embed.set_footer(text="Use !apidetail <id> for full security review")
        
        await ctx.send(embed=embed)
    
    async def _apidetail_logic(self, ctx, api_id: str):
        """Show API security details"""
        apis = self.get_apis(ctx.guild.id)
        
        api_id = api_id.upper()
        if not api_id.startswith('API-'):
            api_id = f"API-{api_id}"
        
        api = apis.get(api_id)
        if not api:
            await ctx.send(f"❌ API not found: {api_id}")
            return
        
        risk = api['risk_score']
        color = discord.Color.red() if risk >= 70 else discord.Color.orange() if risk >= 50 else discord.Color.gold() if risk >= 30 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"🔌 {api['name']}",
            description=f"Endpoint: `{api['endpoint']}`",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="API ID", value=f"`{api['id']}`", inline=True)
        embed.add_field(name="Status", value=api['status'].title(), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk}/100", inline=True)
        
        embed.add_field(name="Security Configuration", value="━" * 25, inline=False)
        embed.add_field(name="Authentication", value=api['authentication'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Rate Limiting", value="✅ Yes" if api['rate_limiting_enabled'] else "❌ No", inline=True)
        embed.add_field(name="HTTPS/TLS", value="✅ Yes" if api['uses_https'] else "❌ No", inline=True)
        embed.add_field(name="Versioned", value="✅ Yes" if api['versioned'] else "❌ No", inline=True)
        embed.add_field(name="Access Logging", value="✅ Yes" if api['access_logging_enabled'] else "❌ No", inline=True)
        embed.add_field(name="Public Access", value="🌐 Yes" if api['public_access'] else "🔒 No", inline=True)
        
        if api['vulnerabilities']:
            vuln_str = "\n".join([f"• {v}" for v in api['vulnerabilities'][:5]])
            embed.add_field(name="⚠️ Known Vulnerabilities", value=vuln_str, inline=False)
        
        if api['deprecation_date']:
            embed.add_field(name="⚠️ Deprecation Date", value=api['deprecation_date'], inline=False)
        
        if api['last_security_audit']:
            last = datetime.fromisoformat(api['last_security_audit']).strftime('%Y-%m-%d')
            embed.add_field(name="Last Security Audit", value=last, inline=True)
        
        embed.set_footer(text="Sentinel API Security Governance")
        
        await ctx.send(embed=embed)
    
    async def _apiscan_logic(self, ctx):
        """Scan all APIs for security issues"""
        apis = self.get_apis(ctx.guild.id)
        
        if not apis:
            await ctx.send("🔌 No APIs to scan.")
            return
        
        issues = []
        
        for api in apis.values():
            if api['risk_score'] >= 70:
                issues.append(f"🔴 {api['name']}: HIGH RISK ({api['risk_score']}/100)")
            if api['public_access']:
                issues.append(f"🌐 {api['name']}: Publicly accessible API")
            if not api['uses_https']:
                issues.append(f"⚠️ {api['name']}: Not using HTTPS")
            if api['authentication'] == 'none':
                issues.append(f"🔓 {api['name']}: No authentication configured")
        
        embed = discord.Embed(
            title="🔍 API Security Scan",
            description=f"Scanned {len(apis)} API(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        secure = sum(1 for a in apis.values() if a['risk_score'] < 50)
        embed.add_field(name="✅ Secure APIs", value=f"{secure}/{len(apis)} APIs below risk threshold", inline=False)
        
        if issues:
            embed.add_field(name="⚠️ Security Issues", value="\n".join(issues[:8]), inline=False)
            if len(issues) > 8:
                embed.add_field(name="... and more", value=f"+{len(issues) - 8} additional issues", inline=False)
            embed.color = discord.Color.orange()
        else:
            embed.add_field(name="✅ All APIs Secure", value="No high-risk configurations detected", inline=False)
            embed.color = discord.Color.green()
        
        embed.set_footer(text="Use !apidetail <id> to remediate issues")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='apiadd')
    async def apiadd_prefix(self, ctx, api_name: str, endpoint: str, auth_type: str = 'api_key'):
        """Add API to inventory - Prefix command"""
        await self._apiadd_logic(ctx, api_name, endpoint, auth_type)
    
    @commands.command(name='apiinventory')
    async def apiinventory_prefix(self, ctx):
        """List all APIs - Prefix command"""
        await self._apiinventory_logic(ctx)
    
    @commands.command(name='apidetail')
    async def apidetail_prefix(self, ctx, api_id: str):
        """Show API details - Prefix command"""
        await self._apidetail_logic(ctx, api_id)
    
    @commands.command(name='apiscan')
    async def apiscan_prefix(self, ctx):
        """Scan APIs for issues - Prefix command"""
        await self._apiscan_logic(ctx)

async def setup(bot):
    await bot.add_cog(APISecurityGovernance(bot))
