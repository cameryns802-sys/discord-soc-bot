"""Digital Forensics Case Manager - Chain of custody with hashing"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
import hashlib
from typing import Dict
from cogs.core.pst_timezone import get_now_pst

class DigitalForensicsCaseManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/forensics_cases.json"
        self.max_attachment_hash_bytes = 10 * 1024 * 1024
        self.data = {
            "cases": {},
            "evidence": {},
            "case_counter": 0,
            "evidence_counter": 0,
            "unassigned_deleted": []
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

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    async def _hash_attachment(self, attachment: discord.Attachment) -> Dict:
        info = {
            "filename": attachment.filename,
            "size": attachment.size,
            "url": attachment.url,
            "sha256": None,
            "status": "pending"
        }
        if attachment.size > self.max_attachment_hash_bytes:
            info["status"] = "skipped_large"
            return info
        try:
            data = await attachment.read()
            info["sha256"] = hashlib.sha256(data).hexdigest()
            info["status"] = "hashed"
        except Exception:
            info["status"] = "error"
        return info

    def _create_evidence(self, guild_id: int, collected_by: int, source: str, payload: Dict) -> str:
        self.data["evidence_counter"] += 1
        evid = str(self.data["evidence_counter"])
        entry = {
            "id": evid,
            "guild_id": guild_id,
            "source": source,
            "collected_by": collected_by,
            "collected_at": get_now_pst().isoformat(),
            "payload": payload,
            "custody": [
                {
                    "action": "collected",
                    "timestamp": get_now_pst().isoformat(),
                    "user_id": collected_by,
                    "notes": source
                }
            ]
        }
        self.data["evidence"][evid] = entry
        return evid

    def _add_custody(self, evidence_id: str, action: str, user_id: int, notes: str):
        if evidence_id not in self.data["evidence"]:
            return
        self.data["evidence"][evidence_id]["custody"].append({
            "action": action,
            "timestamp": get_now_pst().isoformat(),
            "user_id": user_id,
            "notes": notes
        })

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        payload = {
            "message_id": message.id,
            "channel_id": message.channel.id,
            "author_id": message.author.id,
            "content_hash": self._hash_text(message.content or ""),
            "content_preview": (message.content or "")[:200],
            "created_at": message.created_at.replace(tzinfo=None).isoformat(),
            "deleted_at": get_now_pst().isoformat(),
            "attachments": []
        }
        for attachment in message.attachments:
            payload["attachments"].append({
                "filename": attachment.filename,
                "size": attachment.size,
                "url": attachment.url,
                "sha256": None,
                "status": "unread"
            })
        evid = self._create_evidence(message.guild.id, self.bot.user.id if self.bot.user else 0, "deleted_message", payload)
        self.data["unassigned_deleted"].append(evid)
        self._save_data()

    @app_commands.command(name="forensicscase_open", description="Open a digital forensics case")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_open(self, interaction: discord.Interaction, title: str, incident_id: str = ""):
        self.data["case_counter"] += 1
        cid = str(self.data["case_counter"])
        self.data["cases"][cid] = {
            "id": cid,
            "title": title,
            "incident_id": incident_id,
            "status": "open",
            "created_by": interaction.user.id,
            "created_at": get_now_pst().isoformat(),
            "evidence_ids": []
        }
        self._save_data()
        await interaction.response.send_message(f"? Case #{cid} opened: {title}")

    @app_commands.command(name="forensicscase_addmsg", description="Add message evidence by ID")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_addmsg(self, interaction: discord.Interaction, case_id: str, message_id: str, channel: discord.TextChannel = None):
        if case_id not in self.data["cases"]:
            await interaction.response.send_message("? Case not found", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        if channel is None:
            channel = interaction.channel
        try:
            msg = await channel.fetch_message(int(message_id))
        except Exception:
            await interaction.response.send_message("? Message not found", ephemeral=True)
            return

        payload = {
            "message_id": msg.id,
            "channel_id": msg.channel.id,
            "author_id": msg.author.id,
            "content_hash": self._hash_text(msg.content or ""),
            "content_preview": (msg.content or "")[:200],
            "created_at": msg.created_at.replace(tzinfo=None).isoformat(),
            "attachments": []
        }
        for attachment in msg.attachments:
            payload["attachments"].append(await self._hash_attachment(attachment))

        evid = self._create_evidence(interaction.guild.id, interaction.user.id, "message", payload)
        self.data["cases"][case_id]["evidence_ids"].append(evid)
        self._add_custody(evid, "linked_to_case", interaction.user.id, f"Case {case_id}")
        self._save_data()
        await interaction.response.send_message(f"?? Evidence {evid} added to Case {case_id}")

    @app_commands.command(name="forensicscase_linkdeleted", description="Link deleted-message evidence to case")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_linkdeleted(self, interaction: discord.Interaction, case_id: str, evidence_id: str):
        if case_id not in self.data["cases"]:
            await interaction.response.send_message("? Case not found", ephemeral=True)
            return
        if evidence_id not in self.data["evidence"]:
            await interaction.response.send_message("? Evidence not found", ephemeral=True)
            return
        if evidence_id in self.data["cases"][case_id]["evidence_ids"]:
            await interaction.response.send_message("?? Evidence already linked", ephemeral=True)
            return
        self.data["cases"][case_id]["evidence_ids"].append(evidence_id)
        if evidence_id in self.data["unassigned_deleted"]:
            self.data["unassigned_deleted"].remove(evidence_id)
        self._add_custody(evidence_id, "linked_to_case", interaction.user.id, f"Case {case_id}")
        self._save_data()
        await interaction.response.send_message(f"? Linked evidence {evidence_id} to case {case_id}")

    @app_commands.command(name="forensicscase_unassigned", description="List unassigned deleted-message evidence")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_unassigned(self, interaction: discord.Interaction):
        if not self.data["unassigned_deleted"]:
            await interaction.response.send_message("?? No unassigned deleted evidence", ephemeral=True)
            return
        embed = discord.Embed(title="??? Unassigned Deleted Evidence", color=discord.Color.orange())
        for evid in self.data["unassigned_deleted"][-10:]:
            payload = self.data["evidence"].get(evid, {}).get("payload", {})
            embed.add_field(
                name=f"Evidence {evid}",
                value=f"Msg: {payload.get('message_id')} | Channel: {payload.get('channel_id')}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="forensicscase_view", description="View forensics case")
    async def forensicscase_view(self, interaction: discord.Interaction, case_id: str):
        if case_id not in self.data["cases"]:
            await interaction.response.send_message("? Case not found", ephemeral=True)
            return
        case = self.data["cases"][case_id]
        embed = discord.Embed(title=f"Case #{case_id}: {case['title']}", color=discord.Color.blue())
        embed.add_field(name="Status", value=case["status"].upper(), inline=True)
        embed.add_field(name="Incident ID", value=case.get("incident_id") or "N/A", inline=True)
        embed.add_field(name="Evidence Count", value=str(len(case["evidence_ids"])), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="forensicscase_list", description="List forensics cases")
    async def forensicscase_list(self, interaction: discord.Interaction):
        if not self.data["cases"]:
            await interaction.response.send_message("?? No cases yet", ephemeral=True)
            return
        embed = discord.Embed(title="?? Forensics Cases", color=discord.Color.blue())
        for cid, case in list(self.data["cases"].items())[-10:]:
            embed.add_field(
                name=f"Case {cid} - {case['title']}",
                value=f"Status: {case['status']} | Evidence: {len(case['evidence_ids'])}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="forensicscase_close", description="Close forensics case")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_close(self, interaction: discord.Interaction, case_id: str, summary: str = "Resolved"):
        if case_id not in self.data["cases"]:
            await interaction.response.send_message("? Case not found", ephemeral=True)
            return
        self.data["cases"][case_id]["status"] = "closed"
        self.data["cases"][case_id]["closed_at"] = get_now_pst().isoformat()
        self.data["cases"][case_id]["summary"] = summary
        self._save_data()
        await interaction.response.send_message(f"? Case {case_id} closed")

    @app_commands.command(name="forensicscase_export", description="Export case evidence to JSON file")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def forensicscase_export(self, interaction: discord.Interaction, case_id: str):
        if case_id not in self.data["cases"]:
            await interaction.response.send_message("? Case not found", ephemeral=True)
            return
        case = self.data["cases"][case_id]
        evidence = [self.data["evidence"][eid] for eid in case["evidence_ids"] if eid in self.data["evidence"]]
        export_data = {
            "case": case,
            "evidence": evidence
        }
        os.makedirs("data/forensics_exports", exist_ok=True)
        export_path = f"data/forensics_exports/case_{case_id}.json"
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        await interaction.response.send_message(f"?? Exported to {export_path}")

async def setup(bot):
    await bot.add_cog(DigitalForensicsCaseManager(bot))
