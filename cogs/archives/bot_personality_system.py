"""
Bot Personality System: Toggleable personas affecting tone and communication style.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class BotPersonalityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/bot_personality.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "current_personality": "professional",
            "personality_history": [],
            "easter_eggs": [],
            "reaction_pool": {},
            "joke_count": 0,
            "personality_settings": {
                "professional": {"emoji_frequency": "low", "formality": "high", "humor": "none"},
                "friendly": {"emoji_frequency": "medium", "formality": "medium", "humor": "light"},
                "meme": {"emoji_frequency": "high", "formality": "low", "humor": "maximum"},
                "stoic": {"emoji_frequency": "none", "formality": "maximum", "humor": "none"}
            }
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="set_personality")
    async def set_personality(self, ctx, personality: str):
        """Set bot personality (professional, friendly, meme, stoic)."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        valid = ["professional", "friendly", "meme", "stoic"]
        if personality not in valid:
            await ctx.send(f"❌ Invalid personality. Valid: {', '.join(valid)}")
            return
        
        old_personality = self.data["current_personality"]
        self.data["current_personality"] = personality
        self.data["personality_history"].append({
            "personality": personality,
            "changed_by": str(ctx.author.id),
            "changed_at": datetime.utcnow().isoformat()
        })
        self.save_data(self.data)
        
        emoji_map = {"professional": "🤖", "friendly": "😊", "meme": "🎉", "stoic": "🗿"}
        
        embed = discord.Embed(
            title=f"{emoji_map[personality]} Personality Changed",
            description=f"{old_personality.upper()} → {personality.upper()}",
            color=discord.Color.blue()
        )
        
        settings = self.data["personality_settings"][personality]
        embed.add_field(name="Formality", value=settings["formality"], inline=True)
        embed.add_field(name="Humor Level", value=settings["humor"], inline=True)
        embed.add_field(name="Emoji Frequency", value=settings["emoji_frequency"], inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="current_personality")
    async def current_personality(self, ctx):
        """View current bot personality."""
        personality = self.data["current_personality"]
        settings = self.data["personality_settings"][personality]
        
        emoji_map = {"professional": "🤖", "friendly": "😊", "meme": "🎉", "stoic": "🗿"}
        
        embed = discord.Embed(
            title=f"{emoji_map[personality]} Current Personality",
            description=f"Mode: {personality.upper()}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Formality", value=settings["formality"], inline=True)
        embed.add_field(name="Humor", value=settings["humor"], inline=True)
        embed.add_field(name="Emoji Frequency", value=settings["emoji_frequency"], inline=True)
        embed.add_field(name="Total Changes", value=str(len(self.data["personality_history"])), inline=True)
        embed.add_field(name="Jokes Told", value=str(self.data["joke_count"]), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="add_easter_egg")
    async def add_easter_egg(self, ctx, trigger: str, *, response: str):
        """Add an easter egg (personality-specific joke/reaction)."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        self.data["easter_eggs"].append({
            "trigger": trigger,
            "response": response,
            "added_by": str(ctx.author.id),
            "added_at": datetime.utcnow().isoformat()
        })
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Easter Egg Added",
            description=f"Trigger: {trigger}",
            color=discord.Color.green()
        )
        embed.add_field(name="Response", value=response, inline=False)
        embed.add_field(name="Total Easter Eggs", value=str(len(self.data["easter_eggs"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="list_easter_eggs")
    async def list_easter_eggs(self, ctx):
        """List all easter eggs."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        eggs = self.data["easter_eggs"]
        
        embed = discord.Embed(
            title="🥚 Easter Eggs",
            description=f"Total: {len(eggs)}",
            color=discord.Color.blue()
        )
        
        for egg in eggs[:10]:
            embed.add_field(name=f"🎯 {egg['trigger']}", value=egg['response'], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="personality_history")
    async def personality_history(self, ctx):
        """View personality change history."""
        history = self.data["personality_history"][-10:]  # Last 10 changes
        
        embed = discord.Embed(
            title="📜 Personality History",
            description=f"Recent Changes: {len(history)}",
            color=discord.Color.blue()
        )
        
        for change in reversed(history):
            embed.add_field(
                name=change["personality"].upper(),
                value=f"<t:{int(datetime.fromisoformat(change['changed_at']).timestamp())}>",
                inline=True
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="test_personality")
    async def test_personality(self, ctx, personality: str):
        """Preview a personality."""
        valid = ["professional", "friendly", "meme", "stoic"]
        if personality not in valid:
            await ctx.send(f"❌ Invalid personality. Valid: {', '.join(valid)}")
            return
        
        test_responses = {
            "professional": "Processing request with optimal efficiency. Status: NOMINAL. 🤖",
            "friendly": "Hey there! Happy to help! 😊 What can I do for you?",
            "meme": "AYOOO THE BOT IS HERE 🎉 Let's get this bread! 🚀",
            "stoic": "Your request has been noted. Proceeding with duty. 🗿"
        }
        
        embed = discord.Embed(
            title=f"Preview: {personality.upper()}",
            description=test_responses[personality],
            color=discord.Color.blue()
        )
        
        settings = self.data["personality_settings"][personality]
        embed.add_field(name="Formality", value=settings["formality"], inline=True)
        embed.add_field(name="Humor", value=settings["humor"], inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotPersonalityCog(bot))
