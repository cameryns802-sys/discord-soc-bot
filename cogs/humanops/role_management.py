# Role Management System: Create, delete, and manage roles
import discord
from discord.ext import commands
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class RoleManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_templates = {
            "admin": {"color": discord.Color.red(), "permissions": discord.Permissions(administrator=True)},
            "moderator": {"color": discord.Color.orange(), "permissions": discord.Permissions(moderate_members=True, manage_messages=True)},
            "member": {"color": discord.Color.blue(), "permissions": discord.Permissions(send_messages=True, read_messages=True)},
            "verified": {"color": discord.Color.green(), "permissions": discord.Permissions(send_messages=True)},
            "muted": {"color": discord.Color.dark_gray(), "permissions": discord.Permissions()},
            "vip": {"color": discord.Color.gold(), "permissions": discord.Permissions(send_messages=True)},
        }
        self.created_roles = {}  # guild_id: [role_data]

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, name: str, *, description: str = None):
        """Create a custom role. Usage: !createrole RoleName [description]"""
        try:
            role = await ctx.guild.create_role(
                name=name,
                color=discord.Color.random(),
                reason=f"Created by {ctx.author}"
            )
            
            # Store role info
            guild_id = ctx.guild.id
            if guild_id not in self.created_roles:
                self.created_roles[guild_id] = []
            
            self.created_roles[guild_id].append({
                "id": role.id,
                "name": name,
                "description": description,
                "created_by": ctx.author.id,
                "created_at": get_now_pst().isoformat()
            })
            
            embed = discord.Embed(
                title="✅ Role Created",
                description=f"Successfully created role **{name}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Role ID", value=role.id, inline=True)
            embed.add_field(name="Color", value=str(role.color), inline=True)
            if description:
                embed.add_field(name="Description", value=description, inline=False)
            embed.set_footer(text=f"Created by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create roles.")
        except Exception as e:
            await ctx.send(f"❌ Error creating role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createrole_template(self, ctx, template: str, name: str):
        """Create a role from a template. Usage: !createrole_template [admin|moderator|member|verified|muted|vip] RoleName"""
        template = template.lower()
        if template not in self.role_templates:
            await ctx.send(f"❌ Unknown template. Available: {', '.join(self.role_templates.keys())}")
            return
        
        try:
            template_data = self.role_templates[template]
            role = await ctx.guild.create_role(
                name=name,
                color=template_data["color"],
                permissions=template_data["permissions"],
                reason=f"Created from {template} template by {ctx.author}"
            )
            
            embed = discord.Embed(
                title="✅ Role Created from Template",
                description=f"Created **{name}** from **{template}** template",
                color=discord.Color.green()
            )
            embed.add_field(name="Role ID", value=role.id, inline=True)
            embed.add_field(name="Color", value=str(role.color), inline=True)
            embed.add_field(name="Template", value=template.capitalize(), inline=True)
            embed.set_footer(text=f"Created by {ctx.author}")
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create roles.")
        except Exception as e:
            await ctx.send(f"❌ Error creating role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createroles_batch(self, ctx, *, roles_text: str):
        """Create multiple roles at once. Usage: !createroles_batch role1, role2, role3"""
        role_names = [name.strip() for name in roles_text.split(",")]
        created = []
        failed = []
        
        for role_name in role_names:
            try:
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color.random(),
                    reason=f"Batch created by {ctx.author}"
                )
                created.append(f"✅ {role.mention}")
            except Exception as e:
                failed.append(f"❌ {role_name}: {str(e)[:30]}")
        
        embed = discord.Embed(
            title="🎯 Batch Role Creation",
            color=discord.Color.blue()
        )
        
        if created:
            embed.add_field(name=f"✅ Created ({len(created)})", value="\n".join(created), inline=False)
        if failed:
            embed.add_field(name=f"❌ Failed ({len(failed)})", value="\n".join(failed), inline=False)
        
        embed.set_footer(text=f"Total: {len(created)} created, {len(failed)} failed")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx, role: discord.Role):
        """Delete a role. Usage: !deleterole @RoleName"""
        try:
            role_name = role.name
            await role.delete(reason=f"Deleted by {ctx.author}")
            
            embed = discord.Embed(
                title="🗑️ Role Deleted",
                description=f"Successfully deleted role **{role_name}**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete roles.")
        except Exception as e:
            await ctx.send(f"❌ Error deleting role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def editrole(self, ctx, role: discord.Role, *, new_name: str):
        """Rename a role. Usage: !editrole @RoleName NewName"""
        try:
            old_name = role.name
            await role.edit(name=new_name, reason=f"Renamed by {ctx.author}")
            
            embed = discord.Embed(
                title="✏️ Role Renamed",
                description=f"**{old_name}** → **{new_name}**",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to edit roles.")
        except Exception as e:
            await ctx.send(f"❌ Error editing role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolecolor(self, ctx, role: discord.Role, hex_color: str):
        """Change a role's color. Usage: !rolecolor @RoleName #FF0000"""
        try:
            # Parse hex color
            if not hex_color.startswith("#"):
                hex_color = f"#{hex_color}"
            
            color = discord.Color(int(hex_color.lstrip("#"), 16))
            await role.edit(color=color, reason=f"Color changed by {ctx.author}")
            
            embed = discord.Embed(
                title="🎨 Role Color Changed",
                description=f"**{role.name}** color changed to {hex_color}",
                color=color
            )
            embed.add_field(name="Preview", value="████████", inline=False)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Invalid hex color. Use format: #FF0000")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to edit roles.")
        except Exception as e:
            await ctx.send(f"❌ Error changing color: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def assignrole(self, ctx, user: discord.Member, role: discord.Role):
        """Assign a role to a user. Usage: !assignrole @User @Role"""
        try:
            await user.add_roles(role, reason=f"Assigned by {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Role Assigned",
                description=f"Assigned {role.mention} to {user.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign roles.")
        except Exception as e:
            await ctx.send(f"❌ Error assigning role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, user: discord.Member, role: discord.Role):
        """Remove a role from a user. Usage: !removerole @User @Role"""
        try:
            await user.remove_roles(role, reason=f"Removed by {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"Removed {role.mention} from {user.mention}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove roles.")
        except Exception as e:
            await ctx.send(f"❌ Error removing role: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def massassignrole(self, ctx, role: discord.Role, limit: int = 100):
        """Assign role to all members (limited). Usage: !massassignrole @Role [limit]"""
        confirm = await ctx.send(f"⚠️ This will assign {role.mention} to up to {limit} members. React ✅ to confirm.")
        await confirm.add_reaction("✅")
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=lambda r, u: u == ctx.author and str(r.emoji) == "✅")
            
            assigned = 0
            failed = 0
            
            for member in list(ctx.guild.members)[:limit]:
                try:
                    if role not in member.roles:
                        await member.add_roles(role)
                        assigned += 1
                except Exception as e:
                    failed += 1
            
            embed = discord.Embed(
                title="📊 Mass Role Assignment Complete",
                description=f"Assigned {role.mention} to members",
                color=discord.Color.green()
            )
            embed.add_field(name="✅ Assigned", value=str(assigned), inline=True)
            embed.add_field(name="❌ Failed", value=str(failed), inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    async def listroles(self, ctx):
        """List all roles in the server."""
        roles = ctx.guild.roles
        
        # Create paginated list
        chunks = [roles[i:i+15] for i in range(0, len(roles), 15)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📋 Server Roles ({len(roles)} total)",
                color=discord.Color.blue()
            )
            
            role_list = []
            for role in chunk:
                member_count = len([m for m in ctx.guild.members if role in m.roles])
                role_list.append(f"{role.mention} - {member_count} members")
            
            embed.description = "\n".join(role_list)
            embed.set_footer(text=f"Page {i+1}/{len(chunks)}")
            await ctx.send(embed=embed)

    @commands.command()
    async def roleinfo(self, ctx, role: discord.Role):
        """Get information about a role."""
        member_count = len([m for m in ctx.guild.members if role in m.roles])
        
        embed = discord.Embed(
            title=f"ℹ️ Role Information",
            description=role.mention,
            color=role.color
        )
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Members", value=member_count, inline=True)
        embed.add_field(name="Position", value=f"{role.position}/{len(ctx.guild.roles)}", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Created", value=role.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleManagementCog(bot))
