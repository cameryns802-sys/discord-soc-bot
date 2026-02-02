"""
Smart Onboarding Wizard: Guided setup with auto-detection and intelligent suggestions.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SmartOnboardingWizardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/onboarding_wizard.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "guild_setups": {},
            "user_preferences": {},
            "wizard_progress": {},
            "suggested_configs": {},
            "setup_templates": {}
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="start_setup_wizard")
    async def start_setup_wizard(self, ctx):
        """Start the interactive setup wizard."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        
        embed = discord.Embed(
            title="🧙 Setup Wizard",
            description="Welcome to the intelligent setup wizard!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Step 1: Security Level",
            value="What security level does your server need?\n• Basic (starter servers)\n• Intermediate (growing communities)\n• Advanced (large/high-risk servers)",
            inline=False
        )
        embed.set_footer(text="Reply with: basic, intermediate, or advanced")
        
        self.data["wizard_progress"][guild_id] = {
            "step": 1,
            "started_at": datetime.utcnow().isoformat(),
            "responses": []
        }
        self.save_data(self.data)
        
        await ctx.send(embed=embed)

    @commands.command(name="wizard_response")
    async def wizard_response(self, ctx, *, response: str):
        """Respond to wizard step."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.data["wizard_progress"]:
            await ctx.send("❌ No active wizard. Start with /start_setup_wizard")
            return
        
        progress = self.data["wizard_progress"][guild_id]
        progress["responses"].append(response)
        
        if progress["step"] == 1:
            progress["step"] = 2
            embed = discord.Embed(
                title="🧙 Setup Wizard - Step 2",
                description="Great! Now let's configure moderation.",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Moderation Mode",
                value="How strict should auto-moderation be?\n• Lenient (minimal automatic actions)\n• Balanced (moderate filtering)\n• Strict (aggressive filtering)",
                inline=False
            )
        elif progress["step"] == 2:
            progress["step"] = 3
            embed = discord.Embed(
                title="🧙 Setup Wizard - Step 3",
                description="Excellent! Final step.",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Logging & Transparency",
                value="Enable detailed logging?\n• Minimal (events only)\n• Standard (actions logged)\n• Comprehensive (full audit trail)",
                inline=False
            )
        else:
            # Wizard complete
            guild_setup = {
                "responses": progress["responses"],
                "completed_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            self.data["guild_setups"][guild_id] = guild_setup
            
            embed = discord.Embed(
                title="✅ Setup Complete!",
                description="Your server is now configured.",
                color=discord.Color.green()
            )
            embed.add_field(name="Configuration", value="\n".join(progress["responses"]), inline=False)
            embed.add_field(name="Next Steps", value="Use `/configure` to fine-tune settings", inline=False)
            
            del self.data["wizard_progress"][guild_id]
        
        self.save_data(self.data)
        await ctx.send(embed=embed)

    @commands.command(name="suggest_config")
    async def suggest_config(self, ctx):
        """Get AI-suggested configuration for this server."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild = ctx.guild
        
        # Auto-detect server characteristics
        member_count = guild.member_count
        role_count = len(guild.roles)
        channel_count = len(guild.channels)
        
        security_level = "basic"
        if member_count > 500 or role_count > 20:
            security_level = "intermediate"
        if member_count > 5000 or role_count > 50:
            security_level = "advanced"
        
        suggestion = {
            "security_level": security_level,
            "detected_characteristics": {
                "member_count": member_count,
                "role_count": role_count,
                "channel_count": channel_count
            },
            "recommended_features": {
                "basic": ["basic_moderation", "welcome_system", "logging"],
                "intermediate": ["advanced_moderation", "verification", "audit_logging", "threat_detection"],
                "advanced": ["ml_moderation", "advanced_verification", "comprehensive_logging", "advanced_threat_intel"]
            }[security_level]
        }
        
        embed = discord.Embed(
            title="🤖 AI Suggested Configuration",
            description=f"Based on server analysis: {security_level.upper()}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Members", value=str(member_count), inline=True)
        embed.add_field(name="Roles", value=str(role_count), inline=True)
        embed.add_field(name="Channels", value=str(channel_count), inline=True)
        
        features_str = "\n".join([f"• {f}" for f in suggestion["recommended_features"]])
        embed.add_field(name="Recommended Features", value=features_str, inline=False)
        
        embed.set_footer(text="Accept with: /apply_suggested_config")
        
        guild_id = str(guild.id)
        self.data["suggested_configs"][guild_id] = suggestion
        self.save_data(self.data)
        
        await ctx.send(embed=embed)

    @commands.command(name="setup_status")
    async def setup_status(self, ctx):
        """View setup status for this server."""
        guild_id = str(ctx.guild.id)
        
        embed = discord.Embed(
            title="📋 Setup Status",
            color=discord.Color.blue()
        )
        
        if guild_id in self.data["guild_setups"]:
            setup = self.data["guild_setups"][guild_id]
            embed.add_field(name="Status", value="✅ Complete", inline=True)
            embed.add_field(name="Date", value=setup["completed_at"][:10], inline=True)
        elif guild_id in self.data["wizard_progress"]:
            progress = self.data["wizard_progress"][guild_id]
            embed.add_field(name="Status", value="⏳ In Progress", inline=True)
            embed.add_field(name="Step", value=str(progress["step"]) + "/3", inline=True)
        else:
            embed.add_field(name="Status", value="❌ Not Started", inline=True)
            embed.add_field(name="Action", value="Run `/start_setup_wizard`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="reset_wizard")
    async def reset_wizard(self, ctx):
        """Reset setup wizard for this server."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id in self.data["wizard_progress"]:
            del self.data["wizard_progress"][guild_id]
            self.save_data(self.data)
            await ctx.send("✅ Wizard reset. Run `/start_setup_wizard` to begin again.")
        else:
            await ctx.send("❌ No active wizard.")

async def setup(bot):
    await bot.add_cog(SmartOnboardingWizardCog(bot))
