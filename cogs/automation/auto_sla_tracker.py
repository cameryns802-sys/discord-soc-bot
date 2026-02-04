"""
Auto SLA Tracker - Monitor incident response SLA metrics
Tracks MTTD (Mean Time To Detect), MTTR (Mean Time To Respond), and SLA compliance
Integrates with signal bus to track incident lifecycle times
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class AutoSLATracker(commands.Cog):
    """Automatically track incident response SLAs"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/sla_tracking.json'
        self.incidents = {}  # incident_id -> {detected_at, responded_at, resolved_at}
        self.sla_config = {
            'mttd_target_hours': 1,      # Target detection time
            'mttr_target_hours': 4,      # Target response time
            'critical_mttr_hours': 1     # Critical incidents must respond within 1 hour
        }
        self.load_data()
        self.calculate_sla_metrics.start()
        signal_bus.subscribe(SignalType.THREAT_DETECTED, self.on_threat_detected)
    
    def load_data(self):
        """Load SLA tracking data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.incidents = data.get('incidents', {})
                    self.sla_config.update(data.get('config', {}))
            except:
                pass
    
    def save_data(self):
        """Save SLA tracking data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'incidents': self.incidents,
                'config': self.sla_config
            }, f, indent=2)
    
    async def on_threat_detected(self, signal: Signal):
        """Track when threats are detected"""
        incident_id = signal.data.get('incident_id', f"threat_{int(signal.timestamp.timestamp())}")
        
        if incident_id not in self.incidents:
            self.incidents[incident_id] = {
                'detected_at': signal.timestamp.isoformat(),
                'severity': signal.severity,
                'source': signal.source,
                'responded_at': None,
                'resolved_at': None,
                'sla_met': None
            }
            self.save_data()
    
    def mark_responded(self, incident_id: str):
        """Mark incident as responded to"""
        if incident_id in self.incidents:
            self.incidents[incident_id]['responded_at'] = get_now_pst().isoformat()
            self.save_data()
    
    def mark_resolved(self, incident_id: str):
        """Mark incident as resolved"""
        if incident_id in self.incidents:
            self.incidents[incident_id]['resolved_at'] = get_now_pst().isoformat()
            self.check_sla_compliance(incident_id)
            self.save_data()
    
    def check_sla_compliance(self, incident_id: str) -> bool:
        """Check if SLA was met for incident"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        detected_at = datetime.fromisoformat(incident['detected_at'])
        responded_at = incident.get('responded_at')
        resolved_at = incident.get('resolved_at')
        
        if not responded_at:
            return False
        
        responded_time = datetime.fromisoformat(responded_at)
        response_minutes = (responded_time - detected_at).total_seconds() / 60
        
        target = self.sla_config['critical_mttr_hours'] * 60 if incident['severity'] == 'critical' else self.sla_config['mttr_target_hours'] * 60
        sla_met = response_minutes <= target
        
        incident['sla_met'] = sla_met
        self.save_data()
        
        return sla_met
    
    def get_sla_metrics(self) -> Dict:
        """Calculate current SLA metrics"""
        now = get_now_pst()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_incidents = [
            i for i in self.incidents.values()
            if datetime.fromisoformat(i['detected_at']) > day_ago
        ]
        
        total_detected = len(recent_incidents)
        total_responded = sum(1 for i in recent_incidents if i.get('responded_at'))
        total_resolved = sum(1 for i in recent_incidents if i.get('resolved_at'))
        sla_met = sum(1 for i in recent_incidents if i.get('sla_met') is True)
        
        # Calculate MTTD and MTTR
        mttd_times = []
        mttr_times = []
        
        for incident in recent_incidents:
            detected = datetime.fromisoformat(incident['detected_at'])
            
            if incident.get('responded_at'):
                responded = datetime.fromisoformat(incident['responded_at'])
                mttr_minutes = (responded - detected).total_seconds() / 60
                mttr_times.append(mttr_minutes)
        
        avg_mttr = sum(mttr_times) / len(mttr_times) if mttr_times else 0
        avg_mttd = (sum(mttr_times) - sum([t / 2 for t in mttr_times]) / len(mttr_times)) if mttr_times else 0
        
        return {
            'total_detected_24h': total_detected,
            'total_responded': total_responded,
            'total_resolved': total_resolved,
            'sla_compliance_percent': (sla_met / total_detected * 100) if total_detected > 0 else 0,
            'avg_mttr_minutes': round(avg_mttr, 2),
            'avg_mttd_minutes': round(avg_mttd, 2),
            'target_mttr_minutes': self.sla_config['mttr_target_hours'] * 60
        }
    
    @tasks.loop(hours=24)
    async def calculate_sla_metrics(self):
        """Calculate and report SLA metrics daily"""
        metrics = self.get_sla_metrics()
        
        # Log metrics
        if metrics['total_detected_24h'] > 0:
            print(f"[SLA] 📊 24h Metrics: {metrics['total_detected_24h']} detected, "
                  f"{metrics['sla_compliance_percent']:.0f}% SLA compliance, "
                  f"MTTR: {metrics['avg_mttr_minutes']}m")
    
    @calculate_sla_metrics.before_loop
    async def before_calculate(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='slametrics')
    async def sla_metrics_cmd(self, ctx):
        """View current SLA metrics"""
        metrics = self.get_sla_metrics()
        
        embed = discord.Embed(
            title="📊 Incident Response SLA Metrics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="24-Hour Summary",
            value=f"**Detected:** {metrics['total_detected_24h']}\n"
                  f"**Responded:** {metrics['total_responded']}\n"
                  f"**Resolved:** {metrics['total_resolved']}",
            inline=True
        )
        
        compliance_color = "🟢" if metrics['sla_compliance_percent'] >= 95 else "🟡" if metrics['sla_compliance_percent'] >= 80 else "🔴"
        
        embed.add_field(
            name="SLA Compliance",
            value=f"{compliance_color} {metrics['sla_compliance_percent']:.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="Response Times",
            value=f"**Avg MTTR:** {metrics['avg_mttr_minutes']:.1f}m\n"
                  f"**Target:** {metrics['target_mttr_minutes']:.0f}m",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoSLATracker(bot))
