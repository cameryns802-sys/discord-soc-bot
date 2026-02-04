"""On-Call Scheduler & War Room: Consolidated command groups"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from cogs.core.pst_timezone import get_now_pst

class OnCallGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="oncall", description="On-call scheduler commands")
        self.cog = cog

    @app_commands.command(name="create_rotation", description="Create on-call rotation")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_rotation(self, interaction: discord.Interaction, name: str, shift_hours: int = 24):
        self.cog.schedule_counter += 1
        schedule_id = self.cog.schedule_counter
        self.cog.schedules[str(schedule_id)] = {"id": schedule_id, "name": name, "shift_hours": shift_hours, "created_at": get_now_pst().isoformat(), "active": True, "members": [], "current_on_call": None, "current_shift_start": None, "shift_count": 0}
        self.cog.save_schedules()
        await interaction.response.send_message(f"✅ Created rotation #{schedule_id}: {name}")

    @app_commands.command(name="add_member", description="Add member to rotation")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_member(self, interaction: discord.Interaction, rotation_id: int, member: discord.Member):
        schedule_key = str(rotation_id)
        if schedule_key not in self.cog.schedules:
            await interaction.response.send_message("❌ Rotation not found", ephemeral=True)
            return
        if member.id not in self.cog.schedules[schedule_key]["members"]:
            self.cog.schedules[schedule_key]["members"].append(member.id)
            self.cog.save_schedules()
            await interaction.response.send_message(f"✅ Added {member.mention} to rotation #{rotation_id}")
        else:
            await interaction.response.send_message(f"❌ {member.mention} already in rotation", ephemeral=True)

    @app_commands.command(name="start_shift", description="Start next shift in rotation")
    @app_commands.checks.has_permissions(administrator=True)
    async def start_shift(self, interaction: discord.Interaction, rotation_id: int):
        schedule_key = str(rotation_id)
        if schedule_key not in self.cog.schedules:
            await interaction.response.send_message("❌ Rotation not found", ephemeral=True)
            return
        schedule = self.cog.schedules[schedule_key]
        if not schedule["members"]:
            await interaction.response.send_message("❌ No members in rotation", ephemeral=True)
            return
        current_idx = schedule["members"].index(schedule["current_on_call"]) if schedule["current_on_call"] in schedule["members"] else -1
        next_idx = (current_idx + 1) % len(schedule["members"])
        schedule["current_on_call"] = schedule["members"][next_idx]
        schedule["current_shift_start"] = get_now_pst().isoformat()
        schedule["shift_count"] += 1
        self.cog.save_schedules()
        await interaction.response.send_message(f"📞 Shift #{schedule['shift_count']} started - On-call: <@{schedule['current_on_call']}>")

    @app_commands.command(name="whoisoncall", description="View current on-call member")
    async def whoisoncall(self, interaction: discord.Interaction, rotation_id: int = None):
        if rotation_id:
            schedule_key = str(rotation_id)
            if schedule_key not in self.cog.schedules:
                await interaction.response.send_message("❌ Rotation not found", ephemeral=True)
                return
            schedule = self.cog.schedules[schedule_key]
            if schedule["current_on_call"]:
                await interaction.response.send_message(f"📞 On-call for {schedule['name']}: <@{schedule['current_on_call']}>")
            else:
                await interaction.response.send_message("ℹ️ No one on-call", ephemeral=True)
        else:
            embed = discord.Embed(title="📞 On-Call Rotations", color=discord.Color.blue())
            for sch in self.cog.schedules.values():
                on_call_str = f"<@{sch['current_on_call']}>" if sch["current_on_call"] else "None"
                embed.add_field(name=sch['name'], value=f"On-Call: {on_call_str}", inline=False)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View on-call statistics")
    async def stats(self, interaction: discord.Interaction):
        total_shifts = sum(s.get('shift_count', 0) for s in self.cog.schedules.values())
        embed = discord.Embed(title="📊 On-Call Statistics", color=discord.Color.blue())
        embed.add_field(name="Active Rotations", value=len(self.cog.schedules), inline=True)
        embed.add_field(name="Total Shifts", value=total_shifts, inline=True)
        await interaction.response.send_message(embed=embed)

class WarRoomGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="warroom", description="War room commands")
        self.cog = cog

    @app_commands.command(name="create", description="Create war room for incident")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def create(self, interaction: discord.Interaction, severity: str, title: str):
        severity = severity.lower()
        if severity not in ["critical", "high", "medium", "low"]:
            await interaction.response.send_message("❌ Severity must be: critical, high, medium, low", ephemeral=True)
            return
        self.cog.room_counter += 1
        room_id = self.cog.room_counter
        color_map = {"critical": 0xFF0000, "high": 0xFF6600, "medium": 0xFFCC00, "low": 0x00CCFF}
        category = discord.utils.get(interaction.guild.categories, name="WAR ROOMS")
        if not category:
            category = await interaction.guild.create_category("WAR ROOMS")
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        channel_name = f"war-room-{room_id}-{severity}"
        channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites, topic=f"Incident Response: {title}")
        self.cog.war_rooms[str(room_id)] = {"id": room_id, "title": title, "severity": severity, "channel_id": channel.id, "created_by": interaction.user.id, "created_at": get_now_pst().isoformat(), "status": "active", "participants": [interaction.user.id], "messages_count": 0, "resolution": None}
        await interaction.response.send_message(f"🚨 War Room #{room_id} created: {channel.mention}")
        await channel.send(embed=discord.Embed(title="War Room Initialized", description=f"**Incident**: {title}\n**Severity**: {severity.upper()}", color=color_map[severity]))

    @app_commands.command(name="invite", description="Invite user to war room")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def invite(self, interaction: discord.Interaction, room_id: int, member: discord.Member):
        room_key = str(room_id)
        if room_key not in self.cog.war_rooms:
            await interaction.response.send_message("❌ War room not found", ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.cog.war_rooms[room_key]["channel_id"])
        if not channel:
            await interaction.response.send_message("❌ Channel not found", ephemeral=True)
            return
        await channel.set_permissions(member, read_messages=True, send_messages=True)
        if member.id not in self.cog.war_rooms[room_key]["participants"]:
            self.cog.war_rooms[room_key]["participants"].append(member.id)
        await interaction.response.send_message(f"✅ {member.mention} invited to war room #{room_id}")

    @app_commands.command(name="status", description="View war room status")
    async def status(self, interaction: discord.Interaction, room_id: int):
        room_key = str(room_id)
        if room_key not in self.cog.war_rooms:
            await interaction.response.send_message("❌ War room not found", ephemeral=True)
            return
        room = self.cog.war_rooms[room_key]
        embed = discord.Embed(title=f"War Room #{room_id} Status", description=room["title"], color=discord.Color.blue())
        embed.add_field(name="Severity", value=room["severity"].upper(), inline=True)
        embed.add_field(name="Status", value=room["status"].upper(), inline=True)
        embed.add_field(name="Participants", value=len(room["participants"]), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="close", description="Close war room")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def close(self, interaction: discord.Interaction, room_id: int, resolution: str = "Resolved"):
        room_key = str(room_id)
        if room_key not in self.cog.war_rooms:
            await interaction.response.send_message("❌ War room not found", ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.cog.war_rooms[room_key]["channel_id"])
        if channel:
            await channel.delete(reason=f"War room closed: {resolution}")
        self.cog.war_rooms[room_key]["status"] = "closed"
        self.cog.war_rooms[room_key]["resolution"] = resolution
        await interaction.response.send_message(f"✅ War room #{room_id} closed")

    @app_commands.command(name="list", description="List all war rooms")
    async def list(self, interaction: discord.Interaction):
        active_rooms = [r for r in self.cog.war_rooms.values() if r["status"] == "active"]
        if not active_rooms:
            await interaction.response.send_message("ℹ️ No active war rooms", ephemeral=True)
            return
        embed = discord.Embed(title="🚨 Active War Rooms", color=discord.Color.orange())
        for room in active_rooms:
            embed.add_field(name=f"#{room['id']} - {room['severity'].upper()}", value=f"{room['title']}\nParticipants: {len(room['participants'])}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="summary", description="Generate war room summary")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def summary(self, interaction: discord.Interaction, room_id: int):
        room_key = str(room_id)
        if room_key not in self.cog.war_rooms:
            await interaction.response.send_message("❌ War room not found", ephemeral=True)
            return
        room = self.cog.war_rooms[room_key]
        embed = discord.Embed(title=f"📊 War Room #{room_id} Summary", description=room["title"], color=discord.Color.blue())
        embed.add_field(name="Severity", value=room["severity"].upper(), inline=True)
        embed.add_field(name="Status", value=room["status"].upper(), inline=True)
        embed.add_field(name="Participants", value=len(room["participants"]), inline=True)
        if room.get("resolution"):
            embed.add_field(name="Resolution", value=room["resolution"], inline=False)
        await interaction.response.send_message(embed=embed)

class OnCallWarRoomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedules = {}
        self.schedule_counter = 0
        self.on_call_log = []
        self.war_rooms = {}
        self.room_counter = 0
        self.data_file_oncall = "data/on_call_scheduler.json"
        self.load_schedules()
        self.oncall_group = OnCallGroup(self)
        self.warroom_group = WarRoomGroup(self)
        bot.tree.add_command(self.oncall_group)
        bot.tree.add_command(self.warroom_group)

    def load_schedules(self):
        if os.path.exists(self.data_file_oncall):
            try:
                with open(self.data_file_oncall, 'r') as f:
                    data = json.load(f)
                    self.schedules = data.get('schedules', {})
                    self.on_call_log = data.get('on_call_log', [])
                    self.schedule_counter = data.get('schedule_counter', 0)
            except: pass

    def save_schedules(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file_oncall, 'w') as f:
            json.dump({'schedules': self.schedules, 'on_call_log': self.on_call_log[-500:], 'schedule_counter': self.schedule_counter}, f, indent=2)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for room in self.war_rooms.values():
            if message.channel.id == room["channel_id"]:
                room["messages_count"] += 1
                break

    async def cog_unload(self):
        self.bot.tree.remove_command(self.oncall_group.name)
        self.bot.tree.remove_command(self.warroom_group.name)

async def setup(bot):
    await bot.add_cog(OnCallWarRoomCog(bot))
