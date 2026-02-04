"""Sentiment Trend Analysis - Channel-level trend detection and alerts"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from cogs.core.pst_timezone import get_now_pst

POSITIVE_WORDS = {
    "good", "great", "awesome", "nice", "love", "thanks", "amazing", "cool", "glad", "happy", "yay"
}
NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "hate", "angry", "sad", "toxic", "annoying", "mad", "upset", "drama"
}

class SentimentTrendAnalysis(commands.Cog):
    # Define command group at class level
    sentiment_group = app_commands.Group(name="sentiment", description="Sentiment analysis and trends")
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/sentiment_trends.json"
        self.data = {"channels": {}, "config": {}}
        self._load_data()
        self.trend_task.start()

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

    def _get_config(self, guild_id: int) -> dict:
        gkey = str(guild_id)
        if gkey not in self.data["config"]:
            self.data["config"][gkey] = {
                "alert_channel_id": None,
                "drop_threshold": -0.25
            }
        return self.data["config"][gkey]

    def _score_text(self, text: str) -> float:
        words = [w.strip(".,!?\"'").lower() for w in text.split()]
        if not words:
            return 0.0
        pos = sum(1 for w in words if w in POSITIVE_WORDS)
        neg = sum(1 for w in words if w in NEGATIVE_WORDS)
        return (pos - neg) / max(len(words), 1)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        score = self._score_text(message.content or "")
        gkey = str(message.guild.id)
        ckey = str(message.channel.id)
        self.data["channels"].setdefault(gkey, {})
        channel_data = self.data["channels"][gkey].setdefault(ckey, {"scores": [], "ema": 0.0, "last_alert": None})
        channel_data["scores"].append({"t": get_now_pst().isoformat(), "s": score})
        channel_data["scores"] = channel_data["scores"][-500:]
        alpha = 0.2
        channel_data["ema"] = alpha * score + (1 - alpha) * channel_data.get("ema", 0.0)
        self._save_data()

    @tasks.loop(hours=1)
    async def trend_task(self):
        now = get_now_pst()
        for guild in self.bot.guilds:
            gkey = str(guild.id)
            channels = self.data["channels"].get(gkey, {})
            config = self._get_config(guild.id)
            for ckey, stats in channels.items():
                recent = [x for x in stats["scores"] if datetime.fromisoformat(x["t"]) > now - timedelta(hours=6)]
                if len(recent) < 10:
                    continue
                avg = sum(x["s"] for x in recent) / len(recent)
                drop = avg - stats.get("ema", 0.0)
                if drop < config["drop_threshold"]:
                    last_alert = stats.get("last_alert")
                    if last_alert and datetime.fromisoformat(last_alert) > now - timedelta(hours=6):
                        continue
                    stats["last_alert"] = now.isoformat()
                    self._save_data()
                    channel = guild.get_channel(int(ckey))
                    alert_channel = guild.get_channel(config.get("alert_channel_id")) if config.get("alert_channel_id") else guild.system_channel
                    if alert_channel and alert_channel.permissions_for(guild.me).send_messages:
                        await alert_channel.send(
                            f"?? Sentiment drop detected in {channel.mention if channel else '#unknown'} (avg {avg:.2f})"
                        )

    @sentiment_group.command(name="trends", description="View sentiment trends for a channel")
    async def sentiment_trends(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        channel = channel or interaction.channel
        gkey = str(interaction.guild.id)
        ckey = str(channel.id)
        stats = self.data["channels"].get(gkey, {}).get(ckey)
        if not stats:
            await interaction.response.send_message("?? No sentiment data yet", ephemeral=True)
            return
        recent = stats["scores"][-100:]
        avg = sum(x["s"] for x in recent) / len(recent) if recent else 0.0
        embed = discord.Embed(title="?? Sentiment Trends", color=discord.Color.purple())
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Recent Avg", value=f"{avg:.2f}", inline=True)
        embed.add_field(name="EMA", value=f"{stats.get('ema', 0.0):.2f}", inline=True)
        await interaction.response.send_message(embed=embed)

    @sentiment_group.command(name="config", description="Configure sentiment alerts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sentiment_config(self, interaction: discord.Interaction, alert_channel: discord.TextChannel, drop_threshold: float = -0.25):
        config = self._get_config(interaction.guild.id)
        config["alert_channel_id"] = alert_channel.id
        config["drop_threshold"] = drop_threshold
        self._save_data()
        await interaction.response.send_message("? Sentiment alert configuration updated")

async def setup(bot):
    await bot.add_cog(SentimentTrendAnalysis(bot))
