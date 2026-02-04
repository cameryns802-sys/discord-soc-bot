"""
Secret Lifecycle Manager - Manage secrets from creation to retirement
Secret provisioning, rotation, revocation, and audit
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class SecretLifecycleManager(commands.Cog):
    """Manage cryptographic secret lifecycle"""
    
    def __init__(self, bot):
        self.bot = bot
        self.secrets_file = 'data/secret_lifecycle.json'
        self.secrets = {}
        self.load_secrets()
    
    def load_secrets(self):
        """Load secret registry"""
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'r') as f:
                    self.secrets = json.load(f)
            except:
                self.secrets = {}
        else:
            self.secrets = {}
    
    def save_secrets(self):
        """Save secret registry"""
        os.makedirs(os.path.dirname(self.secrets_file), exist_ok=True)
        with open(self.secrets_file, 'w') as f:
            # Never save actual secret values
            safe_secrets = {k: {kk: vv for kk, vv in v.items() if kk != 'value'} 
                           for k, v in self.secrets.items()}
            json.dump(safe_secrets, f, indent=2)
    
    async def provision_secret(self, name: str, secret_type: str, ttl_days: int = 90) -> Dict:
        """Provision a new secret"""
        secret_id = f"secret_{len(self.secrets) + 1}"
        
        self.secrets[secret_id] = {
            'name': name,
            'type': secret_type,
            'created_at': get_now_pst().isoformat(),
            'expires_at': (get_now_pst() + timedelta(days=ttl_days)).isoformat(),
            'status': 'active',
            'rotations': 0
        }
        
        self.save_secrets()
        
        return {
            'secret_id': secret_id,
            'status': 'provisioned',
            'ttl_days': ttl_days
        }
    
    async def rotate_secret(self, secret_id: str) -> Dict:
        """Rotate an existing secret"""
        if secret_id not in self.secrets:
            return {'error': 'Secret not found'}
        
        secret = self.secrets[secret_id]
        secret['rotations'] += 1
        secret['last_rotated'] = get_now_pst().isoformat()
        
        self.save_secrets()
        
        return {
            'secret_id': secret_id,
            'rotation_count': secret['rotations'],
            'status': 'rotated'
        }
    
    async def revoke_secret(self, secret_id: str) -> Dict:
        """Revoke a secret"""
        if secret_id not in self.secrets:
            return {'error': 'Secret not found'}
        
        self.secrets[secret_id]['status'] = 'revoked'
        self.secrets[secret_id]['revoked_at'] = get_now_pst().isoformat()
        
        self.save_secrets()
        
        return {
            'secret_id': secret_id,
            'status': 'revoked'
        }
    
    def get_expiring_secrets(self, days_until: int = 7) -> List[Dict]:
        """Get secrets expiring soon"""
        expiring = []
        cutoff = get_now_pst() + timedelta(days=days_until)
        
        for secret_id, secret in self.secrets.items():
            if secret['status'] == 'active':
                expires = datetime.fromisoformat(secret['expires_at'])
                if expires < cutoff:
                    expiring.append({
                        'secret_id': secret_id,
                        'name': secret['name'],
                        'expires_at': secret['expires_at']
                    })
        
        return expiring
    
    @commands.command(name='secretlifecycle')
    async def lifecycle_status(self, ctx):
        """View secret lifecycle status (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        expiring = self.get_expiring_secrets()
        active = sum(1 for s in self.secrets.values() if s['status'] == 'active')
        
        embed = discord.Embed(
            title="🔐 Secret Lifecycle Status",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Active Secrets", value=str(active), inline=True)
        embed.add_field(name="Expiring Soon", value=str(len(expiring)), inline=True)
        embed.add_field(name="Total Secrets", value=str(len(self.secrets)), inline=True)
        
        if expiring:
            expiring_str = ", ".join([f"{s['name']}" for s in expiring[:3]])
            embed.add_field(name="Expiring Secrets", value=expiring_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecretLifecycleManager(bot))
