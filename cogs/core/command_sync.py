"""Command Sync
Owner-only prefix command to sync slash commands.
"""

import discord
from discord.ext import commands

from cogs.core.pst_timezone import get_now_pst


class CommandSync(commands.Cog):
    """Sync application commands to Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync_commands", aliases=["sync"])
    @commands.is_owner()
    async def sync_commands(self, ctx, guild_id: int = None):
        """Sync slash commands globally or to a specific guild"""
        try:
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)

                embed = discord.Embed(
                    title="Commands Synced",
                    description=f"Synced {len(synced)} slash commands to guild {guild_id}",
                    color=discord.Color.green(),
                    timestamp=get_now_pst()
                )
                embed.add_field(name="Scope", value="Guild", inline=True)
                embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
            else:
                synced = await self.bot.tree.sync()

                embed = discord.Embed(
                    title="Commands Synced",
                    description=f"Synced {len(synced)} slash commands globally",
                    color=discord.Color.green(),
                    timestamp=get_now_pst()
                )
                embed.add_field(name="Scope", value="Global", inline=True)
                embed.add_field(name="Commands", value=str(len(synced)), inline=True)
                embed.add_field(name="Note", value="Global sync can take up to 1 hour", inline=False)

            await ctx.send(embed=embed)
        except Exception as exc:
            await ctx.send(f"Error syncing commands: {exc}")


async def setup(bot):
    await bot.add_cog(CommandSync(bot))
