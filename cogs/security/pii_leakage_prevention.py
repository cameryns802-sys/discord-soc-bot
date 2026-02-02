"""
PII Leakage Prevention: Real-time scanning, quarantine, notification, anonymization suggestions.
"""
import discord
from discord.ext import commands
import json
import os
import re
from datetime import datetime

class PIILeakagePreventionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/pii_prevention.json"
        self.data = self.load_data()
        
        # PII patterns
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
            "api_key": r"[a-zA-Z0-9_-]{32,}",
            "password": r"(password|pwd|passwd|pass)\s*[:=]\s*[^\s]+",
            "credit_card_name": r"(?:visa|mastercard|amex|american express)\s+\d+",
            "bank_account": r"account\s*[:=]\s*\d{8,17}"
        }

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "detected_leaks": [],
            "quarantined_content": [],
            "user_warnings": {},
            "scanning_enabled": True,
            "auto_delete": False,
            "notify_admins": True,
            "pii_stats": {
                "total_scans": 0,
                "leaks_found": 0,
                "messages_deleted": 0
            }
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def detect_pii(self, text):
        """Scan text for PII patterns."""
        detected = []
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detected.append({
                    "type": pii_type,
                    "value": match.group(),
                    "position": match.start()
                })
        return detected

    def anonymize_pii(self, text, pii_list):
        """Replace detected PII with anonymized markers."""
        anonymized = text
        for pii in sorted(pii_list, key=lambda p: p["position"], reverse=True):
            pii_type = pii["type"]
            mask = f"[{pii_type.upper()}]"
            anonymized = anonymized[:pii["position"]] + mask + anonymized[pii["position"]+len(pii["value"]):]
        return anonymized

    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for PII leakage."""
        if message.author.bot or not self.data["scanning_enabled"]:
            return
        
        pii_detected = self.detect_pii(message.content)
        
        if pii_detected:
            self.data["pii_stats"]["leaks_found"] += 1
            
            leak_record = {
                "user": str(message.author),
                "user_id": message.author.id,
                "channel": str(message.channel),
                "content_sample": message.content[:100],
                "pii_types": list(set(p["type"] for p in pii_detected)),
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message.id
            }
            
            self.data["detected_leaks"].append(leak_record)
            
            # Add user warning
            if message.author.id not in self.data["user_warnings"]:
                self.data["user_warnings"][str(message.author.id)] = {"count": 0, "last_incident": None}
            
            self.data["user_warnings"][str(message.author.id)]["count"] += 1
            self.data["user_warnings"][str(message.author.id)]["last_incident"] = datetime.utcnow().isoformat()
            
            self.save_data(self.data)
            
            # Notify user
            try:
                embed = discord.Embed(
                    title="⚠️ PII Leakage Detected",
                    description="Your message contained personally identifiable information.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Detected PII Types", value=", ".join(set(p["type"] for p in pii_detected)), inline=False)
                embed.add_field(name="⚠️ Action", value="Message will be reviewed by staff", inline=False)
                
                await message.author.send(embed=embed)
            except:
                pass
            
            # Optionally delete message
            if self.data["auto_delete"]:
                try:
                    await message.delete()
                    self.data["pii_stats"]["messages_deleted"] += 1
                    self.save_data(self.data)
                except:
                    pass

    @commands.command(name="scan_text_pii")
    async def scan_text_pii(self, ctx, *, text: str):
        """Scan text for PII without sending it."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        pii_detected = self.detect_pii(text)
        self.data["pii_stats"]["total_scans"] += 1
        
        if pii_detected:
            anonymized = self.anonymize_pii(text, pii_detected)
            
            embed = discord.Embed(
                title="🔍 PII Scan Results",
                description="Sensitive data detected",
                color=discord.Color.orange()
            )
            embed.add_field(name="PII Found", value=str(len(pii_detected)), inline=True)
            embed.add_field(name="Types Detected", value=", ".join(set(p["type"] for p in pii_detected)), inline=True)
            embed.add_field(name="Original", value=text[:150], inline=False)
            embed.add_field(name="Anonymized", value=anonymized[:150], inline=False)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="✅ PII Scan Passed",
                description="No PII detected in text",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        self.save_data(self.data)

    @commands.command(name="scan_channel_pii")
    async def scan_channel_pii(self, ctx, limit: int = 100):
        """Scan recent messages in channel for PII."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        channel = ctx.channel
        leaks_found = 0
        
        async for message in channel.history(limit=limit):
            if not message.author.bot:
                pii = self.detect_pii(message.content)
                if pii:
                    leaks_found += 1
                    leak_record = {
                        "user": str(message.author),
                        "user_id": message.author.id,
                        "channel": str(channel),
                        "pii_types": list(set(p["type"] for p in pii)),
                        "timestamp": datetime.utcnow().isoformat(),
                        "message_id": message.id
                    }
                    self.data["detected_leaks"].append(leak_record)
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="📊 Channel PII Scan",
            description=f"Scanned {limit} messages in {channel.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Messages Scanned", value=str(limit), inline=True)
        embed.add_field(name="Leaks Found", value=str(leaks_found), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="quarantine_message")
    async def quarantine_message(self, ctx, message_id: int, reason: str = "PII"):
        """Quarantine a message for review."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        try:
            message = await ctx.channel.fetch_message(message_id)
            
            quarantine_record = {
                "message_id": message_id,
                "author": str(message.author),
                "content": message.content[:200],
                "reason": reason,
                "quarantined_at": datetime.utcnow().isoformat(),
                "status": "QUARANTINED"
            }
            
            self.data["quarantined_content"].append(quarantine_record)
            self.save_data(self.data)
            
            embed = discord.Embed(
                title="🔒 Message Quarantined",
                description=f"Message {message_id} quarantined for review",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Author", value=str(message.author), inline=True)
            embed.add_field(name="Status", value="Under review", inline=False)
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send(f"❌ Message {message_id} not found.")

    @commands.command(name="pii_user_warnings")
    async def pii_user_warnings(self, ctx, user: discord.Member = None):
        """Check PII leak warnings for a user."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        target = user or ctx.author
        user_id_str = str(target.id)
        
        if user_id_str not in self.data["user_warnings"]:
            await ctx.send(f"✅ {target.mention} has no PII leak incidents.")
            return
        
        warnings = self.data["user_warnings"][user_id_str]
        
        embed = discord.Embed(
            title="⚠️ PII Leak Warning History",
            description=f"User: {target.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Total Incidents", value=str(warnings["count"]), inline=True)
        embed.add_field(name="Last Incident", value=warnings["last_incident"], inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="toggle_pii_scanning")
    async def toggle_pii_scanning(self, ctx):
        """Enable/disable automatic PII scanning."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        self.data["scanning_enabled"] = not self.data["scanning_enabled"]
        self.save_data(self.data)
        
        status = "✅ ENABLED" if self.data["scanning_enabled"] else "❌ DISABLED"
        
        embed = discord.Embed(
            title="🔍 PII Scanning Toggle",
            description=f"Status: {status}",
            color=discord.Color.green() if self.data["scanning_enabled"] else discord.Color.red()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="toggle_auto_delete")
    async def toggle_auto_delete(self, ctx):
        """Enable/disable automatic deletion of messages with PII."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        self.data["auto_delete"] = not self.data["auto_delete"]
        self.save_data(self.data)
        
        status = "✅ ENABLED" if self.data["auto_delete"] else "❌ DISABLED"
        
        embed = discord.Embed(
            title="🗑️ Auto-Delete Toggle",
            description=f"Status: {status}",
            color=discord.Color.red() if self.data["auto_delete"] else discord.Color.green()
        )
        embed.add_field(name="⚠️ Warning", value="Messages with detected PII will be deleted automatically", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="pii_stats")
    async def pii_stats(self, ctx):
        """View PII prevention statistics."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        stats = self.data["pii_stats"]
        
        embed = discord.Embed(
            title="📊 PII Prevention Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Scans", value=str(stats["total_scans"]), inline=True)
        embed.add_field(name="Leaks Found", value=str(stats["leaks_found"]), inline=True)
        embed.add_field(name="Messages Deleted", value=str(stats["messages_deleted"]), inline=True)
        
        if stats["leaks_found"] > 0:
            prevention_rate = (stats["messages_deleted"] / stats["leaks_found"] * 100)
            embed.add_field(name="Prevention Rate", value=f"{prevention_rate:.1f}%", inline=True)
        
        embed.add_field(name="Status", value="✅ Active" if self.data["scanning_enabled"] else "❌ Disabled", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PIILeakagePreventionCog(bot))
