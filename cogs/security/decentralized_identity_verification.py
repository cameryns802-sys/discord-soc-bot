"""Decentralized Identity Verification - Proof capture and approval workflow"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import hashlib
import json
import os
from cogs.core.pst_timezone import get_now_pst

class DecentralizedIdentityVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/identity_verifications.json"
        self.data = {
            "pending": {},
            "verifications": {},
            "counter": 0,
            "config": {}
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

    def _hash_proof(self, proof: str) -> str:
        return hashlib.sha256(proof.encode("utf-8", errors="ignore")).hexdigest()

    def _get_guild_config(self, guild_id: int) -> dict:
        gkey = str(guild_id)
        if gkey not in self.data["config"]:
            self.data["config"][gkey] = {
                "verification_role": "Verified",
                "providers": ["oidc", "sso", "did", "pgp"]
            }
        return self.data["config"][gkey]

    @app_commands.command(name="idverify_start", description="Start identity verification")
    async def idverify_start(self, interaction: discord.Interaction, provider: str, identity: str):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        config = self._get_guild_config(interaction.guild.id)
        if provider.lower() not in config["providers"]:
            await interaction.response.send_message("? Provider not supported", ephemeral=True)
            return
        self.data["counter"] += 1
        pid = str(self.data["counter"])
        nonce = hashlib.sha256(f"{interaction.user.id}-{get_now_pst().isoformat()}".encode()).hexdigest()[:10]
        self.data["pending"][pid] = {
            "id": pid,
            "user_id": interaction.user.id,
            "provider": provider.lower(),
            "identity": identity,
            "nonce": nonce,
            "created_at": get_now_pst().isoformat(),
            "expires_at": (get_now_pst() + timedelta(hours=24)).isoformat(),
            "status": "pending"
        }
        self._save_data()
        await interaction.response.send_message(
            f"?? Verification started. Pending ID: {pid}\n"
            f"Include nonce `{nonce}` in your proof and submit with /idverify_submit",
            ephemeral=True
        )

    @app_commands.command(name="idverify_submit", description="Submit identity proof")
    async def idverify_submit(self, interaction: discord.Interaction, pending_id: str, proof: str):
        if pending_id not in self.data["pending"]:
            await interaction.response.send_message("? Pending request not found", ephemeral=True)
            return
        pending = self.data["pending"][pending_id]
        if pending["user_id"] != interaction.user.id:
            await interaction.response.send_message("? You can only submit your own request", ephemeral=True)
            return
        pending["proof_hash"] = self._hash_proof(proof)
        pending["submitted_at"] = get_now_pst().isoformat()
        pending["status"] = "submitted"
        self._save_data()
        await interaction.response.send_message("? Proof submitted. Awaiting staff approval.", ephemeral=True)

    @app_commands.command(name="idverify_approve", description="Approve identity verification")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def idverify_approve(self, interaction: discord.Interaction, pending_id: str):
        if pending_id not in self.data["pending"]:
            await interaction.response.send_message("? Pending request not found", ephemeral=True)
            return
        pending = self.data["pending"].pop(pending_id)
        gkey = str(interaction.guild.id)
        self.data["verifications"][str(pending["user_id"])] = {
            "provider": pending["provider"],
            "identity": pending["identity"],
            "proof_hash": pending.get("proof_hash"),
            "verified_by": interaction.user.id,
            "verified_at": get_now_pst().isoformat(),
            "status": "verified"
        }
        self._save_data()

        role_name = self._get_guild_config(interaction.guild.id).get("verification_role")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        member = interaction.guild.get_member(pending["user_id"])
        if role and member:
            try:
                await member.add_roles(role, reason="Identity verification approved")
            except Exception:
                pass

        await interaction.response.send_message(f"? Approved verification for <@{pending['user_id']}>.")

    @app_commands.command(name="idverify_reject", description="Reject identity verification")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def idverify_reject(self, interaction: discord.Interaction, pending_id: str, reason: str = "Insufficient proof"):
        if pending_id not in self.data["pending"]:
            await interaction.response.send_message("? Pending request not found", ephemeral=True)
            return
        pending = self.data["pending"].pop(pending_id)
        self._save_data()
        await interaction.response.send_message(f"?? Rejected verification for <@{pending['user_id']}>: {reason}")

    @app_commands.command(name="idverify_status", description="Check verification status")
    async def idverify_status(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        record = self.data["verifications"].get(str(member.id))
        if not record:
            await interaction.response.send_message("?? No verification on record", ephemeral=True)
            return
        embed = discord.Embed(title="?? Identity Verification", color=discord.Color.green())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Provider", value=record.get("provider"), inline=True)
        embed.add_field(name="Identity", value=record.get("identity"), inline=False)
        embed.add_field(name="Verified At", value=record.get("verified_at"), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="idverify_config", description="Configure identity verification")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def idverify_config(self, interaction: discord.Interaction, verification_role: str):
        config = self._get_guild_config(interaction.guild.id)
        config["verification_role"] = verification_role
        self._save_data()
        await interaction.response.send_message(f"? Verification role set to {verification_role}")

    @app_commands.command(name="idverify_addprovider", description="Add allowed identity provider")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def idverify_addprovider(self, interaction: discord.Interaction, provider: str):
        config = self._get_guild_config(interaction.guild.id)
        if provider.lower() not in config["providers"]:
            config["providers"].append(provider.lower())
            self._save_data()
        await interaction.response.send_message(f"? Provider added: {provider}")

    @app_commands.command(name="idverify_removeprovider", description="Remove allowed identity provider")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def idverify_removeprovider(self, interaction: discord.Interaction, provider: str):
        config = self._get_guild_config(interaction.guild.id)
        if provider.lower() in config["providers"]:
            config["providers"].remove(provider.lower())
            self._save_data()
        await interaction.response.send_message(f"??? Provider removed: {provider}")

async def setup(bot):
    await bot.add_cog(DecentralizedIdentityVerification(bot))
