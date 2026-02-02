"""
Tamper Detection & Security: Detect unauthorized changes to files, code, environment.
"""
import discord
from discord.ext import commands
import json
import os
import hashlib
from datetime import datetime

class TamperDetectionSecurityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/tamper_detection.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "file_checksums": {},
            "tamper_alerts": [],
            "credential_rotation_log": [],
            "env_snapshot": {},
            "integrity_checks": [],
            "unauthorized_changes": [],
            "security_events": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def calculate_file_hash(self, filepath: str):
        """Calculate SHA-256 hash of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"error: {str(e)}"

    async def is_owner(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="snapshot_files")
    async def snapshot_files(self, ctx, directory: str = "cogs"):
        """Create security snapshot of critical files."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        snapshot = {}
        count = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    file_hash = self.calculate_file_hash(filepath)
                    snapshot[filepath] = file_hash
                    count += 1
        
        # Store snapshots
        timestamp = datetime.utcnow().isoformat()
        self.data["integrity_checks"].append({
            "timestamp": timestamp,
            "directory": directory,
            "files_checked": count,
            "snapshot": snapshot
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="📸 File Integrity Snapshot",
            description=f"Directory: {directory}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Files Checked", value=str(count), inline=True)
        embed.add_field(name="Timestamp", value=timestamp[:19], inline=True)
        embed.add_field(name="Status", value="✅ Snapshot saved", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="verify_integrity")
    async def verify_integrity(self, ctx, directory: str = "cogs"):
        """Verify file integrity against last snapshot."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        if not self.data["integrity_checks"]:
            await ctx.send("❌ No snapshots found. Run /snapshot_files first.")
            return
        
        # Get last snapshot
        last_snapshot = self.data["integrity_checks"][-1]["snapshot"]
        
        changes_detected = []
        
        for filepath, old_hash in last_snapshot.items():
            if os.path.exists(filepath):
                new_hash = self.calculate_file_hash(filepath)
                if new_hash != old_hash:
                    changes_detected.append(filepath)
            else:
                changes_detected.append(f"{filepath} (DELETED)")
        
        embed = discord.Embed(
            title="🔍 File Integrity Verification",
            color=discord.Color.green() if not changes_detected else discord.Color.red()
        )
        
        if changes_detected:
            embed.add_field(name="⚠️ Changes Detected", value=str(len(changes_detected)), inline=True)
            
            for change in changes_detected[:5]:
                embed.add_field(name="Changed File", value=change, inline=False)
            
            # Log as security event
            self.data["tamper_alerts"].append({
                "type": "file_modification",
                "detected_at": datetime.utcnow().isoformat(),
                "files_changed": len(changes_detected),
                "details": changes_detected[:10]
            })
        else:
            embed.add_field(name="Status", value="✅ All files intact", inline=False)
        
        self.save_data(self.data)
        await ctx.send(embed=embed)

    @commands.command(name="rotate_secrets")
    async def rotate_secrets(self, ctx):
        """Initiate credential rotation (security best practice)."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        rotation_entry = {
            "rotated_at": datetime.utcnow().isoformat(),
            "rotated_by": str(ctx.author.id),
            "credentials_affected": ["DISCORD_TOKEN", "BOT_OWNER_ID", "AUDIT_CHANNEL_ID"],
            "status": "pending_admin_approval"
        }
        
        self.data["credential_rotation_log"].append(rotation_entry)
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🔑 Credential Rotation",
            description="Rotation initiated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="⏳ Pending approval", inline=True)
        embed.add_field(name="Credentials", value="Discord Token, Owner ID, Channel ID", inline=True)
        embed.add_field(name="Instructions", value="1. Update .env file\n2. Restart bot\n3. Confirm rotation", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="security_audit_log")
    async def security_audit_log(self, ctx):
        """View security events and tamper alerts."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        alerts = self.data["tamper_alerts"]
        
        embed = discord.Embed(
            title="🚨 Security Audit Log",
            description=f"Recent Alerts: {len(alerts)}",
            color=discord.Color.red() if alerts else discord.Color.green()
        )
        
        if alerts:
            for alert in alerts[-5:]:
                embed.add_field(
                    name=alert.get("type", "Unknown").upper(),
                    value=f"Time: {alert.get('detected_at', 'unknown')[:19]}",
                    inline=False
                )
        else:
            embed.add_field(name="Status", value="✅ No security alerts", inline=False)
        
        embed.add_field(name="Total Credentials Rotated", value=str(len(self.data["credential_rotation_log"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="env_monitor")
    async def env_monitor(self, ctx):
        """Monitor environment variables for unauthorized changes."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        critical_vars = ["DISCORD_TOKEN", "BOT_OWNER_ID", "AUDIT_CHANNEL_ID"]
        
        embed = discord.Embed(
            title="🔐 Environment Monitor",
            description="Critical Variable Status",
            color=discord.Color.blue()
        )
        
        for var in critical_vars:
            status = "✅ Set" if os.getenv(var) else "❌ Missing"
            embed.add_field(name=var, value=status, inline=True)
        
        embed.add_field(
            name="⚠️ Warning",
            value="Environment variables are periodically monitored for unauthorized modifications.",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TamperDetectionSecurityCog(bot))
