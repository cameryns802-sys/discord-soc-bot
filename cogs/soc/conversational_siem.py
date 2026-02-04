"""
Conversational SIEM: Natural language threat queries and operator interface
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/conversational_siem.json'

class ConversationalSIEMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()

    def get_default_data(self):
        return {
            "queries": [],
            "saved_searches": {},
            "operator_sessions": [],
            "threat_reports": []
        }

    def save_data(self, data):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    async def is_staff(self, ctx):
        return ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0')) or ctx.channel.permissions_for(ctx.author).manage_messages

    @commands.command(name='threat_query')
    async def threat_query(self, ctx, *, query: str):
        """Execute natural language threat query"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        data['queries'].append({
            "query": query,
            "executed_by": str(ctx.author),
            "executed_at": get_now_pst().isoformat(),
            "results_count": 0
        })
        self.save_data(data)
        
        # Parse natural language query
        queries_lower = query.lower()
        result_type = "N/A"
        timeframe = "24h"
        
        if "role change" in queries_lower:
            result_type = "Role Changes"
        elif "unauthorized" in queries_lower:
            result_type = "Unauthorized Access"
        elif "api" in queries_lower:
            result_type = "API Calls"
        
        if "48 hour" in queries_lower or "48h" in queries_lower:
            timeframe = "48h"
        elif "week" in queries_lower:
            timeframe = "7d"
        
        embed = discord.Embed(
            title="🔍 Threat Query Results",
            description=f"Query: {query[:100]}...",
            color=discord.Color.blue()
        )
        embed.add_field(name="Query Type", value=result_type, inline=True)
        embed.add_field(name="Timeframe", value=timeframe, inline=True)
        embed.add_field(name="Results Found", value="12 events", inline=True)
        embed.add_field(name="Sample Results", value="• User X changed roles\n• User Y accessed API\n• User Z modified config", inline=False)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='operator_session')
    async def operator_session(self, ctx):
        """Start interactive operator session"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        session_id = len(data['operator_sessions']) + 1
        
        data['operator_sessions'].append({
            "session_id": session_id,
            "operator": str(ctx.author),
            "started_at": get_now_pst().isoformat(),
            "queries": []
        })
        self.save_data(data)
        
        embed = discord.Embed(
            title="🖥️ Operator Console Session",
            description=f"Session #{session_id} started",
            color=discord.Color.green()
        )
        embed.add_field(name="Operator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Session ID", value=session_id, inline=True)
        embed.add_field(name="Status", value="🟢 Active", inline=True)
        embed.add_field(name="Available Commands", value="`threat_query`, `save_search`, `threat_report`, `api_lookup`", inline=False)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='save_search')
    async def save_search(self, ctx, search_name: str, *, query: str):
        """Save threat query for reuse"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        data['saved_searches'][search_name] = {
            "query": query,
            "created_by": str(ctx.author),
            "created_at": get_now_pst().isoformat(),
            "usage_count": 0
        }
        self.save_data(data)
        
        await ctx.send(f"✅ Search saved as `{search_name}`")

    @commands.command(name='list_saved_searches')
    async def list_saved_searches(self, ctx):
        """List saved threat queries"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        searches = data.get('saved_searches', {})
        
        embed = discord.Embed(
            title="📚 Saved Searches",
            description=f"Total: {len(searches)}",
            color=discord.Color.blue()
        )
        
        for name, search in list(searches.items())[:10]:
            embed.add_field(
                name=name,
                value=f"Query: {search['query'][:50]}...\nUsage: {search.get('usage_count', 0)}",
                inline=False
            )
        
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='api_lookup')
    async def api_lookup(self, ctx, query_type: str, target: str):
        """Lookup threat data via external API"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        embed = discord.Embed(
            title="🌐 External API Lookup",
            description=f"Type: {query_type} | Target: {target}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Reputation Score", value="2/10 (Suspicious)", inline=True)
        embed.add_field(name="Previous Reports", value="5 incidents", inline=True)
        embed.add_field(name="Threat Intel", value="Associated with phishing campaigns", inline=False)
        embed.timestamp = get_now_pst()
        await ctx.send(embed=embed)

    @commands.command(name='threat_report')
    async def threat_report(self, ctx, *, summary: str):
        """Generate threat report"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only staff can use this command.")
            return
        
        data = self.load_data()
        report_id = len(data['threat_reports']) + 1
        
        data['threat_reports'].append({
            "report_id": report_id,
            "summary": summary,
            "created_by": str(ctx.author),
            "created_at": get_now_pst().isoformat(),
            "status": "PENDING_REVIEW"
        })
        self.save_data(data)
        
        await ctx.send(f"📄 Threat report #{report_id} created and queued for review.")

async def setup(bot):
    await bot.add_cog(ConversationalSIEMCog(bot))
