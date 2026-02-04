# Security Ticket/Case Management System
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/tickets.json'

def load_tickets():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return get_default_tickets()
    return get_default_tickets()

def get_default_tickets():
    return {
        "tickets": [],
        "ticket_counter": 1000
    }

def save_tickets(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_ticket_id():
    data = load_tickets()
    ticket_id = data.get('ticket_counter', 1000) + 1
    data['ticket_counter'] = ticket_id
    save_tickets(data)
    return f"TKT-{ticket_id}"

class TicketManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='create_ticket')
    async def create_ticket(self, ctx, title: str, *, description: str):
        """Create a new security ticket"""
        ticket_id = get_next_ticket_id()
        
        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "created_by": ctx.author.id,
            "created_at": get_now_pst().isoformat(),
            "status": "open",
            "priority": "medium",
            "assigned_to": None,
            "comments": [],
            "attachments": []
        }
        
        data = load_tickets()
        data['tickets'].append(ticket)
        save_tickets(data)
        
        embed = discord.Embed(
            title=f"✅ Ticket Created",
            description=title,
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed.add_field(name="Status", value="🔵 Open", inline=True)
        embed.add_field(name="Priority", value="🟡 Medium", inline=True)
        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        await ctx.send(embed=embed)

    @commands.command(name='list_tickets')
    async def list_tickets(self, ctx, status: str = "all"):
        """List security tickets"""
        data = load_tickets()
        tickets = data.get('tickets', [])
        
        if status != "all":
            tickets = [t for t in tickets if t.get('status') == status]
        
        if not tickets:
            await ctx.send(f"No tickets found with status: {status}")
            return
        
        embed = discord.Embed(
            title="🎫 Security Tickets",
            description=f"Total: {len(tickets)} tickets ({status})",
            color=discord.Color.blue()
        )
        
        for ticket in tickets[:10]:  # Show first 10
            status_emoji = {
                'open': '🔵',
                'in_progress': '🟡',
                'resolved': '🟢',
                'closed': '⚫'
            }.get(ticket.get('status', 'unknown'), '❓')
            
            priority_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(ticket.get('priority', 'unknown'), '❓')
            
            embed.add_field(
                name=f"{status_emoji} {ticket.get('id')} - {ticket.get('title')}",
                value=f"{priority_emoji} {ticket.get('priority').upper()} | Created: {ticket.get('created_at', 'N/A')[:10]}",
                inline=False
            )
        
        embed.set_footer(text="Use !ticket <id> to view details")
        await ctx.send(embed=embed)

    @commands.command(name='ticket')
    async def view_ticket(self, ctx, ticket_id: str):
        """View ticket details"""
        data = load_tickets()
        ticket = next((t for t in data.get('tickets', []) if t.get('id') == ticket_id), None)
        
        if not ticket:
            await ctx.send("❌ Ticket not found")
            return
        
        status_colors = {
            'open': discord.Color.blue(),
            'in_progress': discord.Color.orange(),
            'resolved': discord.Color.green(),
            'closed': discord.Color.greyple()
        }
        
        embed = discord.Embed(
            title=f"🎫 {ticket.get('id')} - {ticket.get('title')}",
            color=status_colors.get(ticket.get('status'), discord.Color.blue()),
            timestamp=datetime.fromisoformat(ticket.get('created_at', get_now_pst().isoformat()))
        )
        
        embed.add_field(name="Status", value=ticket.get('status').upper(), inline=True)
        embed.add_field(name="Priority", value=ticket.get('priority').upper(), inline=True)
        embed.add_field(name="Assigned To", value=f"<@{ticket.get('assigned_to')}>" if ticket.get('assigned_to') else "Unassigned", inline=True)
        embed.add_field(name="Description", value=ticket.get('description'), inline=False)
        
        comments = ticket.get('comments', [])
        if comments:
            comments_text = "\n".join([f"• **{c.get('author')}**: {c.get('text')}" for c in comments[-3:]])
            embed.add_field(name="Recent Comments", value=comments_text, inline=False)
        
        embed.set_footer(text=f"Created by User {ticket.get('created_by')}")
        await ctx.send(embed=embed)

    @commands.command(name='assign_ticket')
    async def assign_ticket(self, ctx, ticket_id: str, user: discord.Member):
        """Assign ticket to a team member"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can assign tickets")
            return
        
        data = load_tickets()
        ticket = next((t for t in data.get('tickets', []) if t.get('id') == ticket_id), None)
        
        if not ticket:
            await ctx.send("❌ Ticket not found")
            return
        
        ticket['assigned_to'] = user.id
        save_tickets(data)
        
        embed = discord.Embed(
            title="✅ Ticket Assigned",
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed.add_field(name="Assigned To", value=user.mention, inline=True)
        embed.add_field(name="Assigned By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='update_ticket_status')
    async def update_ticket_status(self, ctx, ticket_id: str, status: str):
        """Update ticket status (open, in_progress, resolved, closed)"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can update tickets")
            return
        
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
        if status not in valid_statuses:
            await ctx.send(f"❌ Invalid status. Valid: {', '.join(valid_statuses)}")
            return
        
        data = load_tickets()
        ticket = next((t for t in data.get('tickets', []) if t.get('id') == ticket_id), None)
        
        if not ticket:
            await ctx.send("❌ Ticket not found")
            return
        
        old_status = ticket.get('status')
        ticket['status'] = status
        save_tickets(data)
        
        embed = discord.Embed(
            title="✅ Ticket Status Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed.add_field(name="Old Status", value=old_status.upper(), inline=True)
        embed.add_field(name="New Status", value=status.upper(), inline=True)
        embed.add_field(name="Updated By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='comment_ticket')
    async def comment_ticket(self, ctx, ticket_id: str, *, comment: str):
        """Add comment to ticket"""
        data = load_tickets()
        ticket = next((t for t in data.get('tickets', []) if t.get('id') == ticket_id), None)
        
        if not ticket:
            await ctx.send("❌ Ticket not found")
            return
        
        comment_obj = {
            "author": ctx.author.name,
            "author_id": ctx.author.id,
            "text": comment,
            "timestamp": get_now_pst().isoformat()
        }
        
        if 'comments' not in ticket:
            ticket['comments'] = []
        
        ticket['comments'].append(comment_obj)
        save_tickets(data)
        
        embed = discord.Embed(
            title="✅ Comment Added",
            description=comment,
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed.add_field(name="Author", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='close_ticket')
    async def close_ticket(self, ctx, ticket_id: str):
        """Close a resolved ticket"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can close tickets")
            return
        
        data = load_tickets()
        ticket = next((t for t in data.get('tickets', []) if t.get('id') == ticket_id), None)
        
        if not ticket:
            await ctx.send("❌ Ticket not found")
            return
        
        ticket['status'] = 'closed'
        ticket['closed_at'] = get_now_pst().isoformat()
        ticket['closed_by'] = ctx.author.id
        save_tickets(data)
        
        embed = discord.Embed(
            title="✅ Ticket Closed",
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed.add_field(name="Closed By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == 233662304272834560

async def setup(bot):
    await bot.add_cog(TicketManagementCog(bot))
