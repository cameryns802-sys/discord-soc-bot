"""
Server Setup - Auto-create SOC roles, channels, and permissions
Configure Sentinel bot infrastructure for security operations
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os

class ServerSetupCog(commands.Cog):
    """Create and manage server infrastructure for SOC operations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_file = 'data/server_setups.json'
        self.load_setup_data()
    
    def load_setup_data(self):
        """Load setup data"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.setup_file):
            with open(self.setup_file, 'w') as f:
                json.dump({}, f)
    
    def get_setup_data(self, guild_id):
        """Get setup data for guild"""
        try:
            with open(self.setup_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_setup_data(self, guild_id, data):
        """Save setup data for guild"""
        try:
            with open(self.setup_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        
        all_data[str(guild_id)] = data
        with open(self.setup_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    # ==================== ROLES ====================
    
    SENTINEL_ROLES = {
        "🛡️ Sentinel Admin": {
            "color": discord.Color.red(),
            "permissions": discord.Permissions(
                administrator=True,
                manage_guild=True,
                manage_roles=True,
                manage_channels=True,
                ban_members=True,
                kick_members=True,
                manage_messages=True
            ),
            "hoist": True,
            "mentionable": True,
            "description": "SOC Leadership - Full administrative control"
        },
        "🎯 Incident Commander": {
            "color": discord.Color.orange(),
            "permissions": discord.Permissions(
                manage_channels=True,
                send_messages=True,
                read_messages=True,
                manage_messages=True,
                mention_everyone=True,
                create_instant_invite=True
            ),
            "hoist": True,
            "mentionable": True,
            "description": "Leads incident response operations"
        },
        "🔍 Security Analyst": {
            "color": discord.Color.blue(),
            "permissions": discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                view_audit_log=True,
                manage_messages=True
            ),
            "hoist": True,
            "mentionable": True,
            "description": "Investigates threats and analyzes security events"
        },
        "🛡️ Defender": {
            "color": discord.Color.green(),
            "permissions": discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            ),
            "hoist": True,
            "mentionable": True,
            "description": "Responds to security threats"
        },
        "👁️ Monitor": {
            "color": discord.Color.gold(),
            "permissions": discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True
            ),
            "hoist": False,
            "mentionable": False,
            "description": "Monitors security metrics and alerts"
        },
        "📊 Analyst": {
            "color": discord.Color.blurple(),
            "permissions": discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True
            ),
            "hoist": False,
            "mentionable": False,
            "description": "Analyzes threat intelligence data"
        },
        "🔐 Compliance Officer": {
            "color": discord.Color.purple(),
            "permissions": discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                view_audit_log=True
            ),
            "hoist": True,
            "mentionable": True,
            "description": "Manages compliance and governance"
        }
    }
    
    # ==================== CHANNELS ====================
    
    SENTINEL_CHANNELS = {
        "soc-command-center": {
            "type": "text",
            "description": "Command center for incident response coordination",
            "topic": "🎯 Incident Response Command Center"
        },
        "threat-intelligence": {
            "type": "text",
            "description": "Threat intelligence feeds and analysis",
            "topic": "📡 Real-time threat intelligence and IOC tracking"
        },
        "incident-alerts": {
            "type": "text",
            "description": "Critical security incident alerts",
            "topic": "🚨 Critical security incidents and breaches"
        },
        "threat-hunting": {
            "type": "text",
            "description": "Proactive threat hunting campaigns",
            "topic": "🔍 Proactive threat hunting and investigations"
        },
        "vulnerability-management": {
            "type": "text",
            "description": "Vulnerability tracking and remediation",
            "topic": "🔧 Vulnerability assessment and remediation"
        },
        "compliance-tracking": {
            "type": "text",
            "description": "Compliance and governance status",
            "topic": "📋 Compliance framework tracking and evidence"
        },
        "security-metrics": {
            "type": "text",
            "description": "Real-time security metrics and KPIs",
            "topic": "📊 Security posture metrics and SLA tracking"
        },
        "incident-response": {
            "type": "text",
            "description": "General incident response discussion",
            "topic": "🛡️ Incident response coordination"
        },
        "false-positives": {
            "type": "text",
            "description": "False positive triage and analysis",
            "topic": "✅ False positive review and tuning"
        },
        "audit-logs": {
            "type": "text",
            "description": "Security audit log analysis",
            "topic": "📜 Audit logs and security event correlation"
        },
        "soc-voice": {
            "type": "voice",
            "description": "SOC operations voice channel",
            "topic": "🔊 Live incident coordination calls"
        }
    }
    
    @commands.command(name='setup_soc')
    @commands.has_permissions(administrator=True)
    async def setup_soc(self, ctx):
        """Setup complete SOC infrastructure (roles and channels)"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title="🚀 Setting Up Sentinel SOC Infrastructure",
            description="Creating roles and channels for security operations",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        await ctx.send(embed=embed)
        
        # Create roles
        created_roles = 0
        try:
            for role_name, role_data in self.SENTINEL_ROLES.items():
                try:
                    existing = discord.utils.get(guild.roles, name=role_name)
                    if not existing:
                        role = await guild.create_role(
                            name=role_name,
                            color=role_data["color"],
                            permissions=role_data["permissions"],
                            hoist=role_data["hoist"],
                            mentionable=role_data["mentionable"]
                        )
                        created_roles += 1
                        print(f"✅ Created role: {role_name}")
                except Exception as e:
                    print(f"❌ Failed to create role {role_name}: {e}")
        except Exception as e:
            print(f"❌ Role creation error: {e}")
        
        # Create channels
        created_channels = 0
        category = None
        
        try:
            # Create category first
            existing_category = discord.utils.get(guild.categories, name="🔒 Sentinel SOC")
            if not existing_category:
                category = await guild.create_category("🔒 Sentinel SOC")
            else:
                category = existing_category
            
            for channel_name, channel_data in self.SENTINEL_CHANNELS.items():
                try:
                    existing = discord.utils.get(guild.channels, name=channel_name)
                    if not existing:
                        if channel_data["type"] == "text":
                            channel = await guild.create_text_channel(
                                channel_name,
                                category=category,
                                topic=channel_data["topic"],
                                reason="Sentinel SOC setup"
                            )
                        else:
                            channel = await guild.create_voice_channel(
                                channel_name,
                                category=category,
                                reason="Sentinel SOC setup"
                            )
                        created_channels += 1
                        print(f"✅ Created channel: {channel_name}")
                except Exception as e:
                    print(f"❌ Failed to create channel {channel_name}: {e}")
        except Exception as e:
            print(f"❌ Channel creation error: {e}")
        
        # Save setup data
        setup_data = {
            "roles_created": created_roles,
            "channels_created": created_channels,
            "setup_date": datetime.utcnow().isoformat(),
            "setup_by": str(ctx.author)
        }
        self.save_setup_data(guild.id, setup_data)
        
        # Send completion embed
        completion_embed = discord.Embed(
            title="✅ Sentinel SOC Setup Complete",
            description="Infrastructure configured and ready for operations",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        completion_embed.add_field(name="🏷️ Roles Created", value=f"{created_roles} roles", inline=True)
        completion_embed.add_field(name="💬 Channels Created", value=f"{created_channels} channels", inline=True)
        completion_embed.add_field(name="🎯 Category", value="🔒 Sentinel SOC", inline=True)
        
        completion_embed.add_field(name="🛡️ Roles", value="━" * 30, inline=False)
        for role_name in self.SENTINEL_ROLES.keys():
            completion_embed.add_field(name=role_name, value=self.SENTINEL_ROLES[role_name]["description"], inline=False)
        
        completion_embed.add_field(name="📊 Setup Complete", value="━" * 30, inline=False)
        completion_embed.add_field(name="→", value="Assign roles to team members", inline=False)
        completion_embed.add_field(name="→", value="Configure channel permissions as needed", inline=False)
        completion_embed.add_field(name="→", value="Use security commands in appropriate channels", inline=False)
        
        await ctx.send(embed=completion_embed)
    
    @commands.command(name='listroles_sentinel')
    async def listroles_sentinel(self, ctx):
        """List all Sentinel SOC roles"""
        embed = discord.Embed(
            title="🛡️ Sentinel SOC Roles",
            description="Available security operation roles",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for role_name, role_data in self.SENTINEL_ROLES.items():
            embed.add_field(
                name=role_name,
                value=role_data["description"],
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='listchannels_sentinel')
    async def listchannels_sentinel(self, ctx):
        """List all Sentinel SOC channels"""
        embed = discord.Embed(
            title="📡 Sentinel SOC Channels",
            description="Available security operation channels",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for channel_name, channel_data in self.SENTINEL_CHANNELS.items():
            channel_type = "💬" if channel_data["type"] == "text" else "🔊"
            embed.add_field(
                name=f"{channel_type} {channel_name}",
                value=channel_data["description"],
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerSetupCog(bot))
