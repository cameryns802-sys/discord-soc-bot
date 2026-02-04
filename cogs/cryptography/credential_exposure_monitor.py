"""
Credential Exposure Monitor - Detect and respond to credential leaks
Monitor for accidental credential exposure in logs, configs, and communications
"""

import discord
from discord.ext import commands
from datetime import datetime
import re
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class CredentialExposureMonitor(commands.Cog):
    """Monitor for and respond to credential exposure"""
    
    def __init__(self, bot):
        self.bot = bot
        self.exposure_patterns = {
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*[\'"]?([a-z0-9]+)[\'"]?',
            'aws_key': r'(?i)(AKIA[0-9A-Z]{16})',
            'private_key': r'-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----',
            'database_url': r'(?i)(mongodb|postgres|mysql)://[^\s]+',
            'token': r'(?i)(token|bearer|auth)\s*[=:]\s*[\'"]?([a-z0-9]+)[\'"]?'
        }
        self.exposures = []
    
    def scan_for_credentials(self, text: str) -> List[Dict]:
        """Scan text for credential patterns"""
        found_credentials = []
        
        for cred_type, pattern in self.exposure_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                found_credentials.append({
                    'type': cred_type,
                    'pattern': match.group(0)[:50] + '...',  # Truncate for safety
                    'severity': 'critical'
                })
        
        return found_credentials
    
    async def respond_to_exposure(self, exposure: Dict) -> Dict:
        """Respond to detected credential exposure"""
        response = {
            'exposure_type': exposure['type'],
            'actions': [
                'notify_security_team',
                'log_incident',
                'flag_for_investigation'
            ],
            'timestamp': get_now_pst().isoformat()
        }
        
        # In production, this would trigger actual response actions
        self.exposures.append(response)
        
        return response
    
    def get_exposure_report(self) -> Dict:
        """Get report of detected exposures"""
        by_type = {}
        for exposure in self.exposures:
            exp_type = exposure['exposure_type']
            by_type[exp_type] = by_type.get(exp_type, 0) + 1
        
        return {
            'total_exposures': len(self.exposures),
            'by_type': by_type,
            'recent': self.exposures[-5:]
        }
    
    @commands.command(name='credmonitor')
    async def monitor_status(self, ctx):
        """View credential exposure monitoring status (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        report = self.get_exposure_report()
        
        embed = discord.Embed(
            title="🚨 Credential Exposure Monitor",
            color=discord.Color.red() if report['total_exposures'] > 0 else discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Exposures Detected", value=str(report['total_exposures']), inline=True)
        embed.add_field(name="Status", value="⚠️ Active" if report['total_exposures'] > 0 else "✅ Clean", inline=True)
        
        if report['by_type']:
            by_type_str = "\n".join([f"{t}: {c}" for t, c in report['by_type'].items()])
            embed.add_field(name="By Type", value=by_type_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CredentialExposureMonitor(bot))
