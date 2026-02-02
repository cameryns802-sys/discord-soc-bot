import discord
from discord.ext import commands
import random, string, asyncio

class AdvancedVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending = {}
        self.verification_channel_name = "verify"
        self.verified_role_name = "Verified"
        self.code_length = 6
        self.timeout = 300  # seconds

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setverifychannel(self, ctx, channel: discord.TextChannel):
        self.verification_channel_name = channel.name
        await ctx.send(f"Verification channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setverifiedrole(self, ctx, *, role: discord.Role):
        self.verified_role_name = role.name
        await ctx.send(f"Verified role set to {role.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name=self.verification_channel_name)
        role = discord.utils.get(member.guild.roles, name=self.verified_role_name)
        if channel and role:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=self.code_length))
            self.pending[member.id] = code
            await channel.send(f"{member.mention}, please verify by typing: !verify {code}")
            try:
                def check(m):
                    return m.author.id == member.id and m.channel == channel and m.content.strip() == f"!verify {code}"
                await self.bot.wait_for('message', check=check, timeout=self.timeout)
                await member.add_roles(role)
                await channel.send(f"{member.mention} has been verified and given the {role.name} role!")
                del self.pending[member.id]
            except asyncio.TimeoutError:
                await channel.send(f"{member.mention} failed to verify in time.")
                del self.pending[member.id]

async def setup(bot):
    await bot.add_cog(AdvancedVerification(bot))
