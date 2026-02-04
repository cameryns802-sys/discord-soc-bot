"""
Hot-Reload Plugin Manager: Add/remove/update cogs without restarting bot.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import importlib
from cogs.core.pst_timezone import get_now_pst

class HotReloadPluginManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/plugin_manager.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "installed_plugins": {},
            "plugin_marketplace": {},
            "trusted_repos": [],
            "plugin_versions": {},
            "load_history": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_owner(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="hot_load_cog")
    async def hot_load_cog(self, ctx, cog_path: str):
        """Hot-load a cog without restarting bot."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        try:
            await self.bot.load_extension(cog_path)
            
            self.data["installed_plugins"][cog_path] = {
                "status": "loaded",
                "loaded_at": get_now_pst().isoformat(),
                "loaded_by": str(ctx.author.id)
            }
            
            self.data["load_history"].append({
                "action": "load",
                "cog": cog_path,
                "timestamp": get_now_pst().isoformat()
            })
            
            self.save_data(self.data)
            
            embed = discord.Embed(
                title="✅ Cog Loaded",
                description=f"Cog: {cog_path}",
                color=discord.Color.green()
            )
            embed.add_field(name="Status", value="Loaded", inline=True)
            embed.add_field(name="Time", value=get_now_pst().strftime("%H:%M:%S"), inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Failed to Load Cog",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="hot_unload_cog")
    async def hot_unload_cog(self, ctx, cog_path: str):
        """Hot-unload a cog without restarting bot."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        try:
            await self.bot.unload_extension(cog_path)
            
            if cog_path in self.data["installed_plugins"]:
                self.data["installed_plugins"][cog_path]["status"] = "unloaded"
            
            self.data["load_history"].append({
                "action": "unload",
                "cog": cog_path,
                "timestamp": get_now_pst().isoformat()
            })
            
            self.save_data(self.data)
            
            embed = discord.Embed(
                title="✅ Cog Unloaded",
                description=f"Cog: {cog_path}",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Failed to Unload Cog",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="hot_reload_cog")
    async def hot_reload_cog(self, ctx, cog_path: str):
        """Hot-reload a cog (unload and reload)."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        try:
            await self.bot.reload_extension(cog_path)
            
            self.data["installed_plugins"][cog_path] = {
                "status": "reloaded",
                "last_reload": get_now_pst().isoformat(),
                "reloaded_by": str(ctx.author.id)
            }
            
            self.data["load_history"].append({
                "action": "reload",
                "cog": cog_path,
                "timestamp": get_now_pst().isoformat()
            })
            
            self.save_data(self.data)
            
            embed = discord.Embed(
                title="✅ Cog Reloaded",
                description=f"Cog: {cog_path}",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Failed to Reload Cog",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="list_loaded_plugins")
    async def list_loaded_plugins(self, ctx):
        """List all currently loaded plugins."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        loaded = [name for name, info in self.data["installed_plugins"].items() if info.get("status") == "loaded"]
        
        embed = discord.Embed(
            title="📦 Loaded Plugins",
            description=f"Total: {len(loaded)}",
            color=discord.Color.blue()
        )
        
        if loaded:
            for plugin in loaded[:15]:
                embed.add_field(name=plugin, value="✅ Active", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="plugin_load_history")
    async def plugin_load_history(self, ctx):
        """View plugin load/unload history."""
        if not await self.is_owner(ctx):
            await ctx.send("❌ Owner only.")
            return
        
        history = self.data["load_history"][-10:]
        
        embed = discord.Embed(
            title="📜 Plugin Load History",
            description=f"Recent Actions: {len(history)}",
            color=discord.Color.blue()
        )
        
        for entry in reversed(history):
            embed.add_field(
                name=f"{entry['action'].upper()}: {entry['cog']}",
                value=entry['timestamp'][:19],
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="plugin_marketplace")
    async def plugin_marketplace(self, ctx):
        """Browse the plugin marketplace."""
        marketplace = self.data["plugin_marketplace"]
        
        embed = discord.Embed(
            title="🏪 Plugin Marketplace",
            description="Available community plugins",
            color=discord.Color.blue()
        )
        
        if marketplace:
            for name, info in list(marketplace.items())[:5]:
                embed.add_field(
                    name=f"• {name}",
                    value=info.get("description", "No description"),
                    inline=False
                )
        else:
            embed.add_field(name="Status", value="No plugins available yet", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HotReloadPluginManagerCog(bot))
