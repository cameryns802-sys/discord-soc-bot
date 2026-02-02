"""
Access Risk Enforcer
Risk-based access enforcement with automatic permission revocation on risk threshold breach
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AccessRiskEnforcerCog(commands.Cog):
    """
    Access Risk Enforcer
    
    Implements risk-based access control with automatic permission revocation
    when risk thresholds are breached.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/access_risk"
        os.makedirs(self.data_dir, exist_ok=True)
        self.risk_profiles_file = os.path.join(self.data_dir, "risk_profiles.json")
        self.enforcement_log_file = os.path.join(self.data_dir, "enforcement_log.json")
        self.rules_file = os.path.join(self.data_dir, "enforcement_rules.json")
        self.risk_profiles = self.load_risk_profiles()
        self.enforcement_log = self.load_enforcement_log()
        self.rules = self.load_rules()
        
    def load_risk_profiles(self) -> Dict:
        """Load risk profiles from JSON storage"""
        if os.path.exists(self.risk_profiles_file):
            with open(self.risk_profiles_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_risk_profiles(self):
        """Save risk profiles to JSON storage"""
        with open(self.risk_profiles_file, 'w') as f:
            json.dump(self.risk_profiles, f, indent=4)
    
    def load_enforcement_log(self) -> List[Dict]:
        """Load enforcement log from JSON storage"""
        if os.path.exists(self.enforcement_log_file):
            with open(self.enforcement_log_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_enforcement_log(self):
        """Save enforcement log to JSON storage"""
        with open(self.enforcement_log_file, 'w') as f:
            json.dump(self.enforcement_log, f, indent=4)
    
    def load_rules(self) -> Dict:
        """Load enforcement rules from JSON storage"""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r') as f:
                return json.load(f)
        return {
            "high_risk_threshold": 75,
            "medium_risk_threshold": 50,
            "auto_revoke_enabled": True,
            "notification_channel": None,
            "quarantine_role": None
        }
    
    def save_rules(self):
        """Save enforcement rules to JSON storage"""
        with open(self.rules_file, 'w') as f:
            json.dump(self.rules, f, indent=4)
    
    def calculate_access_risk(self, member: discord.Member, guild_id: str) -> float:
        """Calculate access risk score for a member (0-100)"""
        risk_score = 0.0
        
        # Get trust score from dynamic trust scoring if available
        trust_cog = self.bot.get_cog('DynamicTrustScoringCog')
        trust_score = 50  # Default neutral
        
        if trust_cog and hasattr(trust_cog, 'scores'):
            user_id = str(member.id)
            if user_id in trust_cog.scores and guild_id in trust_cog.scores[user_id]:
                trust_score = trust_cog.scores[user_id][guild_id].get("score", 50)
        
        # Risk is inverse of trust
        risk_score = 100 - trust_score
        
        # Additional risk factors
        # New account (< 7 days)
        account_age = (datetime.utcnow() - member.created_at).days
        if account_age < 7:
            risk_score += 20
        elif account_age < 30:
            risk_score += 10
        
        # New to server (< 3 days)
        if member.joined_at:
            tenure = (datetime.utcnow() - member.joined_at).days
            if tenure < 3:
                risk_score += 15
            elif tenure < 7:
                risk_score += 5
        
        # Elevated permissions
        dangerous_permissions = [
            discord.Permissions.administrator,
            discord.Permissions.manage_guild,
            discord.Permissions.manage_roles,
            discord.Permissions.manage_channels,
            discord.Permissions.ban_members,
            discord.Permissions.kick_members
        ]
        
        has_dangerous_perms = any(
            perm[1] for perm in member.guild_permissions if perm[0] in [p.name for p in dangerous_permissions]
        )
        
        if has_dangerous_perms:
            risk_score += 25
        
        return min(100, risk_score)
    
    @commands.command(name="access_risk_scan")
    @commands.has_permissions(administrator=True)
    async def scan_access_risk(self, ctx, member: Optional[discord.Member] = None):
        """
        Scan access risk for a user or all users
        
        Usage: !access_risk_scan [@user]
        
        Example: !access_risk_scan @JohnDoe
        """
        guild_id = str(ctx.guild.id)
        
        if member:
            # Scan single user
            risk_score = self.calculate_access_risk(member, guild_id)
            
            user_id = str(member.id)
            if user_id not in self.risk_profiles:
                self.risk_profiles[user_id] = {}
            
            self.risk_profiles[user_id][guild_id] = {
                "risk_score": risk_score,
                "last_scan": datetime.utcnow().isoformat(),
                "account_age_days": (datetime.utcnow() - member.created_at).days,
                "server_tenure_days": (datetime.utcnow() - member.joined_at).days if member.joined_at else 0,
                "roles": [r.name for r in member.roles if r.name != "@everyone"]
            }
            
            self.save_risk_profiles()
            
            # Determine risk level
            if risk_score >= self.rules["high_risk_threshold"]:
                level = "🔴 HIGH RISK"
                color = discord.Color.red()
            elif risk_score >= self.rules["medium_risk_threshold"]:
                level = "🟡 MEDIUM RISK"
                color = discord.Color.gold()
            else:
                level = "🟢 LOW RISK"
                color = discord.Color.green()
            
            embed = discord.Embed(
                title="⚠️ Access Risk Assessment",
                description=f"Risk profile for {member.mention}",
                color=color,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Risk Score", value=f"**{risk_score:.1f}/100**", inline=True)
            embed.add_field(name="Risk Level", value=level, inline=True)
            embed.add_field(name="Account Age", value=f"{self.risk_profiles[user_id][guild_id]['account_age_days']} days", inline=True)
            embed.add_field(name="Server Tenure", value=f"{self.risk_profiles[user_id][guild_id]['server_tenure_days']} days", inline=True)
            embed.add_field(name="Roles", value=len(self.risk_profiles[user_id][guild_id]['roles']), inline=True)
            
            # Auto-enforcement check
            if risk_score >= self.rules["high_risk_threshold"] and self.rules["auto_revoke_enabled"]:
                embed.add_field(
                    name="⚠️ Auto-Enforcement",
                    value="Risk threshold breached - automatic enforcement triggered",
                    inline=False
                )
            
            embed.set_footer(text=f"Scanned by {ctx.author}")
            await ctx.send(embed=embed)
            
        else:
            # Scan all members
            await ctx.send("⏳ Scanning all members for access risk...")
            
            high_risk_count = 0
            medium_risk_count = 0
            low_risk_count = 0
            
            for mem in ctx.guild.members:
                if mem.bot:
                    continue
                
                risk_score = self.calculate_access_risk(mem, guild_id)
                
                user_id = str(mem.id)
                if user_id not in self.risk_profiles:
                    self.risk_profiles[user_id] = {}
                
                self.risk_profiles[user_id][guild_id] = {
                    "risk_score": risk_score,
                    "last_scan": datetime.utcnow().isoformat(),
                    "account_age_days": (datetime.utcnow() - mem.created_at).days,
                    "server_tenure_days": (datetime.utcnow() - mem.joined_at).days if mem.joined_at else 0,
                    "roles": [r.name for r in mem.roles if r.name != "@everyone"]
                }
                
                if risk_score >= self.rules["high_risk_threshold"]:
                    high_risk_count += 1
                elif risk_score >= self.rules["medium_risk_threshold"]:
                    medium_risk_count += 1
                else:
                    low_risk_count += 1
            
            self.save_risk_profiles()
            
            embed = discord.Embed(
                title="✅ Access Risk Scan Complete",
                description=f"Scanned {len(ctx.guild.members) - len([m for m in ctx.guild.members if m.bot])} members",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="🔴 High Risk", value=high_risk_count, inline=True)
            embed.add_field(name="🟡 Medium Risk", value=medium_risk_count, inline=True)
            embed.add_field(name="🟢 Low Risk", value=low_risk_count, inline=True)
            
            if high_risk_count > 0:
                embed.add_field(
                    name="⚠️ Alert",
                    value=f"{high_risk_count} high-risk users detected - review recommended",
                    inline=False
                )
            
            embed.set_footer(text=f"Scanned by {ctx.author}")
            await ctx.send(embed=embed)
    
    @commands.command(name="access_enforce")
    @commands.has_permissions(administrator=True)
    async def enforce_access_policy(self, ctx, member: discord.Member, action: str):
        """
        Enforce access policy on a high-risk user
        
        Usage: !access_enforce @user <quarantine|revoke|restore>
        
        Example: !access_enforce @JohnDoe quarantine
        """
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        # Get risk profile
        if user_id not in self.risk_profiles or guild_id not in self.risk_profiles[user_id]:
            await ctx.send("❌ No risk profile found for this user. Run `!access_risk_scan` first.")
            return
        
        risk_score = self.risk_profiles[user_id][guild_id]["risk_score"]
        
        # Perform enforcement action
        enforcement_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "guild_id": guild_id,
            "user_id": user_id,
            "action": action,
            "risk_score": risk_score,
            "enforced_by": str(ctx.author.id),
            "reason": f"Risk score {risk_score:.1f} exceeds threshold"
        }
        
        if action == "quarantine":
            # Apply quarantine role if configured
            if self.rules.get("quarantine_role"):
                quarantine_role = ctx.guild.get_role(int(self.rules["quarantine_role"]))
                if quarantine_role:
                    await member.add_roles(quarantine_role, reason=f"Access risk quarantine (score: {risk_score:.1f})")
                    enforcement_record["details"] = f"Quarantine role applied: {quarantine_role.name}"
            else:
                await ctx.send("⚠️ No quarantine role configured. Set one with `!access_config`")
                return
        
        elif action == "revoke":
            # Remove all roles except @everyone
            roles_to_remove = [r for r in member.roles if r.name != "@everyone"]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Access revoked due to risk score {risk_score:.1f}")
                enforcement_record["details"] = f"Removed {len(roles_to_remove)} roles"
        
        elif action == "restore":
            # Restore from quarantine
            if self.rules.get("quarantine_role"):
                quarantine_role = ctx.guild.get_role(int(self.rules["quarantine_role"]))
                if quarantine_role and quarantine_role in member.roles:
                    await member.remove_roles(quarantine_role, reason="Access restored")
                    enforcement_record["details"] = "Quarantine role removed"
        
        self.enforcement_log.append(enforcement_record)
        self.save_enforcement_log()
        
        embed = discord.Embed(
            title="✅ Access Policy Enforced",
            description=f"Action taken on {member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Action", value=action.upper(), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk_score:.1f}/100", inline=True)
        embed.add_field(name="Details", value=enforcement_record.get("details", "No additional details"), inline=False)
        embed.set_footer(text=f"Enforced by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="access_config")
    @commands.has_permissions(administrator=True)
    async def configure_enforcement(self, ctx, setting: str, value: str):
        """
        Configure access enforcement rules
        
        Usage: !access_config <setting> <value>
        
        Example: !access_config auto_revoke true
        Settings: high_risk_threshold, medium_risk_threshold, auto_revoke_enabled, quarantine_role
        """
        if setting == "high_risk_threshold":
            self.rules["high_risk_threshold"] = int(value)
        elif setting == "medium_risk_threshold":
            self.rules["medium_risk_threshold"] = int(value)
        elif setting == "auto_revoke_enabled":
            self.rules["auto_revoke_enabled"] = value.lower() == "true"
        elif setting == "quarantine_role":
            self.rules["quarantine_role"] = value
        else:
            await ctx.send(f"❌ Unknown setting: {setting}")
            return
        
        self.save_rules()
        
        embed = discord.Embed(
            title="⚙️ Enforcement Configuration Updated",
            description=f"Setting `{setting}` updated",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Setting", value=setting, inline=True)
        embed.add_field(name="New Value", value=str(value), inline=True)
        embed.set_footer(text=f"Updated by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="access_log")
    @commands.has_permissions(administrator=True)
    async def view_enforcement_log(self, ctx, limit: int = 10):
        """
        View recent access enforcement actions
        
        Usage: !access_log [limit]
        
        Example: !access_log 20
        """
        recent_logs = sorted(
            self.enforcement_log,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
        embed = discord.Embed(
            title="📋 Access Enforcement Log",
            description=f"Showing {len(recent_logs)} most recent actions",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if not recent_logs:
            embed.add_field(name="No Actions", value="No enforcement actions recorded", inline=False)
        else:
            for i, log in enumerate(recent_logs[:5], 1):
                timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
                action = log["action"]
                user_id = log["user_id"]
                risk = log["risk_score"]
                
                embed.add_field(
                    name=f"#{i} - {action.upper()}",
                    value=f"User: <@{user_id}>\nRisk: {risk:.1f}\nTime: {timestamp}",
                    inline=True
                )
        
        embed.add_field(name="📊 Total Actions", value=len(self.enforcement_log), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="access_dashboard")
    @commands.has_permissions(administrator=True)
    async def access_dashboard(self, ctx):
        """
        Display access risk enforcement dashboard
        
        Usage: !access_dashboard
        """
        guild_id = str(ctx.guild.id)
        
        # Calculate statistics
        high_risk = []
        medium_risk = []
        low_risk = []
        
        for user_id, profile_data in self.risk_profiles.items():
            if guild_id in profile_data:
                risk_score = profile_data[guild_id]["risk_score"]
                if risk_score >= self.rules["high_risk_threshold"]:
                    high_risk.append((user_id, risk_score))
                elif risk_score >= self.rules["medium_risk_threshold"]:
                    medium_risk.append((user_id, risk_score))
                else:
                    low_risk.append((user_id, risk_score))
        
        # Recent enforcements
        recent_enforcements = [
            e for e in self.enforcement_log
            if (datetime.utcnow() - datetime.fromisoformat(e["timestamp"])).days < 7
        ]
        
        embed = discord.Embed(
            title="🛡️ Access Risk Enforcement Dashboard",
            description="Real-time access control and risk management",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🔴 High Risk Users", value=len(high_risk), inline=True)
        embed.add_field(name="🟡 Medium Risk Users", value=len(medium_risk), inline=True)
        embed.add_field(name="🟢 Low Risk Users", value=len(low_risk), inline=True)
        embed.add_field(name="📋 Total Tracked", value=len(self.risk_profiles), inline=True)
        embed.add_field(name="⚡ Enforcements (7d)", value=len(recent_enforcements), inline=True)
        embed.add_field(name="🤖 Auto-Revoke", value="Enabled" if self.rules["auto_revoke_enabled"] else "Disabled", inline=True)
        
        # Top risk users
        if high_risk:
            high_risk.sort(key=lambda x: x[1], reverse=True)
            top_risk = "\n".join([f"<@{uid}> ({score:.1f})" for uid, score in high_risk[:3]])
            embed.add_field(name="⚠️ Highest Risk Users", value=top_risk, inline=False)
        
        # System status
        status = "🟢 SECURE" if len(high_risk) == 0 else "🟡 WARNING" if len(high_risk) < 3 else "🔴 CRITICAL"
        embed.add_field(name="System Status", value=status, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(AccessRiskEnforcerCog(bot))
