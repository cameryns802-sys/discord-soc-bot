import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class CompromiseDetectorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scans_file = "data/compromise_scans.json"
        self.indicators_file = "data/iocs.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.scans_file):
            with open(self.scans_file) as f:
                self.scans = json.load(f)
        else:
            self.scans = []
        
        if os.path.exists(self.indicators_file):
            with open(self.indicators_file) as f:
                self.iocs = json.load(f)
        else:
            self.iocs = {"ips": [], "hashes": [], "domains": []}

    def save_data(self):
        os.makedirs("data", exist_ok=True)
        with open(self.scans_file, 'w') as f:
            json.dump(self.scans, f, indent=2)
        with open(self.indicators_file, 'w') as f:
            json.dump(self.iocs, f, indent=2)

    @commands.command()
    async def scansystem(self, ctx, system_name: str):
        """Scan a system for compromise indicators"""
        scan = {
            "id": len(self.scans) + 1,
            "system": system_name,
            "findings": [],
            "severity": "CLEAN",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Simulate detection of indicators
        import random
        if random.randint(1, 10) <= 3:  # 30% chance of findings
            scan["findings"] = [
                "Suspicious process: cmd.exe with parent explorer.exe",
                "Unusual outbound connection to 192.168.1.100:4444",
                "Registry modification detected in HKLM\\Run"
            ]
            scan["severity"] = "HIGH"
        
        self.scans.append(scan)
        self.save_data()
        
        color = discord.Color.red() if scan["severity"] == "HIGH" else discord.Color.green()
        embed = discord.Embed(
            title="🔍 System Compromise Scan",
            description=f"System: **{system_name}**",
            color=color
        )
        embed.add_field(name="Scan ID", value=f"#{scan['id']}", inline=True)
        embed.add_field(name="Status", value=scan["severity"], inline=True)
        
        if scan["findings"]:
            findings_text = "\n".join([f"⚠️ {f}" for f in scan["findings"][:5]])
            embed.add_field(name="Findings", value=findings_text, inline=False)
        else:
            embed.add_field(name="Result", value="✅ No indicators of compromise detected", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def addioc(self, ctx, ioc_type: str, value: str):
        """Add indicator of compromise (type: ip/hash/domain)"""
        if ioc_type.lower() not in ["ip", "hash", "domain"]:
            await ctx.send("❌ Type must be: ip, hash, or domain")
            return
        
        self.iocs[f"{ioc_type.lower()}s"].append(value)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ IOC Added",
            description=f"Type: {ioc_type.upper()}\nValue: `{value}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def iocsearch(self, ctx, indicator: str):
        """Search for an indicator in known IOCs"""
        found = False
        ioc_type = "Unknown"
        
        if indicator in self.iocs["ips"]:
            found = True
            ioc_type = "IP Address"
        elif indicator in self.iocs["hashes"]:
            found = True
            ioc_type = "File Hash"
        elif indicator in self.iocs["domains"]:
            found = True
            ioc_type = "Domain"
        
        color = discord.Color.red() if found else discord.Color.green()
        status = "🚨 FOUND IN IOC DATABASE" if found else "✅ Not in IOC database"
        
        embed = discord.Embed(
            title="🔍 IOC Search Result",
            description=f"Indicator: `{indicator}`",
            color=color
        )
        embed.add_field(name="Status", value=status, inline=False)
        if found:
            embed.add_field(name="Type", value=ioc_type, inline=True)
            embed.add_field(name="Risk Level", value="🔴 HIGH", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def iocinventory(self, ctx):
        """Show IOC inventory"""
        embed = discord.Embed(
            title="📊 IOC Inventory",
            color=discord.Color.blue()
        )
        embed.add_field(name="Malicious IPs", value=str(len(self.iocs["ips"])), inline=True)
        embed.add_field(name="File Hashes", value=str(len(self.iocs["hashes"])), inline=True)
        embed.add_field(name="Malicious Domains", value=str(len(self.iocs["domains"])), inline=True)
        embed.add_field(name="Total IOCs", value=str(sum(len(v) for v in self.iocs.values())), inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CompromiseDetectorCog(bot))
