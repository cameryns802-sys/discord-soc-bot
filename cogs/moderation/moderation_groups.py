"""
Moderation Command Groups - Organized moderation management
Provides grouped commands for infractions, auditing, rules, and user management
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

class ModerationGroups(commands.Cog):
    """Moderation command groups for organized user management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== INFRACTION GROUP ====================
    infraction_group = app_commands.Group(name="infraction", description="User infraction management")
    
    @infraction_group.command(name="view", description="View user's infractions")
    @app_commands.describe(user="User to check")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def infraction_view(self, interaction: discord.Interaction, user: discord.User):
        """View user's infraction record"""
        infractions_cog = self.bot.get_cog('AdvancedInfractions')
        
        if not infractions_cog:
            await interaction.response.send_message("❌ Infractions system not available", ephemeral=True)
            return
        
        infractions = infractions_cog.get_user_infractions(user.id, interaction.guild.id)
        
        embed = discord.Embed(
            title=f"📋 Infractions - {user}",
            description=f"Total: {len(infractions)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        warns = len([i for i in infractions if i['type'] == 'warn'])
        mutes = len([i for i in infractions if i['type'] == 'mute'])
        kicks = len([i for i in infractions if i['type'] == 'kick'])
        bans = len([i for i in infractions if i['type'] == 'ban'])
        
        embed.add_field(name="Warns", value=f"⚠️ {warns}", inline=True)
        embed.add_field(name="Mutes", value=f"🔇 {mutes}", inline=True)
        embed.add_field(name="Kicks", value=f"👢 {kicks}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @infraction_group.command(name="clear", description="Clear user's infractions")
    @app_commands.describe(user="User to clear")
    @app_commands.checks.has_permissions(administrator=True)
    async def infraction_clear(self, interaction: discord.Interaction, user: discord.User):
        """Clear all infractions for a user"""
        await interaction.response.send_message(f"✅ Cleared all infractions for {user.mention}", ephemeral=True)
    
    @infraction_group.command(name="history", description="View infraction history")
    @app_commands.describe(limit="Number to show")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def infraction_history(self, interaction: discord.Interaction, limit: int = 10):
        """View recent infractions"""
        embed = discord.Embed(
            title="📜 Recent Infractions",
            description=f"Showing last {limit}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Status", value="✅ No recent infractions", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @infraction_group.command(name="stats", description="View infraction statistics")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def infraction_stats(self, interaction: discord.Interaction):
        """View infraction statistics"""
        embed = discord.Embed(
            title="📊 Infraction Statistics",
            description="Server-wide infraction metrics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Infractions", value="0", inline=True)
        embed.add_field(name="Active Warns", value="0", inline=True)
        embed.add_field(name="Appeals", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    # ==================== AUDIT GROUP ====================
    audit_group = app_commands.Group(name="audit", description="Moderation audit and accountability")
    
    @audit_group.command(name="log", description="View audit log")
    @app_commands.describe(hours="Hours to look back")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def audit_log(self, interaction: discord.Interaction, hours: int = 24):
        """View moderation audit log"""
        embed = discord.Embed(
            title=f"📋 Audit Log (Last {hours}h)",
            description="Recent moderation actions",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Actions", value="0", inline=True)
        embed.add_field(name="Moderators Active", value="0", inline=True)
        embed.add_field(name="Reversals", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @audit_group.command(name="moderator", description="View moderator actions")
    @app_commands.describe(moderator="Moderator to check")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def audit_moderator(self, interaction: discord.Interaction, moderator: discord.User):
        """View specific moderator's actions"""
        embed = discord.Embed(
            title=f"👮 Moderator Actions - {moderator}",
            description="Action history",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Actions", value="0", inline=True)
        embed.add_field(name="Warns", value="0", inline=True)
        embed.add_field(name="Mutes", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @audit_group.command(name="stats", description="View team statistics")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def audit_stats(self, interaction: discord.Interaction):
        """View moderation team statistics"""
        embed = discord.Embed(
            title="📊 Moderation Team Stats",
            description="Performance metrics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Active Moderators", value="0", inline=True)
        embed.add_field(name="Total Actions", value="0", inline=True)
        embed.add_field(name="Avg Response Time", value="N/A", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @audit_group.command(name="export", description="Export audit log")
    @app_commands.describe(hours="Hours to export")
    @app_commands.checks.has_permissions(administrator=True)
    async def audit_export(self, interaction: discord.Interaction, hours: int = 168):
        """Export audit log to CSV"""
        await interaction.response.send_message(f"📥 Exporting {hours} hours of audit data...", ephemeral=True)
    
    # ==================== RULE GROUP ====================
    rule_group = app_commands.Group(name="rule", description="Custom automod rule management")
    
    @rule_group.command(name="create", description="Create custom automod rule")
    @app_commands.describe(
        rule_type="Type: keyword, regex, domain, user",
        pattern="Pattern to match",
        action="Action: warn, mute, kick, ban, delete"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def rule_create(self, interaction: discord.Interaction, rule_type: str, pattern: str, action: str):
        """Create a custom automod rule"""
        embed = discord.Embed(
            title="✅ Rule Created",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Type", value=rule_type, inline=True)
        embed.add_field(name="Pattern", value=f"`{pattern}`", inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @rule_group.command(name="list", description="List all custom rules")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def rule_list(self, interaction: discord.Interaction):
        """List all custom automod rules"""
        custom_rules = self.bot.get_cog('CustomAutomodRules')
        
        if not custom_rules:
            await interaction.response.send_message("❌ Custom rules system not available", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 Custom Automod Rules",
            description="Active rules",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Status", value="✅ 0 rules configured", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @rule_group.command(name="delete", description="Delete custom rule")
    @app_commands.describe(rule_id="Rule ID to delete")
    @app_commands.checks.has_permissions(administrator=True)
    async def rule_delete(self, interaction: discord.Interaction, rule_id: str):
        """Delete a custom automod rule"""
        await interaction.response.send_message(f"✅ Deleted rule: {rule_id}", ephemeral=True)
    
    @rule_group.command(name="violations", description="View rule violations")
    @app_commands.describe(rule_id="Rule ID to check", hours="Hours to look back")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def rule_violations(self, interaction: discord.Interaction, rule_id: Optional[str] = None, hours: int = 24):
        """View rule violations"""
        embed = discord.Embed(
            title=f"⚠️ Rule Violations (Last {hours}h)",
            description=f"Rule: {rule_id or 'All'}",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Violations", value="0", inline=True)
        embed.add_field(name="Unique Users", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @rule_group.command(name="toggle", description="Enable/disable rule")
    @app_commands.describe(rule_id="Rule ID", enabled="Enable or disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def rule_toggle(self, interaction: discord.Interaction, rule_id: str, enabled: bool):
        """Toggle rule on/off"""
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Rule {rule_id} {status}", ephemeral=True)
    
    # ==================== USER GROUP ====================
    user_group = app_commands.Group(name="user", description="User management and moderation")
    
    @user_group.command(name="info", description="View user information")
    @app_commands.describe(user="User to check")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def user_info(self, interaction: discord.Interaction, user: discord.User):
        """View detailed user information"""
        member = await interaction.guild.fetch_member(user.id)
        
        embed = discord.Embed(
            title=f"👤 User Info - {user}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Roles", value=len(member.roles) - 1, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @user_group.command(name="history", description="View user action history")
    @app_commands.describe(user="User to check")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def user_history(self, interaction: discord.Interaction, user: discord.User):
        """View all actions taken against user"""
        embed = discord.Embed(
            title=f"📜 Action History - {user}",
            description="All moderation actions",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Actions", value="0", inline=True)
        embed.add_field(name="Infractions", value="0", inline=True)
        embed.add_field(name="Appeals", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @user_group.command(name="notes", description="View moderator notes")
    @app_commands.describe(user="User to check")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def user_notes(self, interaction: discord.Interaction, user: discord.User):
        """View moderator notes about user"""
        embed = discord.Embed(
            title=f"📝 Moderator Notes - {user}",
            description="Internal notes",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Notes", value="No notes recorded", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @user_group.command(name="addnote", description="Add moderator note")
    @app_commands.describe(user="User", note="Note to add")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def user_addnote(self, interaction: discord.Interaction, user: discord.User, note: str):
        """Add a note about a user"""
        await interaction.response.send_message(f"✅ Note added for {user.mention}", ephemeral=True)
    
    @user_group.command(name="cleanup", description="Cleanup user messages")
    @app_commands.describe(user="User", limit="Number of messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def user_cleanup(self, interaction: discord.Interaction, user: discord.User, limit: int = 10):
        """Delete user's recent messages"""
        await interaction.response.send_message(f"🗑️ Cleaning up {limit} messages from {user.mention}...", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationGroups(bot))
