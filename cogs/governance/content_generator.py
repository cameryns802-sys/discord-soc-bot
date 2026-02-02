"""
Content Generator: Generate server rules, Terms of Service, and community guidelines
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional, List
import json
import os

DEFAULT_RULES = [
    "Be respectful to all members",
    "No spamming or flooding the chat",
    "No hate speech, harassment, or discrimination",
    "No NSFW or inappropriate content",
    "No advertising or self-promotion without permission",
    "Follow Discord's Terms of Service",
    "Protect your personal information and privacy",
    "Report suspicious or harmful behavior to staff",
    "No impersonation of staff or other users",
    "Use appropriate channels for different topics"
]

COMMUNITY_GUIDELINES = [
    "Treat everyone with respect and kindness",
    "Help create a welcoming environment for new members",
    "Think before you post - consider how others might interpret your words",
    "Respect different opinions and engage in constructive discussions",
    "Use content warnings when discussing sensitive topics",
    "Don't share personal information about yourself or others",
    "Report violations to moderators instead of escalating conflicts",
    "Follow channel-specific rules and topics",
    "Don't backseat moderate - let the staff handle rule enforcement",
    "Have fun and enjoy the community!"
]

class ContentGenerator(commands.Cog):
    """Generate server rules, ToS, and community guidelines"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.rules_file = os.path.join(self.data_dir, "server_rules.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.server_rules = self._load_rules()
    
    def _load_rules(self):
        """Load server rules from file"""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_rules(self):
        """Save server rules to file"""
        with open(self.rules_file, 'w') as f:
            json.dump(self.server_rules, f, indent=2)
    
    # ==================== GENERATE RULES ====================
    
    @commands.command(name='generaterules')
    @commands.has_permissions(administrator=True)
    async def generaterules(self, ctx, style: str = "default"):
        """Generate server rules"""
        await self._generaterules_logic(ctx, style)
    
    @app_commands.command(name="generaterules", description="Generate comprehensive server rules")
    @app_commands.describe(style="Style: default, strict, casual, gaming, professional")
    @app_commands.checks.has_permissions(administrator=True)
    async def generaterules_slash(self, interaction: discord.Interaction, style: str = "default"):
        """Generate rules using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._generaterules_logic(ctx, style)
    
    async def _generaterules_logic(self, ctx, style: str):
        style = style.lower()
        
        # Select rules based on style
        if style == "strict":
            rules = DEFAULT_RULES + [
                "Violations will result in immediate action",
                "No second chances for serious violations",
                "All conversations are monitored by moderation team"
            ]
        elif style == "casual":
            rules = [
                "Be chill and respectful",
                "Don't spam - nobody likes that",
                "Keep it friendly and fun",
                "NSFW stuff stays out",
                "Listen to the mods when they speak up",
                "Use common sense"
            ]
        elif style == "gaming":
            rules = [
                "Respect your fellow gamers",
                "No cheating or game exploits discussion",
                "Keep voice channels clear during raids/matches",
                "No spoilers without warnings",
                "Share tips but don't backseat game",
                "GG means GG - stay sportsmanlike",
                "No toxic behavior or rage-quitting drama"
            ] + DEFAULT_RULES[:5]
        elif style == "professional":
            rules = [
                "Maintain professional conduct at all times",
                "Share knowledge and expertise constructively",
                "Respect intellectual property and confidentiality",
                "Use appropriate language and tone",
                "Network respectfully - no aggressive self-promotion",
                "Keep discussions on-topic and productive",
                "Follow industry standards and best practices"
            ]
        else:  # default
            rules = DEFAULT_RULES
        
        # Save to guild
        guild_key = str(ctx.guild.id)
        self.server_rules[guild_key] = {
            'rules': rules,
            'style': style,
            'generated_at': datetime.now(datetime.UTC).isoformat(),
            'generated_by': ctx.author.id
        }
        self._save_rules()
        
        # Create embed
        embed = discord.Embed(
            title=f"📋 {ctx.guild.name} - Server Rules",
            description=f"Generated in **{style}** style",
            color=discord.Color.blue(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        for i, rule in enumerate(rules[:15], 1):  # Max 15 rules
            embed.add_field(
                name=f"Rule {i}",
                value=rule,
                inline=False
            )
        
        embed.set_footer(text=f"Generated by {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==================== GENERATE TOS ====================
    
    @commands.command(name='generatetos')
    @commands.has_permissions(administrator=True)
    async def generatetos(self, ctx):
        """Generate Terms of Service"""
        await self._generatetos_logic(ctx)
    
    @app_commands.command(name="generatetos", description="Generate server Terms of Service")
    @app_commands.checks.has_permissions(administrator=True)
    async def generatetos_slash(self, interaction: discord.Interaction):
        """Generate ToS using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._generatetos_logic(ctx)
    
    async def _generatetos_logic(self, ctx):
        guild_key = str(ctx.guild.id)
        
        # Get current rules or use defaults
        rules = DEFAULT_RULES
        if guild_key in self.server_rules:
            rules = self.server_rules[guild_key]['rules']
        
        embed = discord.Embed(
            title=f"📜 {ctx.guild.name} - Terms of Service",
            description="By using this server, you agree to the following terms:",
            color=discord.Color.gold(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        # Terms sections
        embed.add_field(
            name="1️⃣ Agreement",
            value="By joining and participating in this server, you acknowledge that you have read, understood, and agree to abide by these Terms of Service and Discord's Terms of Service.",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ Server Rules",
            value=f"All members must follow the {len(rules)} server rules. Use `/generaterules` to view them. Violations may result in warnings, timeouts, kicks, or bans.",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ Content Policy",
            value="All content shared in this server must comply with Discord's Terms of Service and Community Guidelines. NSFW, illegal, or harmful content is strictly prohibited.",
            inline=False
        )
        
        embed.add_field(
            name="4️⃣ Privacy & Data",
            value="Your messages and activity in this server may be logged for moderation purposes. Do not share personal information. We respect your privacy and follow Discord's privacy policy.",
            inline=False
        )
        
        embed.add_field(
            name="5️⃣ Moderation",
            value="Moderators have the final say on all matters. Arguing with moderators or attempting to circumvent punishments will result in additional action.",
            inline=False
        )
        
        embed.add_field(
            name="6️⃣ Appeals",
            value="If you believe you were punished unfairly, you may submit an appeal using `/appeal`. Appeals are reviewed by senior moderators.",
            inline=False
        )
        
        embed.add_field(
            name="7️⃣ Changes",
            value="These terms may be updated at any time. Continued use of the server after updates constitutes acceptance of the new terms.",
            inline=False
        )
        
        embed.add_field(
            name="8️⃣ Termination",
            value="We reserve the right to remove any user from this server at any time for any reason, including violation of these terms or Discord's ToS.",
            inline=False
        )
        
        embed.set_footer(text=f"Generated by {ctx.author.name} • Last Updated")
        
        await ctx.send(embed=embed)
    
    # ==================== GENERATE GUIDELINES ====================
    
    @commands.command(name='generateguidelines')
    @commands.has_permissions(administrator=True)
    async def generateguidelines(self, ctx):
        """Generate community guidelines"""
        await self._generateguidelines_logic(ctx)
    
    @app_commands.command(name="generateguidelines", description="Generate community guidelines")
    @app_commands.checks.has_permissions(administrator=True)
    async def generateguidelines_slash(self, interaction: discord.Interaction):
        """Generate guidelines using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._generateguidelines_logic(ctx)
    
    async def _generateguidelines_logic(self, ctx):
        embed = discord.Embed(
            title=f"🤝 {ctx.guild.name} - Community Guidelines",
            description="These guidelines help create a positive and welcoming environment for everyone",
            color=discord.Color.green(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        for i, guideline in enumerate(COMMUNITY_GUIDELINES, 1):
            embed.add_field(
                name=f"{i}. {guideline.split('-')[0] if '-' in guideline else guideline[:30]}",
                value=guideline,
                inline=False
            )
        
        embed.add_field(
            name="💡 Remember",
            value="These are guidelines, not strict rules. Use common sense and be excellent to each other!",
            inline=False
        )
        
        embed.set_footer(text=f"Generated by {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    # ==================== ADD CUSTOM RULE ====================
    
    @commands.command(name='addrule')
    @commands.has_permissions(administrator=True)
    async def addrule(self, ctx, *, rule: str):
        """Add a custom rule"""
        await self._addrule_logic(ctx, rule)
    
    @app_commands.command(name="addrule", description="Add a custom rule to server rules")
    @app_commands.describe(rule="The rule text to add")
    @app_commands.checks.has_permissions(administrator=True)
    async def addrule_slash(self, interaction: discord.Interaction, rule: str):
        """Add rule using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._addrule_logic(ctx, rule)
    
    async def _addrule_logic(self, ctx, rule: str):
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.server_rules:
            self.server_rules[guild_key] = {
                'rules': DEFAULT_RULES.copy(),
                'style': 'default',
                'generated_at': datetime.now(datetime.UTC).isoformat(),
                'generated_by': ctx.author.id
            }
        
        self.server_rules[guild_key]['rules'].append(rule)
        self._save_rules()
        
        embed = discord.Embed(
            title="✅ Rule Added",
            description=f"Rule #{len(self.server_rules[guild_key]['rules'])}",
            color=discord.Color.green(),
            timestamp=datetime.now(datetime.UTC)
        )
        embed.add_field(name="New Rule", value=rule, inline=False)
        embed.add_field(name="Added by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Total Rules", value=str(len(self.server_rules[guild_key]['rules'])), inline=True)
        
        await ctx.send(embed=embed)
    
    # ==================== REMOVE RULE ====================
    
    @commands.command(name='removerule')
    @commands.has_permissions(administrator=True)
    async def removerule(self, ctx, rule_number: int):
        """Remove a rule by number"""
        await self._removerule_logic(ctx, rule_number)
    
    @app_commands.command(name="removerule", description="Remove a rule by its number")
    @app_commands.describe(rule_number="Rule number to remove (1-based)")
    @app_commands.checks.has_permissions(administrator=True)
    async def removerule_slash(self, interaction: discord.Interaction, rule_number: int):
        """Remove rule using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._removerule_logic(ctx, rule_number)
    
    async def _removerule_logic(self, ctx, rule_number: int):
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.server_rules:
            await ctx.send("❌ No rules found. Use `/generaterules` first.")
            return
        
        rules = self.server_rules[guild_key]['rules']
        
        if rule_number < 1 or rule_number > len(rules):
            await ctx.send(f"❌ Invalid rule number. Must be between 1 and {len(rules)}")
            return
        
        removed_rule = rules.pop(rule_number - 1)
        self._save_rules()
        
        embed = discord.Embed(
            title="🗑️ Rule Removed",
            description=f"Rule #{rule_number} has been removed",
            color=discord.Color.orange(),
            timestamp=datetime.now(datetime.UTC)
        )
        embed.add_field(name="Removed Rule", value=removed_rule, inline=False)
        embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Remaining Rules", value=str(len(rules)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ContentGenerator(bot))
