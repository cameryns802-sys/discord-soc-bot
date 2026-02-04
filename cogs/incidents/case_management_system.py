"""
Case Management & Incident Lifecycle: Full case tracking, escalation, resolution, evidence linking.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class CaseManagementSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/case_management.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "cases": {},
            "case_counter": 1,
            "escalations": [],
            "evidence_vault": {},
            "case_templates": {},
            "resolution_notes": {},
            "case_correlations": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def generate_case_id(self):
        """Generate unique case ID."""
        case_id = f"CASE-{self.data['case_counter']:05d}"
        self.data['case_counter'] += 1
        return case_id

    @commands.command(name="create_case")
    async def create_case(self, ctx, severity: str, *, title: str):
        """Create a new incident case."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        valid_severity = ["critical", "high", "medium", "low"]
        if severity.lower() not in valid_severity:
            await ctx.send(f"❌ Invalid severity. Use: {', '.join(valid_severity)}")
            return
        
        case_id = self.generate_case_id()
        
        case = {
            "case_id": case_id,
            "title": title,
            "severity": severity.upper(),
            "status": "OPEN",
            "created_by": str(ctx.author.id),
            "created_at": get_now_pst().isoformat(),
            "assigned_to": None,
            "evidence": [],
            "timeline": [{
                "timestamp": get_now_pst().isoformat(),
                "action": "CASE_CREATED",
                "user": str(ctx.author.id),
                "details": f"Case created with severity {severity.upper()}"
            }],
            "escalation_level": 0,
            "tags": [],
            "related_cases": []
        }
        
        self.data["cases"][case_id] = case
        self.save_data(self.data)
        
        # Color based on severity
        color_map = {"CRITICAL": discord.Color.red(), "HIGH": discord.Color.orange(), 
                     "MEDIUM": discord.Color.gold(), "LOW": discord.Color.blue()}
        
        embed = discord.Embed(
            title=f"🎫 Case Created: {case_id}",
            description=title,
            color=color_map[severity.upper()]
        )
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Status", value="OPEN", inline=True)
        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Assigned To", value="Unassigned", inline=True)
        embed.set_footer(text=f"Use !case_details {case_id} to view full details")
        
        await ctx.send(embed=embed)

    @commands.command(name="assign_case")
    async def assign_case(self, ctx, case_id: str, member: discord.Member):
        """Assign a case to a team member."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id not in self.data["cases"]:
            await ctx.send(f"❌ Case {case_id} not found.")
            return
        
        case = self.data["cases"][case_id]
        case["assigned_to"] = str(member.id)
        case["timeline"].append({
            "timestamp": get_now_pst().isoformat(),
            "action": "ASSIGNED",
            "user": str(ctx.author.id),
            "details": f"Case assigned to {member.name}"
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"✅ Case Assigned: {case_id}",
            description=f"Assigned to: {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Title", value=case["title"], inline=False)
        embed.add_field(name="Severity", value=case["severity"], inline=True)
        
        await ctx.send(embed=embed)
        
        # DM assignee
        try:
            await member.send(f"📋 You have been assigned to case {case_id}: {case['title']}")
        except:
            pass

    @commands.command(name="escalate_case")
    async def escalate_case(self, ctx, case_id: str, *, reason: str):
        """Escalate a case to higher priority."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id not in self.data["cases"]:
            await ctx.send(f"❌ Case {case_id} not found.")
            return
        
        case = self.data["cases"][case_id]
        case["escalation_level"] += 1
        
        # Auto-upgrade severity on escalation
        severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        current_idx = severity_order.index(case["severity"])
        if current_idx < len(severity_order) - 1:
            case["severity"] = severity_order[current_idx + 1]
        
        escalation = {
            "case_id": case_id,
            "escalated_by": str(ctx.author.id),
            "escalated_at": get_now_pst().isoformat(),
            "reason": reason,
            "new_severity": case["severity"],
            "escalation_level": case["escalation_level"]
        }
        
        self.data["escalations"].append(escalation)
        
        case["timeline"].append({
            "timestamp": get_now_pst().isoformat(),
            "action": "ESCALATED",
            "user": str(ctx.author.id),
            "details": f"Escalated to level {case['escalation_level']}: {reason}"
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"⚠️ Case Escalated: {case_id}",
            description=reason,
            color=discord.Color.red()
        )
        embed.add_field(name="New Severity", value=case["severity"], inline=True)
        embed.add_field(name="Escalation Level", value=str(case["escalation_level"]), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="add_evidence")
    async def add_evidence(self, ctx, case_id: str, evidence_type: str, *, description: str):
        """Add evidence to a case."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id not in self.data["cases"]:
            await ctx.send(f"❌ Case {case_id} not found.")
            return
        
        evidence_id = f"EVD-{len(self.data['evidence_vault']) + 1:04d}"
        
        evidence = {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "type": evidence_type,
            "description": description,
            "submitted_by": str(ctx.author.id),
            "submitted_at": get_now_pst().isoformat(),
            "attachments": [att.url for att in ctx.message.attachments],
            "integrity_hash": "SHA256:placeholder",  # Would compute real hash
            "chain_of_custody": [{
                "timestamp": get_now_pst().isoformat(),
                "action": "COLLECTED",
                "user": str(ctx.author.id)
            }]
        }
        
        self.data["evidence_vault"][evidence_id] = evidence
        self.data["cases"][case_id]["evidence"].append(evidence_id)
        
        self.data["cases"][case_id]["timeline"].append({
            "timestamp": get_now_pst().isoformat(),
            "action": "EVIDENCE_ADDED",
            "user": str(ctx.author.id),
            "details": f"Evidence {evidence_id} added: {evidence_type}"
        })
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"📎 Evidence Added: {evidence_id}",
            description=description,
            color=discord.Color.blue()
        )
        embed.add_field(name="Case", value=case_id, inline=True)
        embed.add_field(name="Type", value=evidence_type, inline=True)
        embed.add_field(name="Attachments", value=str(len(ctx.message.attachments)), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="resolve_case")
    async def resolve_case(self, ctx, case_id: str, *, resolution: str):
        """Resolve and close a case."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id not in self.data["cases"]:
            await ctx.send(f"❌ Case {case_id} not found.")
            return
        
        case = self.data["cases"][case_id]
        case["status"] = "RESOLVED"
        case["resolved_by"] = str(ctx.author.id)
        case["resolved_at"] = get_now_pst().isoformat()
        case["resolution"] = resolution
        
        case["timeline"].append({
            "timestamp": get_now_pst().isoformat(),
            "action": "RESOLVED",
            "user": str(ctx.author.id),
            "details": f"Case resolved: {resolution}"
        })
        
        self.data["resolution_notes"][case_id] = {
            "resolution": resolution,
            "resolved_by": str(ctx.author.id),
            "resolved_at": get_now_pst().isoformat()
        }
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"✅ Case Resolved: {case_id}",
            description=resolution,
            color=discord.Color.green()
        )
        embed.add_field(name="Title", value=case["title"], inline=False)
        embed.add_field(name="Final Severity", value=case["severity"], inline=True)
        embed.add_field(name="Evidence Count", value=str(len(case["evidence"])), inline=True)
        embed.add_field(name="Total Timeline Events", value=str(len(case["timeline"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="case_details")
    async def case_details(self, ctx, case_id: str):
        """View full case details."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id not in self.data["cases"]:
            await ctx.send(f"❌ Case {case_id} not found.")
            return
        
        case = self.data["cases"][case_id]
        
        color_map = {"CRITICAL": discord.Color.red(), "HIGH": discord.Color.orange(), 
                     "MEDIUM": discord.Color.gold(), "LOW": discord.Color.blue()}
        
        embed = discord.Embed(
            title=f"📋 Case Details: {case_id}",
            description=case["title"],
            color=color_map.get(case["severity"], discord.Color.blue())
        )
        
        embed.add_field(name="Status", value=case["status"], inline=True)
        embed.add_field(name="Severity", value=case["severity"], inline=True)
        embed.add_field(name="Escalation Level", value=str(case["escalation_level"]), inline=True)
        
        created_by = await self.bot.fetch_user(int(case["created_by"]))
        embed.add_field(name="Created By", value=created_by.mention if created_by else "Unknown", inline=True)
        embed.add_field(name="Created At", value=case["created_at"][:19], inline=True)
        
        if case["assigned_to"]:
            assigned = await self.bot.fetch_user(int(case["assigned_to"]))
            embed.add_field(name="Assigned To", value=assigned.mention if assigned else "Unknown", inline=True)
        
        embed.add_field(name="Evidence Items", value=str(len(case["evidence"])), inline=True)
        embed.add_field(name="Timeline Events", value=str(len(case["timeline"])), inline=True)
        
        if case.get("resolved_at"):
            embed.add_field(name="Resolved At", value=case["resolved_at"][:19], inline=True)
        
        if case.get("tags"):
            embed.add_field(name="Tags", value=", ".join(case["tags"]), inline=False)
        
        embed.set_footer(text="Use !case_timeline for full event history")
        
        await ctx.send(embed=embed)

    @commands.command(name="list_cases")
    async def list_cases(self, ctx, status: str = "all"):
        """List all cases (optional filter by status)."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        cases = self.data["cases"]
        
        if status.lower() != "all":
            cases = {k: v for k, v in cases.items() if v["status"].lower() == status.lower()}
        
        embed = discord.Embed(
            title="📋 Case List",
            description=f"Filter: {status.upper()}",
            color=discord.Color.blue()
        )
        
        if not cases:
            embed.add_field(name="No Cases", value="No cases match the filter", inline=False)
        else:
            for case_id, case in list(cases.items())[:10]:
                embed.add_field(
                    name=f"{case_id} - {case['severity']}",
                    value=f"{case['title'][:50]}... | Status: {case['status']}",
                    inline=False
                )
        
        embed.set_footer(text=f"Total: {len(cases)} cases | Showing first 10")
        
        await ctx.send(embed=embed)

    @commands.command(name="correlate_cases")
    async def correlate_cases(self, ctx, case_id1: str, case_id2: str, *, reason: str):
        """Link two related cases."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if case_id1 not in self.data["cases"] or case_id2 not in self.data["cases"]:
            await ctx.send("❌ One or both cases not found.")
            return
        
        correlation = {
            "case1": case_id1,
            "case2": case_id2,
            "reason": reason,
            "correlated_by": str(ctx.author.id),
            "correlated_at": get_now_pst().isoformat()
        }
        
        self.data["case_correlations"].append(correlation)
        self.data["cases"][case_id1]["related_cases"].append(case_id2)
        self.data["cases"][case_id2]["related_cases"].append(case_id1)
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🔗 Cases Correlated",
            description=reason,
            color=discord.Color.purple()
        )
        embed.add_field(name="Case 1", value=case_id1, inline=True)
        embed.add_field(name="Case 2", value=case_id2, inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CaseManagementSystemCog(bot))
