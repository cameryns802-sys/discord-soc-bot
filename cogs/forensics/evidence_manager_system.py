# Evidence Manager: Digital forensics, chain of custody, evidence storage
import discord
from discord.ext import commands
from datetime import datetime
import json
import os

class EvidenceManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.evidence_items = {}
        self.evidence_chains = {}
        self.evidence_counter = 0
        self.chain_counter = 0
        self.data_file = "data/evidence_manager.json"
        self.load_evidence()

    def load_evidence(self):
        """Load evidence data."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.evidence_items = data.get('evidence_items', {})
                    self.evidence_chains = data.get('evidence_chains', {})
                    self.evidence_counter = data.get('evidence_counter', 0)
                    self.chain_counter = data.get('chain_counter', 0)
            except:
                pass

    def save_evidence(self):
        """Save evidence data."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'evidence_items': self.evidence_items,
                'evidence_chains': self.evidence_chains,
                'evidence_counter': self.evidence_counter,
                'chain_counter': self.chain_counter
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createevidence(self, ctx, case_name: str, evidence_type: str, *, description: str):
        """Create evidence item. Usage: !createevidence <case_name> <log|file|screenshot|conversation> description"""
        valid_types = ['log', 'file', 'screenshot', 'conversation', 'system', 'network', 'other']
        if evidence_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid type. Use: {', '.join(valid_types)}")
            return
        
        self.evidence_counter += 1
        evidence_id = self.evidence_counter
        
        self.chain_counter += 1
        chain_id = self.chain_counter
        
        evidence_data = {
            "id": evidence_id,
            "case": case_name,
            "type": evidence_type.lower(),
            "description": description,
            "created_by": ctx.author.id,
            "created_at": datetime.utcnow().isoformat(),
            "chain_id": chain_id,
            "hash": f"hash_{evidence_id}",
            "size_bytes": len(description),
            "status": "collected",
            "access_log": [{
                "user_id": ctx.author.id,
                "action": "created",
                "timestamp": datetime.utcnow().isoformat()
            }],
            "tags": [],
            "related_incidents": []
        }
        
        chain_data = {
            "id": chain_id,
            "evidence_id": evidence_id,
            "case": case_name,
            "custodian": ctx.author.id,
            "created_at": datetime.utcnow().isoformat(),
            "transfers": [{
                "from": "collection",
                "to": ctx.author.id,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": "Initial collection"
            }],
            "status": "active"
        }
        
        self.evidence_items[str(evidence_id)] = evidence_data
        self.evidence_chains[str(chain_id)] = chain_data
        self.save_evidence()
        
        embed = discord.Embed(
            title=f"✅ Evidence Created #{evidence_id}",
            description=description[:100],
            color=discord.Color.green()
        )
        embed.add_field(name="Case", value=case_name, inline=True)
        embed.add_field(name="Type", value=evidence_type.upper(), inline=True)
        embed.add_field(name="Chain ID", value=chain_id, inline=True)
        embed.add_field(name="Hash", value=f"hash_{evidence_id}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtag(self, ctx, evidence_id: int, *, tag: str):
        """Add tag to evidence. Usage: !addtag <evidence_id> tag_name"""
        evidence_key = str(evidence_id)
        if evidence_key not in self.evidence_items:
            await ctx.send("❌ Evidence not found.")
            return
        
        evidence = self.evidence_items[evidence_key]
        if tag.lower() not in evidence["tags"]:
            evidence["tags"].append(tag.lower())
            self.save_evidence()
            await ctx.send(f"✅ Tag '{tag}' added to evidence #{evidence_id}")
        else:
            await ctx.send("❌ Tag already exists.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def transfercustody(self, ctx, evidence_id: int, recipient: discord.Member, *, notes: str = ""):
        """Transfer evidence custody. Usage: !transfercustody <evidence_id> @member [notes]"""
        evidence_key = str(evidence_id)
        if evidence_key not in self.evidence_items:
            await ctx.send("❌ Evidence not found.")
            return
        
        evidence = self.evidence_items[evidence_key]
        chain_id = evidence["chain_id"]
        chain = self.evidence_chains[str(chain_id)]
        
        # Log access
        evidence["access_log"].append({
            "user_id": ctx.author.id,
            "action": "transferred",
            "timestamp": datetime.utcnow().isoformat(),
            "notes": notes
        })
        
        # Record transfer in chain of custody
        chain["transfers"].append({
            "from": ctx.author.id,
            "to": recipient.id,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": notes
        })
        chain["custodian"] = recipient.id
        
        self.save_evidence()
        
        embed = discord.Embed(
            title=f"✅ Custody Transferred",
            description=f"Evidence #{evidence_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="From", value=f"<@{ctx.author.id}>", inline=True)
        embed.add_field(name="To", value=f"<@{recipient.id}>", inline=True)
        embed.add_field(name="Notes", value=notes or "None", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def viewevidence(self, ctx, evidence_id: int):
        """View evidence details."""
        evidence_key = str(evidence_id)
        if evidence_key not in self.evidence_items:
            await ctx.send("❌ Evidence not found.")
            return
        
        evidence = self.evidence_items[evidence_key]
        
        # Log access
        evidence["access_log"].append({
            "user_id": ctx.author.id,
            "action": "viewed",
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save_evidence()
        
        embed = discord.Embed(
            title=f"Evidence #{evidence_id}",
            description=evidence['description'][:150],
            color=discord.Color.blue()
        )
        embed.add_field(name="Case", value=evidence['case'], inline=True)
        embed.add_field(name="Type", value=evidence['type'].upper(), inline=True)
        embed.add_field(name="Status", value=evidence['status'].upper(), inline=True)
        embed.add_field(name="Hash", value=evidence['hash'], inline=False)
        embed.add_field(name="Size", value=f"{evidence['size_bytes']} bytes", inline=True)
        embed.add_field(name="Created", value=evidence['created_at'], inline=False)
        
        if evidence["tags"]:
            embed.add_field(name="Tags", value=", ".join(evidence['tags']), inline=False)
        
        embed.add_field(name="Access Count", value=len(evidence['access_log']), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def chainofcustody(self, ctx, evidence_id: int):
        """View chain of custody. Usage: !chainofcustody <evidence_id>"""
        evidence_key = str(evidence_id)
        if evidence_key not in self.evidence_items:
            await ctx.send("❌ Evidence not found.")
            return
        
        evidence = self.evidence_items[evidence_key]
        chain_id = evidence["chain_id"]
        chain = self.evidence_chains[str(chain_id)]
        
        embed = discord.Embed(
            title=f"🔗 Chain of Custody for Evidence #{evidence_id}",
            description=f"Case: {evidence['case']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Custodian", value=f"<@{chain['custodian']}>", inline=False)
        
        transfers_text = ""
        for i, transfer in enumerate(chain["transfers"][:10], 1):
            transfers_text += f"{i}. From: <@{transfer['from']}> → To: <@{transfer['to']}> | {transfer['timestamp']}\n"
            if transfer['notes']:
                transfers_text += f"   Notes: {transfer['notes']}\n"
        
        embed.add_field(name="Transfers", value=transfers_text or "No transfers", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def casevidence(self, ctx, *, case_name: str):
        """View all evidence for a case. Usage: !casevidence <case_name>"""
        case_evidence = [e for e in self.evidence_items.values() if e['case'].lower() == case_name.lower()]
        
        if not case_evidence:
            await ctx.send(f"ℹ️ No evidence for case '{case_name}'")
            return
        
        embed = discord.Embed(
            title=f"📋 Evidence for Case: {case_name}",
            description=f"Total: {len(case_evidence)}",
            color=discord.Color.blue()
        )
        
        for evidence in case_evidence[:10]:
            embed.add_field(
                name=f"#{evidence['id']} | {evidence['type'].upper()}",
                value=f"Status: {evidence['status']} | Tags: {', '.join(evidence['tags']) if evidence['tags'] else 'None'}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def evidencestats(self, ctx):
        """View evidence statistics."""
        cases = set(e['case'] for e in self.evidence_items.values())
        
        embed = discord.Embed(
            title="📊 Evidence Manager Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Evidence Items", value=len(self.evidence_items), inline=True)
        embed.add_field(name="Cases", value=len(cases), inline=True)
        embed.add_field(name="Chains of Custody", value=len(self.evidence_chains), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EvidenceManagerCog(bot))
