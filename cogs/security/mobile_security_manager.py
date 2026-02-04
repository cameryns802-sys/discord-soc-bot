"""
Mobile Security Posture Manager - Mobile device and app security
Track and monitor mobile device security, compliance, and vulnerabilities
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
from cogs.core.pst_timezone import get_now_pst

class MobileSecurityManager(commands.Cog):
    """Mobile device and application security management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.devices_file = 'data/mobile_devices.json'
        self.policies_file = 'data/mobile_policies.json'
        self.load_data()
    
    def load_data(self):
        """Load mobile data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.devices_file):
            with open(self.devices_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.policies_file):
            with open(self.policies_file, 'w') as f:
                json.dump({}, f)
    
    def get_devices(self, guild_id):
        """Get devices for guild"""
        with open(self.devices_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_devices(self, guild_id, devices):
        """Save devices"""
        with open(self.devices_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = devices
        with open(self.devices_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_device_security_score(self, device):
        """Calculate device security score (0-100)"""
        score = 100
        
        # OS security level
        os_version = device.get('os_version', 'Unknown')
        if 'outdated' in os_version.lower():
            score -= 30
        
        # Encryption
        if not device.get('encryption_enabled', False):
            score -= 20
        
        # MFA
        if not device.get('mfa_enabled', False):
            score -= 15
        
        # Password policy
        if not device.get('password_policy_enforced', False):
            score -= 10
        
        # Antivirus/Malware
        if not device.get('antivirus_installed', False):
            score -= 15
        
        # Device isolation
        if device.get('is_compromised', False):
            score -= 50
        
        # Last security check
        if device.get('last_security_check'):
            last = datetime.fromisoformat(device['last_security_check'])
            days_since = (get_now_pst() - last).days
            if days_since > 30:
                score -= 20
        else:
            score -= 25
        
        # App permissions
        if device.get('excessive_permissions', False):
            score -= 15
        
        return max(0, min(100, score))
    
    async def _mobileadd_logic(self, ctx, device_name: str, device_type: str, owner_name: str = None):
        """Add mobile device"""
        devices = self.get_devices(ctx.guild.id)
        
        device_id = f"MOB-{str(uuid.uuid4())[:8].upper()}"
        
        device = {
            'id': device_id,
            'name': device_name,
            'type': device_type.lower(),
            'owner': owner_name or 'Unknown',
            'added_at': get_now_pst().isoformat(),
            'os_version': 'Latest',
            'encryption_enabled': True,
            'mfa_enabled': True,
            'password_policy_enforced': True,
            'antivirus_installed': True,
            'is_compromised': False,
            'excessive_permissions': False,
            'last_security_check': get_now_pst().isoformat(),
            'security_score': 100,
            'compliance_status': 'compliant',
            'installed_apps': [],
            'vulnerabilities': []
        }
        
        device['security_score'] = self.calculate_device_security_score(device)
        devices[device_id] = device
        self.save_devices(ctx.guild.id, devices)
        
        embed = discord.Embed(
            title="📱 Mobile Device Added",
            description=f"**{device_name}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Device ID", value=f"`{device_id}`", inline=True)
        embed.add_field(name="Type", value=device_type, inline=True)
        embed.add_field(name="Owner", value=owner_name or "Unknown", inline=True)
        embed.add_field(name="Security Score", value="100/100 (Compliant)", inline=True)
        embed.add_field(name="Encryption", value="✅ Enabled", inline=True)
        embed.add_field(name="Status", value="🟢 COMPLIANT", inline=True)
        
        embed.set_footer(text="Use !mobilescan to check device compliance")
        
        await ctx.send(embed=embed)
    
    async def _mobiledevices_logic(self, ctx):
        """List mobile devices"""
        devices = self.get_devices(ctx.guild.id)
        
        if not devices:
            await ctx.send("📱 No mobile devices registered yet.")
            return
        
        # Sort by security score
        sorted_devices = sorted(devices.values(), key=lambda d: d['security_score'])
        
        embed = discord.Embed(
            title="📱 Mobile Device Inventory",
            description=f"{len(sorted_devices)} device(s) managed",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        compliant = sum(1 for d in devices.values() if d['compliance_status'] == 'compliant')
        compromised = sum(1 for d in devices.values() if d['is_compromised'])
        
        embed.add_field(name="Compliance Status", value=f"✅ {compliant} compliant | ⚠️ {len(devices) - compliant} non-compliant", inline=False)
        if compromised:
            embed.add_field(name="⚠️ Compromised", value=f"🔴 {compromised} device(s) potentially compromised", inline=False)
        
        for device in sorted_devices[:8]:
            status = '🔴' if device['is_compromised'] else '🟠' if device['security_score'] < 60 else '🟡' if device['security_score'] < 80 else '🟢'
            
            embed.add_field(
                name=f"{status} {device['name']} ({device['id']})",
                value=f"Owner: {device['owner']} | Type: {device['type'].title()} | Score: {device['security_score']}/100",
                inline=False
            )
        
        if len(sorted_devices) > 8:
            embed.add_field(name="... and more", value=f"+{len(sorted_devices) - 8} additional devices", inline=False)
        
        embed.set_footer(text="Use !mobiledetail <id> for full device profile")
        
        await ctx.send(embed=embed)
    
    async def _mobiledetail_logic(self, ctx, device_id: str):
        """Show device details"""
        devices = self.get_devices(ctx.guild.id)
        
        device_id = device_id.upper()
        if not device_id.startswith('MOB-'):
            device_id = f"MOB-{device_id}"
        
        device = devices.get(device_id)
        if not device:
            await ctx.send(f"❌ Device not found: {device_id}")
            return
        
        score = device['security_score']
        color = discord.Color.red() if device['is_compromised'] else discord.Color.orange() if score < 60 else discord.Color.gold() if score < 80 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"📱 {device['name']}",
            description=f"Device Type: {device['type'].title()}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Device ID", value=f"`{device['id']}`", inline=True)
        embed.add_field(name="Owner", value=device['owner'], inline=True)
        embed.add_field(name="Security Score", value=f"{score}/100", inline=True)
        
        embed.add_field(name="Security Configuration", value="━" * 25, inline=False)
        embed.add_field(name="Encryption", value="✅ Enabled" if device['encryption_enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="MFA", value="✅ Enabled" if device['mfa_enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Password Policy", value="✅ Enforced" if device['password_policy_enforced'] else "❌ Not Enforced", inline=True)
        embed.add_field(name="Antivirus", value="✅ Installed" if device['antivirus_installed'] else "❌ Not Installed", inline=True)
        embed.add_field(name="OS Version", value=device['os_version'], inline=True)
        
        if device['is_compromised']:
            embed.add_field(name="⚠️ COMPROMISED", value="Device flagged as potentially compromised", inline=False)
        
        if device['excessive_permissions']:
            embed.add_field(name="⚠️ Permissions", value="Apps with excessive permissions detected", inline=False)
        
        if device['vulnerabilities']:
            vulns = "\n".join([f"• {v}" for v in device['vulnerabilities'][:5]])
            embed.add_field(name="Known Vulnerabilities", value=vulns, inline=False)
        
        embed.add_field(name="Compliance Status", value=device['compliance_status'].title(), inline=True)
        embed.add_field(name="Last Check", value=datetime.fromisoformat(device['last_security_check']).strftime('%Y-%m-%d %H:%M'), inline=True)
        
        embed.set_footer(text="Sentinel Mobile Security Manager")
        
        await ctx.send(embed=embed)
    
    async def _mobilescan_logic(self, ctx):
        """Scan all devices"""
        devices = self.get_devices(ctx.guild.id)
        
        if not devices:
            await ctx.send("📱 No devices to scan.")
            return
        
        # Simulate scan
        issues = []
        for device in devices.values():
            if device['is_compromised']:
                issues.append(f"🔴 {device['name']}: COMPROMISED - Immediate isolation required")
            elif device['security_score'] < 60:
                issues.append(f"🟠 {device['name']}: LOW SECURITY - {100 - device['security_score']} points below threshold")
        
        embed = discord.Embed(
            title="🔍 Mobile Security Scan Results",
            description=f"Scanned {len(devices)} device(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        compliant = sum(1 for d in devices.values() if d['compliance_status'] == 'compliant' and d['security_score'] >= 80)
        embed.add_field(name="✅ Compliant", value=f"{compliant}/{len(devices)} devices pass compliance check", inline=False)
        
        if issues:
            embed.add_field(name="⚠️ Issues Detected", value="\n".join(issues[:5]), inline=False)
            if len(issues) > 5:
                embed.add_field(name="... and more", value=f"+{len(issues) - 5} additional issues", inline=False)
            embed.color = discord.Color.orange()
        else:
            embed.add_field(name="✅ Status", value="All devices compliant", inline=False)
            embed.color = discord.Color.green()
        
        embed.set_footer(text="Use !mobiledetail <id> for remediation steps")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mobileadd')
    async def mobileadd_prefix(self, ctx, device_name: str, device_type: str, owner_name: str = None):
        """Add mobile device - Prefix command"""
        await self._mobileadd_logic(ctx, device_name, device_type, owner_name)
    
    @commands.command(name='mobiledevices')
    async def mobiledevices_prefix(self, ctx):
        """List mobile devices - Prefix command"""
        await self._mobiledevices_logic(ctx)
    
    @commands.command(name='mobiledetail')
    async def mobiledetail_prefix(self, ctx, device_id: str):
        """Show device details - Prefix command"""
        await self._mobiledetail_logic(ctx, device_id)
    
    @commands.command(name='mobilescan')
    async def mobilescan_prefix(self, ctx):
        """Scan all devices - Prefix command"""
        await self._mobilescan_logic(ctx)

async def setup(bot):
    await bot.add_cog(MobileSecurityManager(bot))
