"""Dynamic FAQ/Knowledge AI - Learns from staff answers and provides semantic search"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class DynamicFAQAI(commands.Cog):
    # Create FAQ command group
    faq_group = app_commands.Group(name="faq", description="FAQ management and queries")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/faq_ai.json"
        self.data = {"entries": {}, "counter": 0}
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

    def _similarity(self, a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)

    @faq_group.command(name="add", description="Add FAQ entry")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def faq_add(self, interaction: discord.Interaction, question: str, answer: str, tags: str = ""):
        self.data["counter"] += 1
        fid = str(self.data["counter"])
        self.data["entries"][fid] = {
            "id": fid,
            "question": question,
            "answer": answer,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "created_by": interaction.user.id,
            "created_at": get_now_pst().isoformat(),
            "usage": 0
        }
        self._save_data()
        await interaction.response.send_message(f"? FAQ entry {fid} added")

    @faq_group.command(name="learn", description="Learn FAQ from a staff message")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def faq_learn(self, interaction: discord.Interaction, question: str, message_id: str, channel: discord.TextChannel = None):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        channel = channel or interaction.channel
        try:
            msg = await channel.fetch_message(int(message_id))
        except Exception:
            await interaction.response.send_message("? Message not found", ephemeral=True)
            return
        await self.faq_add(interaction, question, msg.content or "", "learned")

    @faq_group.command(name="remove", description="Remove FAQ entry")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def faq_remove(self, interaction: discord.Interaction, entry_id: str):
        if entry_id not in self.data["entries"]:
            await interaction.response.send_message("? Entry not found", ephemeral=True)
            return
        self.data["entries"].pop(entry_id)
        self._save_data()
        await interaction.response.send_message(f"??? FAQ entry {entry_id} removed")

    @faq_group.command(name="ask", description="Ask the FAQ AI")
    async def faq_ask(self, interaction: discord.Interaction, query: str):
        entries = list(self.data["entries"].values())
        if not entries:
            await interaction.response.send_message("?? No FAQ entries yet", ephemeral=True)
            return

        matches = []
        for entry in entries:
            score = self._similarity(query, entry["question"])
            matches.append((score, entry))
        matches.sort(key=lambda x: x[0], reverse=True)
        top = [m for m in matches if m[0] > 0.2][:3]
        if not top:
            await interaction.response.send_message("?? No close matches found", ephemeral=True)
            return

        embed = discord.Embed(title="?? FAQ AI Results", color=discord.Color.teal())
        for score, entry in top:
            entry["usage"] += 1
            embed.add_field(
                name=f"{entry['question']} ({score:.0%})",
                value=entry["answer"][:300],
                inline=False
            )
        self._save_data()

        # Index query in semantic engine if available
        semantic = self.bot.get_cog("SemanticSimilarityEngine")
        if semantic:
            try:
                semantic.index_query(query, result="faq")
            except Exception:
                pass

        await interaction.response.send_message(embed=embed)

    @faq_group.command(name="stats", description="FAQ AI stats")
    async def faq_stats(self, interaction: discord.Interaction):
        total = len(self.data["entries"])
        usages = sum(e.get("usage", 0) for e in self.data["entries"].values())
        embed = discord.Embed(title="?? FAQ AI Stats", color=discord.Color.teal())
        embed.add_field(name="Entries", value=str(total), inline=True)
        embed.add_field(name="Total Uses", value=str(usages), inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DynamicFAQAI(bot))
