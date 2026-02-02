"""
Custom Help Command with Enhanced Embeds
Provides categorized, paginated help with emoji indicators and detailed descriptions.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import os

class CustomHelp(commands.HelpCommand):
    """Custom help command with enhanced embeds and categorization"""
    
    def __init__(self):
        super().__init__(
            command_attrs={
                'help': 'Shows help about the bot, a command, or a category',
                'aliases': ['h']
            }
        )
        self.owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
    
    def get_command_signature(self, command):
        """Get command signature with prefix"""
        return f'!{command.qualified_name} {command.signature}'
    
    async def send_bot_help(self, mapping):
        """Send main help embed with all categories"""
        ctx = self.context
        
        embed = discord.Embed(
            title="🤖 SOC Bot Command Center",
            description="**Advanced Security Operations Center Bot**\n\nUse `!help <category>` for detailed commands\nUse `!help <command>` for specific command info",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Categorize cogs
        categories = {
            "🛡️ Core Infrastructure": [],
            "🚨 Incident Response": [],
            "🔍 Threat Intelligence": [],
            "📊 Analytics & Monitoring": [],
            "⚙️ Automation": [],
            "👥 Human Operations": [],
            "🔐 Security & Compliance": [],
            "🎯 Threat Hunting": [],
            "🔗 Integrations": [],
            "🛠️ Utilities": []
        }
        
        # Map cogs to categories
        category_mapping = {
            "SignalBusCog": "🛡️ Core Infrastructure",
            "FeatureFlagsCog": "🛡️ Core Infrastructure",
            "DataManager": "🛡️ Core Infrastructure",
            "HumanOverrideCog": "🛡️ Core Infrastructure",
            "AbstentionCog": "🛡️ Core Infrastructure",
            "PromptInjectionCog": "🛡️ Core Infrastructure",
            "OverrideDashboard": "🛡️ Core Infrastructure",
            "DynamicStatus": "🛡️ Core Infrastructure",
            
            "IncidentManagementCog": "🚨 Incident Response",
            "AlertManagementCog": "🚨 Incident Response",
            "DisasterRecoveryCog": "🚨 Incident Response",
            
            "ThreatIntelHub": "🔍 Threat Intelligence",
            "IOCManager": "🔍 Threat Intelligence",
            "ThreatHuntingCog": "🎯 Threat Hunting",
            
            "MLAnomalyDetector": "📊 Analytics & Monitoring",
            "ThreatScorer": "📊 Analytics & Monitoring",
            "WellnessCog": "👥 Human Operations",
            "OnCallManager": "👥 Human Operations",
            
            "AutomatedPlaybookExecutor": "⚙️ Automation",
            
            "Guardrails": "🔐 Security & Compliance",
            "ComplianceTools": "🔐 Security & Compliance",
            "ConsentAuditTrail": "🔐 Security & Compliance",
            "DataRetentionEnforcer": "🔐 Security & Compliance",
            "PIIDetectionCog": "🔐 Security & Compliance",
            
            "SlackIntegrationCog": "🔗 Integrations",
            
            "KnowledgeGraphCog": "📊 Analytics & Monitoring",
            "ChannelModeration": "🔐 Security & Compliance",
            "PermissionAudit": "🔐 Security & Compliance",
            "RoleAssignment": "🛠️ Utilities",
            "AdvancedWelcome": "🛠️ Utilities",
        }
        
        # Organize cogs into categories
        for cog, commands_from_mapping in mapping.items():
            # Handle both Cog objects and command lists
            if cog is None:
                # Commands without a cog
                filtered = await self.filter_commands(commands_from_mapping, sort=True)
                commands_list = list(filtered)
                if commands_list:
                    categories["🛠️ Utilities"].append(f"**No Category** ({len(commands_list)} commands)")
                continue
            
            cog_display_name = type(cog).__name__
            category = category_mapping.get(cog_display_name, "🛠️ Utilities")
            
            # Get command count - await filter_commands and convert to list
            filtered = await self.filter_commands(commands_from_mapping, sort=True)
            commands_list = list(filtered)
            if commands_list:
                categories[category].append(f"**{cog_display_name}** ({len(commands_list)} commands)")
        
        # Add categories to embed
        for category_name, cog_list in categories.items():
            if cog_list:
                value = "\n".join(cog_list[:5])  # Limit to 5 per category
                if len(cog_list) > 5:
                    value += f"\n... and {len(cog_list) - 5} more"
                embed.add_field(name=category_name, value=value, inline=False)
        
        # Add footer - count all commands
        total_commands = 0
        for commands in mapping.values():
            filtered = await self.filter_commands(commands, sort=True)
            total_commands += len(list(filtered))
        
        embed.set_footer(text=f"Total Commands: {total_commands} | Prefix: ! | Use !help <category> for details")
        
        await ctx.send(embed=embed)
    
    async def send_cog_help(self, cog):
        """Send help for a specific cog/category"""
        ctx = self.context
        
        embed = discord.Embed(
            title=f"📋 {cog.qualified_name} Commands",
            description=cog.description or "No description available",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        # Get filtered commands - await and convert to list
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        filtered_commands = list(filtered)
        
        for command in filtered_commands:
            # Check if owner-only
            is_owner_only = any('owner only' in line.lower() for line in (command.help or '').split('\n'))
            owner_badge = " 👑" if is_owner_only else ""
            
            embed.add_field(
                name=f"`!{command.name}`{owner_badge}",
                value=command.short_doc or "No description",
                inline=False
            )
        
        embed.set_footer(text=f"{len(filtered_commands)} commands | Use !help <command> for detailed info")
        
        await ctx.send(embed=embed)
    
    async def send_command_help(self, command):
        """Send help for a specific command"""
        ctx = self.context
        
        # Check if owner-only
        is_owner_only = any('owner only' in line.lower() for line in (command.help or '').split('\n'))
        
        embed = discord.Embed(
            title=f"{'👑 ' if is_owner_only else ''}Command: {command.name}",
            description=command.help or "No description available",
            color=discord.Color.gold() if is_owner_only else discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Usage
        embed.add_field(
            name="📝 Usage",
            value=f"`{self.get_command_signature(command)}`",
            inline=False
        )
        
        # Aliases
        if command.aliases:
            embed.add_field(
                name="🔗 Aliases",
                value=", ".join(f"`!{alias}`" for alias in command.aliases),
                inline=False
            )
        
        # Cooldown
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{cooldown.rate} use(s) per {cooldown.per}s",
                inline=True
            )
        
        # Category
        if command.cog:
            embed.add_field(
                name="📦 Category",
                value=command.cog.qualified_name,
                inline=True
            )
        
        # Owner only badge
        if is_owner_only:
            embed.add_field(
                name="🔒 Permissions",
                value="Owner Only",
                inline=True
            )
        
        embed.set_footer(text="Tip: Arguments in <> are required, [] are optional")
        
        await ctx.send(embed=embed)
    
    async def send_group_help(self, group):
        """Send help for a command group"""
        ctx = self.context
        
        embed = discord.Embed(
            title=f"📚 Command Group: {group.name}",
            description=group.help or "No description available",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        # Usage
        embed.add_field(
            name="📝 Usage",
            value=f"`{self.get_command_signature(group)}`",
            inline=False
        )
        
        # Subcommands
        filtered = await self.filter_commands(group.commands, sort=True)
        filtered_commands = list(filtered)
        if filtered_commands:
            subcommands_list = "\n".join(
                f"`!{group.name} {cmd.name}` - {cmd.short_doc or 'No description'}"
                for cmd in filtered_commands
            )
            embed.add_field(
                name="📋 Subcommands",
                value=subcommands_list,
                inline=False
            )
        
        embed.set_footer(text=f"Use !help {group.name} <subcommand> for more info")
        
        await ctx.send(embed=embed)
    
    async def send_error_message(self, error):
        """Send error message when help fails"""
        ctx = self.context
        
        embed = discord.Embed(
            title="❌ Help Error",
            description=str(error),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Use `!help` to see all categories\n"
                  "• Use `!help <category>` to see category commands\n"
                  "• Use `!help <command>` for command details",
            inline=False
        )
        
        await ctx.send(embed=embed)

class CustomHelpCog(commands.Cog):
    """Custom help command handler"""
    
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelp()
        bot.help_command.cog = self
    
    def cog_unload(self):
        """Restore original help command on unload"""
        self.bot.help_command = self._original_help_command

async def setup(bot):
    await bot.add_cog(CustomHelpCog(bot))
