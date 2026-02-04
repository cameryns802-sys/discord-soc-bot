# Auto-Notification Manager: Smart alert routing and notification control
import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class AutoNotificationManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notification_rules = {}
        self.notification_history = {}
        self.rule_counter = 0
        self.notification_counter = 0
        self.user_preferences = {}
        self.data_file = "data/notifications.json"
        self.load_notifications()

    def load_notifications(self):
        """Load notification configs from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.notification_rules = data.get('rules', {})
                    self.notification_history = data.get('history', {})
                    self.user_preferences = data.get('preferences', {})
                    self.rule_counter = data.get('rule_counter', 0)
                    self.notification_counter = data.get('notification_counter', 0)
            except:
                self.notification_rules = {}

    def save_notifications(self):
        """Save notification configs to JSON file."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'rules': self.notification_rules,
                'history': self.notification_history,
                'preferences': self.user_preferences,
                'rule_counter': self.rule_counter,
                'notification_counter': self.notification_counter
            }, f, indent=2)

    @commands.command()
    async def setnotificationpreference(self, ctx, setting: str, value: str):
        """Set notification preferences. Usage: !setnotificationpreference <severity|frequency|dnd> <value>"""
        user_key = str(ctx.author.id)
        if user_key not in self.user_preferences:
            self.user_preferences[user_key] = {
                "user_id": ctx.author.id,
                "username": str(ctx.author),
                "min_severity": "medium",
                "frequency": "immediate",
                "do_not_disturb": False,
                "dnd_until": None,
                "muted_keywords": [],
                "preferred_channels": [],
                "created_at": get_now_pst().isoformat()
            }
        
        prefs = self.user_preferences[user_key]
        
        if setting == "severity":
            if value not in ['critical', 'high', 'medium', 'low']:
                await ctx.send("❌ Invalid severity. Use: critical, high, medium, low")
                return
            prefs["min_severity"] = value
            await ctx.send(f"✅ Notification severity set to {value.upper()}")
        
        elif setting == "frequency":
            if value not in ['immediate', 'batched', 'daily', 'weekly']:
                await ctx.send("❌ Invalid frequency. Use: immediate, batched, daily, weekly")
                return
            prefs["frequency"] = value
            await ctx.send(f"✅ Notification frequency set to {value.upper()}")
        
        elif setting == "dnd":
            if value.lower() == "on":
                prefs["do_not_disturb"] = True
                await ctx.send("🔕 Do Not Disturb: ON")
            else:
                prefs["do_not_disturb"] = False
                await ctx.send("🔔 Do Not Disturb: OFF")
        
        self.save_notifications()

    @commands.command()
    async def createnotificationrule(self, ctx, trigger_type: str, *, action: str):
        """Create notification rule. Usage: !createnotificationrule <alert|incident|drill|status> action"""
        valid_types = ['alert', 'incident', 'drill', 'status', 'escalation', 'remediation']
        if trigger_type not in valid_types:
            await ctx.send(f"❌ Invalid trigger type. Use: {', '.join(valid_types)}")
            return
        
        self.rule_counter += 1
        rule_id = self.rule_counter
        
        rule_data = {
            "id": rule_id,
            "trigger_type": trigger_type,
            "action": action,
            "enabled": True,
            "created_by": ctx.author.id,
            "created_at": get_now_pst().isoformat(),
            "notification_count": 0,
            "last_notified": None,
            "target_role": None,
            "target_channel": None
        }
        
        self.notification_rules[str(rule_id)] = rule_data
        self.save_notifications()
        
        embed = discord.Embed(
            title=f"✅ Notification Rule #{rule_id} Created",
            description=f"**Trigger:** {trigger_type.upper()}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="Status", value="🟢 Enabled", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setnotificationtarget(self, ctx, rule_id: int, target_type: str, target: str):
        """Set notification target (role or channel). Usage: !setnotificationtarget <rule_id> <role|channel> <@role|#channel>"""
        rule_key = str(rule_id)
        if rule_key not in self.notification_rules:
            await ctx.send("❌ Notification rule not found.")
            return
        
        rule = self.notification_rules[rule_key]
        
        if target_type == "role":
            try:
                role = await commands.RoleConverter().convert(ctx, target)
                rule["target_role"] = role.id
                await ctx.send(f"✅ Rule #{rule_id} will notify {role.mention}")
            except:
                await ctx.send("❌ Could not find role.")
                return
        
        elif target_type == "channel":
            try:
                channel = await commands.TextChannelConverter().convert(ctx, target)
                rule["target_channel"] = channel.id
                await ctx.send(f"✅ Rule #{rule_id} will notify in {channel.mention}")
            except:
                await ctx.send("❌ Could not find channel.")
                return
        
        self.save_notifications()

    @commands.command()
    async def mutenotificationkeyword(self, ctx, *, keyword: str):
        """Mute notifications containing keyword. Usage: !mutenotificationkeyword <keyword>"""
        user_key = str(ctx.author.id)
        if user_key not in self.user_preferences:
            self.user_preferences[user_key] = {
                "user_id": ctx.author.id,
                "username": str(ctx.author),
                "min_severity": "medium",
                "frequency": "immediate",
                "do_not_disturb": False,
                "dnd_until": None,
                "muted_keywords": [],
                "preferred_channels": [],
                "created_at": get_now_pst().isoformat()
            }
        
        prefs = self.user_preferences[user_key]
        if keyword not in prefs["muted_keywords"]:
            prefs["muted_keywords"].append(keyword)
            self.save_notifications()
            await ctx.send(f"🔇 Notifications with '{keyword}' will be muted.")
        else:
            await ctx.send(f"ℹ️ '{keyword}' is already muted.")

    @commands.command()
    async def unmutenotificationkeyword(self, ctx, *, keyword: str):
        """Unmute notifications containing keyword. Usage: !unmutenotificationkeyword <keyword>"""
        user_key = str(ctx.author.id)
        if user_key not in self.user_preferences:
            await ctx.send(f"ℹ️ '{keyword}' is not muted.")
            return
        
        prefs = self.user_preferences[user_key]
        if keyword in prefs["muted_keywords"]:
            prefs["muted_keywords"].remove(keyword)
            self.save_notifications()
            await ctx.send(f"🔔 Notifications with '{keyword}' will now show.")
        else:
            await ctx.send(f"ℹ️ '{keyword}' is not muted.")

    @commands.command()
    async def mynotificationpreferences(self, ctx):
        """View your notification preferences."""
        user_key = str(ctx.author.id)
        if user_key not in self.user_preferences:
            await ctx.send("ℹ️ You have no notification preferences set.")
            return
        
        prefs = self.user_preferences[user_key]
        
        embed = discord.Embed(
            title="🔔 Your Notification Preferences",
            color=discord.Color.blue()
        )
        embed.add_field(name="Min Severity", value=prefs["min_severity"].upper(), inline=True)
        embed.add_field(name="Frequency", value=prefs["frequency"].upper(), inline=True)
        embed.add_field(name="Do Not Disturb", value="✅ ON" if prefs["do_not_disturb"] else "❌ OFF", inline=True)
        embed.add_field(name="Muted Keywords", value=", ".join(prefs["muted_keywords"]) if prefs["muted_keywords"] else "None", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def togglenotificationrule(self, ctx, rule_id: int):
        """Enable/disable notification rule. Usage: !togglenotificationrule <rule_id>"""
        rule_key = str(rule_id)
        if rule_key not in self.notification_rules:
            await ctx.send("❌ Notification rule not found.")
            return
        
        rule = self.notification_rules[rule_key]
        rule["enabled"] = not rule["enabled"]
        self.save_notifications()
        
        status = "🟢 ENABLED" if rule["enabled"] else "🔴 DISABLED"
        await ctx.send(f"✅ Rule #{rule_id} is now {status}")

    @commands.command()
    async def listnotificationrules(self, ctx):
        """List all notification rules."""
        if not self.notification_rules:
            await ctx.send("ℹ️ No notification rules.")
            return
        
        embed = discord.Embed(
            title=f"🔔 Notification Rules ({len(self.notification_rules)})",
            color=discord.Color.blue()
        )
        
        for rule_id, rule in list(self.notification_rules.items())[:10]:
            status = "🟢 ENABLED" if rule["enabled"] else "🔴 DISABLED"
            embed.add_field(
                name=f"#{rule_id} | {rule['trigger_type'].upper()}",
                value=f"{rule['action']}\n{status} | Notifications: {rule['notification_count']}x",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def notificationstats(self, ctx):
        """View notification statistics."""
        embed = discord.Embed(
            title="🔔 Notification Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Active Rules", value=sum(1 for r in self.notification_rules.values() if r["enabled"]), inline=True)
        embed.add_field(name="Total Rules", value=len(self.notification_rules), inline=True)
        embed.add_field(name="Total Notifications Sent", value=sum(r.get("notification_count", 0) for r in self.notification_rules.values()), inline=True)
        embed.add_field(name="Users with Preferences", value=len(self.user_preferences), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoNotificationManagerCog(bot))
