"""
INVESTIGATION ASSISTANT - Help analysts investigate threats

Provides:
- Investigation workflow
- Auto case summarization
- Evidence recommendations
- Hypothesis tracking
"""

import discord
from discord.ext import commands
from typing import Dict, List
import json
import os

from cogs.core.pst_timezone import get_now_pst


class InvestigationAssistant(commands.Cog):
    """Assist analysts during investigations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cases_file = 'data/investigation_cases.json'
        self.cases: Dict = {}
        self.load_cases()
    
    def load_cases(self):
        """Load investigation cases"""
        if os.path.exists(self.cases_file):
            try:
                with open(self.cases_file, 'r') as f:
                    self.cases = json.load(f)
            except:
                pass
    
    def create_investigation(self, event_id: str, title: str) -> Dict:
        """Create new investigation case"""
        case = {
            'case_id': f"CASE-{len(self.cases) + 1}",
            'event_id': event_id,
            'title': title,
            'created_at': get_now_pst().isoformat(),
            'evidence': [],
            'hypotheses': [],
            'timeline': [],
            'status': 'open'
        }
        
        self.cases[case['case_id']] = case
        self._save_cases()
        return case
    
    def add_evidence(self, case_id: str, evidence: Dict) -> bool:
        """Add evidence to case"""
        if case_id in self.cases:
            self.cases[case_id]['evidence'].append(evidence)
            self._save_cases()
            return True
        return False
    
    def add_hypothesis(self, case_id: str, hypothesis: str, confidence: float) -> bool:
        """Add hypothesis to case"""
        if case_id in self.cases:
            self.cases[case_id]['hypotheses'].append({
                'hypothesis': hypothesis,
                'confidence': confidence,
                'added_at': get_now_pst().isoformat()
            })
            self._save_cases()
            return True
        return False
    
    def _save_cases(self):
        """Save cases to disk"""
        os.makedirs(os.path.dirname(self.cases_file), exist_ok=True)
        with open(self.cases_file, 'w') as f:
            json.dump(self.cases, f, indent=2)
    
    @commands.command(name='investigation')
    @commands.is_owner()
    async def list_investigations(self, ctx):
        """List active investigations"""
        embed = discord.Embed(
            title="🔎 Active Investigations",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        open_cases = [c for c in self.cases.values() if c['status'] == 'open']
        embed.add_field(name="Open Cases", value=str(len(open_cases)), inline=True)
        embed.add_field(name="Total Cases", value=str(len(self.cases)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InvestigationAssistant(bot))
