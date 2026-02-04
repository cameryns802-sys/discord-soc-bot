"""
Anti-Cryptocurrency System - Detect and block cryptocurrency-related threats
including wallet addresses, mining links, coin scams, and pump-and-dump schemes
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class AntiCryptocurrencySystem(commands.Cog):
    """Detect and prevent cryptocurrency scams and threats"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/crypto_threats.json'
        
        # Known malicious patterns
        self.crypto_scam_indicators = {
            'keywords': [
                'free crypto', 'easy money', 'guaranteed returns', 'double your coins',
                'instant profit', 'no experience needed', 'life changing', 'limited time',
                'act now', 'don\'t miss out', 'exclusive opportunity', 'pump', 'mooning'
            ],
            'patterns': [
                r'0x[a-fA-F0-9]{40}',  # Ethereum addresses
                r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Bitcoin addresses
                r'[a-km-zA-HJ-NP-Z0-9]{34}',  # Monero addresses
            ]
        }
        
        # Mining indicators
        self.mining_patterns = [
            r'(?i)mining\s+(?:pool|crypto|coin)',
            r'(?i)hash(?:rate|power)',
            r'(?i)gpu.*mining',
            r'(?i)asic\s+miner',
        ]
        
        # Pump and dump indicators
        self.pump_dump_indicators = [
            'dyor', 'not financial advice', 'to the moon', 'hodl',
            'diamond hands', 'paperhands', 'pump the price'
        ]
        
        # Blocked domains
        self.malicious_domains = []
        
        # Threat metrics
        self.detected_threats = []
        self.blocked_users = {}
        
        self.load_crypto_data()
    
    def load_crypto_data(self):
        """Load cryptocurrency threat data"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.malicious_domains = data.get('malicious_domains', [])
                    self.detected_threats = data.get('detected_threats', [])
                    self.blocked_users = data.get('blocked_users', {})
            except:
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        """Initialize default crypto threat data"""
        self.malicious_domains = [
            'coinclaim.io', 'freecrypto.net', 'instant-wallet.com',
            'coin-miner.js', 'crypto-jack.com'
        ]
        self.detected_threats = []
        self.blocked_users = {}
        self.save_crypto_data()
    
    def save_crypto_data(self):
        """Save crypto threat data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'malicious_domains': self.malicious_domains,
                'detected_threats': self.detected_threats[-500:],
                'blocked_users': self.blocked_users
            }, f, indent=2)
    
    def analyze_message_for_crypto_threat(self, content: str) -> tuple[bool, List[str], float]:
        """
        Analyze message for cryptocurrency threats
        Returns: (is_threat, threat_types, confidence)
        """
        threats = []
        confidence = 0.0
        
        content_lower = content.lower()
        
        # Check for scam keywords (multiple = high confidence)
        keyword_count = sum(1 for kw in self.crypto_scam_indicators['keywords'] 
                           if kw in content_lower)
        if keyword_count >= 3:
            threats.append('scam_keywords')
            confidence += 0.4
        
        # Check for crypto addresses
        for pattern in self.crypto_scam_indicators['patterns']:
            if re.search(pattern, content):
                threats.append('crypto_address')
                confidence += 0.3
        
        # Check for mining content
        for pattern in self.mining_patterns:
            if re.search(pattern, content):
                threats.append('mining_content')
                confidence += 0.25
        
        # Check for pump-and-dump indicators (combination = threat)
        pump_indicators = sum(1 for ind in self.pump_dump_indicators 
                            if ind in content_lower)
        if pump_indicators >= 2:
            threats.append('pump_and_dump')
            confidence += 0.35
        
        # Check for malicious domains
        for domain in self.malicious_domains:
            if domain in content_lower:
                threats.append('malicious_domain')
                confidence += 0.5
        
        # Check for invite scams (fake discord invites with crypto promise)
        if 'discord.gg' in content and any(kw in content_lower for kw in ['free', 'crypto', 'money']):
            threats.append('suspicious_invite')
            confidence += 0.3
        
        # Check for file download scams
        if any(ext in content_lower for ext in ['.exe', '.dll', '.bat']) and 'crypto' in content_lower:
            threats.append('malware_risk')
            confidence += 0.6
        
        is_threat = len(threats) > 0
        confidence = min(1.0, confidence)
        
        return is_threat, threats, confidence
    
    async def emit_crypto_threat_signal(self, user: discord.Member, threats: List[str], 
                                       confidence: float, content: str):
        """Emit crypto threat signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='high' if confidence > 0.7 else 'medium',
            source='anti_cryptocurrency',
            data={
                'user': str(user),
                'user_id': user.id,
                'threat_types': threats,
                'message_content': content[:100],
                'confidence': confidence
            },
            confidence=confidence,
            dedup_key=f'crypto:{user.id}:{",".join(threats)}'
        ))
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for cryptocurrency threats"""
        
        if message.author.bot or not message.guild:
            return
        
        is_threat, threat_types, confidence = self.analyze_message_for_crypto_threat(message.content)
        
        if is_threat:
            # Log threat
            threat_record = {
                'timestamp': get_now_pst().isoformat(),
                'user': str(message.author),
                'user_id': message.author.id,
                'guild': str(message.guild),
                'threat_types': threat_types,
                'confidence': confidence,
                'content': message.content[:200],
                'severity': 'high' if confidence > 0.7 else 'medium'
            }
            
            self.detected_threats.append(threat_record)
            self.save_crypto_data()
            
            # Emit signal
            await self.emit_crypto_threat_signal(message.author, threat_types, confidence, message.content)
            
            # Action based on confidence
            if confidence > 0.8:
                # High confidence: Delete message + warn
                try:
                    await message.delete()
                except:
                    pass
                
                # Send warning
                embed = discord.Embed(
                    title="⚠️ Cryptocurrency Threat Detected",
                    description="Your message was removed due to suspected cryptocurrency scam/threat",
                    color=discord.Color.red(),
                    timestamp=get_now_pst()
                )
                
                embed.add_field(name="Detected Threats", value="\n".join([f"• {t}" for t in threat_types]), inline=False)
                embed.add_field(name="Confidence", value=f"{confidence:.0%}", inline=True)
                embed.add_field(name="Action", value="Message deleted", inline=True)
                
                try:
                    await message.author.send(embed=embed)
                except:
                    if message.channel.permissions_for(message.guild.me).send_messages:
                        await message.channel.send(f"{message.author.mention} - Message removed (cryptocurrency threat)", delete_after=5)
                
            elif confidence > 0.6:
                # Medium confidence: Alert mods
                embed = discord.Embed(
                    title="🔍 Possible Cryptocurrency Threat",
                    description=f"Review message from {message.author.mention}",
                    color=discord.Color.orange(),
                    timestamp=get_now_pst()
                )
                
                embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
                embed.add_field(name="Confidence", value=f"{confidence:.0%}", inline=True)
                embed.add_field(name="Threats", value=", ".join(threat_types), inline=False)
                embed.add_field(name="Content", value=message.content[:200], inline=False)
                
                # Send to mod-logs
                mod_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if mod_channel:
                    try:
                        await mod_channel.send(embed=embed)
                    except:
                        pass
    
    @commands.command(name='addblockcryptodomain')
    @commands.has_permissions(manage_guild=True)
    async def add_block_domain_cmd(self, ctx, domain: str, *, reason: str = "Malicious domain"):
        """Add cryptocurrency domain to block list"""
        
        if domain not in self.malicious_domains:
            self.malicious_domains.append(domain)
            self.save_crypto_data()
            
            await ctx.send(f"✅ Added `{domain}` to cryptocurrency block list\n**Reason:** {reason}")
        else:
            await ctx.send(f"⚠️ `{domain}` is already in the block list")
    
    @commands.command(name='cryptothreats')
    @commands.has_permissions(manage_guild=True)
    async def crypto_threats_cmd(self, ctx, limit: int = 10):
        """View recent cryptocurrency threats"""
        
        recent = self.detected_threats[-limit:] if self.detected_threats else []
        
        if not recent:
            await ctx.send("✅ No cryptocurrency threats detected")
            return
        
        embed = discord.Embed(
            title=f"🔴 Recent Cryptocurrency Threats (Last {len(recent)})",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for threat in reversed(recent[:5]):
            threat_str = ", ".join(threat['threat_types'])
            timestamp = threat['timestamp'][:19]  # YYYY-MM-DD HH:MM:SS
            
            embed.add_field(
                name=f"{threat['user']} @ {timestamp}",
                value=f"**Threats:** {threat_str}\n**Confidence:** {threat['confidence']:.0%}\n**Severity:** {threat['severity']}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cryptostats')
    @commands.has_permissions(manage_guild=True)
    async def crypto_stats_cmd(self, ctx):
        """View cryptocurrency threat statistics"""
        
        # Group by threat type
        threat_counts = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for threat in self.detected_threats:
            for t_type in threat['threat_types']:
                threat_counts[t_type] = threat_counts.get(t_type, 0) + 1
            severity_counts[threat.get('severity', 'medium')] += 1
        
        embed = discord.Embed(
            title="📊 Cryptocurrency Threat Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Threats Detected", value=len(self.detected_threats), inline=True)
        embed.add_field(name="Malicious Domains Blocked", value=len(self.malicious_domains), inline=True)
        
        embed.add_field(name="By Severity", value=f"🔴 High: {severity_counts['high']}\n🟠 Medium: {severity_counts['medium']}\n🟡 Low: {severity_counts['low']}", inline=False)
        
        if threat_counts:
            threat_text = "\n".join([f"• {t}: {c}" for t, c in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5]])
            embed.add_field(name="Top Threat Types", value=threat_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiCryptocurrencySystem(bot))
