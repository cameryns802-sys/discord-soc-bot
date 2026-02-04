"""Rate-Limit Management & Load Balancer - Defer low-priority work under load"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
import os
from typing import List, Dict
from cogs.core.pst_timezone import get_now_pst

try:
    from cogs.core.feature_flags import flags
except Exception:
    flags = None

class RateLimitLoadBalancer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/load_balancer.json"
        self.data = {
            "mode": "normal",
            "msg_count": 0,
            "cmd_count": 0,
            "thresholds": {
                "messages_high": 120,
                "commands_high": 30,
                "messages_critical": 240,
                "commands_critical": 60
            },
            "degrade_features": ["ml_anomaly_detection", "generative_responses"],
            "use_safe_mode": False,
            "deferred_messages": []
        }
        self._load_data()
        self.reset_counters.start()
        self.evaluate_load.start()
        self.process_deferred.start()

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

    def enqueue_low_priority_message(self, channel_id: int, content: str):
        self.data["deferred_messages"].append({
            "channel_id": channel_id,
            "content": content,
            "queued_at": get_now_pst().isoformat()
        })
        self.data["deferred_messages"] = self.data["deferred_messages"][-200:]
        self._save_data()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        self.data["msg_count"] += 1

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.data["cmd_count"] += 1

    @tasks.loop(minutes=1)
    async def reset_counters(self):
        self.data["msg_count"] = 0
        self.data["cmd_count"] = 0
        self._save_data()

    @tasks.loop(minutes=1)
    async def evaluate_load(self):
        msgs = self.data["msg_count"]
        cmds = self.data["cmd_count"]
        thresholds = self.data["thresholds"]
        mode = "normal"
        if msgs >= thresholds["messages_critical"] or cmds >= thresholds["commands_critical"]:
            mode = "critical"
        elif msgs >= thresholds["messages_high"] or cmds >= thresholds["commands_high"]:
            mode = "elevated"

        if mode != self.data.get("mode"):
            self.data["mode"] = mode
            self._apply_degradation(mode)
            self._save_data()

    def _apply_degradation(self, mode: str):
        if not flags:
            return
        if mode == "critical" and self.data.get("use_safe_mode"):
            flags.enable_safe_mode()
        elif mode == "normal" and self.data.get("use_safe_mode"):
            flags.disable_safe_mode()

        if mode in ["elevated", "critical"]:
            for feature in self.data.get("degrade_features", []):
                flags.disable_feature(feature, reason="Load balancer")
        elif mode == "normal":
            for feature in self.data.get("degrade_features", []):
                flags.enable_feature(feature, reason="Load normalized")

    @tasks.loop(seconds=30)
    async def process_deferred(self):
        if self.data.get("mode") != "normal":
            return
        if not self.data["deferred_messages"]:
            return
        payload = self.data["deferred_messages"].pop(0)
        channel = self.bot.get_channel(payload["channel_id"])
        if channel:
            try:
                await channel.send(payload["content"])
            except Exception:
                pass
        self._save_data()

    @app_commands.command(name="loadbalancer_status", description="View load balancer status")
    async def loadbalancer_status(self, interaction: discord.Interaction):
        embed = discord.Embed(title="?? Load Balancer Status", color=discord.Color.orange())
        embed.add_field(name="Mode", value=self.data.get("mode"), inline=True)
        embed.add_field(name="Message Rate", value=str(self.data.get("msg_count")), inline=True)
        embed.add_field(name="Command Rate", value=str(self.data.get("cmd_count")), inline=True)
        embed.add_field(name="Deferred Queue", value=str(len(self.data.get("deferred_messages", []))), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loadbalancer_config", description="Configure load thresholds")
    @app_commands.checks.has_permissions(administrator=True)
    async def loadbalancer_config(self, interaction: discord.Interaction, messages_high: int, commands_high: int, messages_critical: int, commands_critical: int):
        self.data["thresholds"] = {
            "messages_high": messages_high,
            "commands_high": commands_high,
            "messages_critical": messages_critical,
            "commands_critical": commands_critical
        }
        self._save_data()
        await interaction.response.send_message("? Load thresholds updated")

    @app_commands.command(name="loadbalancer_defermsg", description="Queue a low-priority message")
    @app_commands.checks.has_permissions(administrator=True)
    async def loadbalancer_defermsg(self, interaction: discord.Interaction, channel: discord.TextChannel, content: str):
        self.enqueue_low_priority_message(channel.id, content)
        await interaction.response.send_message("? Message queued")

async def setup(bot):
    await bot.add_cog(RateLimitLoadBalancer(bot))
