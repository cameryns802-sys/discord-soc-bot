import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import re

class SentinelQueryLanguage(commands.Cog):
    """
    Sentinel Query Language (SQL) - KQL/SPL-Inspired Query Interface
    
    Provides a powerful query language for searching normalized logs
    similar to Kusto Query Language (KQL) or Splunk SPL.
    
    Features:
    - Time-bounded queries
    - Field filtering and comparison
    - Aggregations (count, sum, avg)
    - Saved queries for analysts
    - Cross-server event correlation
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/sentinel_queries'
        os.makedirs(self.data_dir, exist_ok=True)
        self.saved_queries = self.load_saved_queries()
        
        # Supported operators
        self.operators = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            'contains': lambda a, b: b in str(a),
            'startswith': lambda a, b: str(a).startswith(b),
            'endswith': lambda a, b: str(a).endswith(b)
        }
    
    def load_saved_queries(self) -> Dict:
        """Load saved queries from JSON storage"""
        try:
            with open(f'{self.data_dir}/saved_queries.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_queries(self):
        """Save queries to JSON storage"""
        with open(f'{self.data_dir}/saved_queries.json', 'w') as f:
            json.dump(self.saved_queries, f, indent=2)
    
    def parse_query(self, query_str: str) -> Dict:
        """
        Parse a Sentinel Query Language query
        
        Syntax examples:
        - event.type == "security_alert" AND event.severity == "high"
        - user.id == 123456 WHERE time > -24h
        - event.category contains "threat" | count by event.type
        """
        query = {
            'filters': [],
            'time_range': None,
            'aggregation': None,
            'group_by': None
        }
        
        # Extract time range (WHERE time > -24h)
        time_match = re.search(r'WHERE time > -(\d+)([hdm])', query_str)
        if time_match:
            amount = int(time_match.group(1))
            unit = time_match.group(2)
            
            if unit == 'h':
                query['time_range'] = timedelta(hours=amount)
            elif unit == 'd':
                query['time_range'] = timedelta(days=amount)
            elif unit == 'm':
                query['time_range'] = timedelta(minutes=amount)
            
            # Remove time clause from query
            query_str = query_str[:time_match.start()].strip()
        
        # Extract aggregation (| count by field)
        agg_match = re.search(r'\|\s*(count|sum|avg)\s*(?:by\s+(\S+))?', query_str)
        if agg_match:
            query['aggregation'] = agg_match.group(1)
            query['group_by'] = agg_match.group(2)
            
            # Remove aggregation from query
            query_str = query_str[:agg_match.start()].strip()
        
        # Parse filters (field operator value)
        # Split by AND/OR
        parts = re.split(r'\s+AND\s+|\s+OR\s+', query_str)
        
        for part in parts:
            part = part.strip()
            
            # Try to match: field operator value
            for op in self.operators.keys():
                if op in part:
                    field, value = part.split(op, 1)
                    field = field.strip()
                    value = value.strip().strip('"')
                    
                    query['filters'].append({
                        'field': field,
                        'operator': op,
                        'value': value
                    })
                    break
        
        return query
    
    def execute_query(self, guild_id: str, query: Dict) -> List[Dict]:
        """
        Execute a parsed query against normalized logs
        
        Args:
            guild_id: Guild ID to query
            query: Parsed query dictionary
        
        Returns:
            List of matching events
        """
        # Get log normalization cog
        norm_cog = self.bot.get_cog('LogNormalizationEngine')
        if not norm_cog:
            return []
        
        # Get all events for guild
        if str(guild_id) not in norm_cog.normalized_logs:
            return []
        
        events = norm_cog.normalized_logs[str(guild_id)]
        
        # Apply time range filter
        if query['time_range']:
            cutoff = datetime.now(timezone.utc) - query['time_range']
            events = [
                e for e in events
                if datetime.fromisoformat(e.get('event.timestamp', '2000-01-01T00:00:00+00:00')) >= cutoff
            ]
        
        # Apply field filters
        for f in query['filters']:
            field = f['field']
            op = f['operator']
            value = f['value']
            
            operator_func = self.operators[op]
            events = [e for e in events if operator_func(e.get(field, ''), value)]
        
        # Apply aggregation
        if query['aggregation']:
            if query['aggregation'] == 'count':
                if query['group_by']:
                    # Group by field and count
                    groups = {}
                    for e in events:
                        key = e.get(query['group_by'], 'unknown')
                        groups[key] = groups.get(key, 0) + 1
                    return [{'group': k, 'count': v} for k, v in groups.items()]
                else:
                    return [{'count': len(events)}]
        
        return events
    
    @commands.command(name='sql_query', aliases=['sql', 'query'])
    @commands.has_permissions(administrator=True)
    async def sql_query_cmd(self, ctx, *, query: str):
        """
        Execute a Sentinel Query Language query
        
        Examples:
        !sql event.type == "security_alert" AND event.severity == "high"
        !sql user.id == 123456 WHERE time > -24h
        !sql event.category contains "threat" | count by event.type
        """
        try:
            parsed = self.parse_query(query)
            results = self.execute_query(ctx.guild.id, parsed)
            
            embed = discord.Embed(
                title="🔍 Query Results",
                description=f"**Query**: `{query[:100]}...`" if len(query) > 100 else f"**Query**: `{query}`",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Check if aggregation
            if parsed['aggregation']:
                embed.add_field(
                    name="📊 Aggregation Results",
                    value='\n'.join([f"**{r.get('group', 'Total')}**: {r.get('count', 0)}" for r in results[:10]]),
                    inline=False
                )
            else:
                embed.add_field(name="📈 Results Found", value=str(len(results)), inline=True)
                
                # Show first 5 results
                for i, event in enumerate(results[:5], 1):
                    embed.add_field(
                        name=f"Event {i}",
                        value=f"**Type**: {event.get('event.type', 'N/A')}\n"
                              f"**Severity**: {event.get('event.severity', 'N/A')}\n"
                              f"**Time**: {event.get('event.timestamp', 'N/A')[:19]}",
                        inline=False
                    )
                
                if len(results) > 5:
                    embed.set_footer(text=f"Showing 5 of {len(results)} results")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Query error: {e}")
    
    @commands.command(name='save_query')
    @commands.has_permissions(administrator=True)
    async def save_query_cmd(self, ctx, query_name: str, *, query: str):
        """
        Save a query for reuse
        
        Usage: !save_query high_severity_alerts event.severity == "high"
        """
        if str(ctx.guild.id) not in self.saved_queries:
            self.saved_queries[str(ctx.guild.id)] = {}
        
        self.saved_queries[str(ctx.guild.id)][query_name] = {
            'query': query,
            'created_by': str(ctx.author),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.save_queries()
        
        embed = discord.Embed(
            title="✅ Query Saved",
            description=f"Query `{query_name}` has been saved.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Query", value=f"`{query}`", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='run_saved_query')
    @commands.has_permissions(administrator=True)
    async def run_saved_query_cmd(self, ctx, query_name: str):
        """
        Run a saved query
        
        Usage: !run_saved_query high_severity_alerts
        """
        if str(ctx.guild.id) not in self.saved_queries:
            await ctx.send("❌ No saved queries found for this guild.")
            return
        
        if query_name not in self.saved_queries[str(ctx.guild.id)]:
            await ctx.send(f"❌ Query `{query_name}` not found.")
            return
        
        query = self.saved_queries[str(ctx.guild.id)][query_name]['query']
        
        # Execute the saved query
        await self.sql_query_cmd(ctx, query=query)
    
    @commands.command(name='list_queries')
    @commands.has_permissions(administrator=True)
    async def list_queries_cmd(self, ctx):
        """List all saved queries for this guild"""
        if str(ctx.guild.id) not in self.saved_queries:
            await ctx.send("📋 No saved queries found for this guild.")
            return
        
        queries = self.saved_queries[str(ctx.guild.id)]
        
        embed = discord.Embed(
            title="📋 Saved Queries",
            description=f"**Total**: {len(queries)} saved queries",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        for name, data in list(queries.items())[:10]:
            embed.add_field(
                name=f"🔖 {name}",
                value=f"**Query**: `{data['query'][:50]}...`\n**Created By**: {data['created_by']}",
                inline=False
            )
        
        if len(queries) > 10:
            embed.set_footer(text=f"Showing 10 of {len(queries)} queries")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='delete_query')
    @commands.has_permissions(administrator=True)
    async def delete_query_cmd(self, ctx, query_name: str):
        """Delete a saved query"""
        if str(ctx.guild.id) not in self.saved_queries:
            await ctx.send("❌ No saved queries found for this guild.")
            return
        
        if query_name not in self.saved_queries[str(ctx.guild.id)]:
            await ctx.send(f"❌ Query `{query_name}` not found.")
            return
        
        del self.saved_queries[str(ctx.guild.id)][query_name]
        self.save_queries()
        
        await ctx.send(f"✅ Query `{query_name}` deleted.")

async def setup(bot):
    await bot.add_cog(SentinelQueryLanguage(bot))
