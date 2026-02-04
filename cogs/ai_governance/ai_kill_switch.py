"""
AI Kill Switch - Instant global or per-module AI shutdown capability
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class AIKillSwitch(commands.Cog):
    """Emergency shutdown capability for AI systems"""
    
    def __init__(self, bot):
        self.bot = bot
        self.state_file = 'data/ai_kill_switch_state.json'
        self.global_enabled = True
        self.module_states = {}  # module_name: enabled
        self.load_state()
    
    def load_state(self):
        """Load kill switch state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.global_enabled = data.get('global_enabled', True)
                    self.module_states = data.get('module_states', {})
            except:
                pass
    
    def save_state(self):
        """Save kill switch state"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'global_enabled': self.global_enabled,
                'module_states': self.module_states,
                'last_updated': get_now_pst().isoformat()
            }, f, indent=2)
    
    async def global_shutdown(self, reason: str = "Emergency shutdown"):
        """Disable ALL AI systems immediately"""
        self.global_enabled = False
        self.save_state()
        
        # Log shutdown
        print(f"🛑 AI GLOBAL KILL SWITCH ACTIVATED: {reason}")
    
    async def global_restart(self, reason: str = "Resume normal operation"):
        """Re-enable all AI systems"""
        self.global_enabled = True
        self.save_state()
        
        print(f"✅ AI GLOBAL KILL SWITCH RELEASED: {reason}")
    
    async def module_shutdown(self, module_name: str):
        """Disable a specific AI module"""
        self.module_states[module_name] = False
        self.save_state()
    
    async def module_restart(self, module_name: str):
        """Re-enable a specific AI module"""
        self.module_states[module_name] = True
        self.save_state()
    
    def is_enabled(self, module_name: str = None) -> bool:
        """Check if AI is enabled"""
        if not self.global_enabled:
            return False
        
        if module_name:
            return self.module_states.get(module_name, True)
        
        return True
    
    @commands.command(name='aikillswitch')
    async def kill_switch_cmd(self, ctx, action: str = 'status'):
        """Control AI kill switch (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        if action == 'shutdown':
            await self.global_shutdown("Owner initiated shutdown")
            await ctx.send("🛑 AI GLOBAL KILL SWITCH ACTIVATED")
        
        elif action == 'restart':
            await self.global_restart("Owner initiated restart")
            await ctx.send("✅ AI systems resumed")
        
        else:  # status
            embed = discord.Embed(
                title="🔌 AI Kill Switch Status",
                color=discord.Color.red() if not self.global_enabled else discord.Color.green(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Global Status", 
                          value="🛑 DISABLED" if not self.global_enabled else "✅ ENABLED",
                          inline=True)
            
            if self.module_states:
                disabled_modules = [m for m, enabled in self.module_states.items() if not enabled]
                embed.add_field(name="Disabled Modules", 
                              value=", ".join(disabled_modules) if disabled_modules else "None",
                              inline=False)
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIKillSwitch(bot))
