import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class Reminders(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.reminders = []
		self.check_reminders.start()

	@commands.command()
	async def remindme(self, ctx, time: int, *, message: str):
		remind_at = datetime.utcnow() + timedelta(minutes=time)
		self.reminders.append({"user": ctx.author.id, "message": message, "remind_at": remind_at})
		await ctx.send(f"Reminder set for {time} minutes: {message}")

	@tasks.loop(seconds=30)
	async def check_reminders(self):
		now = datetime.utcnow()
		to_remove = []
		for r in self.reminders:
			if now >= r["remind_at"]:
				user = self.bot.get_user(r["user"])
				if user:
					await user.send(f"Reminder: {r['message']}")
				to_remove.append(r)
		for r in to_remove:
			self.reminders.remove(r)

	@check_reminders.before_loop
	async def before_check_reminders(self):
		await self.bot.wait_until_ready()

async def setup(bot):
	await bot.add_cog(Reminders(bot))

