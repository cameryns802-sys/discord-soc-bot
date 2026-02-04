"""
TIER-2 MEMORY: Conversation History Manager
Tracks and manages conversation history for context preservation
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class ConversationHistoryManager(commands.Cog):
    """Conversation history tracking and analysis"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/conversation_history.json'
        self.conversations = {}  # user_id -> list of messages
        self.load_history()
    
    def load_history(self):
        """Load conversation history"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.conversations = json.load(f)
                    total = sum(len(v) for v in self.conversations.values())
                    print(f"[ConversationHistory] ✅ Loaded {total} messages across {len(self.conversations)} conversations")
            except:
                self.conversations = {}
    
    def add_message(self, user_id: int, role: str, content: str, timestamp: str = None):
        """Add message to conversation history"""
        user_key = str(user_id)
        
        if user_key not in self.conversations:
            self.conversations[user_key] = []
        
        message = {
            'role': role,  # 'user', 'assistant', 'system'
            'content': content,
            'timestamp': timestamp or get_now_pst().isoformat(),
            'length': len(content)
        }
        
        self.conversations[user_key].append(message)
        
        # Keep last 500 messages per user
        if len(self.conversations[user_key]) > 500:
            self.conversations[user_key] = self.conversations[user_key][-500:]
        
        self._save_history()
    
    def get_conversation(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get conversation history for user"""
        user_key = str(user_id)
        
        if user_key not in self.conversations:
            return []
        
        return self.conversations[user_key][-limit:]
    
    def get_context_window(self, user_id: int, max_tokens: int = 2000) -> str:
        """Get conversation context within token limit"""
        messages = self.get_conversation(user_id, limit=100)
        context = ""
        token_count = 0
        
        for msg in reversed(messages):
            msg_tokens = len(msg['content'].split())
            
            if token_count + msg_tokens > max_tokens:
                break
            
            context = f"[{msg['role']}]: {msg['content']}\n" + context
            token_count += msg_tokens
        
        return context
    
    def analyze_conversation(self, user_id: int) -> Dict:
        """Analyze conversation patterns"""
        messages = self.get_conversation(user_id, limit=1000)
        
        if not messages:
            return {}
        
        total_messages = len(messages)
        user_messages = [m for m in messages if m['role'] == 'user']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        
        total_tokens = sum(len(m['content'].split()) for m in messages)
        avg_tokens = total_tokens / total_messages if total_messages > 0 else 0
        
        return {
            'total_messages': total_messages,
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_tokens': total_tokens,
            'avg_tokens_per_message': avg_tokens,
            'conversation_length_minutes': 0,  # Would calculate from timestamps
            'topics': []  # Would be analyzed from content
        }
    
    def _save_history(self):
        """Save conversation history"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.conversations, f, indent=2, default=str)
    
    @commands.command(name='conversationanalysis')
    async def conversation_analysis(self, ctx):
        """Analyze your conversation patterns"""
        analysis = self.analyze_conversation(ctx.author.id)
        
        if not analysis:
            await ctx.send("❌ No conversation history found")
            return
        
        embed = discord.Embed(
            title="📊 Conversation Analysis",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Messages", value=str(analysis['total_messages']), inline=True)
        embed.add_field(name="Your Messages", value=str(analysis['user_messages']), inline=True)
        embed.add_field(name="Bot Responses", value=str(analysis['assistant_messages']), inline=True)
        
        embed.add_field(name="Total Tokens", value=str(analysis['total_tokens']), inline=True)
        embed.add_field(name="Avg Tokens/Message", value=f"{analysis['avg_tokens_per_message']:.1f}", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConversationHistoryManager(bot))
