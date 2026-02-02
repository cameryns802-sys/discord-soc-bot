import discord
from discord.ext import commands

class RoleAssignment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.interest_roles = {
            "gaming": None,
            "music": None,
            "coding": None
        }


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setinterestrole(self, ctx, interest: str, role: discord.Role):
        self.interest_roles[interest] = role.id
        embed = discord.Embed(description=f"Role for '{interest}' set to {role.name}", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    async def joininterest(self, ctx, interest: str):
        role_id = self.interest_roles.get(interest)
        if role_id:
            role = ctx.guild.get_role(role_id)
            await ctx.author.add_roles(role)
            embed = discord.Embed(description=f"You have been given the '{role.name}' role!", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="No role set for that interest.", color=discord.Color.red())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleAssignment(bot))
