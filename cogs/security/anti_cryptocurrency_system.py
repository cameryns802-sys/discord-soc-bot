"""
Anti-Cryptocurrency System - Detect and block cryptocurrency wallets, mining links,
crypto scams, and illicit transaction patterns.
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import re
from cogs.core.signal_bus import signal_bus, Signal, SignalType
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class AntiCryptocurrencySystem(commands.Cog):
    """Detect and prevent cryptocurrency scams and mining malware"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/crypto_detection.json'
        
        # Patterns for crypto detection
        self.crypto_patterns = {
            'ethereum': r'0x[a-fA-F0-9]{40}',  # ETH wallet
            'bitcoin': r'(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}',  # BTC address
            'monero': r'4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}',  # XMR address
            'dogecoin': r'D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}',  # DOGE
        }
        
        # Crypto scam keywords
        self.scam_keywords = [
            'pump and dump', 'moon shot', 'get rich quick', 'guaranteed returns',
            'cryptocurrency investment', 'mining bonus', 'exclusive offer',
            'limited time offer', 'blockchain opportunity', 'defi yield'
        ]
        
        # Crypto mining domains
        self.mining_domains = [
            'mining.com', 'coinhive.com', 'deepminer.io', 'webminer.io',
            'monero-miner.io', 'crypto-miner.io'
        ]
        
        self.detections = []
        self.load_detection_data()
    
    def load_detection_data(self):
        """Load crypto detection data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.detections = data.get('detections', [])
            except:
                self.detections = []
        
        self.save_detection_data()
    
    def save_detection_data(self):
        """Save detection data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'detections': self.detections[-500:]  # Keep last 500
            }, f, indent=2)
    
    def detect_wallet_address(self, text: str) -> list:
        """Detect cryptocurrency wallet addresses"""
        
        detected = []
        
        for crypto_type, pattern in self.crypto_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                detected.append({
                    'type': crypto_type,
                    'address': match,
                    'confidence': 0.95
                })
        
        return detected
    
    def detect_mining_malware(self, text: str) -> list:
        """Detect references to mining malware/scripts"""
        
        detected = []
        
        # Check for mining domains
        for domain in self.mining_domains:
            if domain.lower() in text.lower():
                detected.append({
                    'type': 'mining_domain',
                    'domain': domain,
                    'confidence': 0.9
                })
        
        # Check for common mining script patterns
        mining_patterns = [
            r'(?i)coinhive',
            r'(?i)cryptoloot',
            r'(?i)webminer',
            r'(?i)deepminer',
            r'<script[^>]*src=["\'].*?miner.*?["\']',
        ]
        
        for pattern in mining_patterns:
            if re.search(pattern, text):
                detected.append({
                    'type': 'mining_script',
                    'pattern': pattern,
                    'confidence': 0.85
                })
        
        return detected
    
    def detect_crypto_scams(self, text: str) -> list:
        """Detect crypto scam language patterns"""
        
        detected = []
        text_lower = text.lower()
        
        matches = 0
        for keyword in self.scam_keywords:
            if keyword in text_lower:
                matches += 1
        
        if matches >= 2:  # Multiple scam keywords
            detected.append({
                'type': 'crypto_scam_language',
                'keywords_matched': matches,
                'confidence': min(0.99, 0.5 + (matches * 0.15))
            })
        
        # Check for urgency tactics
        urgency_keywords = ['now', 'urgent', 'limited', 'hurry', 'immediate']
        urgency_count = sum(1 for kw in urgency_keywords if kw in text_lower)
        
        if urgency_count >= 2 and matches >= 1:
            detected.append({
                'type': 'urgency_tactics',
                'urgency_keywords': urgency_count,
                'confidence': 0.75
            })
        
        return detected
    
    async def emit_crypto_signal(self, msg: discord.Message, detections: list, 
                                severity: str = 'medium'):
        """Emit signal for crypto detection"""
        
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity=severity,
            source='anti_cryptocurrency',
            data={
                'reason': 'cryptocurrency_activity_detected',
                'detections': detections,
                'detection_count': len(detections),
                'author': str(msg.author),
                'guild_id': msg.guild.id if msg.guild else None,
                'channel': str(msg.channel)
            },
            confidence=0.88,
            dedup_key=f'crypto:{msg.author.id}:{len(detections)}'
        ))
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor for cryptocurrency activity"""
        
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        content = message.content
        
        # Check for wallet addresses
        wallets = self.detect_wallet_address(content)
        
        # Check for mining malware
        mining = self.detect_mining_malware(content)
        
        # Check for scams
        scams = self.detect_crypto_scams(content)
        
        all_detections = wallets + mining + scams
        
        if all_detections:
            # Record detection
            detection_record = {
                'timestamp': get_now_pst().isoformat(),
                'author': str(message.author),
                'author_id': message.author.id,
                'guild': str(message.guild),
                'guild_id': message.guild.id,
                'message_id': message.id,
                'detections': all_detections
            }
            
            self.detections.append(detection_record)
            self.save_detection_data()
            
            # Determine severity
            severity = 'critical' if any(d['confidence'] >= 0.9 for d in all_detections) else 'high'
            
            # Emit signal
            await self.emit_crypto_signal(message, all_detections, severity)
            
            # Delete message
            try:
                await message.delete()
            except:
                pass
            
            # Warn user
            embed = discord.Embed(
                title="🚫 Cryptocurrency Activity Detected",
                description="Your message was removed due to cryptocurrency activity",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(
                name="Detections",
                value="\n".join([f"• {d.get('type', 'unknown')}: {d.get('confidence', 0):.0%}" 
                               for d in all_detections[:5]]),
                inline=False
            )
            
            embed.add_field(
                name="Policy",
                value="Cryptocurrency activity is prohibited in this server",
                inline=False
            )
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
    
    @commands.command(name='cryptodetections')
    @commands.has_permissions(manage_guild=True)
    async def crypto_detections(self, ctx, days: int = 7):
        """View cryptocurrency detections"""
        
        from datetime import timedelta
        cutoff = (get_now_pst() - timedelta(days=days)).isoformat()
        
        recent = [d for d in self.detections if d['timestamp'] > cutoff]
        
        if not recent:
            await ctx.send(f"✅ No crypto activity detected in past {days} days")
            return
        
        # Analyze detections
        by_type = {}
        by_user = {}
        
        for detection in recent:
            for det in detection.get('detections', []):
                det_type = det.get('type', 'unknown')
                by_type[det_type] = by_type.get(det_type, 0) + 1
            
            user = detection['author']
            by_user[user] = by_user.get(user, 0) + 1
        
        embed = discord.Embed(
            title=f"🚫 Cryptocurrency Detection Report ({days}d)",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Detections", value=len(recent), inline=True)
        embed.add_field(name="Affected Users", value=len(by_user), inline=True)
        
        if by_type:
            type_text = "\n".join([f"• {t}: {c}" for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(name="Detection Types", value=type_text, inline=False)
        
        if by_user:
            user_text = "\n".join([f"• {u}: {c} detection(s)" for u, c in sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]])
            embed.add_field(name="Top Users", value=user_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cryptostats')
    async def crypto_stats(self, ctx):
        """View cryptocurrency detection statistics"""
        
        if not self.detections:
            await ctx.send("✅ No detections recorded")
            return
        
        by_type = {}
        by_severity = {}
        
        for detection in self.detections:
            for det in detection.get('detections', []):
                det_type = det.get('type', 'unknown')
                by_type[det_type] = by_type.get(det_type, 0) + 1
                
                conf = det.get('confidence', 0)
                severity = 'critical' if conf >= 0.9 else 'high' if conf >= 0.7 else 'medium'
                by_severity[severity] = by_severity.get(severity, 0) + 1
        
        embed = discord.Embed(
            title="📊 Cryptocurrency Detection Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Detections", value=len(self.detections), inline=True)
        embed.add_field(name="Unique Users", value=len(set(d['author_id'] for d in self.detections)), inline=True)
        
        if by_type:
            type_text = "\n".join([f"• {t}: {c}" for t, c in by_type.items()])
            embed.add_field(name="Detection Types", value=type_text, inline=False)
        
        if by_severity:
            sev_text = "\n".join([f"• {s}: {c}" for s, c in by_severity.items()])
            embed.add_field(name="By Severity", value=sev_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='checkcrypto')
    async def check_crypto_content(self, ctx, *, text: str):
        """Scan text for cryptocurrency activity (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            return
        
        wallets = self.detect_wallet_address(text)
        mining = self.detect_mining_malware(text)
        scams = self.detect_crypto_scams(text)
        
        all_detections = wallets + mining + scams
        
        embed = discord.Embed(
            title="🔍 Crypto Content Check",
            color=discord.Color.blue() if not all_detections else discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        if not all_detections:
            embed.description = "✅ No cryptocurrency activity detected"
        else:
            embed.description = f"🚫 {len(all_detections)} detection(s) found"
            
            for det in all_detections:
                embed.add_field(
                    name=f"{det.get('type', 'unknown')}",
                    value=f"Confidence: {det.get('confidence', 0):.0%}",
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiCryptocurrencySystem(bot))
