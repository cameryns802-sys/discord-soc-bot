# Change Tracking & Auditing System: Track all configuration and permission changes
import discord
from discord.ext import commands
from datetime import datetime
import json
import os

class ChangeTrackingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_log = {}  # change_id: change_data
        self.change_counter = 0
        self.configuration_versions = {}  # version_id: version_data
        self.data_file = "data/changes.json"
        self.load_changes()

    def load_changes(self):
        """Load change log from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.change_log = data.get('changes', {})
                    self.change_counter = data.get('counter', 0)
                    self.configuration_versions = data.get('versions', {})
            except:
                self.change_log = {}

    def save_changes(self):
        """Save change log to JSON file."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'changes': self.change_log,
                'counter': self.change_counter,
                'versions': self.configuration_versions
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def logchange(self, ctx, change_type: str, *, description: str):
        """Log a configuration change. Usage: !logchange <type> description"""
        change_type = change_type.lower()
        valid_types = ["role", "permission", "config", "security", "other"]
        
        if change_type not in valid_types:
            await ctx.send(f"❌ Invalid type. Use: {', '.join(valid_types)}")
            return
        
        self.change_counter += 1
        change_id = self.change_counter
        
        change_data = {
            "id": change_id,
            "type": change_type,
            "description": description,
            "made_by": ctx.author.id,
            "made_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "impact": "medium",
            "rollback_available": True
        }
        
        self.change_log[str(change_id)] = change_data
        self.save_changes()
        
        embed = discord.Embed(
            title=f"✅ Change #{change_id} Logged",
            description=description,
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=change_type.upper(), inline=True)
        embed.add_field(name="Status", value="COMPLETED", inline=True)
        embed.add_field(name="Made By", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"Change ID: {change_id}")
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def approvechange(self, ctx, change_id: int):
        """Approve a pending change. Usage: !approvechange <id>"""
        change_key = str(change_id)
        if change_key not in self.change_log:
            await ctx.send("❌ Change not found.")
            return
        
        change = self.change_log[change_key]
        change["status"] = "approved"
        change["approved_by"] = ctx.author.id
        change["approved_at"] = datetime.utcnow().isoformat()
        self.save_changes()
        
        await ctx.send(f"✅ Change #{change_id} approved by {ctx.author.mention}.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def rejectchange(self, ctx, change_id: int, *, reason: str = "No reason provided"):
        """Reject a pending change. Usage: !rejectchange <id> [reason]"""
        change_key = str(change_id)
        if change_key not in self.change_log:
            await ctx.send("❌ Change not found.")
            return
        
        change = self.change_log[change_key]
        change["status"] = "rejected"
        change["rejected_by"] = ctx.author.id
        change["rejection_reason"] = reason
        change["rejected_at"] = datetime.utcnow().isoformat()
        self.save_changes()
        
        embed = discord.Embed(
            title=f"❌ Change #{change_id} Rejected",
            description=change["description"],
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Rejected By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def changehistory(self, ctx, limit: int = 10):
        """View recent changes. Usage: !changehistory [limit]"""
        changes_list = list(self.change_log.values())
        changes_list.sort(key=lambda x: x["made_at"], reverse=True)
        
        if not changes_list:
            await ctx.send("ℹ️ No changes in history.")
            return
        
        embed = discord.Embed(
            title=f"📋 Change History ({len(changes_list)} total)",
            color=discord.Color.blue()
        )
        
        for change in changes_list[:limit]:
            status_badge = "✅" if change["status"] == "completed" else "⏳"
            embed.add_field(
                name=f"{status_badge} #{change['id']} [{change['type'].upper()}]",
                value=f"{change['description']}\nStatus: {change['status']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def changeinfo(self, ctx, change_id: int):
        """Get detailed change information. Usage: !changeinfo <id>"""
        change_key = str(change_id)
        if change_key not in self.change_log:
            await ctx.send("❌ Change not found.")
            return
        
        change = self.change_log[change_key]
        
        embed = discord.Embed(
            title=f"Change #{change_id}",
            description=change["description"],
            color=discord.Color.blue()
        )
        embed.add_field(name="Type", value=change["type"].upper(), inline=True)
        embed.add_field(name="Status", value=change["status"].upper(), inline=True)
        embed.add_field(name="Impact", value=change["impact"].upper(), inline=True)
        embed.add_field(name="Made By", value=f"<@{change['made_by']}>", inline=True)
        embed.add_field(name="Made At", value=change["made_at"].split("T")[0], inline=True)
        embed.add_field(name="Rollback Available", value="Yes" if change["rollback_available"] else "No", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def createversion(self, ctx, *, description: str = "Snapshot"):
        """Create a configuration version/snapshot. Usage: !createversion [description]"""
        version_id = f"v{len(self.configuration_versions) + 1}"
        
        version_data = {
            "version_id": version_id,
            "description": description,
            "created_by": ctx.author.id,
            "created_at": datetime.utcnow().isoformat(),
            "changes_count": len(self.change_log)
        }
        
        self.configuration_versions[version_id] = version_data
        self.save_changes()
        
        embed = discord.Embed(
            title=f"✅ Version {version_id} Created",
            description=description,
            color=discord.Color.green()
        )
        embed.add_field(name="Changes in Version", value=str(version_data["changes_count"]), inline=True)
        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def listversionss(self, ctx):
        """List all configuration versions."""
        embed = discord.Embed(
            title="📦 Configuration Versions",
            color=discord.Color.blue()
        )
        
        if not self.configuration_versions:
            embed.description = "No versions created yet."
        else:
            for version_id, version in self.configuration_versions.items():
                embed.add_field(
                    name=version_id,
                    value=f"{version['description']}\nChanges: {version['changes_count']} | Created: {version['created_at'].split('T')[0]}",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def changestats(self, ctx):
        """View change statistics."""
        total_changes = len(self.change_log)
        
        type_counts = {}
        status_counts = {}
        
        for change in self.change_log.values():
            change_type = change["type"]
            status = change["status"]
            
            type_counts[change_type] = type_counts.get(change_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        embed = discord.Embed(
            title="📊 Change Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Changes", value=str(total_changes), inline=True)
        embed.add_field(name="Versions", value=str(len(self.configuration_versions)), inline=True)
        
        for status, count in status_counts.items():
            embed.add_field(name=status.capitalize(), value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChangeTrackingCog(bot))
