"""
Ticket System
Complete ticketing system for user requests, incident tracking, and case management.
Features: Create, claim, assign, close, comment, priority levels, status tracking, transcripts.
"""

import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
from typing import Optional

# Import button components
try:
    from cogs.incidents.ticket_buttons import TicketActionButtons
    BUTTONS_AVAILABLE = True
except ImportError:
    BUTTONS_AVAILABLE = False

class TicketSystem(commands.Cog):
    """Full-featured ticketing system for SOC operations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/tickets.json'
        self.config_file = 'data/ticket_config.json'
        self.load_data()
        self.load_config()
    
    def load_data(self):
        """Load ticket data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.tickets = json.load(f)
        else:
            self.tickets = {}
    
    def save_data(self):
        """Save ticket data"""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.tickets, f, indent=4)
    
    def load_config(self):
        """Load ticket configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
    
    def save_config(self):
        """Save ticket configuration"""
        os.makedirs('data', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get_next_ticket_id(self, guild_id: str) -> str:
        """Generate next ticket ID for guild"""
        guild_tickets = [t for t in self.tickets.values() if t['guild_id'] == guild_id]
        if not guild_tickets:
            return f"TKT-{guild_id}-0001"
        
        max_num = max([int(t['ticket_id'].split('-')[-1]) for t in guild_tickets])
        return f"TKT-{guild_id}-{str(max_num + 1).zfill(4)}"
    
    def get_ticket_category(self, guild_id: int) -> Optional[discord.CategoryChannel]:
        """Get configured ticket category channel"""
        category_id = self.config.get(str(guild_id), {}).get('ticket_category')
        if category_id:
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild.get_channel(category_id)
        return None
    
    def get_staff_role(self, guild_id: int) -> Optional[discord.Role]:
        """Get configured staff role for ticket access"""
        role_id = self.config.get(str(guild_id), {}).get('staff_role')
        if role_id:
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild.get_role(role_id)
        return None
    
    # ==================== TICKET COMMANDS ====================
    
    @commands.command(name='createticket', aliases=['newticket', 'ticket'])
    async def _create_ticket_logic(self, ctx, priority: str, description: str, is_slash: bool = False):
        """
        Create a new ticket
        
        Usage: !createticket <priority> <description>
        Priority: low, medium, high, critical
        Example: !createticket high Suspicious login from unknown IP
        """
        await self._create_ticket_logic(ctx, priority, description, is_slash=False)
    
    @app_commands.command(name="createticket", description="Create a new security ticket")
    @app_commands.describe(priority="Ticket priority level", description="Ticket description")
    async def create_ticket_slash(self, interaction: discord.Interaction, priority: str = "medium", description: str = ""):
        """
        Create a new ticket using slash command
        """
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.guild = interaction.guild
                self.channel = interaction.channel
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    await interaction.followup.send(embed=kwargs['embed'])
                else:
                    await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._create_ticket_logic(ctx, priority, description, is_slash=True)
    
    async def _create_ticket_logic(self, ctx, priority: str, description: str, is_slash: bool = False):
        # Validate priority
        priority = priority.lower()
        if priority not in ['low', 'medium', 'high', 'critical']:
            await ctx.send("❌ Invalid priority. Use: low, medium, high, or critical")
            return
        
        guild_id = str(ctx.guild.id)
        ticket_id = self.get_next_ticket_id(guild_id)
        
        # Create ticket data
        ticket = {
            'ticket_id': ticket_id,
            'guild_id': guild_id,
            'creator_id': ctx.author.id,
            'creator_name': str(ctx.author),
            'priority': priority,
            'status': 'open',
            'description': description,
            'assigned_to': None,
            'assigned_name': None,
            'created_at': datetime.datetime.now(datetime.UTC).isoformat(),
            'updated_at': datetime.datetime.now(datetime.UTC).isoformat(),
            'closed_at': None,
            'closed_by': None,
            'channel_id': None,
            'comments': []
        }
        
        # Try to create dedicated ticket channel
        category = self.get_ticket_category(ctx.guild.id)
        staff_role = self.get_staff_role(ctx.guild.id)
        
        if category:
            # Create private ticket channel
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            
            try:
                channel = await ctx.guild.create_text_channel(
                    name=f"ticket-{ticket_id.split('-')[-1]}",
                    category=category,
                    overwrites=overwrites,
                    topic=f"Ticket {ticket_id} | Priority: {priority.upper()} | Created by {ctx.author}"
                )
                
                ticket['channel_id'] = channel.id
                
                # Send initial message in ticket channel
                embed = discord.Embed(
                    title=f"🎫 Ticket {ticket_id}",
                    description=description,
                    color=self.get_priority_color(priority),
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.add_field(name="Priority", value=priority.upper(), inline=True)
                embed.add_field(name="Status", value="🟢 OPEN", inline=True)
                embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
                embed.set_footer(text=f"Use !claimticket to take ownership")
                
                await channel.send(f"{ctx.author.mention} {staff_role.mention if staff_role else ''}", embed=embed)
                
            except discord.Forbidden:
                await ctx.send("⚠️ Cannot create ticket channel. Ticket created without dedicated channel.")
        
        # Save ticket
        self.tickets[ticket_id] = ticket
        self.save_data()
        
        # Confirmation embed
        embed = discord.Embed(
            title="✅ Ticket Created",
            description=f"Your ticket has been created: **{ticket_id}**",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Priority", value=priority.upper(), inline=True)
        embed.add_field(name="Status", value="Open", inline=True)
        if ticket['channel_id']:
            embed.add_field(name="Channel", value=f"<#{ticket['channel_id']}>", inline=True)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='viewticket')
    async def view_ticket(self, ctx, ticket_id: str):
        """
        View detailed information about a ticket
        
        Usage: !viewticket <ticket_id>
        Example: !viewticket TKT-1234567890-0001
        """
        await self._view_ticket_logic(ctx, ticket_id)
    
    @app_commands.command(name="viewticket", description="View ticket details")
    @app_commands.describe(ticket_id="Ticket ID (e.g., TKT-1234567890-0001)")
    async def view_ticket_slash(self, interaction: discord.Interaction, ticket_id: str):
        """
        View ticket using slash command
        """
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    await interaction.followup.send(embed=kwargs['embed'])
                else:
                    await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._view_ticket_logic(ctx, ticket_id)
    
    async def _view_ticket_logic(self, ctx, ticket_id: str):
        ticket_id = ticket_id.upper()
        
        if ticket_id not in self.tickets:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found.")
            return
        
        ticket = self.tickets[ticket_id]
        
        # Build embed
        embed = discord.Embed(
            title=f"🎫 Ticket {ticket_id}",
            description=ticket['description'],
            color=self.get_priority_color(ticket['priority']),
            timestamp=datetime.datetime.fromisoformat(ticket['created_at'])
        )
        
        # Status with emoji
        status_emoji = {
            'open': '🟢',
            'in_progress': '🟡',
            'waiting': '🟠',
            'closed': '⚫'
        }
        status_display = f"{status_emoji.get(ticket['status'], '⚪')} {ticket['status'].upper().replace('_', ' ')}"
        
        embed.add_field(name="Status", value=status_display, inline=True)
        embed.add_field(name="Priority", value=ticket['priority'].upper(), inline=True)
        embed.add_field(name="Created By", value=f"<@{ticket['creator_id']}>", inline=True)
        
        if ticket['assigned_to']:
            embed.add_field(name="Assigned To", value=f"<@{ticket['assigned_to']}>", inline=True)
        else:
            embed.add_field(name="Assigned To", value="Unassigned", inline=True)
        
        if ticket['channel_id']:
            embed.add_field(name="Channel", value=f"<#{ticket['channel_id']}>", inline=True)
        
        # Timestamps
        created_ts = int(datetime.datetime.fromisoformat(ticket['created_at']).timestamp())
        updated_ts = int(datetime.datetime.fromisoformat(ticket['updated_at']).timestamp())
        embed.add_field(name="Created", value=f"<t:{created_ts}:R>", inline=True)
        embed.add_field(name="Last Updated", value=f"<t:{updated_ts}:R>", inline=True)
        
        if ticket['closed_at']:
            closed_ts = int(datetime.datetime.fromisoformat(ticket['closed_at']).timestamp())
            embed.add_field(name="Closed", value=f"<t:{closed_ts}:R>", inline=True)
        
        # Comments
        if ticket['comments']:
            comments_text = "\n".join([
                f"**{c['author_name']}** (<t:{int(datetime.datetime.fromisoformat(c['timestamp']).timestamp())}:R>): {c['content'][:100]}"
                for c in ticket['comments'][-3:]  # Last 3 comments
            ])
            embed.add_field(name=f"Recent Comments ({len(ticket['comments'])} total)", value=comments_text, inline=False)
        
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        # Add interactive buttons if available and ticket is not closed
        view = None
        if BUTTONS_AVAILABLE and ticket['status'] != 'closed':
            view = TicketActionButtons(self, ticket_id, timeout=None)
        
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='claimticket')
    async def claim_ticket(self, ctx, ticket_id: str):
        """
        Claim an unassigned ticket
        
        Usage: !claimticket <ticket_id>
        Example: !claimticket TKT-1234567890-0001
        """
        ticket_id = ticket_id.upper()
        
        if ticket_id not in self.tickets:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found.")
            return
        
        ticket = self.tickets[ticket_id]
        
        if ticket['status'] == 'closed':
            await ctx.send("❌ Cannot claim a closed ticket.")
            return
        
        if ticket['assigned_to']:
            await ctx.send(f"❌ Ticket already assigned to <@{ticket['assigned_to']}>")
            return
        
        # Assign ticket
        ticket['assigned_to'] = ctx.author.id
        ticket['assigned_name'] = str(ctx.author)
        ticket['status'] = 'in_progress'
        ticket['updated_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Add system comment
        ticket['comments'].append({
            'author_id': self.bot.user.id,
            'author_name': 'System',
            'content': f"Ticket claimed by {ctx.author.mention}",
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f"You have claimed ticket **{ticket_id}**",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Status", value="🟡 IN PROGRESS", inline=True)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)
        
        # Notify in ticket channel
        if ticket['channel_id']:
            channel = ctx.guild.get_channel(ticket['channel_id'])
            if channel:
                await channel.send(f"🟡 {ctx.author.mention} has claimed this ticket and is working on it.")
    
    @commands.command(name='assignticket')
    @commands.has_permissions(manage_messages=True)
    async def assign_ticket(self, ctx, ticket_id: str, member: discord.Member):
        """
        Assign a ticket to a specific member
        
        Usage: !assignticket <ticket_id> <member>
        Example: !assignticket TKT-1234567890-0001 @user
        """
        ticket_id = ticket_id.upper()
        
        if ticket_id not in self.tickets:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found.")
            return
        
        ticket = self.tickets[ticket_id]
        
        if ticket['status'] == 'closed':
            await ctx.send("❌ Cannot assign a closed ticket.")
            return
        
        # Assign ticket
        old_assignee = ticket['assigned_name']
        ticket['assigned_to'] = member.id
        ticket['assigned_name'] = str(member)
        ticket['status'] = 'in_progress'
        ticket['updated_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Add system comment
        if old_assignee:
            message = f"Ticket reassigned from {old_assignee} to {member.mention} by {ctx.author.mention}"
        else:
            message = f"Ticket assigned to {member.mention} by {ctx.author.mention}"
        
        ticket['comments'].append({
            'author_id': self.bot.user.id,
            'author_name': 'System',
            'content': message,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Ticket Assigned",
            description=f"Ticket **{ticket_id}** assigned to {member.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)
        
        # Notify assignee
        try:
            dm_embed = discord.Embed(
                title="🎫 Ticket Assigned",
                description=f"You have been assigned to ticket **{ticket_id}**",
                color=discord.Color.blue()
            )
            dm_embed.add_field(name="Description", value=ticket['description'][:1024], inline=False)
            dm_embed.add_field(name="Priority", value=ticket['priority'].upper(), inline=True)
            if ticket['channel_id']:
                dm_embed.add_field(name="Channel", value=f"<#{ticket['channel_id']}>", inline=True)
            await member.send(embed=dm_embed)
        except:
            pass
    
    @commands.command(name='closeticket')
    async def close_ticket(self, ctx, ticket_id: str, *, resolution: str = "Resolved"):
        """
        Close a ticket with resolution notes
        
        Usage: !closeticket <ticket_id> [resolution]
        Example: !closeticket TKT-1234567890-0001 False positive, no action needed
        """
        ticket_id = ticket_id.upper()
        
        if ticket_id not in self.tickets:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found.")
            return
        
        ticket = self.tickets[ticket_id]
        
        if ticket['status'] == 'closed':
            await ctx.send("❌ Ticket is already closed.")
            return
        
        # Check permissions (creator, assigned, or staff)
        staff_role = self.get_staff_role(ctx.guild.id)
        is_authorized = (
            ctx.author.id == ticket['creator_id'] or
            ctx.author.id == ticket['assigned_to'] or
            (staff_role and staff_role in ctx.author.roles) or
            ctx.author.guild_permissions.manage_messages
        )
        
        if not is_authorized:
            await ctx.send("❌ You don't have permission to close this ticket.")
            return
        
        # Close ticket
        ticket['status'] = 'closed'
        ticket['closed_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        ticket['closed_by'] = ctx.author.id
        ticket['updated_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        
        # Add system comment
        ticket['comments'].append({
            'author_id': self.bot.user.id,
            'author_name': 'System',
            'content': f"Ticket closed by {ctx.author.mention}: {resolution}",
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Ticket Closed",
            description=f"Ticket **{ticket_id}** has been closed",
            color=discord.Color.dark_gray(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Resolution", value=resolution, inline=False)
        embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)
        
        # Archive ticket channel
        if ticket['channel_id']:
            channel = ctx.guild.get_channel(ticket['channel_id'])
            if channel:
                await channel.send("⚫ This ticket has been closed. Channel will be archived shortly.")
                # Optionally delete channel after delay
                # await asyncio.sleep(30)
                # await channel.delete(reason=f"Ticket {ticket_id} closed")
    
    @commands.command(name='commentticket', aliases=['ticketcomment'])
    async def comment_ticket(self, ctx, ticket_id: str, *, comment: str):
        """
        Add a comment to a ticket
        
        Usage: !commentticket <ticket_id> <comment>
        Example: !commentticket TKT-1234567890-0001 Investigating the issue now
        """
        ticket_id = ticket_id.upper()
        
        if ticket_id not in self.tickets:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found.")
            return
        
        ticket = self.tickets[ticket_id]
        
        # Add comment
        ticket['comments'].append({
            'author_id': ctx.author.id,
            'author_name': str(ctx.author),
            'content': comment,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        ticket['updated_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        
        self.save_data()
        
        embed = discord.Embed(
            title="💬 Comment Added",
            description=comment,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)
        
        # Post in ticket channel
        if ticket['channel_id']:
            channel = ctx.guild.get_channel(ticket['channel_id'])
            if channel:
                await channel.send(embed=embed)
    
    @commands.command(name='listtickets')
    async def list_tickets(self, ctx, status: str = "open"):
        """
        List tickets by status
        
        Usage: !listtickets [status]
        Status: open, in_progress, closed, all, mine
        Example: !listtickets open
        """
        await self._list_tickets_logic(ctx, status)
    
    @app_commands.command(name="listtickets", description="List tickets by status")
    @app_commands.describe(status="Filter by status: open, in_progress, closed, all, mine")
    async def list_tickets_slash(self, interaction: discord.Interaction, status: str = "open"):
        """
        List tickets using slash command
        """
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    await interaction.followup.send(embed=kwargs['embed'])
                else:
                    await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._list_tickets_logic(ctx, status)
    
    async def _list_tickets_logic(self, ctx, status: str):
        status = status.lower()
        guild_id = str(ctx.guild.id)
        
        # Filter tickets
        if status == "all":
            filtered = [t for t in self.tickets.values() if t['guild_id'] == guild_id]
        elif status == "mine":
            filtered = [t for t in self.tickets.values() if t['guild_id'] == guild_id and (t['creator_id'] == ctx.author.id or t['assigned_to'] == ctx.author.id)]
        else:
            filtered = [t for t in self.tickets.values() if t['guild_id'] == guild_id and t['status'] == status]
        
        if not filtered:
            await ctx.send(f"📋 No tickets found with status: **{status}**")
            return
        
        # Sort by created date (newest first)
        filtered.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Build embed
        embed = discord.Embed(
            title=f"🎫 Tickets - {status.upper().replace('_', ' ')}",
            description=f"Found {len(filtered)} ticket(s)",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        # Show first 10 tickets
        for ticket in filtered[:10]:
            status_emoji = {
                'open': '🟢',
                'in_progress': '🟡',
                'waiting': '🟠',
                'closed': '⚫'
            }
            
            priority_emoji = {
                'low': '🔵',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }
            
            assignee = f"<@{ticket['assigned_to']}>" if ticket['assigned_to'] else "Unassigned"
            created_ts = int(datetime.datetime.fromisoformat(ticket['created_at']).timestamp())
            
            value = f"{priority_emoji.get(ticket['priority'], '⚪')} **{ticket['priority'].upper()}** | {assignee}\n"
            value += f"{ticket['description'][:80]}{'...' if len(ticket['description']) > 80 else ''}\n"
            value += f"Created <t:{created_ts}:R>"
            
            if ticket['channel_id']:
                value += f" | <#{ticket['channel_id']}>"
            
            embed.add_field(
                name=f"{status_emoji.get(ticket['status'], '⚪')} {ticket['ticket_id']}",
                value=value,
                inline=False
            )
        
        if len(filtered) > 10:
            embed.set_footer(text=f"Showing 10 of {len(filtered)} tickets | Use !viewticket <id> for details")
        else:
            embed.set_footer(text=f"Use !viewticket <id> for details")
        
        await ctx.send(embed=embed)
    
    # ==================== CONFIGURATION COMMANDS ====================
    
    @commands.command(name='setuptickets')
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """
        Initial ticket system setup (Admin only)
        
        Usage: !setuptickets
        Creates ticket category and sets up basic configuration
        """
        guild_id = str(ctx.guild.id)
        
        # Create ticket category
        category = await ctx.guild.create_category(
            name="🎫 Tickets",
            reason="Ticket system setup"
        )
        
        # Save config
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]['ticket_category'] = category.id
        self.save_config()
        
        embed = discord.Embed(
            title="✅ Ticket System Setup Complete",
            description="Ticket system has been configured",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        embed.add_field(name="Ticket Category", value=category.mention, inline=True)
        embed.add_field(name="Next Steps", value="Use `!setticketrole @role` to set staff role", inline=False)
        embed.set_footer(text="Users can now create tickets with !createticket")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='setticketrole')
    @commands.has_permissions(administrator=True)
    async def set_ticket_role(self, ctx, role: discord.Role):
        """
        Set the staff role that can access all tickets
        
        Usage: !setticketrole <role>
        Example: !setticketrole @SOC Team
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]['staff_role'] = role.id
        self.save_config()
        
        embed = discord.Embed(
            title="✅ Staff Role Set",
            description=f"Staff role set to {role.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text="This role will have access to all tickets")
        
        await ctx.send(embed=embed)
    
    # ==================== HELPER METHODS ====================
    
    def get_priority_color(self, priority: str) -> discord.Color:
        """Get embed color based on priority"""
        colors = {
            'low': discord.Color.blue(),
            'medium': discord.Color.gold(),
            'high': discord.Color.orange(),
            'critical': discord.Color.red()
        }
        return colors.get(priority, discord.Color.default())

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
