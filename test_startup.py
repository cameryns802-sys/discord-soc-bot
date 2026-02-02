#!/usr/bin/env python3
"""Quick bot startup test"""

import sys
import os

# Add to path
sys.path.insert(0, os.getcwd())

print("[Test] Starting bot module import...")

try:
    # Just test imports without running bot.start()
    import discord
    print(f"✅ discord.py imported")
    
    from discord.ext import commands
    print(f"✅ discord.ext.commands imported")
    
    # Load dotenv
    from dotenv import load_dotenv
    load_dotenv()
    print(f"✅ dotenv loaded")
    
    # Simulate loading a cog
    from cogs.security.member_risk_profiler import MemberRiskProfiler
    print(f"✅ MemberRiskProfiler imported")
    
    from cogs.threatintel.threat_intelligence_synthesizer import ThreatIntelligenceSynthesizer
    print(f"✅ ThreatIntelligenceSynthesizer imported")
    
    print("\n✅ ALL CRITICAL IMPORTS SUCCESSFUL")
    print("Bot should start successfully once Discord token is available")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
