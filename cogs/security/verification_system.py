"""
Verification System - User verification and role assignment
Prevent unauthorized access to server
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class VerificationSystem(commands.Cog):
    """Handle user verification and role assignment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.verify_file = 'data/verification.json'
        self.load_verify_data()
    
    def load_verify_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.verify_file):
            with open(self.verify_file, 'w') as f:
                json.dump({}, f)
    
    def get_verify_data(self, guild_id):
        try:
            with open(self.verify_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_verify_data(self, guild_id, data):
        try:
            with open(self.verify_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        all_data[str(guild_id)] = data
        with open(self.verify_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Assign verify role to new members"""
        guild = member.guild
        data = self.get_verify_data(guild.id)
        
        if not data.get("enabled"):
            return
        
        verify_role_name = data.get("role_name", "Unverified")
        verify_role = discord.utils.get(guild.roles, name=verify_role_name)
        
        if verify_role:
            try:
                await member.add_roles(verify_role)
                embed = discord.Embed(
                    title="👋 Welcome to the Server!",
                    description="You have been assigned the Unverified role. React to verify.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="How to Verify", value="React to messages in #verification channel", inline=False)
                try:
                    await member.send(embed=embed)
                except:
                    pass
            except Exception as e:
                print(f"❌ Failed to assign verify role: {e}")
    
    @commands.command(name='setup_verification')
    @commands.has_permissions(administrator=True)
    async def setup_verification(self, ctx):
        """Setup verification system"""
        guild = ctx.guild
        
        # Create unverified role
        try:
            unverified_role = discord.utils.get(guild.roles, name="Unverified")
            if not unverified_role:
                unverified_role = await guild.create_role(
                    name="Unverified",
                    color=discord.Color.red(),
                    reason="Verification system"
                )
        except Exception as e:
            await ctx.send(f"❌ Failed to create role: {e}")
            return
        
        # Create verified role
        try:
            verified_role = discord.utils.get(guild.roles, name="Verified")
            if not verified_role:
                verified_role = await guild.create_role(
                    name="Verified",
                    color=discord.Color.green(),
                    reason="Verification system"
                )
        except Exception as e:
            await ctx.send(f"❌ Failed to create role: {e}")
            return
        
        # Save configuration
        data = {
            "enabled": True,
            "role_name": "Unverified",
            "verified_role": "Verified",
            "setup_date": datetime.utcnow().isoformat()
        }
        self.save_verify_data(guild.id, data)
        
        embed = discord.Embed(
            title="✅ Verification System Setup",
            description="Verification system configured",
            color=discord.Color.green()
        )
        embed.add_field(name="Unverified Role", value="🔴 Unverified", inline=True)
        embed.add_field(name="Verified Role", value="🟢 Verified", inline=True)
        embed.add_field(name="Auto-assign", value="✅ Enabled", inline=True)
        embed.add_field(name="New Members", value="Automatically assigned Unverified role", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='verify')
    async def verify_user(self, ctx):
        """Manually verify a user"""
        guild = ctx.guild
        data = self.get_verify_data(guild.id)
        
        if not data.get("enabled"):
            await ctx.send("❌ Verification system not enabled")
            return
        
        verified_role = discord.utils.get(guild.roles, name="Verified")
        unverified_role = discord.utils.get(guild.roles, name="Unverified")
        
        if not verified_role or not unverified_role:
            await ctx.send("❌ Verification roles not found")
            return
        
        try:
            await ctx.author.add_roles(verified_role)
            await ctx.author.remove_roles(unverified_role)
            
            embed = discord.Embed(
                title="✅ User Verified",
                description=f"{ctx.author.mention} has been verified!",
                color=discord.Color.green()
            )
            embed.add_field(name="Status", value="🟢 Verified", inline=True)
            embed.add_field(name="Timestamp", value=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Verification failed: {e}")

async def setup(bot):
    await bot.add_cog(VerificationSystem(bot))
