import discord
from discord.ext import commands

class ServerLockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.locked = False

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        self.locked = True
        await ctx.send("🚨 Server is now in lockdown mode. New joins and messages are restricted.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
        self.locked = False
        await ctx.send("🔓 Server lockdown lifted. Normal operations resumed.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.locked:
            try:
                await member.kick(reason="Server is in lockdown mode.")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.locked and not message.author.guild_permissions.administrator:
            try:
                await message.delete()
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(ServerLockdown(bot))
