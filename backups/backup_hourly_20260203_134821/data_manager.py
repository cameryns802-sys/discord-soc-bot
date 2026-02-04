# Data Manager: Persistent storage for all bot data
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import asyncio

class DataManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.data_file = os.path.join(self.data_dir, "bot_data.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Data containers
        self.data = {
            "warns": {},  # user_id: [warnings]
            "reputation": {},  # user_id: {"rep": int, "given": [], "received": []}
            "levels": {},  # user_id: {"level": int, "xp": int, "messages": int}
            "reminders": [],  # [{user_id, reminder, time, channel_id}]
            "guild_settings": {},  # guild_id: {settings}
            "user_settings": {},  # user_id: {settings}
            "achievements": {},  # user_id: [achievements]
            "suggestions": [],  # [{user, suggestion, timestamp, status}]
            "trivia_scores": {},  # user_id: {"correct": int, "total": int}
            "consent": {},  # user_id: {"given": bool, "timestamp": str}
            "privacy_accepted": {},  # user_id: timestamp
            "tos_accepted": {},  # user_id: timestamp
            "custom_data": {}  # For other cogs to store data
        }
        
        # Load data on startup
        self.load_data()
        
        # Start auto-save task
        self.auto_save.start()
    
    def cog_unload(self):
        """Save data when cog is unloaded."""
        self.auto_save.cancel()
        self.save_data()
    
    def load_data(self):
        """Load all data from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge loaded data with defaults
                    for key in self.data:
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
                print(f"[DataManager] ✅ Loaded data from {self.data_file}")
            except Exception as e:
                print(f"[DataManager] ⚠️ Error loading data: {e}")
        else:
            print(f"[DataManager] ℹ️ No existing data file, starting fresh")
    
    def save_data(self):
        """Save all data to JSON file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"[DataManager] ✅ Data saved to {self.data_file}")
        except Exception as e:
            print(f"[DataManager] ❌ Error saving data: {e}")
    
    @tasks.loop(minutes=5)
    async def auto_save(self):
        """Auto-save data every 5 minutes."""
        self.save_data()
    
    @auto_save.before_loop
    async def before_auto_save(self):
        """Wait until bot is ready before starting auto-save."""
        await self.bot.wait_until_ready()
    
    # ==================== DATA ACCESS METHODS ====================
    
    # Warnings
    def get_warns(self, user_id):
        """Get warnings for a user."""
        return self.data["warns"].get(str(user_id), [])
    
    def add_warn(self, user_id, warn_data):
        """Add a warning to a user."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["warns"]:
            self.data["warns"][user_id_str] = []
        self.data["warns"][user_id_str].append(warn_data)
        self.save_data()
    
    def clear_warns(self, user_id):
        """Clear all warnings for a user."""
        user_id_str = str(user_id)
        if user_id_str in self.data["warns"]:
            del self.data["warns"][user_id_str]
            self.save_data()
    
    # Reputation
    def get_reputation(self, user_id):
        """Get reputation for a user."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["reputation"]:
            self.data["reputation"][user_id_str] = {"rep": 0, "given": [], "received": []}
        return self.data["reputation"][user_id_str]
    
    def add_reputation(self, user_id, amount, from_user_id, reason):
        """Add reputation to a user."""
        user_id_str = str(user_id)
        rep_data = self.get_reputation(user_id)
        rep_data["rep"] += amount
        rep_data["received"].append({
            "from": str(from_user_id),
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.data["reputation"][user_id_str] = rep_data
        self.save_data()
    
    # Levels
    def get_level_data(self, user_id):
        """Get level data for a user."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["levels"]:
            self.data["levels"][user_id_str] = {"level": 1, "xp": 0, "messages": 0}
        return self.data["levels"][user_id_str]
    
    def add_xp(self, user_id, xp_amount):
        """Add XP to a user and level them up if needed."""
        user_id_str = str(user_id)
        level_data = self.get_level_data(user_id)
        level_data["xp"] += xp_amount
        level_data["messages"] += 1
        
        # Level up calculation (100 XP per level, increases by 50 per level)
        xp_needed = 100 + (level_data["level"] * 50)
        if level_data["xp"] >= xp_needed:
            level_data["level"] += 1
            level_data["xp"] = 0
            self.data["levels"][user_id_str] = level_data
            self.save_data()
            return True  # Leveled up
        
        self.data["levels"][user_id_str] = level_data
        return False  # No level up
    
    # Reminders
    def add_reminder(self, user_id, reminder, time, channel_id):
        """Add a reminder."""
        self.data["reminders"].append({
            "user_id": str(user_id),
            "reminder": reminder,
            "time": time,
            "channel_id": str(channel_id)
        })
        self.save_data()
    
    def get_reminders(self, user_id=None):
        """Get all reminders or reminders for a specific user."""
        if user_id:
            return [r for r in self.data["reminders"] if r["user_id"] == str(user_id)]
        return self.data["reminders"]
    
    def remove_reminder(self, index):
        """Remove a reminder by index."""
        if 0 <= index < len(self.data["reminders"]):
            del self.data["reminders"][index]
            self.save_data()
    
    # Guild Settings
    def get_guild_setting(self, guild_id, key, default=None):
        """Get a guild setting."""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.data["guild_settings"]:
            self.data["guild_settings"][guild_id_str] = {}
        return self.data["guild_settings"][guild_id_str].get(key, default)
    
    def set_guild_setting(self, guild_id, key, value):
        """Set a guild setting."""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.data["guild_settings"]:
            self.data["guild_settings"][guild_id_str] = {}
        self.data["guild_settings"][guild_id_str][key] = value
        self.save_data()
    
    # User Settings
    def get_user_setting(self, user_id, key, default=None):
        """Get a user setting."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["user_settings"]:
            self.data["user_settings"][user_id_str] = {}
        return self.data["user_settings"][user_id_str].get(key, default)
    
    def set_user_setting(self, user_id, key, value):
        """Set a user setting."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["user_settings"]:
            self.data["user_settings"][user_id_str] = {}
        self.data["user_settings"][user_id_str][key] = value
        self.save_data()
    
    # Achievements
    def add_achievement(self, user_id, achievement_id):
        """Add an achievement to a user."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["achievements"]:
            self.data["achievements"][user_id_str] = []
        if achievement_id not in self.data["achievements"][user_id_str]:
            self.data["achievements"][user_id_str].append(achievement_id)
            self.save_data()
            return True
        return False
    
    def get_achievements(self, user_id):
        """Get achievements for a user."""
        return self.data["achievements"].get(str(user_id), [])
    
    # Suggestions
    def add_suggestion(self, user_id, suggestion):
        """Add a suggestion."""
        self.data["suggestions"].append({
            "user_id": str(user_id),
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        })
        self.save_data()
    
    def get_suggestions(self):
        """Get all suggestions."""
        return self.data["suggestions"]
    
    # Trivia
    def update_trivia_score(self, user_id, correct):
        """Update trivia score."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["trivia_scores"]:
            self.data["trivia_scores"][user_id_str] = {"correct": 0, "total": 0}
        self.data["trivia_scores"][user_id_str]["total"] += 1
        if correct:
            self.data["trivia_scores"][user_id_str]["correct"] += 1
        self.save_data()
    
    def get_trivia_score(self, user_id):
        """Get trivia score for a user."""
        user_id_str = str(user_id)
        return self.data["trivia_scores"].get(user_id_str, {"correct": 0, "total": 0})
    
    # Consent/Privacy
    def set_consent(self, user_id, given):
        """Set user consent."""
        self.data["consent"][str(user_id)] = {
            "given": given,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.save_data()
    
    def get_consent(self, user_id):
        """Get user consent status."""
        return self.data["consent"].get(str(user_id), {"given": False, "timestamp": None})
    
    def accept_privacy(self, user_id):
        """Mark privacy policy as accepted."""
        self.data["privacy_accepted"][str(user_id)] = datetime.utcnow().isoformat()
        self.save_data()
    
    def accept_tos(self, user_id):
        """Mark ToS as accepted."""
        self.data["tos_accepted"][str(user_id)] = datetime.utcnow().isoformat()
        self.save_data()
    
    # Custom data for other cogs
    def set_custom_data(self, key, value):
        """Set custom data for other cogs."""
        self.data["custom_data"][key] = value
        self.save_data()
    
    def get_custom_data(self, key, default=None):
        """Get custom data for other cogs."""
        return self.data["custom_data"].get(key, default)
    
    # Commands
    @commands.command()
    @commands.is_owner()
    async def savedata(self, ctx):
        """Manually save all data (owner only)."""
        self.save_data()
        await ctx.send("✅ All data saved successfully!")
    
    @commands.command()
    @commands.is_owner()
    async def datastats(self, ctx):
        """View data statistics (owner only)."""
        embed = discord.Embed(title="📊 Data Statistics", color=discord.Color.blue())
        embed.add_field(name="Users with Warnings", value=len(self.data["warns"]), inline=True)
        embed.add_field(name="Users with Reputation", value=len(self.data["reputation"]), inline=True)
        embed.add_field(name="Users with Levels", value=len(self.data["levels"]), inline=True)
        embed.add_field(name="Active Reminders", value=len(self.data["reminders"]), inline=True)
        embed.add_field(name="Suggestions", value=len(self.data["suggestions"]), inline=True)
        embed.add_field(name="Guilds Configured", value=len(self.data["guild_settings"]), inline=True)
        embed.add_field(name="Consents Given", value=len(self.data["consent"]), inline=True)
        embed.add_field(name="Auto-Save", value="Every 5 minutes", inline=True)
        embed.set_footer(text=f"Data file: {self.data_file}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataManager(bot))
