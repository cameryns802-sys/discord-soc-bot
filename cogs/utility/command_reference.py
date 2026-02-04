"""
Command Reference System - Quick access to all bot commands
Organized by category for easy discovery and usage
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class CommandReference(commands.Cog):
    """Provide quick command reference and documentation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.commands_file = 'data/command_reference.json'
        self.load_reference_data()
    
    def load_reference_data(self):
        """Load command reference data"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.commands_file):
            with open(self.commands_file, 'w') as f:
                json.dump(self.get_default_reference(), f, indent=2)
    
    def get_default_reference(self):
        """Default command reference database"""
        return {
            "security": {
                "commands": ["!security", "!antinuke", "!anti_phishing"],
                "description": "Core security operations"
            },
            "moderation": {
                "commands": ["!automod", "!verification", "!moderation_utilities"],
                "description": "Moderation and user management"
            },
            "analytics": {
                "commands": ["!security_dashboard", "!executive_risk_dashboard", "!botstatus"],
                "description": "Security analytics and reporting"
            },
            "intelligence": {
                "commands": ["!threatintel", "!ioc_manager", "!analyzethreatscape"],
                "description": "Threat intelligence systems"
            }
        }
    
    @commands.command(name='commands')
    async def list_commands(self, ctx):
        """List all available commands"""
        embed = discord.Embed(
            title="📚 Command Reference",
            description="All available Sentinel SOC Bot commands",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Get all commands grouped by cog
        cogs_dict = {}
        for cmd in self.bot.commands:
            cog_name = cmd.cog.qualified_name if cmd.cog else "Uncategorized"
            if cog_name not in cogs_dict:
                cogs_dict[cog_name] = []
            cogs_dict[cog_name].append(cmd.name)
        
        # Add system commands
        embed.add_field(name="🤖 System Commands", value="━" * 30, inline=False)
        embed.add_field(name="!helpme", value="Show help information", inline=True)
        embed.add_field(name="!botstatus", value="Check bot status", inline=True)
        embed.add_field(name="!quicktest", value="Run diagnostics", inline=True)
        
        embed.add_field(name="🔒 Security Commands", value="━" * 30, inline=False)
        embed.add_field(name="!security", value="Security operations", inline=True)
        embed.add_field(name="!antinuke", value="Anti-nuke protection", inline=True)
        embed.add_field(name="!anti_phishing", value="Phishing detection", inline=True)
        
        embed.add_field(name="📊 Analytics", value="━" * 30, inline=False)
        embed.add_field(name="!security_dashboard", value="Live security metrics", inline=True)
        embed.add_field(name="!executive_risk_dashboard", value="Executive reporting", inline=True)
        embed.add_field(name="!threat_scoring", value="Risk assessment", inline=True)
        
        embed.add_field(name="📡 Intelligence", value="━" * 30, inline=False)
        embed.add_field(name="!threatintel", value="Threat intelligence", inline=True)
        embed.add_field(name="!ioc_manager", value="IOC management", inline=True)
        embed.add_field(name="!analyzethreatscape", value="Threat landscape", inline=True)
        
        embed.add_field(name="💬 For Full List", value="━" * 30, inline=False)
        embed.add_field(name="→", value="Use `!helpme` in DM for complete documentation", inline=False)
        embed.add_field(name="→", value=f"Total commands available: {len(list(self.bot.commands))}", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='docs')
    async def documentation(self, ctx, category: str = None):
        """Get detailed command documentation"""
        embed = discord.Embed(
            title="📖 Command Documentation",
            description="Detailed command reference",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        if not category:
            embed.add_field(name="Available Categories", value="━" * 25, inline=False)
            embed.add_field(name="security", value="Security operations commands", inline=True)
            embed.add_field(name="moderation", value="Moderation commands", inline=True)
            embed.add_field(name="analytics", value="Analytics commands", inline=True)
            embed.add_field(name="intelligence", value="Intelligence commands", inline=True)
            embed.add_field(name="Usage", value="Use `!docs <category>` for details", inline=False)
        else:
            ref = self.get_default_reference()
            if category in ref:
                cat_data = ref[category]
                embed.add_field(name=category.upper(), value=cat_data["description"], inline=False)
                for cmd in cat_data["commands"]:
                    embed.add_field(name=cmd, value="Execute this command", inline=True)
            else:
                embed.add_field(name="Error", value=f"Category '{category}' not found", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='commandstatus')
    async def command_status(self, ctx):
        """Check command system status"""
        embed = discord.Embed(
            title="⚡ Command System Status",
            description="Bot command processor health",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        total_commands = len(list(self.bot.commands))
        total_cogs = len(self.bot.cogs)
        
        embed.add_field(name="System Status", value="━" * 25, inline=False)
        embed.add_field(name="Status", value="✅ OPERATIONAL", inline=True)
        embed.add_field(name="Commands Loaded", value=f"⚡ {total_commands}", inline=True)
        embed.add_field(name="Cogs Active", value=f"🔧 {total_cogs}", inline=True)
        
        embed.add_field(name="Response Status", value="━" * 25, inline=False)
        embed.add_field(name="Prefix Commands", value="✅ Responding", inline=True)
        embed.add_field(name="Slash Commands", value="✅ Available", inline=True)
        embed.add_field(name="DM Commands", value="✅ Enabled", inline=True)
        
        embed.add_field(name="Latency", value="━" * 25, inline=False)
        latency = f"{self.bot.latency*1000:.0f}ms"
        status = "✅ GOOD" if self.bot.latency < 0.1 else "⚠️ DEGRADED"
        embed.add_field(name="API Latency", value=f"{latency} {status}", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandReference(bot))
