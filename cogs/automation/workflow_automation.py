"""Workflow Automation: Consolidated command group"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class WorkflowGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="workflow", description="Workflow automation commands")
        self.cog = cog

    @app_commands.command(name="create", description="Create new workflow")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create(self, interaction: discord.Interaction, name: str, description: str = "No description"):
        self.cog.workflow_counter += 1
        wf_id = self.cog.workflow_counter
        self.cog.workflows[str(wf_id)] = {"id": wf_id, "name": name, "description": description, "status": "draft", "steps": [], "created_by": interaction.user.id, "created_at": get_now_pst().isoformat(), "execution_count": 0}
        self.cog.save_workflows()
        await interaction.response.send_message(f"✅ Created workflow #{wf_id}: {name}")

    @app_commands.command(name="add_step", description="Add step to workflow")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_step(self, interaction: discord.Interaction, workflow_id: int, step_name: str, action: str):
        wf_key = str(workflow_id)
        if wf_key not in self.cog.workflows:
            await interaction.response.send_message("❌ Workflow not found", ephemeral=True)
            return
        self.cog.workflows[wf_key]["steps"].append({"name": step_name, "action": action, "order": len(self.cog.workflows[wf_key]["steps"]) + 1})
        self.cog.save_workflows()
        await interaction.response.send_message(f"✅ Added step to workflow #{workflow_id}")

    @app_commands.command(name="publish", description="Publish workflow (draft→active)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def publish(self, interaction: discord.Interaction, workflow_id: int):
        wf_key = str(workflow_id)
        if wf_key not in self.cog.workflows:
            await interaction.response.send_message("❌ Workflow not found", ephemeral=True)
            return
        if not self.cog.workflows[wf_key]["steps"]:
            await interaction.response.send_message("❌ Cannot publish workflow with no steps", ephemeral=True)
            return
        self.cog.workflows[wf_key]["status"] = "active"
        self.cog.save_workflows()
        await interaction.response.send_message(f"✅ Published workflow #{workflow_id}")

    @app_commands.command(name="execute", description="Execute workflow")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def execute(self, interaction: discord.Interaction, workflow_id: int):
        wf_key = str(workflow_id)
        if wf_key not in self.cog.workflows:
            await interaction.response.send_message("❌ Workflow not found", ephemeral=True)
            return
        self.cog.execution_counter += 1
        exec_id = self.cog.execution_counter
        self.cog.workflows[wf_key]["execution_count"] += 1
        self.cog.execution_history[str(exec_id)] = {"id": exec_id, "workflow_id": workflow_id, "executed_by": interaction.user.id, "timestamp": get_now_pst().isoformat(), "status": "completed"}
        self.cog.save_workflows()
        await interaction.response.send_message(f"✅ Executed workflow #{workflow_id} (Execution #{exec_id})")

    @app_commands.command(name="info", description="View workflow details")
    async def info(self, interaction: discord.Interaction, workflow_id: int):
        wf_key = str(workflow_id)
        if wf_key not in self.cog.workflows:
            await interaction.response.send_message("❌ Workflow not found", ephemeral=True)
            return
        wf = self.cog.workflows[wf_key]
        embed = discord.Embed(title=f"⚙️ Workflow #{wf['id']}: {wf['name']}", description=wf['description'], color=discord.Color.blue())
        embed.add_field(name="Status", value=wf['status'].upper(), inline=True)
        embed.add_field(name="Steps", value=len(wf['steps']), inline=True)
        embed.add_field(name="Executions", value=wf['execution_count'], inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="List all workflows")
    async def list(self, interaction: discord.Interaction):
        if not self.cog.workflows:
            await interaction.response.send_message("ℹ️ No workflows", ephemeral=True)
            return
        embed = discord.Embed(title="⚙️ Workflows", color=discord.Color.blue())
        for wf in list(self.cog.workflows.values())[:15]:
            embed.add_field(name=f"#{wf['id']} - {wf['name']}", value=f"Status: {wf['status']} | Steps: {len(wf['steps'])} | Runs: {wf['execution_count']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View workflow statistics")
    async def stats(self, interaction: discord.Interaction):
        active = len([w for w in self.cog.workflows.values() if w['status'] == 'active'])
        draft = len([w for w in self.cog.workflows.values() if w['status'] == 'draft'])
        embed = discord.Embed(title="📊 Workflow Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Workflows", value=len(self.cog.workflows), inline=True)
        embed.add_field(name="Active", value=active, inline=True)
        embed.add_field(name="Draft", value=draft, inline=True)
        embed.add_field(name="Total Executions", value=len(self.cog.execution_history), inline=True)
        await interaction.response.send_message(embed=embed)

class WorkflowAutomationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.workflows = {}
        self.execution_history = {}
        self.workflow_counter = 0
        self.execution_counter = 0
        self.data_file = "data/workflows.json"
        self.load_workflows()
        self.workflow_group = WorkflowGroup(self)
        bot.tree.add_command(self.workflow_group)

    def load_workflows(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.workflows = data.get('workflows', {})
                    self.execution_history = data.get('executions', {})
                    self.workflow_counter = data.get('workflow_counter', 0)
                    self.execution_counter = data.get('execution_counter', 0)
            except: pass

    def save_workflows(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'workflows': self.workflows, 'executions': self.execution_history, 'workflow_counter': self.workflow_counter, 'execution_counter': self.execution_counter}, f, indent=2)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.workflow_group.name)

async def setup(bot):
    await bot.add_cog(WorkflowAutomationCog(bot))
