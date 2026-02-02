"""
THREAT SCORER
Dynamic threat risk scoring based on signals, patterns, and system health.

Architecture:
- Calculates real-time threat scores (0-100)
- Factors: signal severity, confidence, frequency, system health
- Provides risk categorization (LOW/MEDIUM/HIGH/CRITICAL)
- Integrates with signal bus for continuous updates
- Offers trend tracking and recommendations
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from statistics import mean

from cogs.core.signal_bus import signal_bus, Signal, SignalType

class ThreatScorer(commands.Cog):
    """Dynamic threat risk scoring system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/threat_scores.json'
        self.threat_history = {}
        self.current_threats = {}
        self.load_threat_data()
        self.setup_signal_listeners()
    
    def load_threat_data(self):
        """Load threat scoring history"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.threat_history = data.get('history', {})
                    self.current_threats = data.get('current', {})
            except:
                self.threat_history = {}
                self.current_threats = {}
        else:
            self.threat_history = {}
            self.current_threats = {}
    
    def save_threat_data(self):
        """Save threat data to disk"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'history': self.threat_history,
                'current': self.current_threats
            }, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus"""
        signal_bus.subscribe('threat_scorer', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Update threat score based on signal"""
        threat_key = f"{signal.source}_{signal.signal_type}"
        
        threat_score = self.calculate_threat_score(signal)
        
        # Update current threat
        self.current_threats[threat_key] = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': signal.source,
            'signal_type': str(signal.signal_type),
            'severity': signal.severity,
            'confidence': signal.confidence,
            'threat_score': threat_score,
            'risk_level': self.get_risk_level(threat_score)
        }
        
        # Add to history
        if threat_key not in self.threat_history:
            self.threat_history[threat_key] = []
        
        self.threat_history[threat_key].append(self.current_threats[threat_key])
        
        # Keep last 100 entries per threat
        if len(self.threat_history[threat_key]) > 100:
            self.threat_history[threat_key] = self.threat_history[threat_key][-100:]
        
        # Emit escalation if score is critical
        if threat_score >= 85:
            await self.emit_critical_threat(signal, threat_score)
        
        self.save_threat_data()
    
    def calculate_threat_score(self, signal: Signal) -> float:
        """Calculate threat risk score (0-100)"""
        score = 0.0
        
        # Base on severity (25 points)
        severity_scores = {
            'CRITICAL': 25,
            'HIGH': 20,
            'MEDIUM': 10,
            'LOW': 5
        }
        score += severity_scores.get(signal.severity, 10)
        
        # Base on confidence (35 points)
        confidence_score = signal.confidence * 35
        score += confidence_score
        
        # Bonus for specific threat types (15 points)
        threat_bonuses = {
            SignalType.THREAT_DETECTED: 15,
            SignalType.UNAUTHORIZED_ACCESS: 20,
            SignalType.ESCALATION_REQUIRED: 10,
            SignalType.POLICY_VIOLATION: 5
        }
        score += threat_bonuses.get(signal.signal_type, 0)
        
        # Pattern analysis bonus (10 points)
        pattern_bonus = self.get_pattern_bonus(signal.source) * 10
        score += pattern_bonus
        
        # Anomaly bonus (15 points)
        if signal.signal_type == SignalType.ANOMALY_DETECTED:
            score += 15
        
        # Threat intel enrichment bonus (15 points)
        threat_intel_bonus = self.get_threat_intel_bonus(signal)
        score += threat_intel_bonus
        
        # Cap at 100
        return min(100.0, score)
    
    def get_threat_intel_bonus(self, signal: Signal) -> float:
        """Calculate bonus based on threat intelligence correlation"""
        # Check if signal is from threat intel hub
        if signal.source == 'threat_intel_hub':
            ioc_matches = signal.data.get('ioc_matches', 0)
            if ioc_matches >= 3:
                return 15.0  # Multiple IOC matches - highly suspicious
            elif ioc_matches >= 1:
                return 10.0  # At least one IOC match
        
        # Check if threat intel enrichment is present
        if signal.data.get('enrichment') == 'threat_intel_correlation':
            return 12.0
        
        return 0.0
    
    def get_pattern_bonus(self, source: str) -> float:
        """Calculate bonus based on repeated threats from same source"""
        threat_keys = [k for k in self.current_threats.keys() if k.startswith(source)]
        
        if not threat_keys:
            return 0.0
        
        # Count threats in last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_count = 0
        
        for key in threat_keys:
            threat = self.current_threats[key]
            ts = datetime.fromisoformat(threat['timestamp'])
            if ts > cutoff:
                recent_count += 1
        
        # Bonus increases with repeated threats
        if recent_count >= 5:
            return 1.0  # 100% bonus (10 points)
        elif recent_count >= 3:
            return 0.7  # 70% bonus
        elif recent_count >= 1:
            return 0.3  # 30% bonus
        
        return 0.0
    
    def get_risk_level(self, score: float) -> str:
        """Convert threat score to risk level"""
        if score >= 85:
            return 'CRITICAL'
        elif score >= 70:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    async def emit_critical_threat(self, signal: Signal, score: float):
        """Emit critical threat signal"""
        critical_signal = Signal(
            signal_type=SignalType.ESCALATION_REQUIRED,
            severity='CRITICAL',
            source='threat_scorer',
            data={
                'original_signal': str(signal.type),
                'threat_score': score,
                'risk_level': self.get_risk_level(score),
                'reason': 'High threat score detected',
                'confidence': 0.99
            }
        )
        
        await signal_bus.emit(critical_signal)
    
    def get_threat_summary(self, hours: int = 24) -> Dict:
        """Get summary of current threats"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        current = []
        for key, threat in self.current_threats.items():
            ts = datetime.fromisoformat(threat['timestamp'])
            if ts > cutoff:
                current.append(threat)
        
        # Categorize by risk level
        by_risk = {}
        for threat in current:
            risk = threat['risk_level']
            if risk not in by_risk:
                by_risk[risk] = []
            by_risk[risk].append(threat)
        
        # Get average score
        avg_score = mean([t['threat_score'] for t in current]) if current else 0.0
        max_score = max([t['threat_score'] for t in current]) if current else 0.0
        
        return {
            'period_hours': hours,
            'total_threats': len(current),
            'by_risk_level': by_risk,
            'avg_threat_score': avg_score,
            'max_threat_score': max_score,
            'critical_count': len(by_risk.get('CRITICAL', [])),
            'high_count': len(by_risk.get('HIGH', [])),
            'medium_count': len(by_risk.get('MEDIUM', []))
        }
    
    def get_threat_trend(self, system: str = None, hours: int = 24) -> List[Dict]:
        """Get threat trend for visualization"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        trend = []
        for key, history in self.threat_history.items():
            if system and not key.startswith(system):
                continue
            
            for threat in history:
                ts = datetime.fromisoformat(threat['timestamp'])
                if ts > cutoff:
                    trend.append({
                        'timestamp': threat['timestamp'],
                        'source': threat['source'],
                        'score': threat['threat_score'],
                        'risk_level': threat['risk_level']
                    })
        
        return sorted(trend, key=lambda x: x['timestamp'])
    
    @commands.command(name='threatsummary')
    async def threat_summary_cmd(self, ctx, hours: int = 24):
        """View current threat summary (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        summary = self.get_threat_summary(hours)
        
        embed = discord.Embed(
            title="🚨 Threat Risk Summary",
            description=f"Analysis of threats over last {hours} hours",
            color=discord.Color.red() if summary['critical_count'] > 0 else discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Total Threats",
            value=str(summary['total_threats']),
            inline=True
        )
        
        embed.add_field(
            name="Avg Threat Score",
            value=f"`{summary['avg_threat_score']:.1f}/100`",
            inline=True
        )
        
        embed.add_field(
            name="Max Threat Score",
            value=f"`{summary['max_threat_score']:.1f}/100`",
            inline=True
        )
        
        # Risk distribution
        risk_text = ""
        risk_text += f"🔴 Critical: {summary['critical_count']}\n"
        risk_text += f"🟠 High: {summary['high_count']}\n"
        risk_text += f"🟡 Medium: {summary['medium_count']}"
        
        embed.add_field(
            name="Risk Distribution",
            value=risk_text,
            inline=False
        )
        
        # Top threats
        all_threats = []
        for risks in summary['by_risk_level'].values():
            all_threats.extend(risks)
        
        if all_threats:
            top_threats = sorted(all_threats, key=lambda x: x['threat_score'], reverse=True)[:5]
            threats_text = ""
            for threat in top_threats:
                risk_emoji = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🔵'
                }.get(threat['risk_level'], '❓')
                
                threats_text += f"{risk_emoji} {threat['source']}: {threat['threat_score']:.0f}/100\n"
            
            embed.add_field(
                name="Top Threats",
                value=threats_text,
                inline=False
            )
        
        embed.set_footer(text="Scores are dynamically calculated based on signals and patterns")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='threattimeline')
    async def threat_timeline_cmd(self, ctx, system: str = None, hours: int = 24):
        """View threat score timeline (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        trend = self.get_threat_trend(system, hours)
        
        if not trend:
            await ctx.send("✅ No threats recorded in timeframe")
            return
        
        embed = discord.Embed(
            title="📈 Threat Score Timeline",
            description=f"Threat progression over last {hours} hours",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if system:
            embed.description += f"\nSystem: `{system}`"
        
        # Group by hour and show trend
        hourly_data = {}
        for threat in trend:
            ts = datetime.fromisoformat(threat['timestamp'])
            hour = ts.strftime('%Y-%m-%d %H:00')
            
            if hour not in hourly_data:
                hourly_data[hour] = []
            
            hourly_data[hour].append(threat['score'])
        
        timeline_text = ""
        for hour in sorted(hourly_data.keys())[-6:]:  # Last 6 hours
            scores = hourly_data[hour]
            avg_score = mean(scores)
            count = len(scores)
            
            # Create visual bar
            bar_length = int(avg_score / 10)
            bar = '█' * bar_length
            
            timeline_text += f"{hour}: {bar} {avg_score:.0f} ({count} signals)\n"
        
        embed.add_field(
            name="Hourly Trend",
            value=timeline_text,
            inline=False
        )
        
        # Statistics
        all_scores = [t['score'] for t in trend]
        embed.add_field(
            name="Statistics",
            value=f"Min: {min(all_scores):.0f}\n"
                  f"Avg: {mean(all_scores):.0f}\n"
                  f"Max: {max(all_scores):.0f}",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreatScorer(bot))
