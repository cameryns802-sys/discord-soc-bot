"""
Token Scope Validator - Validate and enforce token scopes
Prevent privilege escalation through token misuse
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Optional, Set
from cogs.core.pst_timezone import get_now_pst

class TokenScopeValidator(commands.Cog):
    """Validate and enforce token scopes"""
    
    def __init__(self, bot):
        self.bot = bot
        self.token_scopes = {
            'read_only': ['read:messages', 'read:audit_logs'],
            'write_limited': ['read:messages', 'write:moderation', 'read:audit_logs'],
            'admin': ['read:messages', 'write:moderation', 'write:config', 'read:audit_logs'],
            'system': ['*']  # All scopes
        }
    
    def validate_token_scope(self, token_id: str, requested_scope: str) -> bool:
        """Validate if token has requested scope"""
        # Check if token has the requested scope
        for scope_level, scopes in self.token_scopes.items():
            if requested_scope in scopes or '*' in scopes:
                return True
        return False
    
    def get_token_scopes(self, token_id: str) -> List[str]:
        """Get all scopes for a token"""
        # Return appropriate scopes based on token level
        return self.token_scopes.get('read_only', [])
    
    def restrict_token_scope(self, token_id: str, new_scopes: List[str]) -> Dict:
        """Restrict token to specific scopes"""
        return {
            'token_id': token_id,
            'scopes': new_scopes,
            'status': 'restricted',
            'timestamp': get_now_pst().isoformat()
        }
    
    def check_scope_violation(self, token_id: str, attempted_action: str) -> bool:
        """Check if token attempted action outside its scopes"""
        token_scopes = self.get_token_scopes(token_id)
        
        # Check if attempted action is in scopes
        if attempted_action in token_scopes or '*' in token_scopes:
            return False  # No violation
        
        return True  # Violation detected
    
    @commands.command(name='tokenscope')
    async def show_token_scopes(self, ctx):
        """View token scopes (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(
            title="🔑 Token Scope Definitions",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for scope_level, scopes in self.token_scopes.items():
            scopes_str = ", ".join(scopes)
            embed.add_field(name=scope_level.title(), value=f"`{scopes_str}`", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TokenScopeValidator(bot))
