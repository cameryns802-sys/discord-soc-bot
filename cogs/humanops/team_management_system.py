# Team Management System: User roles, permissions, team assignments
import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class TeamManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.teams = {}
        self.team_members = {}
        self.permissions_matrix = {}
        self.team_counter = 0
        self.data_file = "data/team_management.json"
        self.load_teams()

    def load_teams(self):
        """Load team data."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.teams = data.get('teams', {})
                    self.team_members = data.get('team_members', {})
                    self.permissions_matrix = data.get('permissions', {})
                    self.team_counter = data.get('team_counter', 0)
            except:
                pass

    def save_teams(self):
        """Save team data."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'teams': self.teams,
                'team_members': self.team_members,
                'permissions': self.permissions_matrix,
                'team_counter': self.team_counter
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createteam(self, ctx, *, name: str):
        """Create new team. Usage: !createteam <team_name>"""
        self.team_counter += 1
        team_id = self.team_counter
        
        team_data = {
            "id": team_id,
            "name": name,
            "lead": ctx.author.id,
            "created_at": get_now_pst().isoformat(),
            "member_count": 0,
            "members": [],
            "description": "",
            "status": "active"
        }
        
        self.teams[str(team_id)] = team_data
        self.save_teams()
        
        embed = discord.Embed(
            title=f"✅ Team Created #{team_id}",
            description=name,
            color=discord.Color.green()
        )
        embed.add_field(name="Lead", value=f"<@{ctx.author.id}>", inline=True)
        embed.add_field(name="Members", value="1", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtomember(self, ctx, team_id: int, member: discord.Member):
        """Add member to team. Usage: !addtomember <team_id> @member"""
        team_key = str(team_id)
        if team_key not in self.teams:
            await ctx.send("❌ Team not found.")
            return
        
        team = self.teams[team_key]
        
        if member.id not in team["members"]:
            team["members"].append(member.id)
            team["member_count"] = len(team["members"])
            
            self.team_members[str(member.id)] = {
                "user_id": member.id,
                "team_id": team_id,
                "role": "member",
                "added_at": get_now_pst().isoformat(),
                "permissions": []
            }
            
            self.save_teams()
            
            await ctx.send(f"✅ {member.mention} added to team '{team['name']}'")
        else:
            await ctx.send(f"❌ {member.mention} already in team.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmemberrole(self, ctx, member: discord.Member, team_id: int, role: str):
        """Set member role in team. Usage: !setmemberrole @member <team_id> <analyst|engineer|lead>"""
        valid_roles = ['analyst', 'engineer', 'lead', 'member']
        if role.lower() not in valid_roles:
            await ctx.send(f"❌ Invalid role. Use: {', '.join(valid_roles)}")
            return
        
        team_key = str(team_id)
        if team_key not in self.teams:
            await ctx.send("❌ Team not found.")
            return
        
        member_key = str(member.id)
        if member_key not in self.team_members or self.team_members[member_key]["team_id"] != team_id:
            await ctx.send("❌ Member not in this team.")
            return
        
        self.team_members[member_key]["role"] = role.lower()
        self.save_teams()
        
        await ctx.send(f"✅ {member.mention} role set to {role.upper()} in team #{team_id}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def grantpermission(self, ctx, member: discord.Member, *, permission: str):
        """Grant permission to member. Usage: !grantpermission @member permission_name"""
        member_key = str(member.id)
        
        if member_key not in self.team_members:
            await ctx.send("❌ Member not in any team.")
            return
        
        if permission.lower() not in self.team_members[member_key]["permissions"]:
            self.team_members[member_key]["permissions"].append(permission.lower())
            self.save_teams()
            
            await ctx.send(f"✅ Permission '{permission}' granted to {member.mention}")
        else:
            await ctx.send(f"❌ {member.mention} already has this permission.")

    @commands.command()
    async def viewteam(self, ctx, team_id: int):
        """View team details. Usage: !viewteam <team_id>"""
        team_key = str(team_id)
        if team_key not in self.teams:
            await ctx.send("❌ Team not found.")
            return
        
        team = self.teams[team_key]
        
        embed = discord.Embed(
            title=f"Team: {team['name']}",
            description=team.get('description', 'No description'),
            color=discord.Color.blue()
        )
        embed.add_field(name="Team ID", value=team_id, inline=True)
        embed.add_field(name="Lead", value=f"<@{team['lead']}>", inline=True)
        embed.add_field(name="Members", value=team['member_count'], inline=True)
        embed.add_field(name="Status", value=team['status'].upper(), inline=True)
        
        if team["members"]:
            members_str = "\n".join([f"• <@{m}>" for m in team["members"][:10]])
            embed.add_field(name="Team Members", value=members_str, inline=False)
        
        embed.add_field(name="Created", value=team['created_at'], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def listteams(self, ctx):
        """List all teams."""
        if not self.teams:
            await ctx.send("ℹ️ No teams created.")
            return
        
        embed = discord.Embed(
            title=f"📋 All Teams ({len(self.teams)})",
            color=discord.Color.blue()
        )
        
        for team_id, team in self.teams.items():
            embed.add_field(
                name=f"#{team_id} | {team['name']}",
                value=f"Lead: <@{team['lead']}> | Members: {team['member_count']} | Status: {team['status'].upper()}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def myrole(self, ctx):
        """View your role in teams."""
        member_key = str(ctx.author.id)
        
        if member_key not in self.team_members:
            await ctx.send("ℹ️ You're not assigned to any team.")
            return
        
        member_data = self.team_members[member_key]
        team = self.teams.get(str(member_data["team_id"]))
        
        embed = discord.Embed(
            title=f"Your Team Role",
            color=discord.Color.blue()
        )
        embed.add_field(name="Team", value=team['name'] if team else "Unknown", inline=True)
        embed.add_field(name="Role", value=member_data['role'].upper(), inline=True)
        embed.add_field(name="Permissions", value=", ".join(member_data['permissions']) if member_data['permissions'] else "None", inline=False)
        embed.add_field(name="Added", value=member_data['added_at'], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def teamstats(self, ctx):
        """View team statistics."""
        total_members = sum(t.get('member_count', 0) for t in self.teams.values())
        active_teams = sum(1 for t in self.teams.values() if t.get('status') == 'active')
        
        embed = discord.Embed(
            title="📊 Team Management Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Teams", value=len(self.teams), inline=True)
        embed.add_field(name="Active Teams", value=active_teams, inline=True)
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Unique Users", value=len(self.team_members), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TeamManagementCog(bot))
