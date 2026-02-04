"""Proactive Threat Hunting - MITRE pattern scanning of historical messages"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
import re
from typing import Dict, List
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class ProactiveThreatHunting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/proactive_hunting.json"
        self.message_file = "data/proactive_message_index.json"
        self.patterns = {}
        self.pattern_counter = 0
        self.hunts = {}
        self.hunt_counter = 0
        self.max_messages_per_guild = 5000
        self.max_message_age_days = 30
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                self.patterns = data.get("patterns", {})
                self.pattern_counter = data.get("pattern_counter", 0)
                self.hunts = data.get("hunts", {})
                self.hunt_counter = data.get("hunt_counter", 0)
            except Exception:
                pass
        if not self.patterns:
            self._load_default_patterns()
            self._save_data()

    def _save_data(self):
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump({
                "patterns": self.patterns,
                "pattern_counter": self.pattern_counter,
                "hunts": self.hunts,
                "hunt_counter": self.hunt_counter
            }, f, indent=2)

    def _load_default_patterns(self):
        defaults = [
            {
                "name": "Credential Access",
                "technique_id": "T1003",
                "keywords": ["dump lsass", "mimikatz", "creds", "passwords.txt", "shadow copy"],
                "regex": []
            },
            {
                "name": "Valid Accounts",
                "technique_id": "T1078",
                "keywords": ["account takeover", "credential stuffing", "stolen login", "password reuse"],
                "regex": []
            },
            {
                "name": "Exfiltration Over Web Services",
                "technique_id": "T1567",
                "keywords": ["pastebin", "dropbox", "drive.google.com", "mega.nz", "file.io"],
                "regex": []
            },
            {
                "name": "Phishing",
                "technique_id": "T1566",
                "keywords": ["verify your account", "reset password", "suspicious login", "urgent action"],
                "regex": []
            }
        ]
        for entry in defaults:
            self.pattern_counter += 1
            pid = str(self.pattern_counter)
            self.patterns[pid] = {
                "id": pid,
                "name": entry["name"],
                "technique_id": entry["technique_id"],
                "keywords": entry["keywords"],
                "regex": entry["regex"],
                "created_at": get_now_pst().isoformat(),
                "created_by": "system"
            }

    def _load_messages(self) -> Dict:
        if os.path.exists(self.message_file):
            try:
                with open(self.message_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_messages(self, data: Dict):
        os.makedirs("data", exist_ok=True)
        with open(self.message_file, "w") as f:
            json.dump(data, f, indent=2)

    def _prune_messages(self, guild_messages: List[Dict]) -> List[Dict]:
        cutoff = get_now_pst() - timedelta(days=self.max_message_age_days)
        pruned = [m for m in guild_messages if datetime.fromisoformat(m["created_at"]) >= cutoff]
        if len(pruned) > self.max_messages_per_guild:
            pruned = pruned[-self.max_messages_per_guild:]
        return pruned

    def _match_pattern(self, content: str, pattern: Dict) -> Dict:
        content_l = content.lower()
        matched_keywords = [k for k in pattern.get("keywords", []) if k.lower() in content_l]
        matched_regex = []
        for rx in pattern.get("regex", []):
            try:
                if re.search(rx, content, re.IGNORECASE):
                    matched_regex.append(rx)
            except re.error:
                continue
        score = len(matched_keywords) + (2 * len(matched_regex))
        return {
            "score": score,
            "keywords": matched_keywords,
            "regex": matched_regex
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        data = self._load_messages()
        gkey = str(message.guild.id)
        if gkey not in data:
            data[gkey] = []
        content = message.content or ""
        attachments = [a.filename for a in message.attachments]
        data[gkey].append({
            "id": message.id,
            "author_id": message.author.id,
            "channel_id": message.channel.id,
            "content": content[:1500],
            "attachments": attachments,
            "created_at": message.created_at.replace(tzinfo=None).isoformat(),
            "jump_url": message.jump_url
        })
        data[gkey] = self._prune_messages(data[gkey])
        self._save_messages(data)

    @app_commands.command(name="proactivehunt_scan", description="Scan historical messages for MITRE patterns")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def proactivehunt_scan(self, interaction: discord.Interaction, pattern_id: str = None, days: int = 7, channel: discord.TextChannel = None):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        data = self._load_messages()
        gkey = str(interaction.guild.id)
        if gkey not in data or not data[gkey]:
            await interaction.response.send_message("?? No historical messages indexed yet", ephemeral=True)
            return

        patterns = self.patterns
        if pattern_id:
            if pattern_id not in patterns:
                await interaction.response.send_message("? Pattern ID not found", ephemeral=True)
                return
            patterns = {pattern_id: patterns[pattern_id]}

        cutoff = get_now_pst() - timedelta(days=max(1, days))
        channel_id = channel.id if channel else None

        matches = []
        for msg in data[gkey]:
            msg_time = datetime.fromisoformat(msg["created_at"])
            if msg_time < cutoff:
                continue
            if channel_id and msg["channel_id"] != channel_id:
                continue
            for pid, pattern in patterns.items():
                if not msg["content"]:
                    continue
                result = self._match_pattern(msg["content"], pattern)
                if result["score"] > 0:
                    matches.append({
                        "pattern_id": pid,
                        "pattern_name": pattern["name"],
                        "technique_id": pattern["technique_id"],
                        "message_id": msg["id"],
                        "channel_id": msg["channel_id"],
                        "author_id": msg["author_id"],
                        "created_at": msg["created_at"],
                        "jump_url": msg["jump_url"],
                        "score": result["score"],
                        "keywords": result["keywords"],
                        "regex": result["regex"],
                        "snippet": msg["content"][:200]
                    })

        self.hunt_counter += 1
        hunt_id = str(self.hunt_counter)
        self.hunts[hunt_id] = {
            "id": hunt_id,
            "created_at": get_now_pst().isoformat(),
            "created_by": interaction.user.id,
            "pattern_id": pattern_id,
            "days": days,
            "channel_id": channel_id,
            "match_count": len(matches),
            "matches": matches[:200]
        }
        self._save_data()

        severity = "low"
        if len(matches) >= 10:
            severity = "high"
        elif len(matches) >= 3:
            severity = "medium"

        if matches:
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity=severity,
                source="proactive_threat_hunting",
                data={
                    "hunt_id": hunt_id,
                    "match_count": len(matches),
                    "pattern_id": pattern_id,
                    "confidence": 0.75,
                    "dedup_key": f"proactive_hunt_{hunt_id}"
                }
            ))

        embed = discord.Embed(
            title=f"?? Proactive Hunt #{hunt_id}",
            color=discord.Color.orange(),
            description=f"Matches found: {len(matches)}"
        )
        embed.add_field(name="Days Scanned", value=str(days), inline=True)
        embed.add_field(name="Pattern", value=pattern_id or "All", inline=True)
        if channel:
            embed.add_field(name="Channel", value=channel.mention, inline=True)

        for match in matches[:5]:
            embed.add_field(
                name=f"{match['pattern_name']} ({match['technique_id']})",
                value=f"Author: <@{match['author_id']}> | Score: {match['score']}\n{match['snippet']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="proactivehunt_patterns", description="List active MITRE patterns")
    async def proactivehunt_patterns(self, interaction: discord.Interaction):
        if not self.patterns:
            await interaction.response.send_message("?? No patterns configured", ephemeral=True)
            return
        embed = discord.Embed(title="?? MITRE Hunt Patterns", color=discord.Color.blue())
        for pid, pattern in list(self.patterns.items())[-15:]:
            embed.add_field(
                name=f"{pid} - {pattern['name']} ({pattern['technique_id']})",
                value=f"Keywords: {', '.join(pattern.get('keywords', [])[:5])}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="proactivehunt_addpattern", description="Add MITRE hunting pattern")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def proactivehunt_addpattern(self, interaction: discord.Interaction, name: str, technique_id: str, keywords: str, regex: str = ""):
        self.pattern_counter += 1
        pid = str(self.pattern_counter)
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        regex_list = [r.strip() for r in regex.split(",") if r.strip()]
        self.patterns[pid] = {
            "id": pid,
            "name": name,
            "technique_id": technique_id,
            "keywords": keyword_list,
            "regex": regex_list,
            "created_at": get_now_pst().isoformat(),
            "created_by": interaction.user.id
        }
        self._save_data()
        await interaction.response.send_message(f"? Pattern {pid} added: {name}")

    @app_commands.command(name="proactivehunt_rmpattern", description="Remove MITRE hunting pattern")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def proactivehunt_rmpattern(self, interaction: discord.Interaction, pattern_id: str):
        if pattern_id not in self.patterns:
            await interaction.response.send_message("? Pattern not found", ephemeral=True)
            return
        self.patterns.pop(pattern_id)
        self._save_data()
        await interaction.response.send_message(f"??? Pattern {pattern_id} removed")

    @app_commands.command(name="proactivehunt_history", description="List recent proactive hunts")
    async def proactivehunt_history(self, interaction: discord.Interaction):
        if not self.hunts:
            await interaction.response.send_message("?? No hunts recorded", ephemeral=True)
            return
        embed = discord.Embed(title="?? Proactive Hunt History", color=discord.Color.blue())
        for hid, hunt in list(self.hunts.items())[-10:]:
            embed.add_field(
                name=f"Hunt #{hid}",
                value=f"Matches: {hunt['match_count']} | Days: {hunt['days']} | Created: {hunt['created_at'][:16]}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="proactivehunt_results", description="View proactive hunt results")
    async def proactivehunt_results(self, interaction: discord.Interaction, hunt_id: str):
        if hunt_id not in self.hunts:
            await interaction.response.send_message("? Hunt not found", ephemeral=True)
            return
        hunt = self.hunts[hunt_id]
        embed = discord.Embed(
            title=f"?? Hunt #{hunt_id} Results",
            color=discord.Color.orange(),
            description=f"Matches: {hunt['match_count']}"
        )
        for match in hunt.get("matches", [])[:10]:
            embed.add_field(
                name=f"{match['pattern_name']} ({match['technique_id']})",
                value=f"Author: <@{match['author_id']}> | Score: {match['score']}\n{match['snippet']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProactiveThreatHunting(bot))
