"""
Crypto Compliance Mapper - Map cryptographic systems to compliance frameworks
Ensure crypto implementations meet regulatory and standards requirements
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class CryptoComplianceMapper(commands.Cog):
    """Map crypto implementations to compliance frameworks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.compliance_mappings = {
            'GDPR': {
                'requirement': 'Encryption for personal data',
                'algorithms': ['AES-256', 'ChaCha20'],
                'min_key_length': 256
            },
            'HIPAA': {
                'requirement': 'FIPS 140-2 validated encryption',
                'algorithms': ['AES'],
                'min_key_length': 256
            },
            'PCI-DSS': {
                'requirement': 'Strong encryption for cardholder data',
                'algorithms': ['AES-256'],
                'min_key_length': 256
            },
            'SOC2': {
                'requirement': 'Industry-standard encryption',
                'algorithms': ['AES', 'ChaCha20'],
                'min_key_length': 256
            }
        }
    
    def check_compliance(self, framework: str, implementation: Dict) -> Dict:
        """Check if crypto implementation meets compliance requirements"""
        if framework not in self.compliance_mappings:
            return {'compliant': False, 'reason': f'Unknown framework: {framework}'}
        
        requirement = self.compliance_mappings[framework]
        algorithm = implementation.get('algorithm')
        key_length = implementation.get('key_length', 0)
        
        # Check algorithm
        if algorithm not in requirement['algorithms']:
            return {
                'compliant': False,
                'reason': f'Algorithm {algorithm} not approved. Use: {requirement["algorithms"]}'
            }
        
        # Check key length
        if key_length < requirement['min_key_length']:
            return {
                'compliant': False,
                'reason': f'Key length {key_length} too short. Minimum: {requirement["min_key_length"]}'
            }
        
        return {'compliant': True, 'reason': f'Meets {framework} requirements'}
    
    def get_compliance_mappings(self) -> Dict:
        """Get all compliance mappings"""
        return self.compliance_mappings
    
    def get_suitable_algorithms(self, framework: str) -> List[str]:
        """Get algorithms suitable for a compliance framework"""
        if framework in self.compliance_mappings:
            return self.compliance_mappings[framework]['algorithms']
        return []
    
    @commands.command(name='cryptocompliance')
    async def show_mappings(self, ctx):
        """View crypto compliance mappings (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(
            title="🏛️ Crypto Compliance Mapper",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for framework, req in self.compliance_mappings.items():
            compliance_str = f"Requirement: {req['requirement']}\n"
            compliance_str += f"Algorithms: {', '.join(req['algorithms'])}\n"
            compliance_str += f"Min Key Length: {req['min_key_length']} bits"
            
            embed.add_field(name=framework, value=compliance_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CryptoComplianceMapper(bot))
