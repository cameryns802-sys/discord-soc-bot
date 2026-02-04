"""
Encryption Policy Engine - Enforce encryption policies and standards
Encryption requirement definitions and compliance checking
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class EncryptionPolicyEngine(commands.Cog):
    """Enforce encryption policies across the system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.policies = {
            'at_rest': {
                'required': True,
                'algorithm': 'AES-256-GCM',
                'key_length': 256
            },
            'in_transit': {
                'required': True,
                'algorithm': 'TLS1.3',
                'min_cipher_strength': 256
            },
            'end_to_end': {
                'required': True,
                'algorithm': 'AES-256-GCM',
                'key_exchange': 'ECDH-P256'
            }
        }
    
    def check_encryption_compliance(self, data_location: str, encryption_details: Dict) -> Dict:
        """Check if data encryption meets policy"""
        if data_location not in self.policies:
            return {'compliant': False, 'reason': 'Unknown location'}
        
        policy = self.policies[data_location]
        encrypted = encryption_details.get('encrypted', False)
        
        if not encrypted and policy['required']:
            return {'compliant': False, 'reason': 'Encryption required but not applied'}
        
        algorithm = encryption_details.get('algorithm')
        if algorithm != policy['algorithm']:
            return {'compliant': False, 'reason': f'Wrong algorithm. Required: {policy["algorithm"]}'}
        
        return {'compliant': True, 'reason': 'Meets policy'}
    
    def get_policy(self, location: str) -> Dict:
        """Get encryption policy for a location"""
        return self.policies.get(location, {})
    
    def set_policy(self, location: str, algorithm: str, key_length: int = None):
        """Update encryption policy"""
        if location not in self.policies:
            self.policies[location] = {}
        
        self.policies[location]['algorithm'] = algorithm
        if key_length:
            self.policies[location]['key_length'] = key_length
    
    @commands.command(name='encpolicy')
    async def show_policies(self, ctx):
        """View encryption policies (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(
            title="🔐 Encryption Policies",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for location, policy in self.policies.items():
            policy_str = f"Algorithm: {policy['algorithm']}\n"
            if 'key_length' in policy:
                policy_str += f"Key Length: {policy['key_length']} bits\n"
            policy_str += f"Required: {'Yes' if policy['required'] else 'No'}"
            
            embed.add_field(name=location.title(), value=policy_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EncryptionPolicyEngine(bot))
