"""
Interactive Buttons for Ticket System
Provides Discord UI components (buttons, select menus) for ticket management
"""

import discord
from discord.ext import commands
from discord import ui
import datetime

class TicketActionButtons(ui.View):
    """Interactive buttons for ticket actions"""
    
    def __init__(self, ticket_system, ticket_id: str, timeout=None):
        super().__init__(timeout=timeout)
        self.ticket_system = ticket_system
        self.ticket_id = ticket_id
    
    @ui.button(label="Claim Ticket", style=discord.ButtonStyle.primary, emoji="✋")
    async def claim_button(self, interaction: discord.Interaction, button: ui.Button):
        """Claim this ticket"""
        ticket = self.ticket_system.tickets.get(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found", ephemeral=True)
            return
        
        if ticket['status'] == 'closed':
            await interaction.response.send_message("❌ Cannot claim a closed ticket", ephemeral=True)
            return
        
        if ticket.get('assigned_to'):
            await interaction.response.send_message(f"❌ Ticket already assigned to <@{ticket['assigned_to']}>", ephemeral=True)
            return
        
        # Claim ticket
        ticket['assigned_to'] = interaction.user.id
        ticket['assigned_by'] = interaction.user.id
        ticket['assigned_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        ticket['status'] = 'in_progress'
        ticket['comments'].append({
            'user_id': interaction.user.id,
            'username': str(interaction.user),
            'comment': f"🤝 Claimed ticket",
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        self.ticket_system.save_data()
        
        # Send DM notification
        try:
            creator = await interaction.client.fetch_user(ticket['creator_id'])
            embed = discord.Embed(
                title=f"🔔 Ticket {ticket['ticket_id']} Claimed",
                description=f"{interaction.user.mention} has claimed your ticket",
                color=discord.Color.blue()
            )
            await creator.send(embed=embed)
        except:
            pass
        
        await interaction.response.send_message(f"✅ You have claimed ticket **{ticket['ticket_id']}**", ephemeral=True)
        
        # Update the embed
        await self.update_ticket_embed(interaction)
    
    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        """Close this ticket"""
        ticket = self.ticket_system.tickets.get(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found", ephemeral=True)
            return
        
        if ticket['status'] == 'closed':
            await interaction.response.send_message("❌ Ticket is already closed", ephemeral=True)
            return
        
        # Close ticket
        ticket['status'] = 'closed'
        ticket['closed_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        ticket['closed_by'] = interaction.user.id
        ticket['comments'].append({
            'user_id': interaction.user.id,
            'username': str(interaction.user),
            'comment': f"🔒 Closed ticket",
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        self.ticket_system.save_data()
        
        # Notify creator
        try:
            creator = await interaction.client.fetch_user(ticket['creator_id'])
            embed = discord.Embed(
                title=f"🔒 Ticket {ticket['ticket_id']} Closed",
                description=f"Your ticket has been closed by {interaction.user.mention}",
                color=discord.Color.red()
            )
            await creator.send(embed=embed)
        except:
            pass
        
        await interaction.response.send_message(f"✅ Ticket **{ticket['ticket_id']}** has been closed", ephemeral=True)
        
        # Update the embed and disable buttons
        for child in self.children:
            child.disabled = True
        await self.update_ticket_embed(interaction)
    
    @ui.button(label="Add Comment", style=discord.ButtonStyle.secondary, emoji="💬")
    async def comment_button(self, interaction: discord.Interaction, button: ui.Button):
        """Add a comment to this ticket"""
        await interaction.response.send_modal(CommentModal(self.ticket_system, self.ticket_id))
    
    @ui.button(label="Change Priority", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def priority_button(self, interaction: discord.Interaction, button: ui.Button):
        """Change ticket priority"""
        await interaction.response.send_message(
            "Select new priority:",
            view=PrioritySelectView(self.ticket_system, self.ticket_id),
            ephemeral=True
        )
    
    async def update_ticket_embed(self, interaction: discord.Interaction):
        """Update the ticket embed with current information"""
        ticket = self.ticket_system.tickets.get(self.ticket_id)
        if not ticket or not interaction.message:
            return
        
        # Build updated embed
        priority_colors = {
            'low': discord.Color.blue(),
            'medium': discord.Color.gold(),
            'high': discord.Color.orange(),
            'critical': discord.Color.red()
        }
        status_emoji = {
            'open': '🟢',
            'in_progress': '🟡',
            'waiting': '🟠',
            'closed': '⚫'
        }
        
        embed = discord.Embed(
            title=f"🎫 Ticket {ticket['ticket_id']}",
            description=ticket['description'],
            color=priority_colors.get(ticket['priority'], discord.Color.gray()),
            timestamp=datetime.datetime.fromisoformat(ticket['created_at'])
        )
        
        embed.add_field(name="Status", value=f"{status_emoji.get(ticket['status'], '⚪')} {ticket['status'].replace('_', ' ').title()}", inline=True)
        embed.add_field(name="Priority", value=f"{'🔵' if ticket['priority'] == 'low' else '🟡' if ticket['priority'] == 'medium' else '🟠' if ticket['priority'] == 'high' else '🔴'} {ticket['priority'].upper()}", inline=True)
        
        if ticket.get('assigned_to'):
            embed.add_field(name="Assigned To", value=f"<@{ticket['assigned_to']}>", inline=True)
        
        embed.add_field(name="Created By", value=f"<@{ticket['creator_id']}>", inline=True)
        
        if ticket.get('channel_id'):
            embed.add_field(name="Channel", value=f"<#{ticket['channel_id']}>", inline=True)
        
        # Comments
        if ticket['comments']:
            comments_text = "\n".join([
                f"**{c['username']}** ({c['timestamp'][:10]}): {c['comment'][:100]}"
                for c in ticket['comments'][-3:]
            ])
            embed.add_field(name=f"Recent Comments ({len(ticket['comments'])})", value=comments_text, inline=False)
        
        try:
            await interaction.message.edit(embed=embed, view=self)
        except:
            pass

class CommentModal(ui.Modal, title="Add Comment"):
    """Modal for adding comments to tickets"""
    
    comment = ui.TextInput(
        label="Comment",
        style=discord.TextStyle.paragraph,
        placeholder="Enter your comment here...",
        required=True,
        max_length=1000
    )
    
    def __init__(self, ticket_system, ticket_id: str):
        super().__init__()
        self.ticket_system = ticket_system
        self.ticket_id = ticket_id
    
    async def on_submit(self, interaction: discord.Interaction):
        ticket = self.ticket_system.tickets.get(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found", ephemeral=True)
            return
        
        # Add comment
        ticket['comments'].append({
            'user_id': interaction.user.id,
            'username': str(interaction.user),
            'comment': self.comment.value,
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        self.ticket_system.save_data()
        
        await interaction.response.send_message(f"✅ Comment added to ticket **{ticket['ticket_id']}**", ephemeral=True)

class PrioritySelectView(ui.View):
    """Select menu for changing ticket priority"""
    
    def __init__(self, ticket_system, ticket_id: str):
        super().__init__(timeout=60)
        self.ticket_system = ticket_system
        self.ticket_id = ticket_id
        
        # Add select menu
        select = ui.Select(
            placeholder="Choose priority...",
            options=[
                discord.SelectOption(label="Low", value="low", emoji="🔵"),
                discord.SelectOption(label="Medium", value="medium", emoji="🟡"),
                discord.SelectOption(label="High", value="high", emoji="🟠"),
                discord.SelectOption(label="Critical", value="critical", emoji="🔴")
            ]
        )
        select.callback = self.priority_callback
        self.add_item(select)
    
    async def priority_callback(self, interaction: discord.Interaction):
        ticket = self.ticket_system.tickets.get(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found", ephemeral=True)
            return
        
        new_priority = interaction.data['values'][0]
        old_priority = ticket['priority']
        
        ticket['priority'] = new_priority
        ticket['comments'].append({
            'user_id': interaction.user.id,
            'username': str(interaction.user),
            'comment': f"⚡ Changed priority from {old_priority.upper()} to {new_priority.upper()}",
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat()
        })
        self.ticket_system.save_data()
        
        await interaction.response.send_message(
            f"✅ Ticket **{ticket['ticket_id']}** priority changed to **{new_priority.upper()}**",
            ephemeral=True
        )

async def setup(bot):
    """This is a utility module, no cog to register"""
    pass
