"""
Key Rotation Service - Automatic cryptographic key rotation
Handles key lifecycle, rotation policies, and deployment
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple
from cogs.core.pst_timezone import get_now_pst

class KeyRotationService(commands.Cog):
    """Manage cryptographic key rotation and lifecycle"""
    
    def __init__(self, bot):
        self.bot = bot
        self.keys_file = 'data/key_registry.json'
        self.rotation_policies = {
            'api_keys': {'rotate_every_days': 90, 'last_rotation': None},
            'signing_keys': {'rotate_every_days': 180, 'last_rotation': None},
            'encryption_keys': {'rotate_every_days': 365, 'last_rotation': None}
        }
        self.load_keys()
    
    def load_keys(self):
        """Load key registry"""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                    self.rotation_policies = data.get('policies', self.rotation_policies)
            except:
                self.init_keys()
        else:
            self.init_keys()
    
    def init_keys(self):
        """Initialize default key registry"""
        self.save_keys()
    
    def save_keys(self):
        """Save key registry"""
        os.makedirs(os.path.dirname(self.keys_file), exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump({'policies': self.rotation_policies}, f, indent=2)
    
    async def rotate_key(self, key_type: str) -> Dict:
        """Rotate a key and return status"""
        if key_type not in self.rotation_policies:
            return {'error': f'Unknown key type: {key_type}'}
        
        # Generate new key (simulation)
        new_key_id = f"{key_type}_key_{get_now_pst().timestamp()}"
        
        # Update policy
        self.rotation_policies[key_type]['last_rotation'] = get_now_pst().isoformat()
        self.save_keys()
        
        return {
            'key_type': key_type,
            'new_key_id': new_key_id,
            'timestamp': get_now_pst().isoformat(),
            'status': 'rotated'
        }
    
    def get_keys_due_for_rotation(self) -> List[str]:
        """Get list of keys that are due for rotation"""
        due = []
        now = get_now_pst()
        
        for key_type, policy in self.rotation_policies.items():
            last_rotation = policy.get('last_rotation')
            rotate_every = policy.get('rotate_every_days', 90)
            
            if last_rotation:
                last_rot_date = datetime.fromisoformat(last_rotation)
                if (now - last_rot_date) > timedelta(days=rotate_every):
                    due.append(key_type)
        
        return due
    
    def get_rotation_status(self) -> Dict:
        """Get key rotation status"""
        due = self.get_keys_due_for_rotation()
        
        return {
            'keys_due': due,
            'total_keys': len(self.rotation_policies),
            'policies': self.rotation_policies
        }
    
    @commands.command(name='rotatekey')
    async def rotate_key_cmd(self, ctx, key_type: str):
        """Rotate a key (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        result = await self.rotate_key(key_type)
        
        embed = discord.Embed(
            title="🔑 Key Rotated",
            description=f"Key Type: {key_type}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        if 'error' in result:
            embed.color = discord.Color.red()
            embed.add_field(name="Error", value=result['error'], inline=False)
        else:
            embed.add_field(name="New Key ID", value=result['new_key_id'], inline=False)
            embed.add_field(name="Status", value=result['status'], inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(KeyRotationService(bot))
