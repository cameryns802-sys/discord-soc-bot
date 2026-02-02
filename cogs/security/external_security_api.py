import discord
from discord.ext import commands, tasks
import requests

VIRUSTOTAL_API_KEY = "YOUR_API_KEY"  # Replace with your actual API key
VIRUSTOTAL_URL = "https://www.virustotal.com/api/v3/urls"

class ExternalSecurityAPI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # Scan URLs in messages using VirusTotal
        urls = [word for word in message.content.split() if word.startswith("http")]
        for url in urls:
            result = self.scan_url(url)
            if result == "malicious":
                try:
                    await message.delete()
                except Exception:
                    pass
                staff_role = discord.utils.get(message.guild.roles, name="Staff")
                staff_ping = staff_role.mention if staff_role else "@here"
                await message.channel.send(f"🚨 Malicious URL detected and removed: {url} {staff_ping}")

    def scan_url(self, url):
        # Placeholder: In production, use VirusTotal API
        # Here, always return 'clean' for demo
        # To use VirusTotal, uncomment below and set your API key
        # response = requests.post(VIRUSTOTAL_URL, headers={"x-apikey": VIRUSTOTAL_API_KEY}, data={"url": url})
        # if response.status_code == 200:
        #     data = response.json()
        #     if data['data']['attributes']['last_analysis_stats']['malicious'] > 0:
        #         return "malicious"
        # return "clean"
        return "clean"

async def setup(bot):
    await bot.add_cog(ExternalSecurityAPI(bot))
