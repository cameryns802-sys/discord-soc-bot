"""Feature Flags & Kill Switch System - Safe Mode & Graceful Degradation"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, Set
from cogs.core.pst_timezone import get_now_pst

class FeatureFlags:
    """Centralized feature flag management"""
    def __init__(self):
        self.flags_file = "data/feature_flags.json"
        self.flags: Dict[str, Dict] = {
            # Experimental features (default OFF)
            'predictive_moderation': {'enabled': False, 'reason': 'Experimental'},
            'ml_anomaly_detection': {'enabled': False, 'reason': 'Experimental'},
            'generative_responses': {'enabled': False, 'reason': 'Experimental'},
            'red_team_simulation': {'enabled': False, 'reason': 'Experimental'},
            
            # Advanced features (default ON but killable)
            'threat_hunting': {'enabled': True, 'reason': 'Operational'},
            'incident_auto_response': {'enabled': True, 'reason': 'Operational'},
            'pii_auto_detection': {'enabled': True, 'reason': 'Operational'},
            
            # Core features (always ON)
            'automod': {'enabled': True, 'reason': 'Core'},
            'compliance_monitoring': {'enabled': True, 'reason': 'Core'},
            'security_baseline': {'enabled': True, 'reason': 'Core'},
        }
        self.killed_features: Set[str] = set()
        self.safe_mode = False
        self.load_flags()
    
    def load_flags(self):
        """Load flags from disk"""
        if os.path.exists(self.flags_file):
            try:
                with open(self.flags_file, 'r') as f:
                    data = json.load(f)
                    self.flags.update(data.get('flags', {}))
                    self.killed_features = set(data.get('killed', []))
                    self.safe_mode = data.get('safe_mode', False)
            except:
                pass
    
    def save_flags(self):
        """Save flags to disk"""
        os.makedirs(os.path.dirname(self.flags_file), exist_ok=True)
        with open(self.flags_file, 'w') as f:
            json.dump({
                'flags': self.flags,
                'killed': list(self.killed_features),
                'safe_mode': self.safe_mode,
                'updated_at': get_now_pst().isoformat()
            }, f, indent=2)
    
    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        if self.safe_mode and feature not in ['automod', 'compliance_monitoring', 'security_baseline']:
            return False
        if feature in self.killed_features:
            return False
        return self.flags.get(feature, {}).get('enabled', False)
    
    def enable_feature(self, feature: str, reason: str = ""):
        """Enable a feature"""
        if feature in self.flags:
            self.flags[feature]['enabled'] = True
            if reason:
                self.flags[feature]['reason'] = reason
            self.killed_features.discard(feature)
            self.save_flags()
            return True
        return False
    
    def disable_feature(self, feature: str, reason: str = ""):
        """Disable a feature"""
        if feature in ['automod', 'compliance_monitoring', 'security_baseline']:
            return False  # Cannot disable core features
        if feature in self.flags:
            self.flags[feature]['enabled'] = False
            if reason:
                self.flags[feature]['reason'] = reason
            self.save_flags()
            return True
        return False
    
    def kill_feature(self, feature: str) -> bool:
        """Kill a feature (emergency stop)"""
        if feature in ['automod', 'compliance_monitoring', 'security_baseline']:
            return False  # Cannot kill core features
        self.killed_features.add(feature)
        self.save_flags()
        return True
    
    def revive_feature(self, feature: str) -> bool:
        """Revive a killed feature"""
        if feature in self.killed_features:
            self.killed_features.discard(feature)
            self.save_flags()
            return True
        return False
    
    def enable_safe_mode(self):
        """Enable safe mode - only core features"""
        self.safe_mode = True
        self.save_flags()
    
    def disable_safe_mode(self):
        """Disable safe mode"""
        self.safe_mode = False
        self.save_flags()
    
    def get_status(self) -> Dict:
        """Get current flag status"""
        return {
            'safe_mode': self.safe_mode,
            'flags': self.flags,
            'killed_features': list(self.killed_features)
        }

# Global flags instance
flags = FeatureFlags()

class FeatureFlagsCog(commands.Cog):
    """Feature flag management commands"""
    def __init__(self, bot):
        self.bot = bot
        self.flags = flags
    
    @commands.command(name="flags")
    @commands.is_owner()
    async def show_flags(self, ctx):
        """Show all feature flags"""
        status = self.flags.get_status()
        embed = discord.Embed(title="🚩 Feature Flags", color=discord.Color.blue())
        embed.add_field(name="Safe Mode", value="🔴 ON" if status['safe_mode'] else "🟢 OFF", inline=False)
        
        enabled = [f for f, d in status['flags'].items() if d['enabled']]
        disabled = [f for f, d in status['flags'].items() if not d['enabled']]
        
        if enabled:
            embed.add_field(name="🟢 Enabled", value="\n".join(enabled), inline=False)
        if disabled:
            embed.add_field(name="🔴 Disabled", value="\n".join(disabled), inline=False)
        if status['killed_features']:
            embed.add_field(name="💀 Killed (Emergency)", value="\n".join(status['killed_features']), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="killfeature")
    @commands.is_owner()
    async def kill_feature(self, ctx, feature: str):
        """Emergency kill a feature"""
        if self.flags.kill_feature(feature):
            await ctx.send(f"💀 {feature} KILLED (emergency stop activated)")
        else:
            await ctx.send(f"❌ Cannot kill {feature} (core feature or doesn't exist)")
    
    @commands.command(name="safemode")
    @commands.is_owner()
    async def safe_mode(self, ctx, mode: str = "status"):
        """Enable/disable safe mode"""
        if mode == "on":
            self.flags.enable_safe_mode()
            await ctx.send("🔴 SAFE MODE ENABLED - Only core features active")
        elif mode == "off":
            self.flags.disable_safe_mode()
            await ctx.send("🟢 SAFE MODE DISABLED - All features restored")
        else:
            status = "🔴 ON" if self.flags.safe_mode else "🟢 OFF"
            await ctx.send(f"Safe Mode: {status}")

async def setup(bot):
    await bot.add_cog(FeatureFlagsCog(bot))
    print(f"[FeatureFlags] ✅ Feature flag system initialized")
