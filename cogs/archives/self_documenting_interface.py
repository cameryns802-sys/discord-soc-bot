"""
Self-Documenting Interface: Bot explains any command/setting in chat.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SelfDocumentingInterfaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/self_docs.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "command_docs": {},
            "feature_docs": {},
            "setting_docs": {},
            "help_requests": [],
            "documentation_cache": {}
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    @commands.command(name="explain_feature")
    async def explain_feature(self, ctx, *, topic: str):
        """Get in-depth explanation of a command, feature, or setting."""
        
        # Auto-generate documentation
        docs = {
            "health_dashboard": "Shows real-time health metrics: latency, memory usage, CPU, thread count, guild count, cog count, and recent errors. Access with: /health_dashboard",
            "self_repair": "Analyzes bot health and suggests recovery actions for detected issues. Automatically logs recovery attempts for audit trails.",
            "set_personality": "Changes bot communication style. Options: professional (formal), friendly (casual), meme (hilarious), stoic (minimal). Affects tone of all bot responses.",
            "understand": "Uses NLP to parse natural language queries and suggests relevant commands. Learn it, teach it, and it gets smarter!",
            "start_setup_wizard": "Interactive 3-step guided configuration for your server. Auto-detects security needs and recommends settings.",
            "hot_load_cog": "Dynamically load a cog without restarting the bot. Use: /hot_load_cog [cog_path]",
            "challenge": "Start a security awareness challenge. Test your team's knowledge of security best practices.",
            "threat_network_stats": "View statistics from the anonymous threat intelligence network you're connected to.",
            "evidence_package": "Bundle incident data with digital signatures and chain of custody tracking for compliance.",
            "predict_next_action": "AI predicts your next likely action based on conversation history and command patterns."
        }
        
        topic_lower = topic.lower().replace(" ", "_")
        
        # Try to find documentation
        explanation = None
        for key in docs:
            if topic_lower in key or key in topic_lower:
                explanation = docs[key]
                break
        
        if not explanation:
            explanation = f"Documentation for '{topic}' not yet available. Use /list_docs to see documented features."
        
        embed = discord.Embed(
            title=f"📖 Help: {topic}",
            description=explanation,
            color=discord.Color.blue()
        )
        
        # Log help request
        self.data["help_requests"].append({
            "query": topic,
            "user": str(ctx.author.id),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.save_data(self.data)
        await ctx.send(embed=embed)

    @commands.command(name="how_to")
    async def how_to(self, ctx, *, task: str):
        """Get step-by-step instructions for a task."""
        
        instructions = {
            "ban a user": "1. Use /ban @user reason\n2. Bot will log the action\n3. User is removed from server\n4. Check audit log for receipt",
            "setup moderation": "1. Run /start_setup_wizard\n2. Select security level\n3. Configure moderation rules\n4. Enable logging\n5. Done!",
            "enable auto-update": "1. Use /enable_auto_update\n2. Admin approval required\n3. Bot checks for updates daily\n4. Auto-applies security patches",
            "join threat network": "1. Use /join_threat_network\n2. Review privacy terms\n3. Start sharing threat intel\n4. Receive network alerts",
            "verify bot health": "1. Run /health_dashboard\n2. Check all metrics are green\n3. If issues found, run /self_repair\n4. Check recovery status"
        }
        
        task_lower = task.lower()
        instruction = None
        
        for key in instructions:
            if task_lower in key or key in task_lower:
                instruction = instructions[key]
                break
        
        if not instruction:
            instruction = f"Instructions for '{task}' not found. Try /list_docs for available topics."
        
        embed = discord.Embed(
            title=f"🎯 How to: {task}",
            description=instruction,
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="list_docs")
    async def list_docs(self, ctx):
        """List all documented features and commands."""
        
        categories = {
            "Health & Monitoring": ["health_dashboard", "self_repair", "uptime_tracker", "api_health_check"],
            "Personality & Config": ["set_personality", "current_personality", "start_setup_wizard"],
            "Intelligence": ["understand", "predict_next_action", "teach_intent"],
            "Plugins & Extension": ["hot_load_cog", "hot_reload_cog", "list_loaded_plugins"],
            "Security": ["challenge", "tamper_check", "evidence_package"],
            "Analytics": ["analytics_dashboard", "feature_adoption", "user_journey"]
        }
        
        embed = discord.Embed(
            title="📚 Feature Documentation",
            description="All documented commands and features",
            color=discord.Color.blue()
        )
        
        for category, features in categories.items():
            feature_list = "\n".join([f"• {f}" for f in features])
            embed.add_field(name=category, value=feature_list, inline=False)
        
        embed.set_footer(text="Use /explain [command] for details | Use /how_to [task] for instructions")
        
        await ctx.send(embed=embed)

    @commands.command(name="search_docs")
    async def search_docs(self, ctx, *, query: str):
        """Search documentation for relevant topics."""
        
        all_docs = {
            "health_dashboard": "View system health metrics",
            "self_repair": "Auto-healing system",
            "personality": "Bot communication style",
            "intent": "Natural language parsing",
            "wizard": "Setup guidance",
            "plugin": "Plugin management",
            "security": "Security features",
            "evidence": "Audit trail and compliance"
        }
        
        matches = [topic for topic in all_docs if query.lower() in topic.lower()]
        
        embed = discord.Embed(
            title=f"🔍 Search Results: {query}",
            description=f"Found {len(matches)} topics",
            color=discord.Color.blue()
        )
        
        if matches:
            for match in matches:
                embed.add_field(name=f"• {match}", value=all_docs[match], inline=False)
        else:
            embed.add_field(name="No Results", value=f"No documentation found for '{query}'", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SelfDocumentingInterfaceCog(bot))
