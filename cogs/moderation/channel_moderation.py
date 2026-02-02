import discord
from discord.ext import commands

class ChannelModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_rules = {
            # Example: channel_id: ["no_links", "no_images"]
        }

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setchannelrule(self, ctx, channel: discord.TextChannel, *, rule):
        cid = channel.id
        self.channel_rules.setdefault(cid, []).append(rule)
        await ctx.send(f"Rule '{rule}' added for {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        rules = self.channel_rules.get(message.channel.id, [])
        if "no_links" in rules and "http" in message.content:
            try:
                await message.delete()
            except Exception:
                pass
        if "no_images" in rules and any(attachment.content_type and attachment.content_type.startswith("image") for attachment in message.attachments):
            try:
                await message.delete()
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(ChannelModeration(bot))
