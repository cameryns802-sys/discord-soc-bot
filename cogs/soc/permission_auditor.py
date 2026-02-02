"""
Permission Auditor: Scan for and report permission misconfigurations
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class PermissionAuditor(commands.Cog):
    """Audit server permissions for security issues"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='permaudit')
    @commands.has_permissions(manage_roles=True)
    async def permaudit(self, ctx):
        """Audit server permissions"""
        await self._permaudit_logic(ctx)
    
    @app_commands.command(name="permaudit", description="Audit server permissions for security issues")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def permaudit_slash(self, interaction: discord.Interaction):
        """Permission audit using slash command"""
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
        await self._permaudit_logic(ctx)
    
    async def _permaudit_logic(self, ctx):
        guild = ctx.guild
        issues = []
        
        # Check @everyone permissions
        everyone_role = guild.default_role
        if everyone_role.permissions.administrator:
            issues.append(("🔴 CRITICAL", "@everyone has Administrator"))
        
        if everyone_role.permissions.manage_guild:
            issues.append(("🔴 CRITICAL", "@everyone can Manage Server"))
        
        if everyone_role.permissions.manage_roles:
            issues.append(("🔴 CRITICAL", "@everyone can Manage Roles"))
        
        if everyone_role.permissions.manage_channels:
            issues.append(("🔴 CRITICAL", "@everyone can Manage Channels"))
        
        if everyone_role.permissions.mention_everyone:
            issues.append(("⚠️ WARNING", "@everyone can Mention @everyone"))
        
        # Check bot roles
        bot_roles = sum(1 for m in guild.members if m.bot)
        if bot_roles == 0:
            issues.append(("ℹ️ INFO", "No bot roles detected"))
        
        # Find overprivileged roles
        high_perm_roles = []
        for role in guild.roles:
            if role.permissions.administrator and role != guild.owner_role:
                high_perm_roles.append(role)
                if len([m for m in guild.members if role in m.roles]) > 10:
                    issues.append((f"⚠️ WARNING", f"Role '{role.name}' has Admin + {len([m for m in guild.members if role in m.roles])} members"))
        
        # Check for guest access
        for role in guild.roles:
            if "guest" in role.name.lower() and role.permissions.administrator:
                issues.append(("🔴 CRITICAL", f"Guest role '{role.name}' has Administrator"))
        
        # Check channel overrides
        suspicious_overwrites = []
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                for target, overwrite in channel.overwrites.items():
                    if overwrite.administrator == True:
                        suspicious_overwrites.append((channel.name, str(target)))
        
        if suspicious_overwrites:
            issues.append((
                "⚠️ WARNING",
                f"{len(suspicious_overwrites)} channel overrides with Admin perms"
            ))
        
        # Check for public channel permissions
        public_channels_with_perms = 0
        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.default_role)
            if perms.send_messages and perms.manage_messages:
                public_channels_with_perms += 1
        
        if public_channels_with_perms > 0:
            issues.append((
                "⚠️ WARNING",
                f"{public_channels_with_perms} public channels allow message management"
            ))
        
        # Check for excessive permissions
        dangerous_perms = [
            'administrator',
            'manage_guild',
            'manage_channels',
            'manage_roles',
            'manage_webhooks',
            'ban_members',
            'kick_members',
            'moderate_members'
        ]
        
        role_danger_scores = {}
        for role in guild.roles:
            if role == guild.default_role:
                continue
            
            score = 0
            for perm in dangerous_perms:
                if getattr(role.permissions, perm):
                    score += 1
            
            if score >= 3:
                role_danger_scores[role] = score
        
        if role_danger_scores:
            top_dangerous = max(role_danger_scores.items(), key=lambda x: x[1])
            issues.append((
                "⚠️ WARNING",
                f"Role '{top_dangerous[0].name}' has {top_dangerous[1]}/8 dangerous permissions"
            ))
        
        # Create audit report
        severity = "✅"
        if any(issue[0].startswith("🔴") for issue in issues):
            severity = "🔴"
        elif any(issue[0].startswith("⚠️") for issue in issues):
            severity = "⚠️"
        
        embed = discord.Embed(
            title=f"{severity} Permission Audit Report",
            description=f"Scanning {len(guild.roles)} roles, {len(list(guild.text_channels))} channels",
            color=discord.Color.red() if severity == "🔴" else (discord.Color.gold() if severity == "⚠️" else discord.Color.green()),
            timestamp=datetime.now(datetime.UTC)
        )
        
        if issues:
            # Group by severity
            critical = [i for i in issues if i[0].startswith("🔴")]
            warnings = [i for i in issues if i[0].startswith("⚠️")]
            info = [i for i in issues if i[0].startswith("ℹ️")]
            
            if critical:
                embed.add_field(
                    name="🔴 Critical Issues",
                    value="\n".join([f"• {issue[1]}" for issue in critical[:3]]),
                    inline=False
                )
            
            if warnings:
                embed.add_field(
                    name="⚠️ Warnings",
                    value="\n".join([f"• {issue[1]}" for issue in warnings[:3]]),
                    inline=False
                )
            
            if info:
                embed.add_field(
                    name="ℹ️ Information",
                    value="\n".join([f"• {issue[1]}" for issue in info[:2]]),
                    inline=False
                )
        else:
            embed.add_field(
                name="✅ All Clear",
                value="No permission issues detected",
                inline=False
            )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Roles:** {len(guild.roles)}\n**Text Channels:** {len(list(guild.text_channels))}\n**Issues Found:** {len(issues)}",
            inline=False
        )
        
        embed.set_footer(text=f"Audit completed • Guild ID: {guild.id}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PermissionAuditor(bot))
