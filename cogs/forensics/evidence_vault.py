"""
Evidence Vault
Capture message evidence with hashes and chain-of-custody metadata.
"""

import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Tuple

import discord
from discord.ext import commands

from cogs.core.pst_timezone import get_now_pst


MESSAGE_LINK_RE = re.compile(r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)")


class EvidenceVault(commands.Cog):
    """Evidence vault for message capture"""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/evidence_vault.json"
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"counter": 0, "records": {}}

    def _save_data(self) -> None:
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def _next_id(self) -> str:
        self.data["counter"] += 1
        return f"EV-{self.data['counter']:06d}"

    def _hash_message(self, message: discord.Message) -> str:
        payload = {
            "message_id": message.id,
            "author_id": message.author.id,
            "content": message.content or "",
            "attachments": [a.url for a in message.attachments],
            "timestamp": message.created_at.isoformat()
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return digest

    def _parse_reference(self, ref: Optional[str], ctx: commands.Context) -> Tuple[int, int]:
        if not ref:
            return ctx.channel.id, 0

        match = MESSAGE_LINK_RE.search(ref)
        if match:
            return int(match.group(2)), int(match.group(3))

        if ref.isdigit():
            return ctx.channel.id, int(ref)

        raise ValueError("Invalid message reference")

    async def _fetch_message(self, ctx: commands.Context, ref: Optional[str]) -> discord.Message:
        channel_id, message_id = self._parse_reference(ref, ctx)
        channel = ctx.channel if channel_id == ctx.channel.id else self.bot.get_channel(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        if message_id == 0:
            async for msg in channel.history(limit=2):
                if msg.id != ctx.message.id:
                    return msg
            raise ValueError("No message available to capture")

        return await channel.fetch_message(message_id)

    def _record_chain_event(self, record: Dict, action: str, actor_id: int) -> None:
        record.setdefault("chain", []).append({
            "action": action,
            "by": str(actor_id),
            "timestamp": get_now_pst().isoformat()
        })

    @commands.command(name="evidence_capture")
    @commands.has_permissions(manage_messages=True)
    async def evidence_capture(self, ctx, reference: str = None):
        """Capture a message as evidence"""
        try:
            message = await self._fetch_message(ctx, reference)
        except ValueError as exc:
            await ctx.send(f"❌ {exc}")
            return

        evidence_id = self._next_id()
        record = {
            "id": evidence_id,
            "captured_at": get_now_pst().isoformat(),
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "channel_id": str(message.channel.id),
            "message_id": str(message.id),
            "author_id": str(message.author.id),
            "author_tag": str(message.author),
            "content": message.content or "",
            "attachments": [
                {"filename": a.filename, "url": a.url, "size": a.size}
                for a in message.attachments
            ],
            "hash": self._hash_message(message),
            "captured_by": str(ctx.author.id),
            "chain": []
        }
        self._record_chain_event(record, "captured", ctx.author.id)

        self.data["records"][evidence_id] = record
        self._save_data()

        embed = discord.Embed(
            title="🧾 Evidence Captured",
            description=f"Evidence ID: `{evidence_id}`",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Message ID", value=message.id, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Hash", value=f"`{record['hash'][:12]}...`", inline=False)
        embed.set_footer(text="Use !evidence_show <id> to review")
        await ctx.send(embed=embed)

    @commands.command(name="evidence_list")
    @commands.has_permissions(manage_messages=True)
    async def evidence_list(self, ctx, limit: int = 5):
        """List recent evidence captures"""
        limit = max(1, min(20, limit))
        records = list(self.data.get("records", {}).values())
        if not records:
            await ctx.send("✅ No evidence captured yet")
            return

        records = sorted(records, key=lambda r: r.get("captured_at", ""), reverse=True)[:limit]

        embed = discord.Embed(
            title="🧾 Evidence Vault",
            description=f"Showing {len(records)} recent captures",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )

        for record in records:
            value = (
                f"Author: <@{record['author_id']}>\n"
                f"Channel: <#{record['channel_id']}>\n"
                f"Captured: {record['captured_at']}"
            )
            embed.add_field(name=record["id"], value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="evidence_show")
    @commands.has_permissions(manage_messages=True)
    async def evidence_show(self, ctx, evidence_id: str):
        """Show evidence details"""
        record = self.data.get("records", {}).get(evidence_id)
        if not record:
            await ctx.send("❌ Evidence not found")
            return

        self._record_chain_event(record, "viewed", ctx.author.id)
        self._save_data()

        embed = discord.Embed(
            title=f"🧾 Evidence {evidence_id}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Author", value=f"<@{record['author_id']}> ({record['author_tag']})", inline=False)
        embed.add_field(name="Channel", value=f"<#{record['channel_id']}>", inline=True)
        embed.add_field(name="Message ID", value=record["message_id"], inline=True)
        embed.add_field(name="Captured", value=record["captured_at"], inline=True)
        embed.add_field(name="Hash", value=f"`{record['hash']}`", inline=False)
        embed.add_field(name="Content", value=record.get("content", "(no content)")[:1000], inline=False)

        if record.get("attachments"):
            attach_text = "\n".join([f"{a['filename']} ({a['size']} bytes)" for a in record["attachments"]])
            embed.add_field(name="Attachments", value=attach_text, inline=False)

        embed.set_footer(text="Chain-of-custody logged")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EvidenceVault(bot))
