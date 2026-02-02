"""
Zero-Trust Policy Engine
Continuous verification, dynamic policy rules, context-aware access decisions, policy violation tracking
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

class ZeroTrustPolicyEngineCog(commands.Cog):
    """
    Zero-Trust Policy Engine
    
    Implements zero-trust security model with continuous verification,
    dynamic policy rules, and context-aware access decisions.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/zero_trust"
        os.makedirs(self.data_dir, exist_ok=True)
        self.policies_file = os.path.join(self.data_dir, "policies.json")
        self.violations_file = os.path.join(self.data_dir, "violations.json")
        self.verifications_file = os.path.join(self.data_dir, "verifications.json")
        self.policies = self.load_policies()
        self.violations = self.load_violations()
        self.verifications = self.load_verifications()
        
    def load_policies(self) -> Dict:
        """Load zero-trust policies from JSON storage"""
        if os.path.exists(self.policies_file):
            with open(self.policies_file, 'r') as f:
                return json.load(f)
        return {
            "global_policies": [],
            "role_policies": {},
            "channel_policies": {},
            "context_rules": []
        }
    
    def save_policies(self):
        """Save zero-trust policies to JSON storage"""
        with open(self.policies_file, 'w') as f:
            json.dump(self.policies, f, indent=4)
    
    def load_violations(self) -> List[Dict]:
        """Load policy violations from JSON storage"""
        if os.path.exists(self.violations_file):
            with open(self.violations_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_violations(self):
        """Save policy violations to JSON storage"""
        with open(self.violations_file, 'w') as f:
            json.dump(self.violations, f, indent=4)
    
    def load_verifications(self) -> Dict:
        """Load verification logs from JSON storage"""
        if os.path.exists(self.verifications_file):
            with open(self.verifications_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_verifications(self):
        """Save verification logs to JSON storage"""
        with open(self.verifications_file, 'w') as f:
            json.dump(self.verifications, f, indent=4)
    
    @commands.command(name="zt_add_policy")
    @commands.has_permissions(administrator=True)
    async def add_policy(self, ctx, policy_type: str, *, policy_rules: str):
        """
        Add a new zero-trust policy
        
        Usage: !zt_add_policy <global|role|channel|context> <policy_rules>
        
        Example: !zt_add_policy global verify_every_10m=true,max_failures=3
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.policies["global_policies"]:
            self.policies["global_policies"] = []
        
        # Parse policy rules
        rules = {}
        for rule in policy_rules.split(','):
            if '=' in rule:
                key, value = rule.split('=', 1)
                rules[key.strip()] = value.strip()
        
        policy = {
            "id": len(self.policies["global_policies"]) + 1,
            "type": policy_type,
            "rules": rules,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": str(ctx.author.id),
            "active": True
        }
        
        if policy_type == "global":
            self.policies["global_policies"].append(policy)
        elif policy_type == "role":
            if guild_id not in self.policies["role_policies"]:
                self.policies["role_policies"][guild_id] = []
            self.policies["role_policies"][guild_id].append(policy)
        elif policy_type == "channel":
            if guild_id not in self.policies["channel_policies"]:
                self.policies["channel_policies"][guild_id] = []
            self.policies["channel_policies"][guild_id].append(policy)
        elif policy_type == "context":
            self.policies["context_rules"].append(policy)
        
        self.save_policies()
        
        embed = discord.Embed(
            title="✅ Zero-Trust Policy Added",
            description=f"New {policy_type} policy created",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Policy ID", value=f"#{policy['id']}", inline=True)
        embed.add_field(name="Type", value=policy_type.upper(), inline=True)
        embed.add_field(name="Rules", value=f"```json\n{json.dumps(rules, indent=2)}\n```", inline=False)
        embed.set_footer(text=f"Created by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="zt_list_policies")
    @commands.has_permissions(administrator=True)
    async def list_policies(self, ctx, policy_type: Optional[str] = None):
        """
        List all zero-trust policies
        
        Usage: !zt_list_policies [policy_type]
        
        Example: !zt_list_policies global
        """
        embed = discord.Embed(
            title="🔒 Zero-Trust Policies",
            description="Current active policies",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Global policies
        if not policy_type or policy_type == "global":
            global_count = len(self.policies["global_policies"])
            embed.add_field(
                name="🌐 Global Policies",
                value=f"{global_count} active policies",
                inline=True
            )
        
        # Role policies
        if not policy_type or policy_type == "role":
            role_count = sum(len(v) for v in self.policies["role_policies"].values())
            embed.add_field(
                name="👥 Role Policies",
                value=f"{role_count} active policies",
                inline=True
            )
        
        # Channel policies
        if not policy_type or policy_type == "channel":
            channel_count = sum(len(v) for v in self.policies["channel_policies"].values())
            embed.add_field(
                name="📢 Channel Policies",
                value=f"{channel_count} active policies",
                inline=True
            )
        
        # Context rules
        if not policy_type or policy_type == "context":
            context_count = len(self.policies["context_rules"])
            embed.add_field(
                name="🎯 Context Rules",
                value=f"{context_count} active rules",
                inline=True
            )
        
        # Show recent policies
        all_policies = []
        all_policies.extend(self.policies["global_policies"])
        for policies in self.policies["role_policies"].values():
            all_policies.extend(policies)
        for policies in self.policies["channel_policies"].values():
            all_policies.extend(policies)
        all_policies.extend(self.policies["context_rules"])
        
        recent_policies = sorted(all_policies, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        
        if recent_policies:
            policy_list = "\n".join([
                f"**#{p['id']}** ({p['type']}) - {len(p['rules'])} rules"
                for p in recent_policies
            ])
            embed.add_field(name="📋 Recent Policies", value=policy_list, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="zt_verify")
    @commands.has_permissions(administrator=True)
    async def verify_user(self, ctx, member: discord.Member):
        """
        Perform continuous verification on a user
        
        Usage: !zt_verify @user
        
        Example: !zt_verify @JohnDoe
        """
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        # Check verification history
        if user_id not in self.verifications:
            self.verifications[user_id] = []
        
        # Perform verification checks
        checks = {
            "account_age": (datetime.utcnow() - member.created_at).days,
            "server_tenure": (datetime.utcnow() - member.joined_at).days if member.joined_at else 0,
            "roles": len(member.roles),
            "verification_status": "verified" if member.verified else "unverified",
            "bot_account": member.bot,
            "premium_subscriber": member.premium_since is not None
        }
        
        # Calculate trust score (0-100)
        trust_score = 50  # Base score
        if checks["account_age"] > 30:
            trust_score += 10
        if checks["server_tenure"] > 7:
            trust_score += 10
        if checks["roles"] > 1:
            trust_score += 10
        if checks["verification_status"] == "verified":
            trust_score += 10
        if not checks["bot_account"]:
            trust_score += 10
        
        verification = {
            "timestamp": datetime.utcnow().isoformat(),
            "guild_id": guild_id,
            "checks": checks,
            "trust_score": min(trust_score, 100),
            "verified_by": str(ctx.author.id),
            "status": "passed" if trust_score >= 60 else "failed"
        }
        
        self.verifications[user_id].append(verification)
        self.save_verifications()
        
        # Create embed
        color = discord.Color.green() if verification["status"] == "passed" else discord.Color.red()
        embed = discord.Embed(
            title="🔍 Zero-Trust Verification",
            description=f"Verification result for {member.mention}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Trust Score", value=f"**{trust_score}/100**", inline=True)
        embed.add_field(name="Status", value=verification["status"].upper(), inline=True)
        embed.add_field(name="Account Age", value=f"{checks['account_age']} days", inline=True)
        embed.add_field(name="Server Tenure", value=f"{checks['server_tenure']} days", inline=True)
        embed.add_field(name="Roles", value=checks['roles'], inline=True)
        embed.add_field(name="Verified", value=checks['verification_status'], inline=True)
        
        embed.set_footer(text=f"Verified by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="zt_violations")
    @commands.has_permissions(administrator=True)
    async def list_violations(self, ctx, limit: int = 10):
        """
        List recent zero-trust policy violations
        
        Usage: !zt_violations [limit]
        
        Example: !zt_violations 20
        """
        recent_violations = sorted(
            self.violations,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        embed = discord.Embed(
            title="⚠️ Zero-Trust Policy Violations",
            description=f"Showing {len(recent_violations)} most recent violations",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        if not recent_violations:
            embed.add_field(
                name="No Violations",
                value="No policy violations recorded",
                inline=False
            )
        else:
            for i, violation in enumerate(recent_violations[:5], 1):
                user_id = violation.get("user_id", "Unknown")
                policy_id = violation.get("policy_id", "Unknown")
                severity = violation.get("severity", "medium")
                
                embed.add_field(
                    name=f"#{i} - Policy {policy_id}",
                    value=f"User: <@{user_id}>\nSeverity: {severity.upper()}\nTime: {violation.get('timestamp', 'Unknown')[:19]}",
                    inline=True
                )
        
        total_violations = len(self.violations)
        embed.add_field(
            name="📊 Statistics",
            value=f"Total violations: {total_violations}",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="zt_enforce")
    @commands.has_permissions(administrator=True)
    async def enforce_policy(self, ctx, policy_id: int, member: discord.Member):
        """
        Manually enforce a zero-trust policy on a user
        
        Usage: !zt_enforce <policy_id> @user
        
        Example: !zt_enforce 1 @JohnDoe
        """
        # Find policy
        policy = None
        for p in self.policies["global_policies"]:
            if p["id"] == policy_id:
                policy = p
                break
        
        if not policy:
            embed = discord.Embed(
                title="❌ Policy Not Found",
                description=f"No policy found with ID {policy_id}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Record enforcement
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "guild_id": str(ctx.guild.id),
            "user_id": str(member.id),
            "policy_id": policy_id,
            "policy_type": policy["type"],
            "enforced_by": str(ctx.author.id),
            "severity": "high",
            "action": "manual_enforcement"
        }
        
        self.violations.append(violation)
        self.save_violations()
        
        embed = discord.Embed(
            title="✅ Policy Enforced",
            description=f"Zero-trust policy enforced on {member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Policy ID", value=f"#{policy_id}", inline=True)
        embed.add_field(name="Policy Type", value=policy["type"].upper(), inline=True)
        embed.add_field(name="Target User", value=member.mention, inline=True)
        embed.add_field(
            name="Policy Rules",
            value=f"```json\n{json.dumps(policy['rules'], indent=2)}\n```",
            inline=False
        )
        embed.set_footer(text=f"Enforced by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="zt_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """
        Display zero-trust security dashboard
        
        Usage: !zt_dashboard
        """
        # Calculate statistics
        total_policies = len(self.policies["global_policies"])
        total_policies += sum(len(v) for v in self.policies["role_policies"].values())
        total_policies += sum(len(v) for v in self.policies["channel_policies"].values())
        total_policies += len(self.policies["context_rules"])
        
        total_violations = len(self.violations)
        total_verifications = sum(len(v) for v in self.verifications.values())
        
        # Recent violations (last 24h)
        now = datetime.utcnow()
        recent_violations = [
            v for v in self.violations
            if (now - datetime.fromisoformat(v["timestamp"])).days < 1
        ]
        
        embed = discord.Embed(
            title="🔒 Zero-Trust Security Dashboard",
            description="Continuous verification and policy enforcement status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📋 Active Policies", value=total_policies, inline=True)
        embed.add_field(name="⚠️ Total Violations", value=total_violations, inline=True)
        embed.add_field(name="✅ Total Verifications", value=total_verifications, inline=True)
        embed.add_field(name="🔴 Last 24h Violations", value=len(recent_violations), inline=True)
        embed.add_field(name="🟢 Policy Compliance", value=f"{max(0, 100 - len(recent_violations) * 5)}%", inline=True)
        embed.add_field(name="🎯 Trust Model", value="Zero-Trust", inline=True)
        
        # Status indicator
        status = "🟢 HEALTHY" if len(recent_violations) < 5 else "🟡 WARNING" if len(recent_violations) < 10 else "🔴 CRITICAL"
        embed.add_field(name="System Status", value=status, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(ZeroTrustPolicyEngineCog(bot))
