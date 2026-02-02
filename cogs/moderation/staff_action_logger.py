import discord
from discord.ext import commands
import datetime

class StaffActionLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actions = []

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.actions.append({
            "action": "ban",
            "user": user.id,
            "guild": guild.id,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        self.actions.append({
            "action": "unban",
            "user": user.id,
            "guild": guild.id,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staffactions(self, ctx):
        """Show recent staff actions."""
        if not self.actions:
            await ctx.send("No staff actions recorded yet.")
            return
        msg = "Recent Staff Actions:\n"
        for entry in self.actions[-10:]:
            user = self.bot.get_user(entry["user"]) or entry["user"]
            msg += f"Action: {entry['action']}, User: {user}, Time: {entry['timestamp']}\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(StaffActionLogger(bot))
