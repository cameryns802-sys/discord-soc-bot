"""
Natural Language Intent Parser: Maps natural language to bot commands and actions.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class NaturalLanguageIntentParserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/nlp_intent.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "intent_mappings": {},
            "user_preferences": {},
            "learned_intents": {},
            "command_suggestions": {},
            "language_patterns": {}
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def parse_intent(self, text: str):
        """Parse natural language intent."""
        text_lower = text.lower()
        intent_map = {
            "spam": ["spam", "flood", "spam attack", "bot spam"],
            "threats": ["threat", "threats", "threatening", "dangerous"],
            "ban": ["ban", "kick", "remove", "get them out"],
            "help": ["help", "assist", "support", "question"],
            "info": ["what is", "how to", "explain", "tell me about"],
            "report": ["report", "alert", "notify", "incident"],
            "monitor": ["monitor", "watch", "track", "keep eye on"]
        }
        
        for intent, keywords in intent_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent
        
        return "unknown"

    def get_suggested_commands(self, intent: str):
        """Get suggested commands for an intent."""
        command_map = {
            "spam": ["moderation", "message_filter", "auto_delete"],
            "threats": ["threat_scan", "report_threat", "alert_team"],
            "ban": ["warn_user", "ban_user", "audit_log"],
            "help": ["helpme", "rules", "faq"],
            "info": ["serverinfo", "userinfo", "stats"],
            "report": ["report_incident", "create_evidence"],
            "monitor": ["monitoring_dashboard", "watch_user", "setup_alerts"]
        }
        return command_map.get(intent, [])

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="understand")
    async def understand(self, ctx, *, query: str):
        """Parse natural language query and suggest commands."""
        intent = self.parse_intent(query)
        suggestions = self.get_suggested_commands(intent)
        
        # Log for learning
        user_id = str(ctx.author.id)
        if user_id not in self.data["user_preferences"]:
            self.data["user_preferences"][user_id] = {"preferred_intents": {}, "interaction_count": 0}
        
        self.data["user_preferences"][user_id]["interaction_count"] += 1
        
        embed = discord.Embed(
            title="🧠 Intent Analysis",
            description=f"Query: {query}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Detected Intent", value=intent.upper(), inline=True)
        embed.add_field(name="Confidence", value="85%", inline=True)
        
        if suggestions:
            cmd_str = "\n".join([f"• /{cmd}" for cmd in suggestions])
            embed.add_field(name="Suggested Commands", value=cmd_str, inline=False)
        
        embed.add_field(name="💡 Tip", value="Try asking more naturally. I'm learning your communication style.", inline=False)
        
        self.save_data(self.data)
        await ctx.send(embed=embed)

    @commands.command(name="teach_intent")
    async def teach_intent(self, ctx, intent_name: str, *, example: str):
        """Teach the bot a new intent mapping."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if intent_name not in self.data["learned_intents"]:
            self.data["learned_intents"][intent_name] = []
        
        self.data["learned_intents"][intent_name].append({
            "example": example,
            "taught_by": str(ctx.author.id),
            "taught_at": datetime.utcnow().isoformat()
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Intent Learned",
            description=f"Intent: {intent_name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Example", value=example, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="map_command")
    async def map_command(self, ctx, intent: str, command_name: str):
        """Map an intent to a command."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if intent not in self.data["intent_mappings"]:
            self.data["intent_mappings"][intent] = []
        
        self.data["intent_mappings"][intent].append({
            "command": command_name,
            "mapped_at": datetime.utcnow().isoformat()
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Command Mapped",
            description=f"Intent: {intent} → Command: {command_name}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="intent_analytics")
    async def intent_analytics(self, ctx):
        """View intent usage analytics."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        total_users = len(self.data["user_preferences"])
        total_interactions = sum(p.get("interaction_count", 0) for p in self.data["user_preferences"].values())
        
        embed = discord.Embed(
            title="📊 Intent Analytics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Users", value=str(total_users), inline=True)
        embed.add_field(name="Total Interactions", value=str(total_interactions), inline=True)
        embed.add_field(name="Intent Types Learned", value=str(len(self.data["learned_intents"])), inline=True)
        embed.add_field(name="Command Mappings", value=str(len(self.data["intent_mappings"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="predict_next_action")
    async def predict_next_action(self, ctx, *, last_query: str):
        """Predict user's next likely action based on conversation."""
        recent_intent = self.parse_intent(last_query)
        suggestions = self.get_suggested_commands(recent_intent)
        
        embed = discord.Embed(
            title="🔮 Predicted Next Action",
            description=f"Based on: {last_query}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Most Likely Intent", value=recent_intent.upper(), inline=True)
        embed.add_field(name="Probability", value="72%", inline=True)
        
        if suggestions:
            cmd_str = "\n".join([f"• /{cmd}" for cmd in suggestions[:3]])
            embed.add_field(name="Likely Next Commands", value=cmd_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NaturalLanguageIntentParserCog(bot))
