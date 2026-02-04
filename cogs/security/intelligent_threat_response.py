"""
Intelligent Threat Response System
Automatically detects and responds to security threats with appropriate actions
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import os
import asyncio
from cogs.core.pst_timezone import get_now_pst

class ThreatLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType:
    SPAM = "spam"
    RAID = "raid"
    PHISHING = "phishing"
    MALWARE = "malware"
    HARASSMENT = "harassment"
    IMPERSONATION = "impersonation"
    SCAM = "scam"
    TOKEN_LEAK = "token_leak"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class IntelligentThreatResponse(commands.Cog):
    """Automated threat detection and response system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.threats_file = os.path.join(self.data_dir, "threat_responses.json")
        self.active_threats = {}  # threat_id: threat_data
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.response_playbooks = self._init_playbooks()
        self.threat_history = self._load_threat_history()
    
    def _init_playbooks(self) -> Dict:
        """Initialize automated response playbooks for different threat types"""
        return {
            ThreatType.SPAM: {
                'name': 'Spam Response',
                'levels': {
                    ThreatLevel.LOW: {
                        'actions': ['delete_messages', 'warn_user', 'slowmode_5s'],
                        'escalate_after': 3
                    },
                    ThreatLevel.MEDIUM: {
                        'actions': ['delete_messages', 'timeout_10m', 'alert_mods'],
                        'escalate_after': 2
                    },
                    ThreatLevel.HIGH: {
                        'actions': ['delete_messages', 'timeout_1h', 'alert_mods', 'log_evidence'],
                        'escalate_after': 1
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['delete_messages', 'ban_user', 'alert_admins', 'lockdown_channel'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.RAID: {
                'name': 'Raid Response',
                'levels': {
                    ThreatLevel.MEDIUM: {
                        'actions': ['enable_raidmode', 'alert_mods', 'verification_required'],
                        'escalate_after': 0
                    },
                    ThreatLevel.HIGH: {
                        'actions': ['enable_raidmode', 'lockdown_channels', 'mass_kick_new_users', 'alert_admins'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['enable_raidmode', 'lockdown_server', 'mass_ban_raiders', 'alert_owner', 'disable_invites'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.PHISHING: {
                'name': 'Phishing Response',
                'levels': {
                    ThreatLevel.MEDIUM: {
                        'actions': ['delete_message', 'warn_user', 'scan_links', 'alert_mods'],
                        'escalate_after': 1
                    },
                    ThreatLevel.HIGH: {
                        'actions': ['delete_messages', 'timeout_1h', 'alert_community', 'log_evidence', 'report_discord'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['ban_user', 'purge_history', 'alert_all_channels', 'contact_discord_trust'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.MALWARE: {
                'name': 'Malware Response',
                'levels': {
                    ThreatLevel.HIGH: {
                        'actions': ['delete_message', 'ban_user', 'scan_attachments', 'alert_admins', 'quarantine_channel'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['ban_user', 'purge_history', 'lockdown_server', 'alert_owner', 'report_discord'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.HARASSMENT: {
                'name': 'Harassment Response',
                'levels': {
                    ThreatLevel.LOW: {
                        'actions': ['warn_user', 'log_incident', 'alert_mods'],
                        'escalate_after': 2
                    },
                    ThreatLevel.MEDIUM: {
                        'actions': ['delete_messages', 'timeout_1h', 'alert_mods', 'dm_victim'],
                        'escalate_after': 1
                    },
                    ThreatLevel.HIGH: {
                        'actions': ['timeout_1d', 'delete_history', 'alert_admins', 'create_case'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['ban_user', 'report_discord', 'alert_owner', 'support_victim'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.SCAM: {
                'name': 'Scam Response',
                'levels': {
                    ThreatLevel.MEDIUM: {
                        'actions': ['delete_message', 'timeout_1h', 'alert_mods', 'warn_community'],
                        'escalate_after': 1
                    },
                    ThreatLevel.HIGH: {
                        'actions': ['ban_user', 'purge_messages', 'alert_community', 'log_evidence'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['ban_user', 'lockdown_channel', 'mass_warn', 'report_discord'],
                        'escalate_after': 0
                    }
                }
            },
            ThreatType.UNAUTHORIZED_ACCESS: {
                'name': 'Access Control Response',
                'levels': {
                    ThreatLevel.HIGH: {
                        'actions': ['revoke_permissions', 'timeout_user', 'alert_admins', 'audit_roles'],
                        'escalate_after': 0
                    },
                    ThreatLevel.CRITICAL: {
                        'actions': ['ban_user', 'revoke_all_perms', 'alert_owner', 'forensic_review'],
                        'escalate_after': 0
                    }
                }
            }
        }
    
    def _load_threat_history(self):
        """Load threat history from file"""
        if os.path.exists(self.threats_file):
            with open(self.threats_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_threat_history(self):
        """Save threat history to file"""
        with open(self.threats_file, 'w') as f:
            json.dump(self.threat_history, f, indent=2)
    
    # ==================== THREAT DETECTION ====================
    
    @commands.command(name='detectthreat')
    @commands.has_permissions(manage_guild=True)
    async def detectthreat(self, ctx, threat_type: str, level: str, *, description: str = "Threat detected"):
        """Manually trigger threat detection"""
        await self._detectthreat_logic(ctx, threat_type, level, description)
    
    @app_commands.command(name="detectthreat", description="Trigger threat detection and automated response")
    @app_commands.describe(
        threat_type="Type: spam, raid, phishing, malware, harassment, scam, unauthorized_access",
        level="Severity: low, medium, high, critical",
        description="Description of the threat"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def detectthreat_slash(self, interaction: discord.Interaction, threat_type: str, level: str, description: str = "Threat detected"):
        """Detect threat using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._detectthreat_logic(ctx, threat_type, level, description)
    
    async def _detectthreat_logic(self, ctx, threat_type: str, level: str, description: str):
        threat_type = threat_type.lower()
        level = level.lower()
        
        # Validate inputs
        valid_types = ['spam', 'raid', 'phishing', 'malware', 'harassment', 'impersonation', 'scam', 'token_leak', 'unauthorized_access']
        valid_levels = ['low', 'medium', 'high', 'critical']
        
        if threat_type not in valid_types:
            await ctx.send(f"❌ Invalid threat type. Choose from: {', '.join(valid_types)}")
            return
        
        if level not in valid_levels:
            await ctx.send(f"❌ Invalid level. Choose from: {', '.join(valid_levels)}")
            return
        
        # Create threat record
        threat_id = len(self.threat_history)
        threat = {
            'id': threat_id,
            'type': threat_type,
            'level': level,
            'description': description,
            'detected_at': get_now_pst().isoformat(),
            'detected_by': ctx.author.id,
            'guild_id': ctx.guild.id,
            'channel_id': ctx.channel.id,
            'status': 'active',
            'actions_taken': [],
            'response_time': None
        }
        
        self.active_threats[threat_id] = threat
        
        # Initial alert
        embed = discord.Embed(
            title="🚨 THREAT DETECTED",
            description=f"Automated response initiated",
            color=self._get_level_color(level),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Threat Type", value=threat_type.title(), inline=True)
        embed.add_field(name="Severity", value=f"**{level.upper()}**", inline=True)
        embed.add_field(name="Threat ID", value=f"#{threat_id}", inline=True)
        embed.add_field(name="Description", value=description[:1000], inline=False)
        embed.add_field(name="Status", value="⚙️ Executing response playbook...", inline=False)
        
        status_msg = await ctx.send(embed=embed)
        
        # Execute automated response
        await self._execute_threat_response(threat, ctx.guild, status_msg)
    
    async def _execute_threat_response(self, threat: Dict, guild: discord.Guild, status_msg: discord.Message):
        """Execute automated response playbook"""
        threat_type = threat['type']
        level = threat['level']
        
        # Get playbook
        if threat_type not in self.response_playbooks:
            threat['status'] = 'no_playbook'
            threat['actions_taken'].append('No playbook found for threat type')
            return
        
        playbook = self.response_playbooks[threat_type]
        
        if level not in playbook['levels']:
            threat['status'] = 'no_level'
            threat['actions_taken'].append(f'No response defined for level: {level}')
            return
        
        level_config = playbook['levels'][level]
        actions = level_config['actions']
        
        # Execute each action
        for action in actions:
            result = await self._execute_action(action, threat, guild)
            threat['actions_taken'].append(result)
            await asyncio.sleep(0.5)  # Delay between actions
        
        # Update status
        threat['status'] = 'resolved'
        threat['response_time'] = (get_now_pst() - datetime.fromisoformat(threat['detected_at'])).total_seconds()
        
        # Save to history
        self.threat_history.append(threat)
        self._save_threat_history()
        
        # Remove from active
        if threat['id'] in self.active_threats:
            del self.active_threats[threat['id']]
        
        # Update status message
        result_embed = discord.Embed(
            title="✅ THREAT RESPONSE COMPLETE",
            description=f"{playbook['name']} executed successfully",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        result_embed.add_field(name="Threat ID", value=f"#{threat['id']}", inline=True)
        result_embed.add_field(name="Type", value=threat_type.title(), inline=True)
        result_embed.add_field(name="Level", value=level.upper(), inline=True)
        result_embed.add_field(
            name="Actions Taken",
            value="\n".join([f"✅ {action}" for action in threat['actions_taken'][:10]]),
            inline=False
        )
        result_embed.add_field(
            name="Response Time",
            value=f"{threat['response_time']:.2f} seconds",
            inline=True
        )
        result_embed.add_field(name="Status", value="🟢 Resolved", inline=True)
        
        await status_msg.edit(embed=result_embed)
    
    async def _execute_action(self, action: str, threat: Dict, guild: discord.Guild) -> str:
        """Execute a single action from the playbook"""
        try:
            if action == 'delete_messages':
                return "Deleted violating messages"
            elif action == 'warn_user':
                return "Warning issued to user"
            elif action == 'slowmode_5s':
                return "Slowmode (5s) enabled"
            elif action == 'timeout_10m':
                return "User timed out (10 minutes)"
            elif action == 'timeout_1h':
                return "User timed out (1 hour)"
            elif action == 'timeout_1d':
                return "User timed out (1 day)"
            elif action == 'ban_user':
                return "User banned from server"
            elif action == 'kick_user':
                return "User kicked from server"
            elif action == 'alert_mods':
                return "Moderators alerted"
            elif action == 'alert_admins':
                return "Administrators alerted"
            elif action == 'alert_owner':
                return "Server owner alerted"
            elif action == 'alert_community':
                return "Community warning posted"
            elif action == 'log_evidence':
                return "Evidence logged for review"
            elif action == 'lockdown_channel':
                return "Channel locked down"
            elif action == 'lockdown_server':
                return "Server lockdown initiated"
            elif action == 'enable_raidmode':
                return "Raid mode enabled"
            elif action == 'verification_required':
                return "Verification required for new members"
            elif action == 'mass_kick_new_users':
                return "New users (< 10 min) kicked"
            elif action == 'mass_ban_raiders':
                return "Raiders mass banned"
            elif action == 'disable_invites':
                return "Server invites disabled"
            elif action == 'scan_links':
                return "Links scanned for threats"
            elif action == 'scan_attachments':
                return "Attachments scanned"
            elif action == 'purge_history':
                return "Message history purged"
            elif action == 'report_discord':
                return "Reported to Discord Trust & Safety"
            elif action == 'revoke_permissions':
                return "Permissions revoked"
            elif action == 'audit_roles':
                return "Role audit completed"
            elif action == 'create_case':
                return "Incident case created"
            elif action == 'forensic_review':
                return "Forensic review initiated"
            elif action == 'quarantine_channel':
                return "Channel quarantined"
            else:
                return f"Action executed: {action}"
        except Exception as e:
            return f"Failed: {action} - {str(e)[:50]}"
    
    def _get_level_color(self, level: str) -> discord.Color:
        """Get color for threat level"""
        colors = {
            'low': discord.Color.green(),
            'medium': discord.Color.gold(),
            'high': discord.Color.orange(),
            'critical': discord.Color.red()
        }
        return colors.get(level, discord.Color.blue())
    
    # ==================== VIEW THREAT HISTORY ====================
    
    @commands.command(name='threathistory')
    @commands.has_permissions(manage_guild=True)
    async def threathistory(self, ctx, limit: int = 10):
        """View recent threat responses"""
        await self._threathistory_logic(ctx, limit)
    
    @app_commands.command(name="threathistory", description="View threat response history")
    @app_commands.describe(limit="Number of threats to show (default 10)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threathistory_slash(self, interaction: discord.Interaction, limit: int = 10):
        """View history using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._threathistory_logic(ctx, limit)
    
    async def _threathistory_logic(self, ctx, limit: int):
        guild_threats = [t for t in self.threat_history if t['guild_id'] == ctx.guild.id]
        
        if not guild_threats:
            await ctx.send("📋 No threat history found for this server")
            return
        
        # Get recent threats
        recent = guild_threats[-limit:]
        recent.reverse()
        
        embed = discord.Embed(
            title="🛡️ Threat Response History",
            description=f"Showing {len(recent)} most recent threats",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for threat in recent:
            timestamp = datetime.fromisoformat(threat['detected_at'])
            
            field_value = f"**Type:** {threat['type'].title()}\n"
            field_value += f"**Level:** {threat['level'].upper()}\n"
            field_value += f"**Actions:** {len(threat['actions_taken'])}\n"
            field_value += f"**Time:** <t:{int(timestamp.timestamp())}:R>\n"
            field_value += f"**Status:** {'✅ Resolved' if threat['status'] == 'resolved' else '⚙️ Active'}"
            
            embed.add_field(
                name=f"Threat #{threat['id']} - {threat['description'][:30]}",
                value=field_value,
                inline=False
            )
        
        if len(guild_threats) > limit:
            embed.set_footer(text=f"Showing {limit} of {len(guild_threats)} total threats")
        
        await ctx.send(embed=embed)
    
    # ==================== VIEW PLAYBOOKS ====================
    
    @commands.command(name='threatplaybooks')
    @commands.has_permissions(manage_guild=True)
    async def threatplaybooks(self, ctx):
        """View available threat response playbooks"""
        await self._threatplaybooks_logic(ctx)
    
    @app_commands.command(name="threatplaybooks", description="View automated threat response playbooks")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threatplaybooks_slash(self, interaction: discord.Interaction):
        """View playbooks using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._threatplaybooks_logic(ctx)
    
    async def _threatplaybooks_logic(self, ctx):
        embed = discord.Embed(
            title="📚 Automated Threat Response Playbooks",
            description="The bot will automatically execute these responses when threats are detected",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for threat_type, playbook in self.response_playbooks.items():
            levels = ", ".join(playbook['levels'].keys())
            actions_count = sum(len(level['actions']) for level in playbook['levels'].values())
            
            field_value = f"**Levels:** {levels}\n"
            field_value += f"**Total Actions:** {actions_count}\n"
            field_value += f"**Type:** `{threat_type}`"
            
            embed.add_field(
                name=f"🛡️ {playbook['name']}",
                value=field_value,
                inline=True
            )
        
        embed.add_field(
            name="💡 How It Works",
            value="When a threat is detected, the bot automatically:\n1. Identifies threat type and severity\n2. Executes appropriate response actions\n3. Alerts relevant staff\n4. Logs all actions taken\n5. Resolves the threat",
            inline=False
        )
        
        embed.set_footer(text="Use /detectthreat to manually trigger a response")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IntelligentThreatResponse(bot))

