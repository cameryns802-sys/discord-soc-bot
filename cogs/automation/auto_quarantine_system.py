# Auto-Quarantine System: Isolate suspicious users and channels
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
from cogs.core.pst_timezone import get_now_pst

class AutoQuarantineSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quarantine_rules = {}
        self.quarantined_items = {}
        self.rule_counter = 0
        self.quarantine_counter = 0
        self.data_file = "data/quarantine.json"
        self.load_quarantine()

    def load_quarantine(self):
        """Load quarantine data from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.quarantine_rules = data.get('rules', {})
                    self.quarantined_items = data.get('quarantined', {})
                    self.rule_counter = data.get('rule_counter', 0)
                    self.quarantine_counter = data.get('quarantine_counter', 0)
            except:
                self.quarantine_rules = {}

    def save_quarantine(self):
        """Save quarantine data to JSON file."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'rules': self.quarantine_rules,
                'quarantined': self.quarantined_items,
                'rule_counter': self.rule_counter,
                'quarantine_counter': self.quarantine_counter
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createquarantinerule(self, ctx, item_type: str, trigger: str, *, action: str):
        """Create quarantine rule. Usage: !createquarantinerule <user|channel> <trigger> action"""
        valid_types = ['user', 'channel']
        if item_type not in valid_types:
            await ctx.send(f"❌ Invalid type. Use: {', '.join(valid_types)}")
            return
        
        valid_triggers = ['suspicious_activity', 'multiple_reports', 'policy_violation', 'phishing', 'spam', 'abuse']
        if trigger not in valid_triggers:
            await ctx.send(f"❌ Invalid trigger. Use: {', '.join(valid_triggers)}")
            return
        
        self.rule_counter += 1
        rule_id = self.rule_counter
        
        rule_data = {
            "id": rule_id,
            "item_type": item_type,
            "trigger": trigger,
            "action": action,
            "enabled": True,
            "created_by": ctx.author.id,
            "created_at": get_now_pst().isoformat(),
            "enforcement_count": 0,
            "last_enforced": None
        }
        
        self.quarantine_rules[str(rule_id)] = rule_data
        self.save_quarantine()
        
        embed = discord.Embed(
            title=f"✅ Quarantine Rule #{rule_id} Created",
            description=f"**Type:** {item_type.upper()}\n**Trigger:** {trigger}",
            color=discord.Color.red()
        )
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="Status", value="🟢 Enabled", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quarantineuser(self, ctx, user: discord.Member, *, reason: str = "Suspicious activity"):
        """Quarantine a user. Usage: !quarantineuser @user [reason]"""
        self.quarantine_counter += 1
        quarantine_id = self.quarantine_counter
        
        # Create quarantine role if not exists
        try:
            quarantine_role = discord.utils.get(ctx.guild.roles, name="Quarantined")
            if not quarantine_role:
                quarantine_role = await ctx.guild.create_role(
                    name="Quarantined",
                    color=discord.Color.red(),
                    reason="Auto quarantine role"
                )
        except:
            await ctx.send("❌ Could not create/find quarantine role.")
            return
        
        try:
            await user.add_roles(quarantine_role)
        except:
            await ctx.send("❌ Could not add quarantine role to user.")
            return
        
        quarantine_data = {
            "id": quarantine_id,
            "item_type": "user",
            "item_id": user.id,
            "item_name": str(user),
            "reason": reason,
            "quarantined_by": ctx.author.id,
            "quarantined_at": get_now_pst().isoformat(),
            "released": False,
            "released_at": None,
            "duration_minutes": None
        }
        
        self.quarantined_items[str(quarantine_id)] = quarantine_data
        self.save_quarantine()
        
        embed = discord.Embed(
            title=f"🔒 User Quarantined #{quarantine_id}",
            description=f"{user.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Quarantined By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Time", value=get_now_pst().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quarantinechannel(self, ctx, channel: discord.TextChannel, *, reason: str = "Suspicious activity"):
        """Quarantine a channel. Usage: !quarantinechannel #channel [reason]"""
        self.quarantine_counter += 1
        quarantine_id = self.quarantine_counter
        
        # Remove send permissions from @everyone
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        except:
            await ctx.send("❌ Could not modify channel permissions.")
            return
        
        quarantine_data = {
            "id": quarantine_id,
            "item_type": "channel",
            "item_id": channel.id,
            "item_name": channel.name,
            "reason": reason,
            "quarantined_by": ctx.author.id,
            "quarantined_at": get_now_pst().isoformat(),
            "released": False,
            "released_at": None,
            "duration_minutes": None
        }
        
        self.quarantined_items[str(quarantine_id)] = quarantine_data
        self.save_quarantine()
        
        embed = discord.Embed(
            title=f"🔒 Channel Quarantined #{quarantine_id}",
            description=f"{channel.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Quarantined By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="🔴 LOCKED", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def releaseuser(self, ctx, quarantine_id: int):
        """Release quarantined user. Usage: !releaseuser <quarantine_id>"""
        quarantine_key = str(quarantine_id)
        if quarantine_key not in self.quarantined_items:
            await ctx.send("❌ Quarantine record not found.")
            return
        
        quarantine = self.quarantined_items[quarantine_key]
        if quarantine["item_type"] != "user":
            await ctx.send("❌ This quarantine is not for a user.")
            return
        
        try:
            user = await self.bot.fetch_user(quarantine["item_id"])
            quarantine_role = discord.utils.get(ctx.guild.roles, name="Quarantined")
            if quarantine_role:
                member = ctx.guild.get_member(user.id)
                if member:
                    await member.remove_roles(quarantine_role)
        except:
            pass
        
        quarantine["released"] = True
        quarantine["released_at"] = get_now_pst().isoformat()
        self.save_quarantine()
        
        embed = discord.Embed(
            title=f"✅ User Released from Quarantine #{quarantine_id}",
            description=f"{quarantine['item_name']}",
            color=discord.Color.green()
        )
        embed.add_field(name="Released By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Released At", value=get_now_pst().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def releasechannel(self, ctx, quarantine_id: int):
        """Release quarantined channel. Usage: !releasechannel <quarantine_id>"""
        quarantine_key = str(quarantine_id)
        if quarantine_key not in self.quarantined_items:
            await ctx.send("❌ Quarantine record not found.")
            return
        
        quarantine = self.quarantined_items[quarantine_key]
        if quarantine["item_type"] != "channel":
            await ctx.send("❌ This quarantine is not for a channel.")
            return
        
        try:
            channel = self.bot.get_channel(quarantine["item_id"])
            if channel:
                await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        except:
            pass
        
        quarantine["released"] = True
        quarantine["released_at"] = get_now_pst().isoformat()
        self.save_quarantine()
        
        embed = discord.Embed(
            title=f"✅ Channel Released from Quarantine #{quarantine_id}",
            description=f"{quarantine['item_name']}",
            color=discord.Color.green()
        )
        embed.add_field(name="Released By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Released At", value=get_now_pst().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def listquarantined(self, ctx):
        """List all quarantined items."""
        if not self.quarantined_items:
            await ctx.send("ℹ️ No quarantined items.")
            return
        
        embed = discord.Embed(
            title=f"🔒 Quarantined Items ({len(self.quarantined_items)})",
            color=discord.Color.red()
        )
        
        for q_id, quarantine in list(self.quarantined_items.items())[:10]:
            status = "🔴 LOCKED" if not quarantine["released"] else "✅ RELEASED"
            embed.add_field(
                name=f"#{q_id} | {quarantine['item_type'].upper()}",
                value=f"{quarantine['item_name']}\nReason: {quarantine['reason']}\nStatus: {status}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def quarantinestats(self, ctx):
        """View quarantine statistics."""
        active = sum(1 for q in self.quarantined_items.values() if not q["released"])
        released = sum(1 for q in self.quarantined_items.values() if q["released"])
        
        embed = discord.Embed(
            title="🔒 Quarantine Statistics",
            color=discord.Color.red()
        )
        embed.add_field(name="Total Quarantines", value=len(self.quarantined_items), inline=True)
        embed.add_field(name="Active", value=f"🔴 {active}", inline=True)
        embed.add_field(name="Released", value=f"✅ {released}", inline=True)
        embed.add_field(name="Active Rules", value=sum(1 for r in self.quarantine_rules.values() if r["enabled"]), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoQuarantineSystemCog(bot))
