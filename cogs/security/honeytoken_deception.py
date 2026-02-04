"""Honeytokens & Deception Module - Detect internal recon and token misuse"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
import secrets
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class HoneytokenDeception(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/honeytokens.json"
        self.data = {
            "tokens": {},
            "channels": {},
            "counter": 0,
            "alert_channel_id": None,
            "events": []
        }
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

    def _mask_token(self, token: str) -> str:
        if len(token) <= 6:
            return "*" * len(token)
        return token[:3] + "***" + token[-3:]

    async def _alert(self, guild: discord.Guild, message: str):
        channel_id = self.data.get("alert_channel_id")
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel and channel.permissions_for(guild.me).send_messages:
            await channel.send(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Channel traps
        channel_entry = self.data["channels"].get(str(message.channel.id))
        if channel_entry and channel_entry.get("active", True):
            event = {
                "type": "channel",
                "channel_id": message.channel.id,
                "user_id": message.author.id,
                "timestamp": get_now_pst().isoformat(),
                "content_preview": (message.content or "")[:120]
            }
            self.data["events"].append(event)
            self.data["events"] = self.data["events"][-200:]
            self._save_data()
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity="high",
                source="honeytoken_deception",
                data={
                    "event": "honeychannel_activity",
                    "user_id": message.author.id,
                    "channel_id": message.channel.id,
                    "confidence": 0.9,
                    "dedup_key": f"honey_channel_{message.channel.id}_{message.author.id}"
                }
            ))
            await self._alert(message.guild, f"?? Honeychannel activity by {message.author.mention} in {message.channel.mention}")

        # Token traps
        content = message.content or ""
        for token_id, token_info in self.data["tokens"].items():
            if not token_info.get("active", True):
                continue
            token_value = token_info.get("token")
            if token_value and token_value in content:
                event = {
                    "type": "token",
                    "token_id": token_id,
                    "user_id": message.author.id,
                    "timestamp": get_now_pst().isoformat(),
                    "channel_id": message.channel.id
                }
                self.data["events"].append(event)
                self.data["events"] = self.data["events"][-200:]
                self._save_data()
                await signal_bus.emit(Signal(
                    signal_type=SignalType.THREAT_DETECTED,
                    severity="critical",
                    source="honeytoken_deception",
                    data={
                        "event": "honeytoken_trigger",
                        "token_id": token_id,
                        "user_id": message.author.id,
                        "channel_id": message.channel.id,
                        "confidence": 0.98,
                        "dedup_key": f"honey_token_{token_id}_{message.author.id}"
                    }
                ))
                await self._alert(message.guild, f"?? Honeytoken triggered by {message.author.mention} in {message.channel.mention}")

    @app_commands.command(name="honeytoken_createtoken", description="Create a honeytoken string trap")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def honeytoken_createtoken(self, interaction: discord.Interaction, name: str, token: str = ""):
        self.data["counter"] += 1
        tid = str(self.data["counter"])
        token_value = token.strip() if token else f"HT-{secrets.token_urlsafe(8)}"
        self.data["tokens"][tid] = {
            "id": tid,
            "name": name,
            "token": token_value,
            "created_by": interaction.user.id,
            "created_at": get_now_pst().isoformat(),
            "active": True
        }
        self._save_data()
        await interaction.response.send_message(f"? Honeytoken created: {name}\nValue: `{token_value}`", ephemeral=True)

    @app_commands.command(name="honeytoken_createchannel", description="Create a honeytoken channel trap")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def honeytoken_createchannel(self, interaction: discord.Interaction, name: str):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        staff_role = discord.utils.get(guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        channel = await guild.create_text_channel(name, overwrites=overwrites, reason="Honeytoken trap channel")
        self.data["channels"][str(channel.id)] = {
            "id": channel.id,
            "name": name,
            "created_by": interaction.user.id,
            "created_at": get_now_pst().isoformat(),
            "active": True
        }
        self._save_data()
        await interaction.response.send_message(f"? Honeytoken channel created: {channel.mention}")

    @app_commands.command(name="honeytoken_list", description="List honeytokens and traps")
    async def honeytoken_list(self, interaction: discord.Interaction):
        embed = discord.Embed(title="?? Honeytokens", color=discord.Color.gold())
        if self.data["tokens"]:
            for tid, info in list(self.data["tokens"].items())[-10:]:
                embed.add_field(
                    name=f"Token {tid}: {info['name']}",
                    value=f"Value: {self._mask_token(info['token'])} | Active: {info.get('active', True)}",
                    inline=False
                )
        if self.data["channels"]:
            channels = []
            for cid, info in list(self.data["channels"].items())[-10:]:
                channels.append(f"#{info['name']} (ID: {cid})")
            embed.add_field(name="Honeychannels", value="\n".join(channels), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="honeytoken_disable", description="Disable honeytoken or channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def honeytoken_disable(self, interaction: discord.Interaction, token_id: str = "", channel_id: str = ""):
        if token_id and token_id in self.data["tokens"]:
            self.data["tokens"][token_id]["active"] = False
            self._save_data()
            await interaction.response.send_message(f"?? Honeytoken {token_id} disabled")
            return
        if channel_id and channel_id in self.data["channels"]:
            self.data["channels"][channel_id]["active"] = False
            self._save_data()
            await interaction.response.send_message(f"?? Honeychannel {channel_id} disabled")
            return
        await interaction.response.send_message("? Specify a valid token_id or channel_id", ephemeral=True)

    @app_commands.command(name="honeytoken_setalert", description="Set honeytoken alert channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def honeytoken_setalert(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.data["alert_channel_id"] = channel.id
        self._save_data()
        await interaction.response.send_message(f"? Alert channel set to {channel.mention}")

async def setup(bot):
    await bot.add_cog(HoneytokenDeception(bot))
