"""Staff Scheduling & Rotation - On-call shifts with role updates and clock-in/out"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from cogs.core.pst_timezone import get_now_pst

class StaffSchedulingRotation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/staff_schedules.json"
        self.data = {
            "schedules": {},
            "counter": 0,
            "clock_log": [],
            "config": {}
        }
        self._load_data()
        self.rotation_task.start()

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

    def _get_config(self, guild_id: int) -> dict:
        gkey = str(guild_id)
        if gkey not in self.data["config"]:
            self.data["config"][gkey] = {
                "on_shift_role": "On Shift"
            }
        return self.data["config"][gkey]

    async def _ensure_role(self, guild: discord.Guild, role_name: str) -> discord.Role:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            return role
        try:
            return await guild.create_role(name=role_name, reason="Staff scheduling role")
        except Exception:
            return None

    async def _update_on_call_role(self, guild: discord.Guild, member_id: int, role_name: str, add: bool):
        member = guild.get_member(member_id)
        if not member:
            return
        role = await self._ensure_role(guild, role_name)
        if not role:
            return
        try:
            if add:
                await member.add_roles(role, reason="On-call rotation")
            else:
                await member.remove_roles(role, reason="On-call rotation")
        except Exception:
            pass

    @tasks.loop(minutes=1)
    async def rotation_task(self):
        now = get_now_pst()
        for gkey, schedules in self._schedules_by_guild().items():
            guild = self.bot.get_guild(int(gkey))
            if not guild:
                continue
            for schedule in schedules:
                next_rot = schedule.get("next_rotation_at")
                if not next_rot:
                    continue
                if now >= datetime.fromisoformat(next_rot):
                    await self._rotate_schedule(guild, schedule["id"], auto=True)

    def _schedules_by_guild(self) -> dict:
        grouped = {}
        for sid, schedule in self.data["schedules"].items():
            gkey = str(schedule["guild_id"])
            grouped.setdefault(gkey, []).append(schedule)
        return grouped

    async def _rotate_schedule(self, guild: discord.Guild, schedule_id: str, auto: bool = False):
        schedule = self.data["schedules"].get(schedule_id)
        if not schedule or not schedule["members"]:
            return
        members = schedule["members"]
        current = schedule.get("current_on_call")
        current_idx = members.index(current) if current in members else -1
        next_idx = (current_idx + 1) % len(members)
        next_member = members[next_idx]

        role_name = schedule.get("role_name") or "On Call"
        if current:
            await self._update_on_call_role(guild, current, role_name, add=False)
        await self._update_on_call_role(guild, next_member, role_name, add=True)

        schedule["current_on_call"] = next_member
        schedule["current_shift_start"] = get_now_pst().isoformat()
        schedule["shift_count"] = schedule.get("shift_count", 0) + 1
        schedule["next_rotation_at"] = (get_now_pst() + timedelta(hours=schedule["shift_hours"])).isoformat()
        self._save_data()

        if auto:
            channel = guild.system_channel
            if channel and channel.permissions_for(guild.me).send_messages:
                await channel.send(f"?? Rotation updated for {schedule['name']}: <@{next_member}> is now on-call")

    @app_commands.command(name="staffschedule_create", description="Create staff on-call schedule")
    @app_commands.checks.has_permissions(administrator=True)
    async def staffschedule_create(self, interaction: discord.Interaction, name: str, shift_hours: int = 24, role_name: str = "On Call"):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        self.data["counter"] += 1
        sid = str(self.data["counter"])
        self.data["schedules"][sid] = {
            "id": sid,
            "guild_id": interaction.guild.id,
            "name": name,
            "shift_hours": max(1, shift_hours),
            "role_name": role_name,
            "members": [],
            "current_on_call": None,
            "current_shift_start": None,
            "shift_count": 0,
            "next_rotation_at": None
        }
        self._save_data()
        await interaction.response.send_message(f"? Created schedule #{sid}: {name}")

    @app_commands.command(name="staffschedule_addmember", description="Add member to staff schedule")
    @app_commands.checks.has_permissions(administrator=True)
    async def staffschedule_addmember(self, interaction: discord.Interaction, schedule_id: str, member: discord.Member):
        schedule = self.data["schedules"].get(schedule_id)
        if not schedule:
            await interaction.response.send_message("? Schedule not found", ephemeral=True)
            return
        if member.id not in schedule["members"]:
            schedule["members"].append(member.id)
            self._save_data()
        await interaction.response.send_message(f"? Added {member.mention} to schedule {schedule_id}")

    @app_commands.command(name="staffschedule_removemember", description="Remove member from staff schedule")
    @app_commands.checks.has_permissions(administrator=True)
    async def staffschedule_removemember(self, interaction: discord.Interaction, schedule_id: str, member: discord.Member):
        schedule = self.data["schedules"].get(schedule_id)
        if not schedule:
            await interaction.response.send_message("? Schedule not found", ephemeral=True)
            return
        if member.id in schedule["members"]:
            schedule["members"].remove(member.id)
            self._save_data()
        await interaction.response.send_message(f"? Removed {member.mention} from schedule {schedule_id}")

    @app_commands.command(name="staffschedule_start", description="Start/rotate on-call shift")
    @app_commands.checks.has_permissions(administrator=True)
    async def staffschedule_start(self, interaction: discord.Interaction, schedule_id: str):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        await self._rotate_schedule(interaction.guild, schedule_id)
        await interaction.response.send_message(f"?? Rotation executed for schedule {schedule_id}")

    @app_commands.command(name="staffschedule_status", description="View schedule status")
    async def staffschedule_status(self, interaction: discord.Interaction, schedule_id: str = ""):
        if schedule_id:
            schedule = self.data["schedules"].get(schedule_id)
            if not schedule:
                await interaction.response.send_message("? Schedule not found", ephemeral=True)
                return
            embed = discord.Embed(title=f"Schedule {schedule_id}: {schedule['name']}", color=discord.Color.blue())
            embed.add_field(name="On-Call", value=f"<@{schedule['current_on_call']}>" if schedule.get("current_on_call") else "None", inline=True)
            embed.add_field(name="Next Rotation", value=schedule.get("next_rotation_at") or "Not scheduled", inline=True)
            embed.add_field(name="Members", value=str(len(schedule["members"])), inline=True)
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="?? Staff Schedules", color=discord.Color.blue())
        for sid, schedule in self.data["schedules"].items():
            embed.add_field(
                name=f"{sid} - {schedule['name']}",
                value=f"On-Call: {schedule.get('current_on_call') or 'None'} | Members: {len(schedule['members'])}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="staffschedule_clockin", description="Clock in for accountability")
    async def staffschedule_clockin(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        entry = {
            "user_id": interaction.user.id,
            "action": "clock_in",
            "timestamp": get_now_pst().isoformat()
        }
        self.data["clock_log"].append(entry)
        self.data["clock_log"] = self.data["clock_log"][-1000:]
        config = self._get_config(interaction.guild.id)
        role = await self._ensure_role(interaction.guild, config.get("on_shift_role", "On Shift"))
        if role:
            try:
                await interaction.user.add_roles(role, reason="Clocked in")
            except Exception:
                pass
        self._save_data()
        await interaction.response.send_message("?? Clock-in recorded")

    @app_commands.command(name="staffschedule_clockout", description="Clock out for accountability")
    async def staffschedule_clockout(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("? Guild-only command", ephemeral=True)
            return
        entry = {
            "user_id": interaction.user.id,
            "action": "clock_out",
            "timestamp": get_now_pst().isoformat()
        }
        self.data["clock_log"].append(entry)
        self.data["clock_log"] = self.data["clock_log"][-1000:]
        config = self._get_config(interaction.guild.id)
        role = discord.utils.get(interaction.guild.roles, name=config.get("on_shift_role", "On Shift"))
        if role:
            try:
                await interaction.user.remove_roles(role, reason="Clocked out")
            except Exception:
                pass
        self._save_data()
        await interaction.response.send_message("?? Clock-out recorded")

    @app_commands.command(name="staffschedule_config", description="Configure staff scheduling")
    @app_commands.checks.has_permissions(administrator=True)
    async def staffschedule_config(self, interaction: discord.Interaction, on_shift_role: str):
        config = self._get_config(interaction.guild.id)
        config["on_shift_role"] = on_shift_role
        self._save_data()
        await interaction.response.send_message(f"? On-shift role set to {on_shift_role}")

async def setup(bot):
    await bot.add_cog(StaffSchedulingRotation(bot))
