"""
SOC Copilot (AI Assistant): Conversational AI for SOC operations.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SOCCopilotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/soc_copilot.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "conversations": [],
            "knowledge_base": self.get_default_kb(),
            "suggestions": []
        }

    def get_default_kb(self):
        """Default SOC knowledge base."""
        return {
            "incident_response": {
                "phishing": "1. Isolate affected user 2. Quarantine malicious email 3. Scan for IOCs 4. Reset credentials 5. Monitor for lateral movement",
                "malware": "1. Isolate infected system 2. Collect memory dump 3. Run full AV scan 4. Analyze IOCs 5. Restore from clean backup",
                "data_breach": "1. Contain breach 2. Assess impact 3. Preserve evidence 4. Notify stakeholders 5. Implement remediation",
                "dos_attack": "1. Identify attack vectors 2. Implement rate limiting 3. Filter malicious traffic 4. Scale resources 5. Monitor effectiveness"
            },
            "best_practices": {
                "incident_classification": "Classify by: Severity (Critical/High/Medium/Low), Impact (Confidentiality/Integrity/Availability), Scope (Single user/Department/Organization-wide)",
                "evidence_collection": "Always: 1. Maintain chain of custody 2. Hash all evidence 3. Use forensically sound tools 4. Document every action 5. Timestamp all activities",
                "escalation": "Escalate when: 1. Incident severity increases 2. Impact scope expands 3. Initial containment fails 4. Executive involvement needed 5. Legal implications arise"
            },
            "playbooks": {
                "phishing_response": "Auto-quarantine > Create case > Collect evidence > Analyze sender/links > Block IOCs > User training",
                "privilege_escalation": "Revoke elevated access > Lock account > Review audit logs > Check for persistence > Forensics > Root cause analysis",
                "data_exfiltration": "Block egress > Isolate affected systems > Identify data stolen > Legal notification > Forensic analysis > Remediation"
            }
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def get_ai_response(self, query: str):
        """Generate AI response to SOC query (simulated LLM)."""
        query_lower = query.lower()
        
        # Match keywords to knowledge base
        if "phishing" in query_lower:
            category = "incident_response"
            topic = "phishing"
        elif "malware" in query_lower:
            category = "incident_response"
            topic = "malware"
        elif "breach" in query_lower or "exfiltration" in query_lower:
            category = "incident_response"
            topic = "data_breach"
        elif "dos" in query_lower or "ddos" in query_lower:
            category = "incident_response"
            topic = "dos_attack"
        elif "classify" in query_lower or "severity" in query_lower:
            category = "best_practices"
            topic = "incident_classification"
        elif "evidence" in query_lower or "forensic" in query_lower:
            category = "best_practices"
            topic = "evidence_collection"
        elif "escalate" in query_lower:
            category = "best_practices"
            topic = "escalation"
        elif "playbook" in query_lower:
            # Return all playbooks
            return {
                "response": "Available playbooks:\n" + "\n".join([f"• {k}: {v}" for k, v in self.data["knowledge_base"]["playbooks"].items()]),
                "confidence": 0.95,
                "sources": ["knowledge_base.playbooks"]
            }
        else:
            return {
                "response": "I can help with:\n• Incident response procedures\n• Best practices\n• Playbook recommendations\n• Threat analysis\n\nTry asking about specific incidents like 'How do I respond to phishing?' or 'What's the escalation process?'",
                "confidence": 0.5,
                "sources": ["general"]
            }
        
        if category in self.data["knowledge_base"] and topic in self.data["knowledge_base"][category]:
            response_text = self.data["knowledge_base"][category][topic]
            return {
                "response": response_text,
                "confidence": 0.92,
                "sources": [f"knowledge_base.{category}.{topic}"]
            }
        
        return {
            "response": "I don't have specific guidance on that topic yet. Would you like me to escalate to a senior analyst?",
            "confidence": 0.3,
            "sources": []
        }

    @commands.command(name="ask_copilot")
    async def ask_copilot(self, ctx, *, query: str):
        """Ask SOC Copilot a question."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        # Get AI response
        ai_response = self.get_ai_response(query)
        
        # Record conversation
        conversation = {
            "conversation_id": f"CONV-{len(self.data['conversations']) + 1:05d}",
            "user": str(ctx.author.id),
            "query": query,
            "response": ai_response["response"],
            "confidence": ai_response["confidence"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.data["conversations"].append(conversation)
        self.save_data(self.data)
        
        # Generate embed
        confidence_color = discord.Color.green() if ai_response["confidence"] > 0.8 else discord.Color.orange() if ai_response["confidence"] > 0.5 else discord.Color.red()
        
        embed = discord.Embed(
            title="🤖 SOC Copilot Response",
            description=ai_response["response"],
            color=confidence_color
        )
        
        embed.add_field(name="Confidence", value=f"{ai_response['confidence']*100:.0f}%", inline=True)
        embed.add_field(name="Sources", value=", ".join(ai_response["sources"]) if ai_response["sources"] else "N/A", inline=True)
        
        if ai_response["confidence"] < 0.7:
            embed.set_footer(text="⚠️ Low confidence - Consider consulting senior analyst")
        
        await ctx.send(embed=embed)

    @commands.command(name="suggest_workflow")
    async def suggest_workflow(self, ctx, *, incident_type: str):
        """Get AI-suggested workflow for incident type."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        # Check playbooks
        incident_lower = incident_type.lower()
        
        suggested_playbook = None
        for playbook_name, playbook_steps in self.data["knowledge_base"]["playbooks"].items():
            if incident_lower in playbook_name:
                suggested_playbook = (playbook_name, playbook_steps)
                break
        
        embed = discord.Embed(
            title="🎯 Suggested Workflow",
            description=f"For incident type: {incident_type}",
            color=discord.Color.blue()
        )
        
        if suggested_playbook:
            playbook_name, steps = suggested_playbook
            embed.add_field(name="Playbook", value=playbook_name, inline=False)
            embed.add_field(name="Steps", value=steps, inline=False)
            embed.add_field(name="Recommendation", value="✅ Use automated playbook executor", inline=False)
        else:
            embed.add_field(name="Status", value="⚠️ No exact playbook match", inline=False)
            embed.add_field(name="Recommendation", value="Create custom playbook or consult senior analyst", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="copilot_stats")
    async def copilot_stats(self, ctx):
        """View SOC Copilot usage statistics."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        total_queries = len(self.data["conversations"])
        avg_confidence = sum(conv["confidence"] for conv in self.data["conversations"]) / total_queries if total_queries > 0 else 0
        
        embed = discord.Embed(
            title="📊 SOC Copilot Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Queries", value=str(total_queries), inline=True)
        embed.add_field(name="Avg Confidence", value=f"{avg_confidence*100:.1f}%", inline=True)
        embed.add_field(name="Knowledge Base Topics", value=str(sum(len(cat) for cat in self.data["knowledge_base"].values())), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="add_kb_entry")
    async def add_kb_entry(self, ctx, category: str, topic: str, *, content: str):
        """Add entry to SOC Copilot knowledge base."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if category not in self.data["knowledge_base"]:
            self.data["knowledge_base"][category] = {}
        
        self.data["knowledge_base"][category][topic] = content
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Knowledge Base Updated",
            description=f"Added to category: {category}",
            color=discord.Color.green()
        )
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Content Length", value=f"{len(content)} chars", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="copilot_help")
    async def copilot_help(self, ctx):
        """View SOC Copilot capabilities."""
        embed = discord.Embed(
            title="🤖 SOC Copilot - AI Assistant",
            description="Conversational AI for SOC operations",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💬 Ask Questions",
            value="!ask_copilot <your question>\nExample: !ask_copilot How do I respond to phishing?",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Workflow Suggestions",
            value="!suggest_workflow <incident type>\nExample: !suggest_workflow data breach",
            inline=False
        )
        
        embed.add_field(
            name="📚 Knowledge Base",
            value="• Incident response procedures\n• Best practices\n• Playbook recommendations\n• Escalation guidelines",
            inline=False
        )
        
        embed.add_field(
            name="📊 Statistics",
            value="!copilot_stats - View usage statistics",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SOCCopilotCog(bot))
