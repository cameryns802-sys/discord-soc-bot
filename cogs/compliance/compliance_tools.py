import discord
from discord.ext import commands
import os
import json

DATA_REQUESTS_FILE = "data_requests.json"

class ComplianceTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(DATA_REQUESTS_FILE):
            with open(DATA_REQUESTS_FILE, "w") as f:
                json.dump({}, f)

    @commands.command()
    async def requestdata(self, ctx):
        user_id = str(ctx.author.id)
        with open(DATA_REQUESTS_FILE, "r+") as f:
            data = json.load(f)
            data[user_id] = "export_requested"
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        await ctx.send("Your data export request has been logged. Staff will contact you.")

    @commands.command()
    async def deletedata(self, ctx):
        user_id = str(ctx.author.id)
        with open(DATA_REQUESTS_FILE, "r+") as f:
            data = json.load(f)
            data[user_id] = "delete_requested"
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        await ctx.send("Your data deletion request has been logged. Staff will contact you.")

async def setup(bot):
    await bot.add_cog(ComplianceTools(bot))
