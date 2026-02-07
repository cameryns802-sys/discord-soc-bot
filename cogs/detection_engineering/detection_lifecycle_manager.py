"""
DETECTION ENGINEERING LAYER - Detection Lifecycle Management

Manages:
- Detection rules (SIGMA format)
- Version control & testing
- Coverage analysis
- False positive tuning
- Quality metrics
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from cogs.core.pst_timezone import get_now_pst


class DetectionStatus(Enum):
    DRAFT = "draft"
    TESTING = "testing"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


class SigmaRule:
    """SIGMA detection rule"""
    
    def __init__(self, rule_id: str, title: str, detection_logic: Dict):
        self.rule_id = rule_id
        self.title = title
        self.detection_logic = detection_logic
        self.status = DetectionStatus.DRAFT
        self.version = 1
        self.created_at = get_now_pst()
        self.mitre_techniques = []
        self.false_positive_rate = 0.0
        self.detection_rate = 0.0
        self.test_cases = []
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'title': self.title,
            'detection_logic': self.detection_logic,
            'status': self.status.value,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'mitre_techniques': self.mitre_techniques,
            'false_positive_rate': self.false_positive_rate,
            'detection_rate': self.detection_rate
        }


class DetectionLifecycleManager(commands.Cog):
    """Manage detection rules and their lifecycle"""
    
    def __init__(self, bot):
        self.bot = bot
        self.rules_file = 'data/detection_rules.json'
        self.rules: Dict[str, SigmaRule] = {}
        self.load_rules()
    
    def load_rules(self):
        """Load detection rules"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    for rule_data in data.get('rules', []):
                        rule = SigmaRule(
                            rule_data['rule_id'],
                            rule_data['title'],
                            rule_data['detection_logic']
                        )
                        self.rules[rule.rule_id] = rule
            except:
                pass
    
    def save_rules(self):
        """Save detection rules"""
        os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
        with open(self.rules_file, 'w') as f:
            json.dump({
                'rules': [r.to_dict() for r in self.rules.values()]
            }, f, indent=2)
    
    def create_rule(self, rule_id: str, title: str, detection_logic: Dict) -> SigmaRule:
        """Create new detection rule"""
        rule = SigmaRule(rule_id, title, detection_logic)
        self.rules[rule_id] = rule
        self.save_rules()
        return rule
    
    def get_production_rules(self) -> List[SigmaRule]:
        """Get all production rules"""
        return [r for r in self.rules.values() if r.status == DetectionStatus.PRODUCTION]
    
    def promote_to_production(self, rule_id: str) -> bool:
        """Promote rule to production"""
        if rule_id in self.rules:
            self.rules[rule_id].status = DetectionStatus.PRODUCTION
            self.save_rules()
            return True
        return False
    
    @commands.command(name='detectionrules')
    @commands.is_owner()
    async def list_rules(self, ctx):
        """List detection rules"""
        embed = discord.Embed(
            title="🔍 Detection Rules",
            description=f"Total: {len(self.rules)} rules",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        by_status = {}
        for rule in self.rules.values():
            status = rule.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        for status, count in by_status.items():
            embed.add_field(name=f"{status.title()}", value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DetectionLifecycleManager(bot))
