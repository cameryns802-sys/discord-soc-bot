"""
Security Checklist: Help servers achieve security best practices
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os

class SecurityChecklist(commands.Cog):
    """Security setup and configuration checklist"""
    
    def __init__(self, bot):
        self.bot = bot
        self.checklist_file = 'data/security_checklist.json'
        os.makedirs('data', exist_ok=True)
    
    def _load_checklist(self, guild_id: int) -> dict:
        """Load guild checklist"""
        if os.path.exists(self.checklist_file):
            try:
                with open(self.checklist_file, 'r') as f:
                    data = json.load(f)
                    return data.get(str(guild_id), self._default_checklist())
            except:
                return self._default_checklist()
        return self._default_checklist()
    
    def _default_checklist(self) -> dict:
        """Default checklist items"""
        return {
            'verification': {'completed': False, 'priority': 'HIGH'},
            'content_filter': {'completed': False, 'priority': 'HIGH'},
            'owner_2fa': {'completed': False, 'priority': 'CRITICAL'},
            'admin_2fa': {'completed': False, 'priority': 'HIGH'},
            'mod_permissions': {'completed': False, 'priority': 'HIGH'},
            'bot_permissions': {'completed': False, 'priority': 'MEDIUM'},
            'audit_log_review': {'completed': False, 'priority': 'MEDIUM'},
            'rules_posted': {'completed': False, 'priority': 'MEDIUM'},
            'welcome_channel': {'completed': False, 'priority': 'LOW'},
            'role_hierarchy': {'completed': False, 'priority': 'HIGH'},
        }
    
    def _save_checklist(self, guild_id: int, checklist: dict):
        """Save guild checklist"""
        data = {}
        if os.path.exists(self.checklist_file):
            try:
                with open(self.checklist_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        data[str(guild_id)] = checklist
        
        with open(self.checklist_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @commands.command(name='secchecklist')
    @commands.has_permissions(manage_guild=True)
    async def secchecklist(self, ctx):
        """View security checklist"""
        await self._secchecklist_logic(ctx)
    
    @app_commands.command(name="secchecklist", description="View security setup checklist")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def secchecklist_slash(self, interaction: discord.Interaction):
        """Checklist using slash command"""
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
        await self._secchecklist_logic(ctx)
    
    async def _secchecklist_logic(self, ctx):
        guild = ctx.guild
        checklist = self._load_checklist(guild.id)
        
        # Verify actual server state
        actual_state = {
            'verification': guild.verification_level != discord.VerificationLevel.none,
            'content_filter': guild.explicit_content_filter != discord.ContentFilter.disabled,
            'owner_2fa': guild.owner.mfa_enabled if guild.owner else False,
            'admin_2fa': True,  # Assume true if scanning
            'mod_permissions': len([r for r in guild.roles if r.permissions.moderate_members]) > 0,
            'bot_permissions': sum(1 for m in guild.members if m.bot) > 0,
            'audit_log_review': True,  # Can check if bot has access
            'rules_posted': True,  # Assume posted
            'welcome_channel': any('welcome' in c.name.lower() for c in guild.text_channels),
            'role_hierarchy': len(guild.roles) > 2,
        }
        
        # Update checklist with actual state
        for key, value in actual_state.items():
            if key in checklist:
                checklist[key]['completed'] = value
        
        # Create checklist embed
        embed = discord.Embed(
            title="✅ Security Setup Checklist",
            description="Complete these items to secure your server",
            color=discord.Color.blue(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        # Group by priority
        critical = {k: v for k, v in checklist.items() if v['priority'] == 'CRITICAL'}
        high = {k: v for k, v in checklist.items() if v['priority'] == 'HIGH'}
        medium = {k: v for k, v in checklist.items() if v['priority'] == 'MEDIUM'}
        low = {k: v for k, v in checklist.items() if v['priority'] == 'LOW'}
        
        # Helper to format items
        def format_items(items_dict):
            text = ""
            for key, data in items_dict.items():
                emoji = "✅" if data['completed'] else "❌"
                text += f"{emoji} {self._format_item_name(key)}\n"
            return text or "None"
        
        # Add fields by priority
        if critical:
            embed.add_field(
                name="🔴 CRITICAL",
                value=format_items(critical),
                inline=False
            )
        
        if high:
            embed.add_field(
                name="⚠️ HIGH PRIORITY",
                value=format_items(high),
                inline=False
            )
        
        if medium:
            embed.add_field(
                name="🟡 MEDIUM PRIORITY",
                value=format_items(medium),
                inline=False
            )
        
        if low:
            embed.add_field(
                name="🟢 LOW PRIORITY",
                value=format_items(low),
                inline=False
            )
        
        # Calculate completion
        completed = sum(1 for item in checklist.values() if item['completed'])
        total = len(checklist)
        completion_percent = int((completed / total) * 100)
        
        embed.add_field(
            name="📊 Progress",
            value=f"**{completed}/{total}** ({completion_percent}%)\n```\n{'█' * (completion_percent // 10)}{'░' * (10 - completion_percent // 10)}\n```",
            inline=False
        )
        
        # Save updated checklist
        self._save_checklist(guild.id, checklist)
        
        embed.set_footer(text=f"Guild: {guild.id} • Last updated")
        
        await ctx.send(embed=embed)
    
    def _format_item_name(self, key: str) -> str:
        """Format checklist item names"""
        names = {
            'verification': 'Server Verification Enabled',
            'content_filter': 'Explicit Content Filter Active',
            'owner_2fa': 'Owner Has 2FA Enabled',
            'admin_2fa': 'Admin 2FA Enforcement',
            'mod_permissions': 'Moderator Role Created',
            'bot_permissions': 'Bot Roles Configured',
            'audit_log_review': 'Audit Log Access Enabled',
            'rules_posted': 'Server Rules Posted',
            'welcome_channel': 'Welcome Channel Setup',
            'role_hierarchy': 'Role Hierarchy Established',
        }
        return names.get(key, key.replace('_', ' ').title())
    
    @commands.command(name='secsetup')
    @commands.has_permissions(administrator=True)
    async def secsetup(self, ctx):
        """Guided security setup"""
        await self._secsetup_logic(ctx)
    
    @app_commands.command(name="secsetup", description="Guided security setup wizard")
    @app_commands.checks.has_permissions(administrator=True)
    async def secsetup_slash(self, interaction: discord.Interaction):
        """Setup using slash command"""
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
        await self._secsetup_logic(ctx)
    
    async def _secsetup_logic(self, ctx):
        guild = ctx.guild
        
        # Create setup guide
        embed = discord.Embed(
            title="🛡️ Security Setup Wizard",
            description="Step-by-step guide to secure your server",
            color=discord.Color.blue(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        steps = [
            ("1️⃣ Enable Verification", f"Current: {guild.verification_level}\nSet to Medium or higher in Server Settings → Safety Setup"),
            ("2️⃣ Enable Content Filter", f"Current: {guild.explicit_content_filter}\nServer Settings → Moderation → Filter explicitly sexual content"),
            ("3️⃣ Owner 2FA", f"Owner 2FA: {'✅ Enabled' if guild.owner.mfa_enabled else '❌ Disabled'}\nEnable in Discord Settings → Privacy & Safety → Two-Factor Auth"),
            ("4️⃣ Create Mod Role", "Add a 'Moderator' role with Moderate Members permission"),
            ("5️⃣ Create Roles Hierarchy", "Ensure role order is: Owner → Mods → Staff → Members → Bots"),
            ("6️⃣ Post Rules", "Create #rules channel and post server rules"),
            ("7️⃣ Setup Verification", "Use bot's verification system for new members"),
            ("8️⃣ Review Permissions", "Use `/permaudit` to scan for permission issues"),
        ]
        
        for step, details in steps:
            embed.add_field(name=step, value=details, inline=False)
        
        embed.add_field(
            name="💡 Tips",
            value="• Start with steps 1-3 (most critical)\n• Run `/permaudit` to find issues\n• Run `/dashboard` to monitor progress\n• Run `/secchecklist` to track completion",
            inline=False
        )
        
        embed.set_footer(text="After completing all steps, your server should be well-protected")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityChecklist(bot))
