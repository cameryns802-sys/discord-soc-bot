"""Prompt Injection Detector - Security against LLM prompt injection attacks"""
import re
from typing import List, Dict, Tuple
import discord
from discord.ext import commands
from cogs.core.pst_timezone import get_now_pst

class PromptInjectionDetector:
    """Detect and prevent prompt injection attacks"""
    
    # Regex patterns for common injection attempts
    INJECTION_PATTERNS = [
        r"(?:ignore|forget|disregard|override).*(?:instructions|prompt|rule|guideline)",
        r"(?:system|admin|root)\s*(?:prompt|instruction|rule)",
        r"(?:this\s+)?message\s*is\s*from\s*an?\s*(?:admin|system|operator)",
        r"(?:act\s+as|pretend|assume|you\s+are)\s+(?:an?\s+)?(?:admin|system|operator|gpt)",
        r"(?:execute|run|eval)\s+(?:code|command|instruction)",
        r"(?:show|reveal|tell|expose|dump).*(?:prompt|instruction|rule|system)"
    ]
    
    # Suspicious sequences that appear in injections
    SUSPICIOUS_SEQUENCES = [
        ("<!---", "--->"),  # HTML comments
        ("<!--", "-->"),     # HTML comments
        ("[SYSTEM]", "[/SYSTEM]"),  # System markers
        ("[ADMIN]", "[/ADMIN]"),  # Admin markers
        ("{SYSTEM}", "{/SYSTEM}"),  # Brace markers
        ("<system>", "</system>"),  # XML tags
        ("[OVERRIDE]", "[/OVERRIDE]"),  # Override markers
        ("OVERRIDE:", "END_OVERRIDE")  # Text markers
    ]
    
    def __init__(self):
        self.detected_injections: List[Dict] = []
        self.injection_count = 0
    
    def check_text(self, text: str) -> Tuple[bool, List[str], float]:
        """
        Check text for injection attempts
        Returns: (is_injection, patterns_found, confidence)
        """
        text_lower = text.lower()
        found_patterns = []
        
        # Check regex patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_patterns.append(pattern[:50])
        
        # Check suspicious sequences
        for open_seq, close_seq in self.SUSPICIOUS_SEQUENCES:
            if open_seq.lower() in text_lower:
                found_patterns.append(f"Sequence: {open_seq}")
        
        # Calculate confidence
        confidence = min(1.0, len(found_patterns) / 3.0)
        is_injection = len(found_patterns) > 0
        
        return is_injection, found_patterns, confidence
    
    def sanitize_text(self, text: str) -> str:
        """Remove or escape potentially dangerous sequences"""
        sanitized = text
        
        # Remove common injection markers
        markers_to_remove = [
            r"<!---.*?--->",
            r"<!--.*?-->",
            r"\[SYSTEM\].*?\[/SYSTEM\]",
            r"\[ADMIN\].*?\[/ADMIN\]",
            r"{SYSTEM}.*?{/SYSTEM}",
            r"<system>.*?</system>",
            r"\[OVERRIDE\].*?\[/OVERRIDE\]"
        ]
        
        for marker_pattern in markers_to_remove:
            sanitized = re.sub(marker_pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    def log_injection(self, user_id: int, content: str, patterns: List[str]):
        """Log detected injection attempt"""
        self.detected_injections.append({
            'timestamp': str(__import__('datetime').get_now_pst()),
            'user_id': user_id,
            'content': content[:100],  # First 100 chars only
            'patterns_found': patterns
        })
        self.injection_count += 1

class PromptInjectionCog(commands.Cog):
    """Commands for prompt security monitoring"""
    
    def __init__(self, bot):
        self.bot = bot
        self.detector = PromptInjectionDetector()
    
    @commands.command(name='checkprompt')
    async def check_prompt(self, ctx, *, text: str):
        """Check text for injection patterns (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        is_injection, patterns, confidence = self.detector.check_text(text)
        
        embed = discord.Embed(
            title="🔐 Prompt Injection Analysis",
            color=discord.Color.red() if is_injection else discord.Color.green()
        )
        embed.add_field(name="Status", value="⚠️ INJECTION DETECTED" if is_injection else "✅ SAFE", inline=False)
        embed.add_field(name="Confidence", value=f"{confidence:.1%}", inline=True)
        embed.add_field(name="Patterns Found", value=len(patterns), inline=True)
        
        if patterns:
            embed.add_field(name="Details", value="\n".join(patterns[:5]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='injectionstats')
    async def injection_stats(self, ctx):
        """View injection detection statistics (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(title="📊 Injection Detection Stats", color=discord.Color.blue())
        embed.add_field(name="Total Detections", value=self.detector.injection_count, inline=True)
        embed.add_field(name="Recent Attempts", value=len(self.detector.detected_injections), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sanitize')
    async def sanitize_cmd(self, ctx, *, text: str):
        """Sanitize text by removing injection markers (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        sanitized = self.detector.sanitize_text(text)
        embed = discord.Embed(title="🧹 Sanitized Text", color=discord.Color.blue())
        embed.add_field(name="Original", value=text[:100], inline=False)
        embed.add_field(name="Sanitized", value=sanitized[:100], inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PromptInjectionCog(bot))

# Global singleton for cross-cog access
detector = PromptInjectionDetector()
