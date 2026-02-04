"""Advanced Suggestion & Feedback System - staged workflow with voting threads"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

STATUSES = ["reviewing", "planned", "implemented", "rejected"]

class AdvancedSuggestionFeedback(commands.Cog):
    # Create suggestion command group
    suggestion_group = app_commands.Group(name="suggestion", description="Suggestion management and voting")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/advanced_suggestions.json"
        self.data = {"suggestions": {}, "counter": 0}
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def _save_data(self):
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)

    @suggestion_group.command(name="create", description="Create a community suggestion")
    async def suggestion_create(self, interaction: discord.Interaction, suggestion: str, channel: discord.TextChannel = None):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        target_channel = channel or interaction.channel
        self.data["counter"] += 1
        sid = str(self.data["counter"])
        embed = discord.Embed(title=f"?? Suggestion #{sid}", description=suggestion, color=discord.Color.blurple())
        embed.add_field(name="Status", value="Reviewing", inline=True)
        embed.add_field(name="Author", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Vote with ?? or ??")

        msg = await target_channel.send(embed=embed)
        try:
            await msg.add_reaction("??")
            await msg.add_reaction("??")
        except Exception:
            pass

        thread = None
        try:
            thread = await msg.create_thread(name=f"Suggestion #{sid} Discussion", auto_archive_duration=1440)
        except Exception:
            pass

        self.data["suggestions"][sid] = {
            "id": sid,
            "guild_id": interaction.guild.id,
            "author_id": interaction.user.id,
            "content": suggestion,
            "status": "reviewing",
            "message_id": msg.id,
            "channel_id": target_channel.id,
            "thread_id": thread.id if thread else None,
            "created_at": get_now_pst().isoformat(),
            "updated_at": get_now_pst().isoformat()
        }
        self._save_data()
        await interaction.response.send_message(f"? Suggestion #{sid} created", ephemeral=True)

    @suggestion_group.command(name="status", description="Update suggestion status")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def suggestion_status(self, interaction: discord.Interaction, suggestion_id: str, status: str):
        status = status.lower()
        if status not in STATUSES:
            await interaction.response.send_message(f"? Status must be: {', '.join(STATUSES)}", ephemeral=True)
            return
        suggestion = self.data["suggestions"].get(suggestion_id)
        if not suggestion:
            await interaction.response.send_message("? Suggestion not found", ephemeral=True)
            return
        suggestion["status"] = status
        suggestion["updated_at"] = get_now_pst().isoformat()
        self._save_data()

        # Update embed
        channel = interaction.guild.get_channel(suggestion["channel_id"])
        if channel:
            try:
                msg = await channel.fetch_message(suggestion["message_id"])
                embed = msg.embeds[0] if msg.embeds else discord.Embed(title=f"?? Suggestion #{suggestion_id}")
                embed.clear_fields()
                embed.add_field(name="Status", value=status.title(), inline=True)
                embed.add_field(name="Author", value=f"<@{suggestion['author_id']}>", inline=True)
                embed.description = suggestion["content"]
                embed.set_footer(text="Vote with ?? or ??")
                await msg.edit(embed=embed)
            except Exception:
                pass

        if suggestion.get("thread_id"):
            thread = interaction.guild.get_thread(suggestion["thread_id"])
            if thread:
                await thread.send(f"?? Status updated to **{status.title()}** by {interaction.user.mention}")

        await interaction.response.send_message(f"? Suggestion {suggestion_id} updated to {status}")

    @suggestion_group.command(name="list", description="List suggestions")
    async def suggestion_list(self, interaction: discord.Interaction, status: str = ""):
        suggestions = list(self.data["suggestions"].values())
        if status:
            suggestions = [s for s in suggestions if s.get("status") == status.lower()]
        if not suggestions:
            await interaction.response.send_message("?? No suggestions found", ephemeral=True)
            return
        embed = discord.Embed(title="?? Suggestions", color=discord.Color.blurple())
        for s in suggestions[-10:]:
            embed.add_field(
                name=f"#{s['id']} - {s['status'].title()}",
                value=s["content"][:100],
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @suggestion_group.command(name="view", description="View a suggestion")
    async def suggestion_view(self, interaction: discord.Interaction, suggestion_id: str):
        s = self.data["suggestions"].get(suggestion_id)
        if not s:
            await interaction.response.send_message("? Suggestion not found", ephemeral=True)
            return
        embed = discord.Embed(title=f"Suggestion #{suggestion_id}", color=discord.Color.blurple())
        embed.add_field(name="Status", value=s.get("status").title(), inline=True)
        embed.add_field(name="Author", value=f"<@{s['author_id']}>", inline=True)
        embed.add_field(name="Content", value=s.get("content"), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedSuggestionFeedback(bot))
