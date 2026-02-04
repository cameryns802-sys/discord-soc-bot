"""
IR War Room Manager: Auto-create temporary private channels for incident response.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

class IRWarRoomManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/war_rooms.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "war_rooms": {},
            "room_counter": 1,
            "active_incidents": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="create_war_room")
    async def create_war_room(self, ctx, severity: str, *, incident_title: str):
        """Create an IR war room for incident response."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        severity = severity.upper()
        if severity not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            await ctx.send("❌ Invalid severity. Use: CRITICAL, HIGH, MEDIUM, LOW")
            return
        
        room_id = f"WR-{self.data['room_counter']:04d}"
        self.data['room_counter'] += 1
        
        # Create channel (simulated - would actually create Discord channel)
        channel_name = f"war-room-{room_id.lower()}"
        
        war_room = {
            "room_id": room_id,
            "incident_title": incident_title,
            "severity": severity,
            "channel_name": channel_name,
            "channel_id": None,  # Would store actual Discord channel ID
            "created_by": str(ctx.author.id),
            "created_at": get_now_pst().isoformat(),
            "status": "ACTIVE",
            "participants": [str(ctx.author.id)],
            "timeline": [
                {
                    "timestamp": get_now_pst().isoformat(),
                    "action": "war_room_created",
                    "user": str(ctx.author.id),
                    "details": f"War room created for: {incident_title}"
                }
            ],
            "linked_case": None,
            "auto_cleanup": get_now_pst() + timedelta(hours=48)  # Auto-archive after 48h
        }
        
        # Attempt to create actual Discord channel
        try:
            # Create category if doesn't exist
            category = discord.utils.get(ctx.guild.categories, name="Incident Response")
            if not category:
                category = await ctx.guild.create_category("Incident Response")
            
            # Create private channel
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"🚨 {severity} - {incident_title}"
            )
            
            war_room["channel_id"] = str(channel.id)
            
            # Send welcome message to war room
            embed = discord.Embed(
                title=f"🚨 IR War Room: {room_id}",
                description=incident_title,
                color=discord.Color.red() if severity == "CRITICAL" else discord.Color.orange()
            )
            embed.add_field(name="Severity", value=severity, inline=True)
            embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
            embed.add_field(name="Status", value="ACTIVE", inline=True)
            embed.add_field(name="Commands", value="!invite_to_war_room @user\n!close_war_room\n!war_room_status", inline=False)
            
            await channel.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"⚠️ Could not create channel: {e}. Recording war room anyway.")
        
        self.data["war_rooms"][room_id] = war_room
        self.data["active_incidents"].append(room_id)
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ War Room Created",
            description=f"#{channel_name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Room ID", value=room_id, inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Incident", value=incident_title, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="invite_to_war_room")
    async def invite_to_war_room(self, ctx, room_id: str, member: discord.Member):
        """Invite a user to war room."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if room_id not in self.data["war_rooms"]:
            await ctx.send("❌ War room not found.")
            return
        
        war_room = self.data["war_rooms"][room_id]
        
        if war_room["status"] != "ACTIVE":
            await ctx.send("❌ War room is not active.")
            return
        
        # Add participant
        if str(member.id) not in war_room["participants"]:
            war_room["participants"].append(str(member.id))
            
            # Add timeline entry
            war_room["timeline"].append({
                "timestamp": get_now_pst().isoformat(),
                "action": "participant_added",
                "user": str(ctx.author.id),
                "details": f"Added {member.name} to war room"
            })
            
            # Update channel permissions
            if war_room["channel_id"]:
                try:
                    channel = ctx.guild.get_channel(int(war_room["channel_id"]))
                    if channel:
                        await channel.set_permissions(member, read_messages=True, send_messages=True)
                        await channel.send(f"👋 {member.mention} has been added to the war room.")
                except Exception as e:
                    await ctx.send(f"⚠️ Could not update channel permissions: {e}")
            
            self.save_data(self.data)
            
            await ctx.send(f"✅ {member.mention} added to war room {room_id}")
            
            # Notify member via DM
            try:
                dm_embed = discord.Embed(
                    title="🚨 You've been added to an IR War Room",
                    description=f"War Room: {room_id}\nIncident: {war_room['incident_title']}",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Severity", value=war_room["severity"], inline=True)
                dm_embed.add_field(name="Added By", value=ctx.author.mention, inline=True)
                await member.send(embed=dm_embed)
            except:
                pass
        else:
            await ctx.send(f"⚠️ {member.mention} is already in the war room.")

    @commands.command(name="close_war_room")
    async def close_war_room(self, ctx, room_id: str):
        """Close and archive a war room."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if room_id not in self.data["war_rooms"]:
            await ctx.send("❌ War room not found.")
            return
        
        war_room = self.data["war_rooms"][room_id]
        
        if war_room["status"] == "CLOSED":
            await ctx.send("⚠️ War room already closed.")
            return
        
        war_room["status"] = "CLOSED"
        war_room["closed_by"] = str(ctx.author.id)
        war_room["closed_at"] = get_now_pst().isoformat()
        
        war_room["timeline"].append({
            "timestamp": get_now_pst().isoformat(),
            "action": "war_room_closed",
            "user": str(ctx.author.id),
            "details": "War room closed and archived"
        })
        
        # Remove from active incidents
        if room_id in self.data["active_incidents"]:
            self.data["active_incidents"].remove(room_id)
        
        # Archive channel (move to archive category or delete)
        if war_room["channel_id"]:
            try:
                channel = ctx.guild.get_channel(int(war_room["channel_id"]))
                if channel:
                    # Send closure message
                    embed = discord.Embed(
                        title="✅ War Room Closed",
                        description="This war room has been closed and archived.",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Duration", value=f"{(get_now_pst() - datetime.fromisoformat(war_room['created_at'])).total_seconds() / 3600:.1f} hours", inline=True)
                    await channel.send(embed=embed)
                    
                    # Move to archive category
                    archive_category = discord.utils.get(ctx.guild.categories, name="IR Archive")
                    if not archive_category:
                        archive_category = await ctx.guild.create_category("IR Archive")
                    
                    await channel.edit(category=archive_category, name=f"archived-{war_room['channel_name']}")
            except Exception as e:
                await ctx.send(f"⚠️ Could not archive channel: {e}")
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ War Room Closed",
            description=f"Room ID: {room_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="Incident", value=war_room["incident_title"], inline=False)
        embed.add_field(name="Participants", value=str(len(war_room["participants"])), inline=True)
        embed.add_field(name="Timeline Events", value=str(len(war_room["timeline"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="list_war_rooms")
    async def list_war_rooms(self, ctx, status: str = "active"):
        """List all war rooms."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        status_filter = status.upper()
        if status_filter not in ["ACTIVE", "CLOSED", "ALL"]:
            status_filter = "ACTIVE"
        
        filtered_rooms = [
            (room_id, room) for room_id, room in self.data["war_rooms"].items()
            if status_filter == "ALL" or room["status"] == status_filter
        ]
        
        embed = discord.Embed(
            title=f"🚨 IR War Rooms ({status_filter})",
            description=f"Total: {len(filtered_rooms)} rooms",
            color=discord.Color.blue()
        )
        
        for room_id, room in filtered_rooms[-10:]:
            status_emoji = "🟢" if room["status"] == "ACTIVE" else "⚫"
            embed.add_field(
                name=f"{status_emoji} {room_id}: {room['incident_title'][:50]}",
                value=f"Severity: {room['severity']}\nParticipants: {len(room['participants'])}\nCreated: {room['created_at'][:19]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="war_room_status")
    async def war_room_status(self, ctx, room_id: str):
        """View war room details."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if room_id not in self.data["war_rooms"]:
            await ctx.send("❌ War room not found.")
            return
        
        room = self.data["war_rooms"][room_id]
        
        embed = discord.Embed(
            title=f"🚨 War Room: {room_id}",
            description=room["incident_title"],
            color=discord.Color.red() if room["status"] == "ACTIVE" else discord.Color.green()
        )
        
        embed.add_field(name="Status", value=room["status"], inline=True)
        embed.add_field(name="Severity", value=room["severity"], inline=True)
        embed.add_field(name="Participants", value=str(len(room["participants"])), inline=True)
        embed.add_field(name="Created", value=room["created_at"][:19], inline=True)
        
        if room["status"] == "CLOSED":
            embed.add_field(name="Closed", value=room.get("closed_at", "N/A")[:19], inline=True)
        
        embed.add_field(name="Timeline Events", value=str(len(room["timeline"])), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IRWarRoomManagerCog(bot))
