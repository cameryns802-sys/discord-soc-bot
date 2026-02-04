import os
import sys
import io
import asyncio

# Force UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime
from datetime import timezone
import logging
import uvicorn
from threading import Thread
import pytz
# Set PST timezone globally
PST = pytz.timezone('America/Los_Angeles')
UTC = timezone.utc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))
AUDIT_CHANNEL_ID = int(os.getenv('AUDIT_CHANNEL_ID', '0'))

# API Configuration
API_HOST = os.getenv('API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_ENVIRONMENT = os.getenv('API_ENVIRONMENT', 'development')
API_DEBUG = os.getenv('API_DEBUG', 'false').lower() == 'true'

# TIER-1 System Configuration
AI_GOVERNANCE_ENABLED = os.getenv('AI_GOVERNANCE_ENABLED', 'true').lower() == 'true'
RESILIENCE_ENABLED = os.getenv('RESILIENCE_ENABLED', 'true').lower() == 'true'
CRYPTO_ENABLED = os.getenv('CRYPTO_ENABLED', 'true').lower() == 'true'

# Feature Flags
FEATURE_SIGNAL_BUS = os.getenv('FEATURE_SIGNAL_BUS', 'true').lower() == 'true'
FEATURE_THREAT_INTEL = os.getenv('FEATURE_THREAT_INTEL_HUB', 'true').lower() == 'true'
FEATURE_SECURITY_DASHBOARD = os.getenv('FEATURE_SECURITY_DASHBOARD', 'true').lower() == 'true'

# System Behavior
SAFE_MODE = os.getenv('SAFE_MODE', 'false').lower() == 'true'
AUTO_SYNC_ENABLED = os.getenv('AUTO_SYNC_ENABLED', 'false').lower() == 'true'

api_server = None
api_thread = None

# Track bot start time for uptime
bot_start_time = PST.localize(datetime.datetime.now())

# Track cog loading stats
loaded_count = 0
failed_count = 0

intents = discord.Intents.all()
class CustomBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

def start_api_server():
    """Start FastAPI server in background thread"""
    global api_server, api_thread
    try:
        # Import here to avoid circular imports
        from api.main import app as fastapi_app
        
        config = uvicorn.Config(
            app=fastapi_app,
            host=API_HOST,
            port=API_PORT,
            log_level='info' if API_DEBUG else 'warning',
            access_log=API_DEBUG
        )
        api_server = uvicorn.Server(config)
        
        # Run in background thread
        api_thread = Thread(target=api_server.run, daemon=True)
        api_thread.start()
        
        print(f"[API] ✅ FastAPI server started at http://{API_HOST}:{API_PORT}")
        print(f"[API] 📚 Swagger docs available at http://{API_HOST}:{API_PORT}/docs")
        return True
    except Exception as e:
        print(f"[API] ❌ Failed to start API server: {e}")
        return False

def get_prefix(bot, msg):
    """Dynamic prefix: ! for owner/DMs, mentions for others"""
    if not msg.guild:
        return '!'  # Allow ! prefix in DMs
    if msg.author.id == OWNER_ID:
        return '!'
    return commands.when_mentioned(bot, msg)

bot = CustomBot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None  # Disable default help, we'll load custom one
)

# ==================== SLASH COMMAND SYNC ====================

@bot.tree.command(name="sync", description="[Owner] Sync slash commands to Discord")
async def sync_commands(interaction: discord.Interaction):
    """Sync slash commands to Discord (Owner only)"""
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Owner only command", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(
            f"✅ Successfully synced {len(synced)} slash commands to Discord!\n"
            f"Commands should appear in 1-5 minutes.",
            ephemeral=True
        )
        print(f"[Sync] ✅ Synced {len(synced)} slash commands")
    except Exception as e:
        await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)
        print(f"[Sync] ❌ Sync failed: {e}")

# ==================== COG LOADING STRATEGY ====================
# 
# ARCHITECTURE:
# This bot is a Trust, Safety, Security & Governance Platform
# Think in terms of SIGNALS, POLICIES, CONFIDENCE, HUMAN-IN-LOOP, RESILIENCE
# Not individual features.
#
# LOADING STRATEGY:
# - Only load deterministic, low-risk, core infrastructure cogs
# - Experimental/ML-heavy features use feature flags (on-demand)
# - Moderation & compliance always active
# - Security systems always active
# 
# SIGNAL PIPELINE:
# All security events flow through central signal_bus for deduplication,
# correlation, and human-in-the-loop review before action.
#
# FEATURE FLAGS:
# All experimental features can be killed at runtime via feature_flags cog
# Safe Mode available for graceful degradation under stress
#
# HUMAN OVERSIGHT:
# - All AI decisions tracked in human_override_tracker
# - AI can abstain if confidence is low (abstention_policy)
# - Prompt injection detection prevents adversarial attacks
# - Override analytics reveal bias, patterns, disagreements
#
# MISSING FROM LEGACY COGS:
# These are NOT loaded (implement as services, not cogs):
# - risk_scoring_engine (import, don't register)
# - severity_priority_calculator (import, don't register)
# - false_positive_manager (import, don't register)
#
# ARCHIVES (low ROI, kept for reference):
# archives/bot_personality_system.py
# archives/quantum_safe_crypto.py
# archives/self_documenting_interface.py

import asyncio
import os
import importlib.util

async def load_cogs():
    """Load only essential security cogs to keep the bot clean and focused."""
    skip_dirs = {'.venv', '__pycache__', '.git', 'node_modules', '.github', 'backups', 'transcripts', 'api'}
    
    # WHITELIST: Load ONLY these essential cogs
    # Categorized by function and criticality
    essential_cogs = {
        # ========== CORE INFRASTRUCTURE (ALWAYS REQUIRED) ==========
        'signal_bus',                    # Central signal pipeline
        'feature_flags',                 # Feature flag & kill switch system
        'human_override_tracker',        # Track AI overrides and disagreements
        'abstention_policy',             # AI abstention & escalation logic
        'prompt_injection_detector',     # Prompt injection detection
        'override_dashboard',            # Human override analytics dashboard
        'abstention_alerts',             # Abstention alert & escalation system
        'data_manager',                  # Data persistence layer
        'automated_playbook_executor',   # SOAR playbook automation
        'ml_anomaly_detector',           # ML-based anomaly detection
        'threat_scorer',                 # Dynamic threat risk scoring
        'on_call_manager',               # On-call and escalation management
        'staff_scheduling_rotation',     # Staff scheduling, rotation, clock-in/out
        'threat_intel_hub',              # Threat intelligence & IOC tracking
        'ioc_manager',                   # IOC lifecycle management
        'dynamic_status',                # Dynamic threat level status system
        'autosync_control',              # Auto-sync file/folder monitoring control
        
        # ========== CORE SECURITY SYSTEMS ==========
        'security',                      # Base security operations
        'antinuke',                      # Anti-nuke protection
        'anti_phishing',                 # Phishing detection
        'anti_spam_system',              # Detect and prevent spam messages
        'anti_raid_system',              # Detect and prevent raid attacks
        'anti_impersonation_system',     # Prevent user impersonation attacks
        'anti_cryptocurrency_system',    # Detect and block crypto scams/malware
        'ransomware_early_warning',      # Ransomware early warning detection
        'credential_stuffing_guard',     # Credential stuffing detection and reporting
        'data_integrity_monitor',        # Integrity snapshot monitoring
        'session_hijack_detector',       # Session hijack monitoring
        'privilege_escalation_monitor',  # Privilege escalation tracking
        'secrets_exposure_watcher',      # Secrets exposure monitoring
        'permission_audit',              # Permission change tracking
        'role_change_monitor',           # Role change monitoring
        'webhook_abuse_prevention',      # Webhook abuse detection
        'intelligent_threat_response',   # Automated threat response system
        'decentralized_identity_verification', # Decentralized identity verification
        'honeytoken_deception',          # Honeytokens & deception traps
        # 'auto_escalation_system',        # Disabled: CommandRegistrationError - malformed command name
        # 'auto_quarantine_system',        # Disabled: TypeError in init
        
        # ========== CORE MODERATION ==========
        'automod',                       # Automated moderation
        'channel_moderation',            # Channel-level moderation
        'toxicity_detection',            # Toxicity detection
        'verification_system',           # User verification and role assignment
        # 'moderation_utilities',           # DISABLED: CommandRegistrationError (broken file, backed up as moderation_utilities_BROKEN.py)
        # 'advanced_logging',              # Disabled: CommandRegistrationError - duplicate logging
        'moderation_logging',            # Track all moderation actions
        'channel_lock_system',           # Lock/unlock channels
        # 'advanced_moderation',           # Disabled: CommandRegistrationError - duplicate commands
        'automod_filters',               # Link/invite/spam filtering
        'moderation_history',            # Mod action history & appeals
        'case_peer_review',              # Peer review for high-impact actions
        
        # ========== ADVANCED MODERATION & SECURITY (NEW) ==========
        'advanced_infractions_system',   # Progressive infraction system with escalation & appeals
        'mod_audit_log',                 # Audit all mod actions, detect abuse patterns
        'custom_automod_rules',          # Custom automod rules beyond Discord's built-in
        'invite_link_control',           # Detect & control Discord invite sharing
        'announcement_system',           # Server announcements & scheduled messages
        
        # ========== GROUP COMMAND SYSTEMS (PHASE 5) ==========
        'security_groups',               # Security command groups: /threat, /ioc, /scan, /monitor
        'moderation_groups',             # Moderation command groups: /infraction, /audit, /rule, /user
        'soc_groups',                    # SOC command groups: /incident, /dashboard, /alert, /investigate, /report
        'compliance_groups',             # Compliance command groups: /policy, /data, /consent, /compaudit, /framework
        
        # ========== CORE COMPLIANCE ==========
        'guardrails',                    # Safety guardrails
        'compliance_tools',              # Compliance tooling
        'data_retention_enforcer',       # Data retention policy enforcement
        'consent_audit_trail',           # Consent tracking
        'content_generator',             # Rules/TOS/guidelines generator
        
        # ========== SOC MONITORING & ANALYTICS ==========
        'security_dashboard',            # Real-time security metrics dashboard (renamed: securitydash)
        'audit_log_analyzer',            # Auto-analyze audit logs for threats
        'permission_auditor',            # Permission misconfiguration detection
        # 'security_reports',              # Disabled: CommandRegistrationError - duplicate command name
        'security_checklist',            # Security setup checklist & wizard
        'live_threat_status',            # Real-time threat level & bot status
        'executive_risk_dashboard',      # C-level security and risk reporting
        'incident_forecasting',          # Predictive incident forecasting
        'asset_management',              # IT asset inventory and tracking
        'soc_workflow_automation',       # SOAR-like workflow automation
        'threat_actor_attribution',      # Threat actor profiling and attribution
        'breach_impact_assessment',      # Quantify damage from security breaches
        'security_posture_scoring',      # Continuous security health scoring
        'vulnerability_remediation_tracker', # Track vulnerability remediation SLA
        'sla_metrics_dashboard',         # MTTR, MTTD, SLA compliance tracking
        'incident_pattern_correlation',  # Identify patterns and campaigns

        # ========== CLOUD & EXTERNAL SECURITY ==========
        'vendor_risk_management',        # Third-party vendor security assessment
        'mobile_security_manager',       # Mobile device & app security
        'api_security_governance',       # API inventory & security controls
        'cloud_security_posture',        # Multi-cloud security assessment
        'security_awareness_metrics',    # Training effectiveness & ROI tracking

        # Note: member_risk_profiler in cogs/security (not soc duplicate)
        # Note: threat_intelligence_synthesizer in cogs/threatintel (not soc duplicate)
        'live_event_search_engine',      # Full-text search across all events
        'forensics_evidence_manager',    # Forensic evidence chain of custody
        'digital_forensics_case_manager',# Digital forensics case manager
        'automated_response_playbooks',  # SOAR playbook automation
        'threat_hunting_campaigns',      # Proactive threat hunting
        'proactive_threat_hunting',      # MITRE pattern scanning of historical messages
        'realtime_soc_dashboard',        # Master SOC dashboard (renamed: socdash, sockealthcheck, smetrics)
        'compliance_policy_engine',      # Compliance policy monitoring
        'realtime_threat_feed',          # Threat intelligence feed + IOCs
        'security_baseline_scanner',     # Security config assessment
        'vuln_management_system',        # Vulnerability tracking & remediation
        
        # ========== CORE UTILITIES & DM COMMANDS ==========
        'dm_command_handler',            # DM commands and help system
        'command_reference',             # Command documentation and reference
        'basic_commands',               # Normal utility commands (ping, uptime, avatar, etc.)
        'server_setup',                  # SOC role and channel setup
        'user_dm_notifier',              # User DM notifications and broadcasts
        'welcome_farewell_system',       # Welcome/farewell messages
        'server_analytics',              # Server metrics and statistics
        # 'settings_manager',              # DISABLED: CommandLimitReached - consolidating to groups
        'invite_tracker',                # Invite usage tracking
        'maintenance_mode',              # Maintenance mode and service status
        # 'owner_commands',                # Disabled: TypeError - command registration issue
        'ticket_system',                 # Ticket / support system
        'post_mortem_workflow',         # Post-mortem workflow automation
        
        # ========== ENGAGEMENT SYSTEMS (NEW) ==========
        'reputation_system',             # Reputation system with giving/receiving
        'giveaway_system',               # Giveaway management with reaction-based entry
        'currency_system',               # Virtual economy with wallets and transactions
        'marketplace_system',            # Shop for items, roles, and perks with currency
        'achievement_system',            # Unlock achievements for milestones
        'reaction_roles',                # Reaction-based role assignment
        'starboard',                     # Message highlighting system
        'daily_challenges',              # Daily tasks for bonus rewards
        'advanced_suggestion_feedback',  # Advanced suggestions & feedback workflow
        'sentiment_trend_analysis',      # Sentiment analysis and trending
        'dynamic_faq_ai',                # Dynamic FAQ / knowledge AI
        
        # ========== SOC TRAINING & DRILLS ==========
        'advanced_threat_drills',        # Security drill and training system
        
        # ========== PHASE 12: PRODUCTION INFRASTRUCTURE (10 NEW SYSTEMS) ==========
        'auto_backup_system',            # Automated backup with retention policies
        'command_analytics',             # Command usage telemetry and analytics
        'error_reporting',               # Error tracking and owner notification
        'rate_limiting',                 # Rate limiting and anti-abuse protection
        'blacklist_system',              # User/guild blacklist system
        'performance_profiler',          # Command performance profiling
        # 'health_check_system',           # Disabled: ModuleNotFoundError
        'rate_limit_load_balancer',      # Rate-limit management & load balancer
        'scheduled_tasks_dashboard',     # Background task management
        # 'advanced_logging',              # DISABLED: ClientException - moderation_logging covers needs
        'webhook_notifications',         # External webhook integrations
        'bot_of_bots_health_monitor',    # Heartbeat for external monitor bot
        
        # ========== PHASE 10 EXPANSION (6 Advanced SOC Systems) ==========
        # 'quantified_risk_dashboard',     # Disabled: CommandRegistrationError - duplicate command name
        'threat_landscape_analyzer',     # Real-time threat environment assessment
        'detection_engineering_platform', # Detection rule creation & optimization
        # 'compliance_automation_suite',   # Disabled: CommandRegistrationError - duplicate command name
        'security_baseline_monitor',     # Configuration baseline drift detection
        'security_drill_system',         # Advanced security drill and exercises
        'simulation_system',             # Security simulation and training platform
        # 'security_posture_dashboard',    # Disabled: CommandRegistrationError
        # 'security_dashboard',            # Disabled: Duplicate dashboard command with main_dashboard
        # 'realtime_soc_dashboard',        # Disabled: Duplicate command registration
        'risk_register_system',          # Enterprise risk management
        'threat_actor_intelligence',     # Threat actor profiling & TTPs
        'security_metrics_kpis',         # MTTR, MTTD, SLA tracking
        'attack_surface_monitor',        # Attack surface & exposure tracking
        'security_event_correlation',    # Event correlation & pattern detection
        # 'security_reports',              # Disabled: CommandRegistrationError
        'security_training_system',      # Security awareness training
        'incident_playbook_library',     # Incident response playbooks
        'security_audit_trail',          # Immutable audit logging
        # 'realtime_soc_dashboard',        # Disabled: CommandRegistrationError - use main_dashboard instead
        # 'security_dashboard',            # Disabled: CommandRegistrationError - use main_dashboard instead

        # ========== NEW ADVANCED SYSTEMS (EXPANSION) ==========
        'insider_threat_detection',      # Insider threat behavioral analysis
        # 'breach_response_orchestration',  # Disabled: CommandRegistrationError
        'security_control_framework',    # NIST/CIS control assessment
        'realtime_observability_hub',    # Real-time system health & observability
        'third_party_risk_intelligence', # Supply chain & vendor risk monitoring
        
        # ========== WATCH SYSTEMS (COMPREHENSIVE 24/7 MONITORING) ==========
        'nightwatch_system',             # Night monitoring (7 PM - 7 AM, configurable)
        'daywatch_system',               # Day monitoring (7 AM - 7 PM, configurable)
        'userwatch_system',              # User activity monitoring and behavioral analysis
        'channelwatch_system',           # Channel activity tracking and engagement metrics
        'threatwatch_system',            # Security threat detection and threat actor tracking
        
        # ========== PHASE 11: ENTERPRISE SIEM-GRADE SYSTEMS (22 NEW SYSTEMS) ==========
        # SIEM Log Normalization & Query Language (3)
        'log_normalization_engine',      # SIEM-grade log normalization (ECS-inspired)
        'sentinel_query_language',       # KQL/SPL-inspired query language for logs
        'log_retention_tiers',           # Hot/warm/cold storage with compliance
        
        # MITRE ATT&CK Coverage Engine (3)
        'mitre_attack_mapper',           # Map alerts to ATT&CK tactics/techniques
        'attack_coverage_dashboard',     # ATT&CK coverage % and blind spots
        'technique_gap_analyzer',        # Detection gap analysis & prioritization
        
        # Zero-Trust Policy Enforcement (3)
        'zero_trust_policy_engine',      # Zero-trust continuous verification
        'dynamic_trust_scoring',         # Real-time trust scoring & decay
        'access_risk_enforcer',          # Risk-based access enforcement
        
        # Executive & Board Reporting (3)
        'board_risk_summary',            # Board-level risk summaries & SLA
        'executive_threat_briefing',     # Executive threat briefings (non-technical)
        'quarterly_security_posture_report', # Quarterly posture reports
        
        # Threat Attribution Confidence (2)
        'attribution_confidence_model',  # Confidence scoring for attributions
        'false_flag_detection',          # False flag & deception detection
        
        # Purple Team Mode (2)
        'purple_team_simulator',         # Red vs blue adversarial simulations
        'defense_efficacy_scorer',       # Defense effectiveness & MTTD/MTTR
        
        # Chain-of-Custody Legal Mode (2)
        'legal_hold_manager',            # Legal hold & immutable evidence locking
        'court_admissible_exporter',     # Court-admissible forensic exports
        
        # SOC Health Intelligence (2)
        'soc_fatigue_predictor',         # Analyst burnout & overload prediction
        'alert_noise_optimizer',         # Alert noise reduction & suppression
        
        # Supply Chain Threat Intelligence (2)
        'supply_chain_risk_engine',      # Supply chain & vendor threat intel
        'dependency_threat_monitor',     # Dependency CVE tracking & risk

        # ========== LOGGING & AUDIT ==========
        'action_logging',                # Server-wide action logging
        
        # ========== TIER-2: MEMORY SUBSYSTEM (6 NEW COGS) ==========
        'context_cache',                 # Contextual information caching for rapid decision-making
        'semantic_similarity_engine',    # Semantic query matching and similarity scoring
        'conversation_history_manager',  # Conversation tracking and context preservation
        'knowledge_graph_builder',       # Knowledge graph construction and querying
        'vector_embedding_store',        # Vector embedding storage and similarity search
        'memory_lifecycle_manager',      # Memory retention and lifecycle policies
        
        # ========== TIER-2: ADVERSARY SUBSYSTEM (6 NEW COGS) ==========
        'adversary_behavior_profiler',   # Profile adversary tactics and techniques
        'attack_tree_analyzer',          # Attack tree analysis and path enumeration
        'deception_system',              # Honeypot and deception management
        'attacker_intent_classifier',    # Classify adversary intent and motivation
        'threat_emulation_engine',       # Simulate adversary attacks for testing
        'adversary_learning_system',     # Learn from incidents and adapt defenses
        
        # ========== TIER-2: DECISION ENGINE (6 NEW COGS) ==========
        'multi_criteria_decision_making', # Multi-criteria decision analysis (MCDA)
        'utility_maximizer',              # Utility calculation and optimization
        'constraint_satisfaction_solver', # Constraint satisfaction problem solving
        'tradeoff_analyzer',              # Benefit-cost-risk tradeoff analysis
        'decision_explainability_engine', # Decision explanation and transparency
        'decision_tracking_system',       # Audit log and decision tracking
        
        # ========== TIER-1: AI GOVERNANCE (6 NEW SYSTEMS) ==========
        'model_registry',                # AI model tracking, versioning, risk classification
        'model_risk_assessment',         # Hallucination/bias/misuse risk scoring
        'ai_decision_audit',             # Full decision traceability and explainability
        'confidence_threshold_enforcer', # Confidence-driven human escalation
        'red_team_ai_simulator',         # Adversarial testing framework for AI
        'ai_kill_switch',                # Emergency AI shutdown (global + per-module)
        
        # ========== TIER-1: RESILIENCE (6 NEW SYSTEMS) ==========
        'chaos_injector',                # Chaos engineering for resilience testing
        'blast_radius_analyzer',         # Failure cascade and impact analysis
        'graceful_degradation_engine',   # Automatic feature degradation under load
        'dependency_health_matrix',      # Real-time dependency status monitoring
        'resilience_scorecard',          # Resilience metrics tracking (MTTR, MTTF, availability)
        'auto_failover_simulator',       # Simulate failover scenarios and recovery
        
        # ========== TIER-1: CRYPTOGRAPHY (6 NEW SYSTEMS) ==========
        'key_rotation_service',          # Automatic key rotation and lifecycle
        'secret_lifecycle_manager',      # Secret provisioning, rotation, revocation, audit
        'encryption_policy_engine',      # Encryption requirement enforcement
        'token_scope_validator',         # Token scope validation and privilege control
        'credential_exposure_monitor',   # Detect and respond to credential leaks
        'crypto_compliance_mapper',      # Map crypto to compliance frameworks (GDPR/HIPAA/PCI)
    }
    
    global loaded_count, failed_count
    loaded_count = 0
    failed_count = 0
    
    for root, dirs, files in os.walk('./cogs'):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                cog_name = file[:-3]
                
                # Only load whitelisted cogs
                if cog_name not in essential_cogs:
                    continue
                
                rel_path = os.path.relpath(os.path.join(root, file), './cogs')
                module_path = rel_path.replace(os.sep, '.')[:-3]
                
                try:
                    await bot.load_extension(f'cogs.{module_path}')
                    loaded_count += 1
                    print(f"[Loader] ✅ {cog_name}")
                except Exception as e:
                    failed_count += 1
                    print(f"[Loader] ❌ {cog_name}: {str(e)[:80]}")
    
    print(f"\n[Loader] ✅ Loaded {loaded_count} essential cogs ({failed_count} failed)")
    print(f"[Loader] Command count: {len(list(bot.tree._get_all_commands()))} total")
    
    # Print TIER-1 system status
    print(f"\n[Systems] TIER-1 Configuration:")
    print(f"  - AI Governance: {'✅ ENABLED' if AI_GOVERNANCE_ENABLED else '❌ DISABLED'}")
    print(f"  - Resilience: {'✅ ENABLED' if RESILIENCE_ENABLED else '❌ DISABLED'}")
    print(f"  - Cryptography: {'✅ ENABLED' if CRYPTO_ENABLED else '❌ DISABLED'}")
    print(f"\n[Features] Core Flags:")
    print(f"  - Signal Bus: {'✅ ENABLED' if FEATURE_SIGNAL_BUS else '❌ DISABLED'}")
    print(f"  - Threat Intel: {'✅ ENABLED' if FEATURE_THREAT_INTEL else '❌ DISABLED'}")
    print(f"  - Security Dashboard: {'✅ ENABLED' if FEATURE_SECURITY_DASHBOARD else '❌ DISABLED'}")
    print(f"  - Safe Mode: {'⚠️ ACTIVE' if SAFE_MODE else '🟢 NORMAL'}")
    
    print(f"\n✅ All essential modules loaded. Connecting to Discord...")
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                   ✨ BOT READY FOR OPERATIONS ✨               ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

@bot.event
async def on_ready():
    """Bot ready event - set status and log connection"""
    # Set bot uptime tracking
    if not hasattr(bot, 'uptime'):
        bot.uptime = PST.localize(datetime.datetime.now())
    
    print(f"\n✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"📊 Connected to {len(bot.guilds)} guild(s)")
    print(f"👥 Watching {sum(g.member_count for g in bot.guilds)} users")
    
    # Log ready state
    logger = logging.getLogger('soc_bot')
    logger.info(f"Bot ready - {len(bot.guilds)} guilds, {sum(g.member_count for g in bot.guilds)} users")
    print("🎭 Dynamic status system will manage presence")
    
    # Auto-sync commands on startup
    try:
        print("[Sync] Syncing slash commands to Discord...")
        synced = await bot.tree.sync()
        print(f"[Sync] ✅ Successfully synced {len(synced)} slash commands to Discord!")
    except Exception as e:
        print(f"[Sync] ❌ Failed to sync commands: {e}")
    
    # Send startup embed to owner
    if OWNER_ID:
        try:
            print(f"[Startup] Attempting to send DM to owner {OWNER_ID}...")
            owner = await bot.fetch_user(OWNER_ID)
            print(f"[Startup] Found owner: {owner}")
            embed = discord.Embed(
                title="🤖 SOC Bot Startup Complete",
                description="Bot is now online and ready for operations",
                color=discord.Color.green(),
                timestamp=PST.localize(datetime.datetime.now())
            )
            embed.add_field(name="✅ Status", value="Online", inline=True)
            embed.add_field(name="🏛️ Guilds", value=str(len(bot.guilds)), inline=True)
            embed.add_field(name="👥 Total Users", value=str(sum(g.member_count for g in bot.guilds)), inline=True)
            embed.add_field(name="⚡ Slash Commands", value=str(len(list(bot.tree._get_all_commands()))), inline=True)
            embed.add_field(name="📦 Cogs Loaded", value=str(loaded_count), inline=True)
            embed.add_field(name="🎯 Commands", value=str(len(list(bot.tree._get_all_commands()))), inline=True)
            embed.add_field(name="� API Server", value=f"http://{API_HOST}:{API_PORT}", inline=True)
            embed.add_field(name="📚 API Docs", value=f"http://{API_HOST}:{API_PORT}/docs", inline=True)
            embed.add_field(name="⚙️ TIER-1 Systems", value=f"Governance: {'✅' if AI_GOVERNANCE_ENABLED else '❌'} | Resilience: {'✅' if RESILIENCE_ENABLED else '❌'} | Crypto: {'✅' if CRYPTO_ENABLED else '❌'}", inline=False)
            embed.add_field(name="�🆕 New Systems (Latest)", value="SOAR Playbook | Search | On-Call | Reports | Alerts | KB | Teams | Evidence | API | Slack", inline=False)
            embed.set_footer(text=f"Bot User ID: {bot.user.id}")
            await owner.send(embed=embed)
            print(f"[Startup] ✅ DM sent successfully to owner")
        except discord.Forbidden as e:
            print(f"❌ Cannot send startup DM to owner: DMs are closed - {e}")
        except discord.HTTPException as e:
            print(f"❌ Failed to send startup DM to owner: HTTP error {e}")
        except Exception as e:
            print(f"❌ Could not send startup DM to owner: {type(e).__name__}: {e}")

# ==================== GLOBAL LOGGING & MONITORING ====================
@bot.event
async def on_command(ctx):
    """Log all commands"""
    logger = logging.getLogger('soc_bot')
    logger.info(f"[COMMAND] {ctx.author} -> {ctx.command.name} in {ctx.guild}")
    
    # Get logging cog if available
    logging_cog = bot.get_cog('AdvancedLoggingCog')
    if logging_cog:
        logging_cog.log_command(ctx, ctx.command.name, str(ctx.args), "success")

@bot.event
async def on_member_join(member):
    """Global member join logging"""
    logger = logging.getLogger('soc_bot')
    logger.info(f"[MEMBER_JOIN] {member} joined {member.guild}")
    
    # Log via logging cog
    logging_cog = bot.get_cog('AdvancedLoggingCog')
    if logging_cog:
        logging_cog.log_event("MEMBER_JOIN", {
            "user": str(member),
            "user_id": member.id,
            "guild": str(member.guild),
            "account_age": (PST.localize(datetime.datetime.now()) - member.created_at).days
        })

@bot.event
async def on_member_remove(member):
    """Global member leave logging"""
    logger = logging.getLogger('soc_bot')
    logger.info(f"[MEMBER_LEAVE] {member} left {member.guild}")
    
    logging_cog = bot.get_cog('AdvancedLoggingCog')
    if logging_cog:
        logging_cog.log_event("MEMBER_LEAVE", {
            "user": str(member),
            "user_id": member.id,
            "guild": str(member.guild)
        })

@bot.event
async def on_message(message):
    """Global message logging"""
    if message.author == bot.user or message.author.bot:
        return
    
    logger = logging.getLogger('soc_bot')
    logger.debug(f"[MESSAGE] {message.author} in {message.channel}: {message.content[:50]}")
    
    logging_cog = bot.get_cog('AdvancedLoggingCog')
    if logging_cog:
        logging_cog.log_event("MESSAGE_CREATED", {
            "user": str(message.author),
            "user_id": message.author.id,
            "channel": str(message.channel),
            "content_length": len(message.content)
        })
    
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command. Use `!helpme` for a list of commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`\nUsage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided.\nUsage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't meet the requirements to use this command.")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")

warns = {}

if __name__ == '__main__':
    async def main():
        print("\n")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                    🚀 SOC BOT INITIALIZING...                  ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print("📂 Loading cogs and modules...")
        await load_cogs()
        print("✅ All modules loaded.")
        print()
        
        # Start API server
        print("🌐 Starting API server...")
        if start_api_server():
            print("✅ API server initialized.")
        else:
            print("⚠️ API server failed to start, continuing with Discord bot only.")
        print()
        
        print("🔗 Connecting to Discord...")
        print()
        try:
            await bot.start(TOKEN)
        except KeyboardInterrupt:
            pass  # Graceful shutdown on Ctrl+C
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            # Clean up on shutdown
            print("\n")
            print("╔════════════════════════════════════════════════════════════════╗")
            print("║                    💤 SOC BOT SHUTTING DOWN                    ║")
            print("╚════════════════════════════════════════════════════════════════╝")
            
            # Shutdown API server
            if api_server:
                print("🌐 Shutting down API server...")
                try:
                    api_server.should_exit = True
                    print("🌐 API server stopped.")
                except Exception as e:
                    print(f"⚠️ Error stopping API server: {e}")
            
            print("🛑 Terminating bot process...")
            
            # Send shutdown embed to owner
            if OWNER_ID and not bot.is_closed():
                try:
                    print("[Shutdown] Attempting to send shutdown DM to owner...")
                    owner = await bot.fetch_user(OWNER_ID)
                    print(f"[Shutdown] Found owner: {owner}")
                    embed = discord.Embed(
                        title="💤 SOC Bot Shutting Down",
                        description="Bot is going offline",
                        color=discord.Color.orange(),
                        timestamp=PST.localize(datetime.datetime.now())
                    )
                    embed.add_field(name="Status", value="🔴 Offline", inline=True)
                    embed.add_field(name="Uptime", value=str(PST.localize(datetime.datetime.now()) - bot_start_time).split('.')[0], inline=True)
                    embed.add_field(name="Cleanup", value="In Progress", inline=True)
                    embed.set_footer(text=f"Bot User ID: {bot.user.id}")
                    await owner.send(embed=embed)
                    print("[Shutdown] ✅ Shutdown DM sent successfully to owner")
                except discord.Forbidden as e:
                    print(f"❌ Cannot send shutdown DM to owner: DMs are closed - {e}")
                except discord.HTTPException as e:
                    print(f"❌ Failed to send shutdown DM to owner: HTTP error {e}")
                except Exception as e:
                    print(f"❌ Could not send shutdown DM to owner: {type(e).__name__}: {e}")
            
            # Save all data before shutdown
            print("💾 Saving all data...")
            data_manager = bot.get_cog('DataManager')
            if data_manager:
                data_manager.save_data()
                print("✅ Data saved successfully")
            
            if not bot.is_closed():
                print("🔌 Closing connection...")
                await bot.close()
            print("✅ Cleanup complete.")
            print("👋 Goodbye!\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
