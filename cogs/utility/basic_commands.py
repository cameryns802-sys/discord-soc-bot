import discord
from discord.ext import commands
from datetime import timedelta
import random
from typing import Optional
import re
import math
import asyncio
from cogs.core.pst_timezone import get_now_pst


class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        latency_ms = int(getattr(self.bot, "latency", 0.0) * 1000)
        embed = discord.Embed(
            title="🏓 Pong",
            description=f"WebSocket latency: **{latency_ms}ms**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        start = getattr(self.bot, "uptime", None)
        if start is None:
            start = get_now_pst()
        now = get_now_pst()
        delta = now - start
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        embed = discord.Embed(
            title="⏱️ Uptime",
            description=f"{days}d {hours}h {minutes}m {seconds}s",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="about")
    async def about(self, ctx):
        app_id = getattr(self.bot, "application_id", None) or (self.bot.user.id if self.bot.user else 0)
        embed = discord.Embed(
            title="ℹ️ About",
            description="Sentinel SOC Bot (normal utility commands enabled).",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Application ID", value=str(app_id), inline=True)
        embed.add_field(name="Cogs", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(name="Commands", value=str(len(list(self.bot.commands))), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="invite")
    async def invite(self, ctx, permissions: int = 0):
        app_id = getattr(self.bot, "application_id", None) or (self.bot.user.id if self.bot.user else None)
        if not app_id:
            await ctx.send("❌ Invite link unavailable (bot user not ready yet).")
            return

        url = (
            "https://discord.com/api/oauth2/authorize"
            f"?client_id={app_id}&permissions={int(permissions)}&scope=bot%20applications.commands"
        )
        embed = discord.Embed(
            title="🔗 Invite",
            description="Use this link to invite the bot to a server:",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Invite URL", value=url, inline=False)
        embed.set_footer(text="Tip: !invite 8 generates an Administrator invite link.")
        await ctx.send(embed=embed)

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        avatar_url = member.display_avatar.url
        embed = discord.Embed(
            title=f"🖼️ Avatar — {member}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        created = member.created_at
        joined = getattr(member, "joined_at", None)
        embed = discord.Embed(
            title=f"👤 User Info — {member}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Bot", value=str(member.bot), inline=True)
        embed.add_field(name="Created", value=created.strftime("%Y-%m-%d %H:%M UTC"), inline=False)
        if joined:
            embed.add_field(name="Joined", value=joined.strftime("%Y-%m-%d %H:%M UTC"), inline=False)
        if member.roles and hasattr(ctx, "guild") and ctx.guild:
            roles = [r.mention for r in member.roles if r.name != "@everyone"]
            if roles:
                embed.add_field(name="Roles", value=" ".join(roles[:15]), inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="roll")
    async def roll(self, ctx, dice: str = "1d6"):
        dice = dice.lower().strip()
        if "d" not in dice:
            try:
                sides = int(dice)
                if sides < 2 or sides > 100000:
                    raise ValueError
                result = random.randint(1, sides)
                await ctx.send(f"🎲 Rolled 1-{sides}: **{result}**")
                return
            except ValueError:
                await ctx.send("❌ Usage: `!roll 1d6` or `!roll 20`")
                return

        try:
            count_str, sides_str = dice.split("d", 1)
            count = int(count_str) if count_str else 1
            sides = int(sides_str)
            if not (1 <= count <= 50 and 2 <= sides <= 100000):
                raise ValueError
        except ValueError:
            await ctx.send("❌ Usage: `!roll 2d6` (max 50 dice)")
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        shown = ", ".join(map(str, rolls[:20]))
        if len(rolls) > 20:
            shown += f", … (+{len(rolls) - 20} more)"
        await ctx.send(f"🎲 **{dice}** → [{shown}] = **{total}**")

    @commands.command(name="choose")
    async def choose(self, ctx, *, options: str):
        parts = [p.strip() for p in options.replace(",", "|").split("|") if p.strip()]
        if len(parts) < 2:
            await ctx.send("❌ Usage: `!choose option1 | option2 | option3`")
            return
        choice = random.choice(parts)
        await ctx.send(f"✅ I choose: **{choice}**")

    @commands.command(name="basic_poll", aliases=["poll_basic"])
    async def poll(self, ctx, *, question: str):
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue(),
        )
        msg = await ctx.send(embed=embed)
        try:
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        except discord.Forbidden:
            pass

    @commands.command(name="say", aliases=["echo"])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message: str):
        """
        Make the bot say something in the current channel.
        
        Usage:
            !say <message>
            !echo <message>
            !announce <message>
        
        Examples:
            !say Hello everyone!
            !announce Server maintenance in 1 hour
        """
        if not message.strip():
            await ctx.send("❌ Please provide a message to send.")
            return
        
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        
        await ctx.send(message)

    @commands.command(name="reverse")
    async def reverse(self, ctx, *, text: str):
        """Reverse text"""
        if not text.strip():
            await ctx.send("❌ Please provide text to reverse.")
            return
        await ctx.send(f"🔄 `{text[::-1]}`")

    @commands.command(name="uppercase")
    async def uppercase(self, ctx, *, text: str):
        """Convert text to UPPERCASE"""
        if not text.strip():
            await ctx.send("❌ Please provide text.")
            return
        await ctx.send(f"📝 `{text.upper()}`")

    @commands.command(name="lowercase")
    async def lowercase(self, ctx, *, text: str):
        """Convert text to lowercase"""
        if not text.strip():
            await ctx.send("❌ Please provide text.")
            return
        await ctx.send(f"📝 `{text.lower()}`")

    @commands.command(name="8ball")
    async def eightball(self, ctx, *, question: str = None):
        """Magic 8 ball - Ask a yes/no question"""
        responses = [
            "✅ Yes, definitely",
            "✅ Yes",
            "✅ Most likely",
            "🤷 Maybe",
            "🤷 Ask again later",
            "🤷 Cannot predict now",
            "❌ No",
            "❌ Definitely not",
            "❌ Don't count on it",
            "❌ Very doubtful"
        ]
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8 Ball",
            description=f"**Question:** {question or 'No question asked'}\n\n**Answer:** {answer}",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="flip")
    async def flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        await ctx.send(f"**{result}**")

    @commands.command(name="slots")
    async def slots(self, ctx):
        """Play a slot machine"""
        emojis = ["🍎", "🍊", "🍋", "🍌", "🍇", "🎰", "💰"]
        result = [random.choice(emojis) for _ in range(3)]
        result_str = " ".join(result)
        
        if result[0] == result[1] == result[2]:
            await ctx.send(f"🎰 {result_str} **JACKPOT! 🎉**")
        elif result[0] == result[1] or result[1] == result[2]:
            await ctx.send(f"🎰 {result_str} **Win! 🎊**")
        else:
            await ctx.send(f"🎰 {result_str} Better luck next time!")

    @commands.command(name="guess")
    async def guess(self, ctx):
        """Guess the number (1-10)"""
        number = random.randint(1, 10)
        
        embed = discord.Embed(
            title="🎯 Guess the Number!",
            description="I'm thinking of a number between 1 and 10...\nYou have 10 seconds to guess!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=10,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            
            try:
                guess = int(msg.content)
                if guess == number:
                    await ctx.send(f"🎉 **Correct! It was {number}!**")
                elif guess < number:
                    await ctx.send(f"📈 Too low! The number was {number}.")
                else:
                    await ctx.send(f"📉 Too high! The number was {number}.")
            except ValueError:
                await ctx.send(f"❌ That's not a valid number. The answer was {number}.")
        except:
            await ctx.send(f"⏰ Time's up! The number was {number}.")

    @commands.command(name="math")
    async def math(self, ctx, *, expression: str):
        """
        Calculate a math expression
        Examples: !math 2 + 2, !math sqrt(16), !math 10 * 5
        """
        try:
            # Safe math evaluation
            safe_dict = {
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "ceil": math.ceil,
                "floor": math.floor,
                "abs": abs,
                "pow": pow,
                "pi": math.pi,
                "e": math.e
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            await ctx.send(f"📐 `{expression}` = **{result}**")
        except ZeroDivisionError:
            await ctx.send("❌ Cannot divide by zero!")
        except ValueError as e:
            await ctx.send(f"❌ Math error: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Invalid expression: {str(e)[:100]}")

    @commands.command(name="joke")
    async def joke(self, ctx):
        """Tell a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I'm reading a book on the history of glue - I can't put it down.",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why did the coffee file a police report? It got mugged!",
            "How does a penguin build its house? Igloos it together!",
            "What do you call a boomerang that doesn't come back? A stick!"
        ]
        await ctx.send(f"😄 {random.choice(jokes)}")

    @commands.command(name="randomuser")
    async def randomuser(self, ctx):
        """Pick a random user from the server"""
        if not ctx.guild or not ctx.guild.members:
            await ctx.send("❌ No members in this server.")
            return
        
        # Exclude bot
        members = [m for m in ctx.guild.members if not m.bot]
        if not members:
            await ctx.send("❌ No human members found.")
            return
        
        user = random.choice(members)
        embed = discord.Embed(
            title="🎲 Random User",
            description=f"It's **{user}**!",
            color=discord.Color.random()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="randomrole")
    async def randomrole(self, ctx):
        """Pick a random role from the server"""
        if not ctx.guild or not ctx.guild.roles:
            await ctx.send("❌ No roles in this server.")
            return
        
        # Exclude @everyone
        roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
        if not roles:
            await ctx.send("❌ No roles found.")
            return
        
        role = random.choice(roles)
        embed = discord.Embed(
            title="🎲 Random Role",
            description=f"It's **{role.mention}**!",
            color=role.color
        )
        await ctx.send(embed=embed)

    @commands.command(name="ascii")
    async def ascii(self, ctx, *, text: str = None):
        """Show ASCII art or character info"""
        if not text:
            await ctx.send("❌ Provide text.")
            return
        
        if len(text) == 1:
            # Show ASCII code
            code = ord(text)
            embed = discord.Embed(
                title=f"ASCII Code for '{text}'",
                description=f"**Decimal:** {code}\n**Hex:** {hex(code)}\n**Binary:** {bin(code)}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            # Show text as code
            if len(text) > 100:
                await ctx.send("❌ Text too long (max 100 chars).")
            else:
                await ctx.send(f"```\n{text}\n```")

    @commands.command(name="countdown")
    async def countdown(self, ctx, seconds: int = 10):
        """Start a countdown timer"""
        if seconds < 1 or seconds > 60:
            await ctx.send("❌ Please provide a number between 1 and 60.")
            return
        
        msg = await ctx.send(f"⏳ **{seconds}**")
        for i in range(seconds - 1, 0, -1):
            await asyncio.sleep(1)
            try:
                await msg.edit(content=f"⏳ **{i}**")
            except:
                break
        
        try:
            await msg.edit(content="🔔 **Done!**")
        except:
            pass

    @commands.command(name="compare")
    async def compare(self, ctx, first: str, *, second: str):
        """Compare two things with funny results"""
        comparisons = [
            f"**{first}** is definitely better than **{second}**",
            f"**{second}** beats **{first}** any day",
            f"They're basically the same thing",
            f"**{first}** is 100x cooler",
            f"I'd pick **{second}** over **{first}**",
            f"This is a tough one... **{first}** wins!",
        ]
        await ctx.send(f"🤔 {random.choice(comparisons)}")

    @commands.command(name="rate")
    async def rate(self, ctx, *, thing: str):
        """Rate something 1-10"""
        rating = random.randint(1, 10)
        stars = "⭐" * rating + "☆" * (10 - rating)
        embed = discord.Embed(
            title=f"Rating: {thing}",
            description=f"{stars}\n**{rating}/10**",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ship")
    async def ship(self, ctx, member1: Optional[discord.Member] = None, member2: Optional[discord.Member] = None):
        """Ship two people and get a compatibility percentage"""
        member1 = member1 or ctx.author
        if not member2:
            await ctx.send("❌ Mention two people to ship: `!ship @user1 @user2`")
            return
        
        # Create ship name
        ship_name = member1.name[:len(member1.name)//2] + member2.name[len(member2.name)//2:]
        compatibility = random.randint(10, 100)
        
        bars = int(compatibility / 10)
        percentage_bar = "█" * bars + "░" * (10 - bars)
        
        embed = discord.Embed(
            title=f"💕 Ship: {member1.name} × {member2.name}",
            description=f"**Ship Name:** {ship_name}\n\n**Compatibility:** {percentage_bar} **{compatibility}%**",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name="hug")
    async def hug(self, ctx, member: Optional[discord.Member] = None):
        """Hug someone"""
        if not member:
            await ctx.send("❌ Mention someone to hug: `!hug @user`")
            return
        
        if member == ctx.author:
            await ctx.send(f"🤗 {ctx.author.mention} gives themselves a hug!")
        else:
            await ctx.send(f"🤗 {ctx.author.mention} hugs {member.mention}!")

    @commands.command(name="pat")
    async def pat(self, ctx, member: Optional[discord.Member] = None):
        """Pat someone on the head"""
        if not member:
            await ctx.send("❌ Mention someone to pat: `!pat @user`")
            return
        
        await ctx.send(f"👋 {ctx.author.mention} pats {member.mention} on the head!")

    @commands.command(name="slap")
    async def slap(self, ctx, member: Optional[discord.Member] = None):
        """Slap someone (in jest)"""
        if not member:
            await ctx.send("❌ Mention someone to slap: `!slap @user`")
            return
        
        if member == ctx.author:
            await ctx.send(f"👋 {ctx.author.mention} slaps themselves!")
        else:
            await ctx.send(f"👋 {ctx.author.mention} slaps {member.mention}!")

    @commands.command(name="wave")
    async def wave(self, ctx, member: Optional[discord.Member] = None):
        """Wave to someone"""
        if member:
            await ctx.send(f"👋 {ctx.author.mention} waves to {member.mention}!")
        else:
            await ctx.send(f"👋 {ctx.author.mention} waves to everyone!")

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx, role: discord.Role = None):
        """Get information about a role"""
        role = role or ctx.author.top_role
        
        embed = discord.Embed(
            title=f"Role Info: {role.name}",
            color=role.color
        )
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=role.color, inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Created", value=role.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="channelinfo")
    async def channelinfo(self, ctx, channel: discord.TextChannel = None):
        """Get information about a channel"""
        channel = channel or ctx.channel
        
        embed = discord.Embed(
            title=f"Channel Info: {channel.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        embed.add_field(name="Type", value="Text Channel", inline=True)
        embed.add_field(name="Created", value=channel.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Topic", value=channel.topic or "No topic", inline=False)
        embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s", inline=True)
        embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="membercount")
    async def membercount(self, ctx):
        """Get server member count"""
        guild = ctx.guild
        total = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots
        
        embed = discord.Embed(
            title=f"{guild.name} Members",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Members", value=total, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="time")
    async def time(self, ctx):
        """Show current time"""
        now = get_now_pst()
        embed = discord.Embed(
            title="⏰ Current Time",
            description=now.strftime("%Y-%m-%d %H:%M:%S PST"),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="snowflake")
    async def snowflake(self, ctx, id: int):
        """Decode a Discord snowflake ID"""
        try:
            # Extract timestamp from snowflake
            timestamp = (id >> 22) + 1420070400000
            dt = datetime.datetime.fromtimestamp(timestamp / 1000, tz=datetime.timezone.utc)
            
            embed = discord.Embed(
                title="Snowflake Decoder",
                color=discord.Color.blue()
            )
            embed.add_field(name="Snowflake ID", value=id, inline=False)
            embed.add_field(name="Created At", value=dt.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.add_field(name="Timestamp", value=timestamp, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Invalid snowflake: {e}")

    @commands.command(name="remind")
    async def remind(self, ctx, seconds: int, *, message: str):
        """Set a reminder"""
        if seconds < 1 or seconds > 3600:
            await ctx.send("❌ Reminder must be between 1 and 3600 seconds.")
            return
        
        await ctx.send(f"⏰ Reminder set for {seconds} seconds!")
        await asyncio.sleep(seconds)
        
        try:
            await ctx.author.send(f"🔔 **Reminder:** {message}")
        except:
            await ctx.send(f"{ctx.author.mention} 🔔 **Reminder:** {message}")

    @commands.command(name="fortune")
    async def fortune(self, ctx):
        """Get a random fortune"""
        fortunes = [
            "A journey of a thousand miles begins with a single step.",
            "The best time to plant a tree was 20 years ago. The second best time is now.",
            "Success is not final, failure is not fatal.",
            "It does not matter how slowly you go as long as you do not stop.",
            "Everything you want is on the other side of fear.",
            "The only impossible journey is the one you never begin.",
            "In the middle of difficulty lies opportunity.",
            "You are braver than you believe, stronger than you seem.",
            "The future belongs to those who believe in the beauty of their dreams.",
            "Don't watch the clock; do what it does. Keep going."
        ]
        embed = discord.Embed(
            title="✨ Fortune",
            description=random.choice(fortunes),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="emoji")
    async def emoji_cmd(self, ctx, emoji: str = None):
        """Get info about an emoji"""
        if not emoji:
            await ctx.send("❌ Provide an emoji: `!emoji 😀`")
            return
        
        embed = discord.Embed(
            title="Emoji Info",
            color=discord.Color.blue()
        )
        embed.add_field(name="Emoji", value=emoji, inline=True)
        embed.add_field(name="Unicode", value=f"`{emoji.encode('unicode-escape').decode('ascii')}`", inline=True)
        embed.add_field(name="Unicode Name", value=emoji.encode('unicode-escape').decode('ascii'), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="prefix")
    async def prefix_cmd(self, ctx):
        """Show the bot prefix"""
        embed = discord.Embed(
            title="Bot Prefix",
            description="Use `!` to run commands\n\nExample: `!ping`",
            color=discord.Color.blue()
        )
        embed.add_field(name="Slash Commands", value="Type `/` to see slash command list", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="color")
    async def color(self, ctx, hex_color: str = None):
        """Show a color"""
        if not hex_color:
            hex_color = f"{random.randint(0, 0xFFFFFF):06x}"
        
        try:
            # Remove # if present
            hex_color = hex_color.lstrip("#")
            color_int = int(hex_color, 16)
            color_obj = discord.Color(color_int)
            
            embed = discord.Embed(
                title="Color Preview",
                color=color_obj
            )
            embed.add_field(name="Hex", value=f"#{hex_color.upper()}", inline=True)
            embed.add_field(name="RGB", value=f"rgb({color_int >> 16}, {(color_int >> 8) & 0xFF}, {color_int & 0xFF})", inline=True)
            embed.add_field(name="Decimal", value=color_int, inline=True)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Invalid hex color. Use format: `#RRGGBB` or `RRGGBB`")

    @commands.command(name="dice")
    async def dice(self, ctx, sides: int = 6):
        """Roll a single die"""
        if sides < 2 or sides > 100000:
            await ctx.send("❌ Sides must be between 2 and 100000.")
            return
        
        result = random.randint(1, sides)
        await ctx.send(f"🎲 Rolled **d{sides}**: **{result}**")

async def setup(bot):
    await bot.add_cog(BasicCommands(bot))
