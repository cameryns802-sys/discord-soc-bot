"""
ML ANOMALY DETECTOR
Machine learning-based behavioral anomaly detection for improved threat identification.

Architecture:
- Monitors behavioral patterns across systems
- Detects deviations from baseline
- Uses simple statistical models (mean/std dev)
- Integrates with signal bus
- Provides anomaly scores and recommendations
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from statistics import mean, stdev
import math

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class MLAnomalyDetector(commands.Cog):
    """Machine learning-based anomaly detection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/anomaly_detection.json'
        self.baselines = {}
        self.anomalies = []
        self.load_baselines()
        self.setup_signal_listeners()
    
    def load_baselines(self):
        """Load baseline behavioral data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.baselines = data.get('baselines', {})
                    self.anomalies = data.get('anomalies', [])
            except:
                self.baselines = {}
                self.anomalies = []
        else:
            self.baselines = {}
            self.anomalies = []
    
    def save_baselines(self):
        """Save baseline data to disk"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'baselines': self.baselines,
                'anomalies': self.anomalies
            }, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus for all signals"""
        signal_bus.subscribe('ml_anomaly_detector', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Analyze incoming signals for anomalies"""
        system = signal.source
        
        # Update baselines
        if system not in self.baselines:
            self.baselines[system] = {
                'signal_count': 0,
                'confidence_scores': [],
                'severity_levels': [],
                'last_signals': []
            }
        
        baseline = self.baselines[system]
        
        # Add to historical data
        baseline['signal_count'] += 1
        baseline['confidence_scores'].append(signal.confidence)
        baseline['last_signals'].append({
            'timestamp': get_now_pst().isoformat(),
            'type': str(signal.signal_type),
            'confidence': signal.confidence,
            'severity': signal.severity
        })
        
        # Keep only last 100 signals
        if len(baseline['last_signals']) > 100:
            baseline['last_signals'] = baseline['last_signals'][-100:]
        if len(baseline['confidence_scores']) > 100:
            baseline['confidence_scores'] = baseline['confidence_scores'][-100:]
        
        # Detect anomalies
        anomaly_score = self.detect_anomaly(system, signal)
        
        if anomaly_score > 0.7:  # Anomaly threshold
            await self.record_anomaly(system, signal, anomaly_score)
            await self.emit_anomaly_signal(system, signal, anomaly_score)
        
        self.save_baselines()
    
    def detect_anomaly(self, system: str, signal: Signal) -> float:
        """Detect if a signal is anomalous using statistical methods"""
        baseline = self.baselines[system]
        
        # Need at least 5 samples for meaningful statistics
        if len(baseline['confidence_scores']) < 5:
            return 0.0  # Not enough data
        
        scores = baseline['confidence_scores']
        
        try:
            avg_confidence = mean(scores)
            std_confidence = stdev(scores) if len(scores) > 1 else 0.0
        except:
            return 0.0
        
        # Z-score: how many standard deviations from mean
        if std_confidence == 0:
            z_score = 0
        else:
            z_score = abs((signal.confidence - avg_confidence) / std_confidence)
        
        # Normalize z-score to 0-1 range
        anomaly_score = min(1.0, z_score / 3.0)  # 3 sigma = very unusual
        
        # Boost score if confidence is very low or very high
        if signal.confidence < 0.4:
            anomaly_score = max(anomaly_score, 0.6)
        elif signal.confidence > 0.98:
            anomaly_score = max(anomaly_score, 0.5)
        
        # Boost score if signal type is unusual
        signal_types = [s['type'] for s in baseline['last_signals']]
        if str(signal.signal_type) not in signal_types:
            anomaly_score = max(anomaly_score, 0.4)
        
        return anomaly_score
    
    async def record_anomaly(self, system: str, signal: Signal, score: float):
        """Record detected anomaly"""
        anomaly = {
            'timestamp': get_now_pst().isoformat(),
            'system': system,
            'signal_type': str(signal.signal_type),
            'confidence': signal.confidence,
            'severity': signal.severity,
            'anomaly_score': score,
            'description': self._generate_description(system, signal, score)
        }
        
        self.anomalies.append(anomaly)
        # Keep last 500 anomalies
        if len(self.anomalies) > 500:
            self.anomalies = self.anomalies[-500:]
        
        self.save_baselines()
    
    def _generate_description(self, system: str, signal: Signal, score: float) -> str:
        """Generate human-readable anomaly description"""
        baseline = self.baselines[system]
        
        if len(baseline['confidence_scores']) < 5:
            return "Insufficient data for analysis"
        
        try:
            avg_conf = mean(baseline['confidence_scores'])
        except:
            avg_conf = 0.5
        
        if signal.confidence < avg_conf - 0.2:
            return f"Unusually low confidence ({signal.confidence:.2%} vs avg {avg_conf:.2%})"
        elif signal.confidence > avg_conf + 0.2:
            return f"Unusually high confidence ({signal.confidence:.2%} vs avg {avg_conf:.2%})"
        else:
            return f"Anomalous signal pattern detected (score: {score:.2f})"
    
    async def emit_anomaly_signal(self, system: str, signal: Signal, score: float):
        """Emit anomaly detection signal"""
        anomaly_signal = Signal(
            signal_type=SignalType.ANOMALY_DETECTED,
            severity='HIGH' if score > 0.85 else 'MEDIUM',
            source='ml_anomaly_detector',
            data={
                'system': system,
                'original_signal_type': str(signal.type),
                'original_confidence': signal.confidence,
                'anomaly_score': score,
                'detection_method': 'statistical_zscore',
                'confidence': min(0.99, 0.7 + score * 0.3)  # 0.7-0.99 range
            }
        )
        
        await signal_bus.emit(anomaly_signal)
    
    def get_anomaly_report(self, hours: int = 24, system: str = None) -> Dict:
        """Generate anomaly detection report"""
        cutoff = get_now_pst() - timedelta(hours=hours)
        
        recent = [
            a for a in self.anomalies
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]
        
        if system:
            recent = [a for a in recent if a['system'] == system]
        
        # Group by system
        by_system = {}
        for anomaly in recent:
            sys = anomaly['system']
            if sys not in by_system:
                by_system[sys] = {
                    'count': 0,
                    'avg_score': 0.0,
                    'max_score': 0.0,
                    'anomalies': []
                }
            
            by_system[sys]['count'] += 1
            by_system[sys]['max_score'] = max(by_system[sys]['max_score'], anomaly['anomaly_score'])
            by_system[sys]['anomalies'].append(anomaly)
        
        # Calculate average scores
        for sys in by_system:
            scores = [a['anomaly_score'] for a in by_system[sys]['anomalies']]
            by_system[sys]['avg_score'] = mean(scores) if scores else 0.0
        
        return {
            'period_hours': hours,
            'total_anomalies': len(recent),
            'by_system': by_system,
            'high_risk_systems': [
                sys for sys, data in by_system.items()
                if data['max_score'] > 0.85
            ]
        }
    
    def get_system_baseline(self, system: str) -> Dict:
        """Get baseline statistics for a system"""
        if system not in self.baselines:
            return {'status': 'insufficient_data'}
        
        baseline = self.baselines[system]
        scores = baseline['confidence_scores']
        
        if len(scores) < 5:
            return {
                'status': 'insufficient_data',
                'sample_count': len(scores),
                'needed': 5
            }
        
        try:
            avg = mean(scores)
            std = stdev(scores)
        except:
            return {'status': 'error'}
        
        return {
            'status': 'valid',
            'sample_count': len(scores),
            'avg_confidence': avg,
            'std_dev': std,
            'min_confidence': min(scores),
            'max_confidence': max(scores),
            'recent_signals': baseline['last_signals'][-10:]
        }
    
    @commands.command(name='anomalyreport')
    async def anomaly_report_cmd(self, ctx, hours: int = 24, system: str = None):
        """View anomaly detection report (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        report = self.get_anomaly_report(hours, system)
        
        if report['total_anomalies'] == 0:
            await ctx.send(f"✅ No anomalies detected in the last {hours} hours")
            return
        
        embed = discord.Embed(
            title="🔍 Anomaly Detection Report",
            description=f"{report['total_anomalies']} anomalies detected",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Period",
            value=f"Last {hours} hours",
            inline=True
        )
        
        embed.add_field(
            name="Total Anomalies",
            value=str(report['total_anomalies']),
            inline=True
        )
        
        # High-risk systems
        if report['high_risk_systems']:
            embed.add_field(
                name="⚠️ High-Risk Systems",
                value="\n".join([f"`{s}`" for s in report['high_risk_systems']]),
                inline=False
            )
        
        # By system breakdown
        for system, data in sorted(report['by_system'].items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            field_value = f"Count: {data['count']}\n"
            field_value += f"Avg Score: {data['avg_score']:.2f}\n"
            field_value += f"Max Score: {data['max_score']:.2f}"
            
            embed.add_field(
                name=f"System: {system}",
                value=field_value,
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='baselineinfo')
    async def baseline_info_cmd(self, ctx, system: str):
        """View baseline statistics for a system (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        baseline = self.get_system_baseline(system)
        
        if baseline['status'] == 'insufficient_data':
            await ctx.send(
                f"❌ Insufficient data for {system}. "
                f"Need {baseline.get('needed', 5)} samples, have {baseline.get('sample_count', 0)}"
            )
            return
        
        embed = discord.Embed(
            title=f"📊 Baseline Statistics: {system}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Sample Count",
            value=str(baseline['sample_count']),
            inline=True
        )
        
        embed.add_field(
            name="Avg Confidence",
            value=f"`{baseline['avg_confidence']:.2%}`",
            inline=True
        )
        
        embed.add_field(
            name="Std Dev",
            value=f"`{baseline['std_dev']:.4f}`",
            inline=True
        )
        
        embed.add_field(
            name="Range",
            value=f"{baseline['min_confidence']:.2%} - {baseline['max_confidence']:.2%}",
            inline=False
        )
        
        embed.set_footer(text="Higher std dev indicates more variable confidence")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MLAnomalyDetector(bot))
