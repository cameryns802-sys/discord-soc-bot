"""Knowledge Base: Consolidated command group"""
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class KBGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="kb", description="Knowledge base commands")
        self.cog = cog

    @app_commands.command(name="add", description="Add article to knowledge base")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def add(self, interaction: discord.Interaction, category: str, title: str, content: str):
        self.cog.article_counter += 1
        art_id = str(self.cog.article_counter)
        self.cog.articles[art_id] = {"id": art_id, "title": title, "content": content, "category": category.lower(), "created_by": interaction.user.id, "created_at": datetime.get_now_pst().isoformat(), "views": 0}
        if category.lower() not in self.cog.categories:
            self.cog.categories.append(category.lower())
        self.cog.save_data()
        await interaction.response.send_message(f"✅ Added article #{art_id}: {title}")

    @app_commands.command(name="search", description="Search knowledge base")
    async def search(self, interaction: discord.Interaction, query: str):
        results = [a for a in self.cog.articles.values() if query.lower() in a['title'].lower() or query.lower() in a['content'].lower()]
        if not results:
            await interaction.response.send_message(f"ℹ️ No results for: {query}", ephemeral=True)
            return
        embed = discord.Embed(title=f"🔍 Search Results: {query}", color=discord.Color.blue())
        for art in results[:10]:
            embed.add_field(name=f"#{art['id']} - {art['title']}", value=f"Category: {art['category']} | Views: {art['views']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="article", description="View article by ID")
    async def article(self, interaction: discord.Interaction, article_id: str):
        if article_id not in self.cog.articles:
            await interaction.response.send_message("❌ Article not found", ephemeral=True)
            return
        art = self.cog.articles[article_id]
        art['views'] += 1
        self.cog.save_data()
        embed = discord.Embed(title=f"📄 {art['title']}", description=art['content'][:1000], color=discord.Color.blue())
        embed.add_field(name="Category", value=art['category'], inline=True)
        embed.add_field(name="Views", value=art['views'], inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="category", description="List articles in category")
    async def category(self, interaction: discord.Interaction, category: str):
        arts = [a for a in self.cog.articles.values() if a['category'] == category.lower()]
        if not arts:
            await interaction.response.send_message(f"ℹ️ No articles in: {category}", ephemeral=True)
            return
        embed = discord.Embed(title=f"📚 Category: {category}", color=discord.Color.blue())
        for art in arts[:15]:
            embed.add_field(name=f"#{art['id']} - {art['title']}", value=f"Views: {art['views']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="categories", description="List all categories")
    async def categories(self, interaction: discord.Interaction):
        if not self.cog.categories:
            await interaction.response.send_message("ℹ️ No categories", ephemeral=True)
            return
        embed = discord.Embed(title="📚 KB Categories", color=discord.Color.blue())
        for cat in self.cog.categories:
            count = len([a for a in self.cog.articles.values() if a['category'] == cat])
            embed.add_field(name=cat.capitalize(), value=f"{count} articles", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="popular", description="View most popular articles")
    async def popular(self, interaction: discord.Interaction):
        sorted_arts = sorted(self.cog.articles.values(), key=lambda a: a['views'], reverse=True)
        embed = discord.Embed(title="🔥 Popular Articles", color=discord.Color.blue())
        for art in sorted_arts[:10]:
            embed.add_field(name=f"#{art['id']} - {art['title']}", value=f"Category: {art['category']} | Views: {art['views']}", inline=False)
        await interaction.response.send_message(embed=embed)

class KnowledgeBaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.articles = {}
        self.categories = []
        self.article_counter = 0
        self.data_file = "data/knowledge_base.json"
        self.load_data()
        self.kb_group = KBGroup(self)
        bot.tree.add_command(self.kb_group)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.articles = data.get('articles', {})
                    self.categories = data.get('categories', [])
                    self.article_counter = data.get('counter', 0)
            except: pass

    def save_data(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'articles': self.articles, 'categories': self.categories, 'counter': self.article_counter}, f, indent=2)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.kb_group.name)

async def setup(bot):
    await bot.add_cog(KnowledgeBaseCog(bot))
