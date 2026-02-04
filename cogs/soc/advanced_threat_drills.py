"""
Advanced Threat Drill System
Simulates real-world security threats to train the bot and security team
Validates incident response capabilities and improves threat handling
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
import random
import asyncio
from typing import Optional, List, Dict
from cogs.core.pst_timezone import get_now_pst
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class DrillType:
    """Available drill scenarios"""
    PHISHING_ATTACK = "phishing_attack"
    RAID_SIMULATION = "raid_simulation"
    MALWARE_OUTBREAK = "malware_outbreak"
    SPAM_ATTACK = "spam_attack"
    DATA_BREACH = "data_breach"
    INSIDER_THREAT = "insider_threat"
    DDOS_ATTACK = "ddos_attack"
    RANSOMWARE = "ransomware"
    SOCIAL_ENGINEERING = "social_engineering"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ZERO_DAY_EXPLOIT = "zero_day_exploit"

class DrillDifficulty:
    """Drill difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class AdvancedThreatDrills(commands.Cog):
    """Advanced security drill and training system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data'
        self.drills_file = os.path.join(self.data_dir, 'threat_drills.json')
        self.active_drills = {}  # guild_id -> drill_data
        self.drill_history = []
        self.drill_templates = self._init_drill_templates()
        self.load_drill_data()
    
    # Command group for all drill commands
    drill_group = app_commands.Group(name="drill", description="Security threat simulation drills")
    
    def load_drill_data(self):
        """Load drill history"""
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.drills_file):
            try:
                with open(self.drills_file, 'r') as f:
                    data = json.load(f)
                    self.drill_history = data.get('history', [])
            except:
                self.drill_history = []
        else:
            self.save_drill_data()
    
    def save_drill_data(self):
        """Save drill history"""
        with open(self.drills_file, 'w') as f:
            json.dump({
                'history': self.drill_history[-200:]  # Keep last 200 drills
            }, f, indent=2)
    
    # ==================== EVENT SIMULATION SYSTEM ====================
    
    async def simulate_drill_events(self, guild: discord.Guild, drill_type: str, channel: discord.TextChannel):
        """Start simulating events for active drill"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        # Send initial drill alert
        alert_embed = discord.Embed(
            title="🚨 DRILL IN PROGRESS",
            description=f"**{drill['template']['name']}**\n\nThis is a simulation - security systems are being tested",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        alert_embed.add_field(name="Drill ID", value=drill['drill_id'], inline=True)
        alert_embed.add_field(name="Difficulty", value=drill['difficulty'].upper(), inline=True)
        alert_embed.add_field(name="Duration", value=f"~{drill['template']['duration_minutes']} minutes", inline=True)
        
        await channel.send(embed=alert_embed)
        
        # Start event simulation based on drill type
        if drill_type == DrillType.PHISHING_ATTACK:
            await self.simulate_phishing_attack(guild, channel)
        elif drill_type == DrillType.RAID_SIMULATION:
            await self.simulate_raid_attack(guild, channel)
        elif drill_type == DrillType.MALWARE_OUTBREAK:
            await self.simulate_malware_outbreak(guild, channel)
        elif drill_type == DrillType.SPAM_ATTACK:
            await self.simulate_spam_attack(guild, channel)
        elif drill_type == DrillType.DATA_BREACH:
            await self.simulate_data_breach(guild, channel)
        elif drill_type == DrillType.INSIDER_THREAT:
            await self.simulate_insider_threat(guild, channel)
        elif drill_type == DrillType.DDOS_ATTACK:
            await self.simulate_ddos_attack(guild, channel)
        elif drill_type == DrillType.RANSOMWARE:
            await self.simulate_ransomware(guild, channel)
    
    async def simulate_phishing_attack(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate phishing attack with fake malicious links"""
        fake_phishing_messages = [
            "🎁 **URGENT**: Your Discord Nitro is expiring! Click here to renew: `hxxp://discord-nitro-gift.com/claim`",
            "⚠️ **Security Alert**: Unusual activity detected on your account. Verify here: `hxxp://discord-verify-account.com`",
            "💰 **You won $1000!** Claim your prize now: `hxxp://free-discord-giveaway.com/winner`",
            "🔒 **Action Required**: Discord is updating security. Verify your account: `hxxp://discord-security-update.com`",
            "🎮 **Free Nitro for 1 Year!** Limited time offer: `hxxp://discord-free-nitro.com/offer`"
        ]
        
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        # Send 3-5 phishing messages over time
        num_messages = random.randint(3, 5)
        
        for i in range(num_messages):
            if guild.id not in self.active_drills:  # Check if drill still active
                break
            
            # Random delay between messages
            await asyncio.sleep(random.randint(15, 45))
            
            message = random.choice(fake_phishing_messages)
            
            try:
                drill_msg = await channel.send(f"[DRILL SIMULATION] {message}")
                
                # Emit threat signal for security systems to detect
                await signal_bus.emit(Signal(
                    signal_type=SignalType.THREAT_DETECTED,
                    severity='high',
                    source='drill_simulation',
                    data={
                        'drill_id': drill['drill_id'],
                        'threat_type': 'phishing',
                        'message_id': drill_msg.id,
                        'content': message,
                        'indicators': ['suspicious_link', 'urgency_language', 'impersonation']
                    },
                    confidence=1.0,
                    dedup_key=f"drill:{drill['drill_id']}:phishing:{i}"
                ))
                
                # Record event
                drill['events'].append({
                    'timestamp': get_now_pst().isoformat(),
                    'type': 'phishing_message',
                    'message_id': drill_msg.id,
                    'detected': False
                })
                
            except Exception as e:
                print(f"[Drill] Failed to send phishing simulation: {e}")
    
    async def simulate_raid_attack(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate raid attack with rapid fake joins"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        # Announce raid simulation
        await channel.send("[DRILL SIMULATION] 🚨 **Simulating mass member join (raid pattern)**")
        
        # Emit raid signals rapidly
        for i in range(15):
            if guild.id not in self.active_drills:
                break
            
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='critical',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'raid',
                    'simulated_user': f'RaidBot#{random.randint(1000, 9999)}',
                    'join_rate': '15 joins/10 seconds',
                    'indicators': ['mass_join', 'suspicious_pattern', 'new_accounts']
                },
                confidence=1.0,
                dedup_key=f"drill:{drill['drill_id']}:raid:{i}"
            ))
            
            drill['events'].append({
                'timestamp': get_now_pst().isoformat(),
                'type': 'simulated_raid_join',
                'user_number': i + 1
            })
            
            await asyncio.sleep(0.5)  # Rapid joins
    
    async def simulate_malware_outbreak(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate malware outbreak with malicious file alerts"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        malware_files = [
            "invoice_2026.exe",
            "discord_update.scr",
            "FREE_NITRO_GENERATOR.bat",
            "important_document.pdf.exe",
            "game_hack_tool.zip"
        ]
        
        await channel.send("[DRILL SIMULATION] ☣️ **Simulating malware detection alerts**")
        
        for i, filename in enumerate(malware_files[:3]):
            if guild.id not in self.active_drills:
                break
            
            await asyncio.sleep(random.randint(10, 30))
            
            await channel.send(f"[DRILL SIMULATION] ⚠️ Suspicious file detected: `{filename}`")
            
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='critical',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'malware',
                    'filename': filename,
                    'indicators': ['malicious_extension', 'suspicious_name', 'untrusted_source']
                },
                confidence=0.95,
                dedup_key=f"drill:{drill['drill_id']}:malware:{i}"
            ))
            
            drill['events'].append({
                'timestamp': get_now_pst().isoformat(),
                'type': 'malware_detection',
                'filename': filename
            })
    
    async def simulate_spam_attack(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate spam attack with rapid repeated messages"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        await channel.send("[DRILL SIMULATION] 📢 **Simulating spam attack**")
        
        spam_message = "🎁 FREE NITRO GIVEAWAY! Click here now! Limited time!"
        
        for i in range(10):
            if guild.id not in self.active_drills:
                break
            
            try:
                msg = await channel.send(f"[DRILL SIMULATION] {spam_message}")
                
                await signal_bus.emit(Signal(
                    signal_type=SignalType.THREAT_DETECTED,
                    severity='medium',
                    source='drill_simulation',
                    data={
                        'drill_id': drill['drill_id'],
                        'threat_type': 'spam',
                        'message_id': msg.id,
                        'rate': '10 messages/5 seconds'
                    },
                    confidence=1.0,
                    dedup_key=f"drill:{drill['drill_id']}:spam:{i}"
                ))
                
                drill['events'].append({
                    'timestamp': get_now_pst().isoformat(),
                    'type': 'spam_message',
                    'message_id': msg.id
                })
                
            except Exception as e:
                print(f"[Drill] Spam simulation error: {e}")
            
            await asyncio.sleep(0.5)
    
    async def simulate_data_breach(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate data breach detection"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        await channel.send("[DRILL SIMULATION] 🔓 **Simulating unauthorized data access**")
        
        breach_events = [
            "Unauthorized database query detected",
            "Sensitive file access from unknown IP",
            "Data exfiltration pattern detected",
            "Privilege escalation attempt",
            "Credentials leaked on external site"
        ]
        
        for i, event in enumerate(breach_events[:3]):
            if guild.id not in self.active_drills:
                break
            
            await asyncio.sleep(random.randint(15, 30))
            
            await channel.send(f"[DRILL SIMULATION] ⚠️ {event}")
            
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='critical',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'data_breach',
                    'event': event,
                    'indicators': ['unauthorized_access', 'data_exfiltration', 'anomalous_behavior']
                },
                confidence=0.90,
                dedup_key=f"drill:{drill['drill_id']}:breach:{i}"
            ))
            
            drill['events'].append({
                'timestamp': get_now_pst().isoformat(),
                'type': 'breach_event',
                'description': event
            })
    
    async def simulate_insider_threat(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate insider threat behavior"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        await channel.send("[DRILL SIMULATION] 👤 **Simulating insider threat activity**")
        
        insider_actions = [
            "Unusual file download volume detected",
            "After-hours access from trusted account",
            "Attempt to disable monitoring systems",
            "Copying sensitive data to external storage",
            "Accessing restricted areas without authorization"
        ]
        
        for i, action in enumerate(insider_actions[:3]):
            if guild.id not in self.active_drills:
                break
            
            await asyncio.sleep(random.randint(20, 40))
            
            await channel.send(f"[DRILL SIMULATION] ⚠️ {action}")
            
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='high',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'insider_threat',
                    'action': action,
                    'indicators': ['anomalous_behavior', 'policy_violation', 'suspicious_activity']
                },
                confidence=0.85,
                dedup_key=f"drill:{drill['drill_id']}:insider:{i}"
            ))
            
            drill['events'].append({
                'timestamp': get_now_pst().isoformat(),
                'type': 'insider_activity',
                'action': action
            })
    
    async def simulate_ddos_attack(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate DDoS attack patterns"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        await channel.send("[DRILL SIMULATION] 🌐 **Simulating DDoS attack traffic**")
        
        await channel.send("[DRILL SIMULATION] ⚠️ High volume of requests detected from multiple IPs")
        await channel.send("[DRILL SIMULATION] ⚠️ Service degradation detected - Response time: 5000ms")
        await channel.send("[DRILL SIMULATION] ⚠️ Connection pool exhaustion - 95% capacity")
        
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='critical',
            source='drill_simulation',
            data={
                'drill_id': drill['drill_id'],
                'threat_type': 'ddos',
                'indicators': ['high_traffic_volume', 'service_degradation', 'multiple_sources'],
                'traffic_rate': '10000 req/sec',
                'connection_saturation': '95%'
            },
            confidence=0.98,
            dedup_key=f"drill:{drill['drill_id']}:ddos"
        ))
        
        drill['events'].append({
            'timestamp': get_now_pst().isoformat(),
            'type': 'ddos_attack',
            'severity': 'critical'
        })
    
    async def simulate_ransomware(self, guild: discord.Guild, channel: discord.TextChannel):
        """Simulate ransomware detection"""
        if guild.id not in self.active_drills:
            return
        
        drill = self.active_drills[guild.id]
        
        await channel.send("[DRILL SIMULATION] 🔒 **Simulating ransomware activity**")
        
        await asyncio.sleep(5)
        await channel.send("[DRILL SIMULATION] ⚠️ File encryption activity detected")
        
        await asyncio.sleep(10)
        await channel.send("[DRILL SIMULATION] ⚠️ Ransom note detected: `YOUR_FILES_ARE_ENCRYPTED.txt`")
        
        await asyncio.sleep(10)
        await channel.send("[DRILL SIMULATION] ⚠️ Multiple file extensions changed to `.locked`")
        
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='critical',
            source='drill_simulation',
            data={
                'drill_id': drill['drill_id'],
                'threat_type': 'ransomware',
                'indicators': ['file_encryption', 'ransom_note', 'suspicious_process'],
                'files_affected': 'simulated',
                'ransomware_family': 'SimulatedLocker'
            },
            confidence=0.99,
            dedup_key=f"drill:{drill['drill_id']}:ransomware"
        ))
        
        drill['events'].append({
            'timestamp': get_now_pst().isoformat(),
            'type': 'ransomware_detected',
            'severity': 'critical'
        })
    
    def _init_drill_templates(self) -> Dict:
        """Initialize drill scenario templates"""
        return {
            DrillType.PHISHING_ATTACK: {
                'name': '🎣 Phishing Attack Simulation',
                'description': 'Simulates a phishing campaign targeting users',
                'duration_minutes': 15,
                'objectives': [
                    'Detect suspicious links',
                    'Identify phishing indicators',
                    'Block malicious messages',
                    'Alert security team',
                    'Quarantine affected users'
                ],
                'success_criteria': {
                    'detection_time': 60,  # seconds
                    'block_rate': 90,  # percentage
                    'false_positives': 5  # max allowed
                },
                'indicators': [
                    'Suspicious URL patterns',
                    'Urgent language',
                    'Credential requests',
                    'Spoofed sender addresses'
                ]
            },
            DrillType.RAID_SIMULATION: {
                'name': '🚨 Raid Attack Simulation',
                'description': 'Simulates mass coordinated join attack',
                'duration_minutes': 10,
                'objectives': [
                    'Detect abnormal join rates',
                    'Enable raid protection',
                    'Mass kick/ban raiders',
                    'Preserve legitimate users',
                    'Restore normal operations'
                ],
                'success_criteria': {
                    'detection_time': 30,
                    'mitigation_time': 120,
                    'false_positives': 0
                },
                'indicators': [
                    'Rapid member joins',
                    'Similar account patterns',
                    'Coordinated spam',
                    'New accounts'
                ]
            },
            DrillType.MALWARE_OUTBREAK: {
                'name': '🦠 Malware Outbreak Simulation',
                'description': 'Simulates malware spreading through attachments',
                'duration_minutes': 20,
                'objectives': [
                    'Detect malicious files',
                    'Scan attachments',
                    'Quarantine infected systems',
                    'Alert affected users',
                    'Prevent spread'
                ],
                'success_criteria': {
                    'detection_time': 45,
                    'containment_time': 300,
                    'spread_prevention': 95
                },
                'indicators': [
                    'Suspicious file extensions',
                    'Unusual download patterns',
                    'Encoded payloads',
                    'Rapid file sharing'
                ]
            },
            DrillType.DATA_BREACH: {
                'name': '💾 Data Breach Simulation',
                'description': 'Simulates unauthorized data access attempt',
                'duration_minutes': 25,
                'objectives': [
                    'Detect unauthorized access',
                    'Identify compromised accounts',
                    'Revoke access privileges',
                    'Audit data exposure',
                    'Initiate breach protocol'
                ],
                'success_criteria': {
                    'detection_time': 90,
                    'response_time': 180,
                    'data_protection': 100
                },
                'indicators': [
                    'Unusual access patterns',
                    'Off-hours activity',
                    'Bulk data downloads',
                    'Failed auth attempts'
                ]
            },
            DrillType.INSIDER_THREAT: {
                'name': '👤 Insider Threat Simulation',
                'description': 'Simulates malicious insider activity',
                'duration_minutes': 30,
                'objectives': [
                    'Detect behavioral anomalies',
                    'Monitor privilege abuse',
                    'Track data access',
                    'Investigate suspicious actions',
                    'Contain insider threat'
                ],
                'success_criteria': {
                    'detection_time': 300,
                    'investigation_accuracy': 90,
                    'containment_success': 100
                },
                'indicators': [
                    'Privilege escalation attempts',
                    'Unusual data access',
                    'Policy violations',
                    'Access to sensitive systems'
                ]
            },
            DrillType.RANSOMWARE: {
                'name': '🔒 Ransomware Attack Simulation',
                'description': 'Simulates ransomware encryption attempt',
                'duration_minutes': 20,
                'objectives': [
                    'Detect encryption activity',
                    'Isolate affected systems',
                    'Block C2 communications',
                    'Restore from backups',
                    'Prevent spread'
                ],
                'success_criteria': {
                    'detection_time': 60,
                    'isolation_time': 120,
                    'recovery_success': 100
                },
                'indicators': [
                    'Rapid file modifications',
                    'Suspicious encryption',
                    'Ransom notes',
                    'C2 communications'
                ]
            },
            DrillType.DDOS_ATTACK: {
                'name': '💥 DDoS Attack Simulation',
                'description': 'Simulates distributed denial of service attack',
                'duration_minutes': 15,
                'objectives': [
                    'Detect traffic anomalies',
                    'Enable rate limiting',
                    'Filter malicious traffic',
                    'Maintain service availability',
                    'Trace attack source'
                ],
                'success_criteria': {
                    'detection_time': 30,
                    'mitigation_time': 180,
                    'uptime_maintained': 95
                },
                'indicators': [
                    'Traffic spikes',
                    'Repeated requests',
                    'Distributed sources',
                    'Service degradation'
                ]
            },
            DrillType.SOCIAL_ENGINEERING: {
                'name': '🎭 Social Engineering Simulation',
                'description': 'Simulates social engineering attacks',
                'duration_minutes': 25,
                'objectives': [
                    'Recognize manipulation tactics',
                    'Verify suspicious requests',
                    'Report phishing attempts',
                    'Protect credentials',
                    'Educate users'
                ],
                'success_criteria': {
                    'detection_rate': 85,
                    'reporting_rate': 90,
                    'credential_protection': 100
                },
                'indicators': [
                    'Urgency tactics',
                    'Authority impersonation',
                    'Unusual requests',
                    'Trust exploitation'
                ]
            }
        }
    
    def calculate_drill_score(self, drill_data: Dict) -> int:
        """Calculate drill performance score (0-100)"""
        score = 0
        template = self.drill_templates[drill_data['type']]
        criteria = template['success_criteria']
        results = drill_data.get('results', {})
        
        # Detection time score (30 points)
        if 'detection_time' in criteria and 'detection_time' in results:
            target_time = criteria['detection_time']
            actual_time = results['detection_time']
            if actual_time <= target_time:
                score += 30
            elif actual_time <= target_time * 1.5:
                score += 20
            elif actual_time <= target_time * 2:
                score += 10
        
        # Response effectiveness (40 points)
        if 'actions_taken' in results:
            actions_taken = results['actions_taken']
            total_objectives = len(template['objectives'])
            completion_rate = min(100, (actions_taken / total_objectives) * 100)
            score += int(completion_rate * 0.4)
        
        # Accuracy (20 points)
        if 'false_positives' in criteria and 'false_positives' in results:
            max_fp = criteria['false_positives']
            actual_fp = results['false_positives']
            if actual_fp <= max_fp:
                score += 20
            elif actual_fp <= max_fp * 2:
                score += 10
        
        # Speed bonus (10 points)
        if 'completion_time' in results:
            target_duration = template['duration_minutes'] * 60
            actual_duration = results['completion_time']
            if actual_duration <= target_duration:
                score += 10
            elif actual_duration <= target_duration * 1.2:
                score += 5
        
        return min(100, score)
    
    async def start_drill(self, guild: discord.Guild, drill_type: str, 
                         difficulty: str = DrillDifficulty.INTERMEDIATE) -> Dict:
        """Start a new security drill"""
        if guild.id in self.active_drills:
            return {'error': 'Drill already active in this server'}
        
        if drill_type not in self.drill_templates:
            return {'error': 'Invalid drill type'}
        
        template = self.drill_templates[drill_type]
        
        drill_data = {
            'drill_id': f"DRILL-{get_now_pst().strftime('%Y%m%d%H%M%S')}",
            'guild_id': guild.id,
            'type': drill_type,
            'difficulty': difficulty,
            'template': template,
            'started_at': get_now_pst().isoformat(),
            'status': 'active',
            'objectives_completed': [],
            'events': [],
            'detections': 0,
            'false_positives': 0,
            'actions_taken': 0
        }
        
        self.active_drills[guild.id] = drill_data
        
        # Emit drill started signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.USER_ESCALATION,
            severity='INFO',
            source='threat_drills',
            data={
                'event': 'drill_started',
                'drill_type': drill_type,
                'drill_id': drill_data['drill_id']
            }
        ))
        
        return {'success': True, 'drill_data': drill_data}
    
    async def start_drill_with_channel(self, guild: discord.Guild, drill_type: str, 
                                      channel: discord.TextChannel,
                                      difficulty: str = DrillDifficulty.INTERMEDIATE) -> Dict:
        """Start drill and begin event simulation"""
        result = await self.start_drill(guild, drill_type, difficulty)
        
        if 'error' in result:
            return result
        
        # Start event simulation in background
        self.bot.loop.create_task(self.simulate_drill_events(guild, drill_type, channel))
        
        return result
    
    async def record_drill_action(self, guild_id: int, action: str, success: bool):
        """Record an action taken during drill"""
        if guild_id not in self.active_drills:
            return
        
        drill = self.active_drills[guild_id]
        drill['actions_taken'] += 1
        drill['events'].append({
            'timestamp': get_now_pst().isoformat(),
            'action': action,
            'success': success
        })
        
        # Check if action matches objectives
        for objective in drill['template']['objectives']:
            if objective.lower() in action.lower():
                if objective not in drill['objectives_completed']:
                    drill['objectives_completed'].append(objective)
    
    async def end_drill(self, guild_id: int) -> Dict:
        """End active drill and generate report"""
        if guild_id not in self.active_drills:
            return {'error': 'No active drill'}
        
        drill = self.active_drills[guild_id]
        drill['ended_at'] = get_now_pst().isoformat()
        drill['status'] = 'completed'
        
        # Calculate metrics
        started = datetime.fromisoformat(drill['started_at'])
        ended = datetime.fromisoformat(drill['ended_at'])
        duration = (ended - started).total_seconds()
        
        drill['results'] = {
            'detection_time': 45,  # Simulated
            'completion_time': duration,
            'actions_taken': drill['actions_taken'],
            'objectives_completed': len(drill['objectives_completed']),
            'total_objectives': len(drill['template']['objectives']),
            'false_positives': drill['false_positives'],
            'detections': drill['detections']
        }
        
        # Calculate score
        drill['score'] = self.calculate_drill_score(drill)
        
        # Save to history
        self.drill_history.append({
            'drill_id': drill['drill_id'],
            'guild_id': guild_id,
            'type': drill['type'],
            'difficulty': drill['difficulty'],
            'score': drill['score'],
            'started_at': drill['started_at'],
            'ended_at': drill['ended_at'],
            'duration_seconds': duration
        })
        self.save_drill_data()
        
        # Remove from active
        del self.active_drills[guild_id]
        
        return {'success': True, 'drill': drill}
    
    # ==================== COMMANDS ====================
    
    @commands.command(name='startdrill')
    @commands.has_permissions(administrator=True)
    async def startdrill_prefix(self, ctx, drill_type: str = None, difficulty: str = 'intermediate'):
        """Start a security drill"""
        await self._startdrill_logic(ctx, drill_type, difficulty)
    
    @drill_group.command(name="start", description="Start a security threat simulation drill")
    @app_commands.describe(
        drill_type="Drill scenario (phishing_attack, raid_simulation, malware_outbreak, etc.)",
        difficulty="Difficulty level (beginner, intermediate, advanced, expert)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def startdrill_slash(self, interaction: discord.Interaction, drill_type: str = None, difficulty: str = 'intermediate'):
        """Start drill using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._startdrill_logic(ctx, drill_type, difficulty)
    
    async def _startdrill_logic(self, ctx, drill_type: str = None, difficulty: str = 'intermediate'):
        """Start security drill"""
        # Show available drills if none specified
        if not drill_type:
            embed = discord.Embed(
                title="🎯 Available Security Drills",
                description="Choose a drill scenario to start training",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            for dtype, template in self.drill_templates.items():
                embed.add_field(
                    name=template['name'],
                    value=f"{template['description']}\n⏱️ Duration: ~{template['duration_minutes']} min",
                    inline=False
                )
            
            embed.add_field(
                name="Usage",
                value="`/startdrill <type> [difficulty]`\nExample: `/startdrill phishing_attack intermediate`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Start the drill with event simulation
        result = await self.start_drill_with_channel(ctx.guild, drill_type, ctx.channel, difficulty)
        
        if 'error' in result:
            await ctx.send(f"❌ {result['error']}")
            return
        
        drill = result['drill_data']
        template = drill['template']
        
        embed = discord.Embed(
            title="🚨 SECURITY DRILL INITIATED",
            description=f"**{template['name']}**\n{template['description']}",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="📋 Drill Information",
            value=f"**ID:** `{drill['drill_id']}`\n**Difficulty:** {difficulty.upper()}\n**Duration:** ~{template['duration_minutes']} minutes",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Objectives",
            value="\n".join([f"• {obj}" for obj in template['objectives']]),
            inline=False
        )
        
        embed.add_field(
            name="🔍 Key Indicators to Watch",
            value="\n".join([f"• {ind}" for ind in template['indicators']]),
            inline=False
        )
        
        embed.add_field(
            name="✅ Success Criteria",
            value="\n".join([f"• **{k.replace('_', ' ').title()}:** {v}" for k, v in template['success_criteria'].items()]),
            inline=False
        )
        
        embed.add_field(
            name="📝 Commands",
            value="`/drillstatus` - Check drill status\n`/enddrill` - End drill and generate report\n`/drillaction <action>` - Log action taken",
            inline=False
        )
        
        embed.set_footer(text="⚠️ This is a TRAINING DRILL - No real threats present")
        
        await ctx.send(embed=embed)
        
        # Start simulating threat events
        asyncio.create_task(self._simulate_drill_events(ctx.guild, drill))
    
    async def _simulate_drill_events(self, guild: discord.Guild, drill: Dict):
        """Simulate threat events during drill"""
        await asyncio.sleep(10)  # Wait 10 seconds before first event
        
        drill_type = drill['type']
        
        # Emit simulated threat signals
        if drill_type == DrillType.PHISHING_ATTACK:
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='HIGH',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'phishing',
                    'simulated': True,
                    'phishing_url': 'http://fake-bank-login.sus/verify',
                    'indicators': ['Suspicious URL', 'Urgent language', 'Credential request']
                }
            ))
        
        elif drill_type == DrillType.RAID_SIMULATION:
            # Simulate rapid joins
            for i in range(5):
                await signal_bus.emit(Signal(
                    signal_type=SignalType.THREAT_DETECTED,
                    severity='CRITICAL',
                    source='drill_simulation',
                    data={
                        'drill_id': drill['drill_id'],
                        'threat_type': 'raid',
                        'simulated': True,
                        'joins_per_second': 15 + i * 5,
                        'new_accounts': True
                    }
                ))
                await asyncio.sleep(5)
        
        elif drill_type == DrillType.MALWARE_OUTBREAK:
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity='CRITICAL',
                source='drill_simulation',
                data={
                    'drill_id': drill['drill_id'],
                    'threat_type': 'malware',
                    'simulated': True,
                    'file_hash': 'a1b2c3d4e5f6',
                    'indicators': ['Suspicious .exe', 'Base64 encoded', 'Obfuscated']
                }
            ))
    
    @commands.command(name='drillstatus')
    async def drillstatus_prefix(self, ctx):
        """Check active drill status"""
        await self._drillstatus_logic(ctx)
    
    @drill_group.command(name="status", description="Check current drill status and progress")
    async def drillstatus_slash(self, interaction: discord.Interaction):
        """Check drill status using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._drillstatus_logic(ctx)
    
    async def _drillstatus_logic(self, ctx):
        """Check drill status"""
        if ctx.guild.id not in self.active_drills:
            await ctx.send("ℹ️ No active drill in this server")
            return
        
        drill = self.active_drills[ctx.guild.id]
        template = drill['template']
        
        started = datetime.fromisoformat(drill['started_at'])
        elapsed = (get_now_pst() - started).total_seconds()
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        
        completion = (len(drill['objectives_completed']) / len(template['objectives'])) * 100
        
        embed = discord.Embed(
            title="📊 Drill Status Report",
            description=f"**{template['name']}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="🆔 Drill ID",
            value=f"`{drill['drill_id']}`",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Elapsed Time",
            value=elapsed_str,
            inline=True
        )
        
        embed.add_field(
            name="📈 Progress",
            value=f"{completion:.0f}%",
            inline=True
        )
        
        embed.add_field(
            name="✅ Objectives Completed",
            value=f"{len(drill['objectives_completed'])}/{len(template['objectives'])}",
            inline=True
        )
        
        embed.add_field(
            name="🎬 Actions Taken",
            value=str(drill['actions_taken']),
            inline=True
        )
        
        embed.add_field(
            name="🔍 Detections",
            value=str(drill['detections']),
            inline=True
        )
        
        if drill['objectives_completed']:
            embed.add_field(
                name="✅ Completed Objectives",
                value="\n".join([f"• {obj}" for obj in drill['objectives_completed']]),
                inline=False
            )
        
        remaining = [obj for obj in template['objectives'] if obj not in drill['objectives_completed']]
        if remaining:
            embed.add_field(
                name="⏳ Remaining Objectives",
                value="\n".join([f"• {obj}" for obj in remaining]),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='enddrill')
    @commands.has_permissions(administrator=True)
    async def enddrill_prefix(self, ctx):
        """End active drill and generate report"""
        await self._enddrill_logic(ctx)
    
    @drill_group.command(name="end", description="End drill and generate performance report")
    @app_commands.checks.has_permissions(administrator=True)
    async def enddrill_slash(self, interaction: discord.Interaction):
        """End drill using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._enddrill_logic(ctx)
    
    async def _enddrill_logic(self, ctx):
        """End drill and generate report"""
        result = await self.end_drill(ctx.guild.id)
        
        if 'error' in result:
            await ctx.send(f"❌ {result['error']}")
            return
        
        drill = result['drill']
        results = drill['results']
        template = drill['template']
        
        score = drill['score']
        
        # Determine grade
        if score >= 90:
            grade = "A+ EXCELLENT"
            color = discord.Color.green()
        elif score >= 80:
            grade = "A VERY GOOD"
            color = discord.Color.blue()
        elif score >= 70:
            grade = "B GOOD"
            color = discord.Color.gold()
        elif score >= 60:
            grade = "C SATISFACTORY"
            color = discord.Color.orange()
        else:
            grade = "F NEEDS IMPROVEMENT"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="📋 DRILL PERFORMANCE REPORT",
            description=f"**{template['name']}**\nDrill completed successfully",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="🏆 Final Score",
            value=f"**{score}/100** - Grade: {grade}",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Duration",
            value=f"{int(results['completion_time'] // 60)}m {int(results['completion_time'] % 60)}s",
            inline=True
        )
        
        embed.add_field(
            name="✅ Objectives",
            value=f"{results['objectives_completed']}/{results['total_objectives']}",
            inline=True
        )
        
        embed.add_field(
            name="🎬 Actions",
            value=str(results['actions_taken']),
            inline=True
        )
        
        embed.add_field(
            name="📊 Performance Metrics",
            value=f"**Detection Time:** {results['detection_time']}s\n**Detections:** {results['detections']}\n**False Positives:** {results['false_positives']}",
            inline=False
        )
        
        # Recommendations
        recommendations = []
        if score < 70:
            recommendations.append("• Review incident response procedures")
        if results['detection_time'] > template['success_criteria'].get('detection_time', 60):
            recommendations.append("• Improve threat detection speed")
        if results['false_positives'] > 5:
            recommendations.append("• Reduce false positive rate")
        if results['objectives_completed'] < results['total_objectives']:
            recommendations.append("• Complete all training objectives")
        
        if recommendations:
            embed.add_field(
                name="💡 Recommendations",
                value="\n".join(recommendations),
                inline=False
            )
        else:
            embed.add_field(
                name="✨ Outstanding Performance!",
                value="All objectives met with excellent execution",
                inline=False
            )
        
        embed.set_footer(text=f"Drill ID: {drill['drill_id']}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='drillhistory')
    async def drillhistory_prefix(self, ctx, limit: int = 10):
        """View drill history"""
        await self._drillhistory_logic(ctx, limit)
    
    @drill_group.command(name="history", description="View past drill performance history")
    @app_commands.describe(limit="Number of drills to show (default 10)")
    async def drillhistory_slash(self, interaction: discord.Interaction, limit: int = 10):
        """View history using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._drillhistory_logic(ctx, limit)
    
    async def _drillhistory_logic(self, ctx, limit: int):
        """View drill history"""
        guild_history = [d for d in self.drill_history if d['guild_id'] == ctx.guild.id]
        
        if not guild_history:
            await ctx.send("📋 No drill history available")
            return
        
        recent = guild_history[-limit:]
        recent.reverse()
        
        embed = discord.Embed(
            title="📚 Drill Performance History",
            description=f"Showing {len(recent)} most recent drills",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for drill in recent:
            template_name = self.drill_templates[drill['type']]['name']
            score = drill['score']
            
            grade_emoji = "🏆" if score >= 90 else "🥇" if score >= 80 else "🥈" if score >= 70 else "🥉"
            
            embed.add_field(
                name=f"{grade_emoji} {template_name}",
                value=f"**Score:** {score}/100\n**Date:** {datetime.fromisoformat(drill['started_at']).strftime('%Y-%m-%d %H:%M')}\n**Duration:** {int(drill['duration_seconds'] // 60)}m",
                inline=True
            )
        
        # Calculate average score
        if guild_history:
            avg_score = sum(d['score'] for d in guild_history) / len(guild_history)
            embed.add_field(
                name="📊 Average Performance",
                value=f"**{avg_score:.1f}/100** across {len(guild_history)} drills",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedThreatDrills(bot))
