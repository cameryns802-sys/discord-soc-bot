"""
AI Model Registry - Track models, versions, scopes, and risk levels
Part of AI Governance Framework
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class ModelRegistry(commands.Cog):
    """Track and manage AI models, versions, scopes, and risk levels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.registry_file = 'data/ai_model_registry.json'
        self.models = {}
        self.load_registry()
    
    def load_registry(self):
        """Load model registry from disk"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self.models = json.load(f)
            except:
                self.models = {}
        else:
            self.models = {}
    
    def save_registry(self):
        """Save model registry to disk"""
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.models, f, indent=2)
    
    def register_model(self, model_name: str, version: str, scope: str, 
                      risk_level: str, description: str = None) -> Dict:
        """Register a new AI model"""
        model_id = f"{model_name}:{version}"
        
        self.models[model_id] = {
            'name': model_name,
            'version': version,
            'scope': scope,  # local, guild, global
            'risk_level': risk_level,  # low, medium, high, critical
            'description': description,
            'registered_at': get_now_pst().isoformat(),
            'active': True,
            'usage_count': 0,
            'error_count': 0
        }
        
        self.save_registry()
        return self.models[model_id]
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID"""
        return self.models.get(model_id)
    
    def list_models_by_scope(self, scope: str) -> List[Dict]:
        """List all models for a given scope"""
        return [m for m in self.models.values() if m['scope'] == scope]
    
    def list_models_by_risk(self, risk_level: str) -> List[Dict]:
        """List all models at a given risk level"""
        return [m for m in self.models.values() if m['risk_level'] == risk_level]
    
    def deactivate_model(self, model_id: str):
        """Deactivate a model"""
        if model_id in self.models:
            self.models[model_id]['active'] = False
            self.save_registry()
    
    def increment_usage(self, model_id: str):
        """Track model usage"""
        if model_id in self.models:
            self.models[model_id]['usage_count'] += 1
            self.save_registry()
    
    def increment_errors(self, model_id: str):
        """Track model errors"""
        if model_id in self.models:
            self.models[model_id]['error_count'] += 1
            self.save_registry()
    
    @commands.command(name='modelregistry')
    async def view_registry(self, ctx):
        """View AI model registry"""
        if not self.models:
            await ctx.send("No models registered")
            return
        
        embed = discord.Embed(
            title="🧠 AI Model Registry",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for model_id, info in list(self.models.items())[:10]:
            status = "✅ Active" if info['active'] else "❌ Inactive"
            embed.add_field(
                name=f"{info['name']} v{info['version']}",
                value=f"Scope: {info['scope']} | Risk: {info['risk_level']} | {status}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModelRegistry(bot))
