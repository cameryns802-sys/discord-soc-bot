import discord
from discord.ext import commands, tasks
import datetime
from cogs.core.pst_timezone import get_now_pst

class SecurityReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_channel_id = None  # Set this to your staff channel ID
        self.last_report = None
        self.send_report.start()

    @tasks.loop(hours=24)
    async def send_report(self):
        if not self.report_channel_id:
            return
        channel = self.bot.get_channel(self.report_channel_id)
        if channel:
            now = datetime.get_now_pst()
            report = f"Security/Compliance Report for {now:%Y-%m-%d}:\n- No major incidents detected.\n- All systems operational."
            await channel.send(report)
            self.last_report = now

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setreportchannel(self, ctx, channel: discord.TextChannel):
        self.report_channel_id = channel.id
        await ctx.send(f"Report channel set to {channel.mention}")

async def setup(bot):
    await bot.add_cog(SecurityReport(bot))
