# Auto-Remediation System: Automatically execute recovery steps
import discord
from discord.ext import commands
from datetime import datetime
import json
import os
import asyncio

class AutoRemediationSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remediation_plans = {}  # plan_id: plan_data
        self.plan_counter = 0
        self.execution_history = {}
        self.data_file = "data/remediation.json"
        self.load_plans()

    def load_plans(self):
        """Load remediation plans from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.remediation_plans = data.get('plans', {})
                    self.plan_counter = data.get('counter', 0)
                    self.execution_history = data.get('history', {})
            except:
                self.remediation_plans = {}

    def save_plans(self):
        """Save remediation plans to JSON file."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'plans': self.remediation_plans,
                'counter': self.plan_counter,
                'history': self.execution_history
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createremediationplan(self, ctx, name: str, *, description: str):
        """Create a remediation plan. Usage: !createremediationplan PlanName description"""
        self.plan_counter += 1
        plan_id = self.plan_counter
        
        plan_data = {
            "id": plan_id,
            "name": name,
            "description": description,
            "status": "draft",
            "steps": [],
            "auto_execute": False,
            "created_by": ctx.author.id,
            "created_at": datetime.utcnow().isoformat(),
            "execution_count": 0,
            "last_executed": None
        }
        
        self.remediation_plans[str(plan_id)] = plan_data
        self.save_plans()
        
        embed = discord.Embed(
            title=f"✅ Remediation Plan #{plan_id} Created",
            description=name,
            color=discord.Color.green()
        )
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Status", value="DRAFT", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addremediationstep(self, ctx, plan_id: int, step_num: int, *, action: str):
        """Add step to remediation plan. Usage: !addremediationstep <id> <step> action"""
        plan_key = str(plan_id)
        if plan_key not in self.remediation_plans:
            await ctx.send("❌ Plan not found.")
            return
        
        plan = self.remediation_plans[plan_key]
        
        step_data = {
            "step": step_num,
            "action": action,
            "created_at": datetime.utcnow().isoformat()
        }
        
        plan["steps"].append(step_data)
        plan["steps"] = sorted(plan["steps"], key=lambda x: x["step"])
        self.save_plans()
        
        await ctx.send(f"✅ Step {step_num} added to plan #{plan_id}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def publishremediationplan(self, ctx, plan_id: int):
        """Publish remediation plan. Usage: !publishremediationplan <id>"""
        plan_key = str(plan_id)
        if plan_key not in self.remediation_plans:
            await ctx.send("❌ Plan not found.")
            return
        
        plan = self.remediation_plans[plan_key]
        if not plan["steps"]:
            await ctx.send("❌ Cannot publish plan without steps.")
            return
        
        plan["status"] = "published"
        plan["published_at"] = datetime.utcnow().isoformat()
        self.save_plans()
        
        embed = discord.Embed(
            title=f"✅ Plan #{plan_id} Published",
            description=plan["name"],
            color=discord.Color.green()
        )
        embed.add_field(name="Steps", value=str(len(plan["steps"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def executeremediationplan(self, ctx, plan_id: int):
        """Execute a remediation plan. Usage: !executeremediationplan <id>"""
        plan_key = str(plan_id)
        if plan_key not in self.remediation_plans:
            await ctx.send("❌ Plan not found.")
            return
        
        plan = self.remediation_plans[plan_key]
        if plan["status"] != "published":
            await ctx.send("❌ Plan is not published.")
            return
        
        # Log execution
        exec_id = f"exec_{plan_id}_{datetime.utcnow().timestamp()}"
        self.execution_history[exec_id] = {
            "plan_id": plan_id,
            "started_at": datetime.utcnow().isoformat(),
            "started_by": ctx.author.id,
            "status": "running",
            "steps_executed": 0
        }
        
        embed = discord.Embed(
            title=f"🔧 Executing Remediation Plan #{plan_id}",
            description=plan["name"],
            color=discord.Color.blue()
        )
        
        # Execute steps
        for step in plan["steps"]:
            embed.add_field(
                name=f"Step {step['step']}",
                value=f"▶️ {step['action']}",
                inline=False
            )
            self.execution_history[exec_id]["steps_executed"] += 1
            await asyncio.sleep(1)  # Simulate execution time
        
        plan["execution_count"] += 1
        plan["last_executed"] = datetime.utcnow().isoformat()
        self.execution_history[exec_id]["status"] = "completed"
        self.execution_history[exec_id]["completed_at"] = datetime.utcnow().isoformat()
        self.save_plans()
        
        embed = discord.Embed(
            title=f"✅ Remediation Plan #{plan_id} Completed",
            description=plan["name"],
            color=discord.Color.green()
        )
        embed.add_field(name="Steps Executed", value=str(self.execution_history[exec_id]["steps_executed"]), inline=True)
        embed.add_field(name="Total Executions", value=str(plan["execution_count"]), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def listremediationplans(self, ctx):
        """List all remediation plans."""
        if not self.remediation_plans:
            await ctx.send("ℹ️ No remediation plans created.")
            return
        
        embed = discord.Embed(
            title=f"📋 Remediation Plans ({len(self.remediation_plans)})",
            color=discord.Color.blue()
        )
        
        for plan_id, plan in list(self.remediation_plans.items())[:10]:
            embed.add_field(
                name=f"#{plan_id} - {plan['name']} [{plan['status'].upper()}]",
                value=f"Steps: {len(plan['steps'])} | Executions: {plan['execution_count']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def remediationstats(self, ctx):
        """View remediation statistics."""
        total = len(self.remediation_plans)
        published = sum(1 for p in self.remediation_plans.values() if p["status"] == "published")
        draft = total - published
        total_executions = sum(p["execution_count"] for p in self.remediation_plans.values())
        
        embed = discord.Embed(
            title="📊 Remediation Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Plans", value=str(total), inline=True)
        embed.add_field(name="Published", value=str(published), inline=True)
        embed.add_field(name="Draft", value=str(draft), inline=True)
        embed.add_field(name="Total Executions", value=str(total_executions), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoRemediationSystemCog(bot))
