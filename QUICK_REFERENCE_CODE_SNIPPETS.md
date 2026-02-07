"""
SENTINEL v10 - QUICK REFERENCE & CODE SNIPPETS

Copy-paste ready code for common tasks.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CREATING & ROUTING EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

# Import what you need
from cogs.architecture.unified_event_schema import (
    UnifiedSecurityEvent, EventType, EventSeverity, EventContext, EventPayload
)
from cogs.architecture.event_router import event_router

# Create an event
event = UnifiedSecurityEvent(
    event_type=EventType.THREAT_DETECTED,
    severity=EventSeverity.HIGH,
    title="Unauthorized access attempt",
    description="User tried to access restricted channel",
    context=EventContext(
        source_module='permission_audit',
        source_system='discord',
        user_id=message.author.id,
        guild_id=message.guild.id
    ),
    payload=EventPayload(
        raw_data={'message': message.content},
        normalized_data={'action': 'unauthorized_access'}
    )
)

# Set confidence
event.confidence = 0.92  # High confidence
event.false_positive_score = 0.05  # Low false positive likelihood

# Route it
await event_router.route_event(event)


# ═══════════════════════════════════════════════════════════════════════════════
# MAKING AUTONOMOUS DECISIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Get decision orchestrator
orchestrator = bot.get_cog('DecisionOrchestrator')

# Make decision
decision = await orchestrator.make_decision(event)

# Check outcome
if decision['outcome'] == 'AUTOMATIC_REMEDIATION':
    # Auto-remediate
    print("Taking automatic action...")
    
elif decision['outcome'] == 'ESCALATE_TO_HUMAN':
    # Send to analyst
    print("Escalating to analyst...")
    
elif decision['outcome'] == 'MONITOR_ONLY':
    # Just watch
    print("Monitoring...")


# ═══════════════════════════════════════════════════════════════════════════════
# WORKING WITH THREAT GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

from cogs.graph_engine.threat_graph import threat_graph

# Add a user node
threat_graph.add_node(
    f"user_{user_id}",
    "user",
    {"name": username, "role": "member"}
)

# Add a role node
threat_graph.add_node(
    f"role_{role_id}",
    "role",
    {"name": role_name, "permissions": perms}
)

# Add relationship
threat_graph.add_edge(
    f"user_{user_id}",
    f"role_{role_id}",
    "ASSIGNED_TO"
)

# Mark as critical
threat_graph.mark_crown_jewel(f"role_{admin_role_id}")

# Find attack paths
paths = threat_graph.find_paths(
    f"user_{attacker_id}",
    f"role_{crown_jewel_id}"
)

# Calculate impact
blast_radius = threat_graph.get_blast_radius(f"user_{compromised_user_id}")
print(f"Blast radius: {blast_radius['cascade_affected']} nodes affected")

# Get stats
stats = threat_graph.get_statistics()
print(f"Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")


# ═══════════════════════════════════════════════════════════════════════════════
# INVESTIGATION WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════

# Get investigation assistant
investigator = bot.get_cog('InvestigationAssistant')

# Create new case
case = investigator.create_investigation(
    event_id=event.event_id,
    title="Phishing Incident - User Compromise"
)

# Add evidence
investigator.add_evidence(
    case['case_id'],
    {
        'type': 'discord_message',
        'timestamp': datetime.now(),
        'content': "Phishing link posted by user",
        'severity': 'HIGH'
    }
)

# Add hypothesis
investigator.add_hypothesis(
    case['case_id'],
    "User account was compromised via phishing",
    confidence=0.85
)

# Query case
case_data = investigator.cases[case['case_id']]
print(f"Evidence collected: {len(case_data['evidence'])}")
print(f"Hypotheses: {len(case_data['hypotheses'])}")


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNING SECURITY CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

from cogs.continuous_validation.control_validation_engine import bot.get_cog

validator = bot.get_cog('ControlValidationEngine')

# Test specific control
result = validator.test_control('antiphishing')
print(f"Antiphishing test: {result['result']}")

# Get coverage gaps
gaps = validator.get_coverage_gaps()
print(f"Coverage gaps found: {gaps['total_gaps']}")
for gap in gaps['gaps']:
    print(f"  - {gap['control']}: {gap['gap']:.0%}")


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTING IDENTITY THREATS
# ═══════════════════════════════════════════════════════════════════════════════

from cogs.identity_security.impossible_travel_detector import bot.get_cog

detector = bot.get_cog('ImpossibleTravelDetector')

# Check for impossible travel
threat = detector.check_impossible_travel(
    user_id="123456",
    new_location={
        "latitude": 34.0522,  # LA
        "longitude": -118.2437,
        "timestamp": datetime.now()
    }
)

if threat:
    print(f"THREAT: {threat['severity']}")
    print(f"Required speed: {threat['required_speed_kmh']:.0f} km/h")
    
    # Create event from this
    event = UnifiedSecurityEvent(
        event_type=EventType.THREAT_DETECTED,
        severity=EventSeverity.HIGH,
        title="Impossible travel detected",
        payload=EventPayload(raw_data=threat)
    )
    await event_router.route_event(event)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYZING ROOT CAUSE
# ═══════════════════════════════════════════════════════════════════════════════

from cogs.cognitive_reasoning.causal_inference_engine import bot.get_cog

reasoner = bot.get_cog('CausalInferenceEngine')

# Find root cause
analysis = reasoner.find_root_cause("symptom_event_id")
print(f"Root cause: {analysis['likely_root_cause']}")
print(f"Confidence: {analysis['confidence']:.0%}")
print(f"Chain: {' → '.join(analysis['chain'])}")

# Check causality
causality = reasoner.infer_causality("event_1_id", "event_2_id")
print(f"Event 1 caused Event 2: {causality['likely_causal']}")
print(f"Confidence: {causality['confidence']:.0%}")


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNING FOR EXTERNAL EXPOSURE
# ═══════════════════════════════════════════════════════════════════════════════

from cogs.external_exposure.internet_scanner import bot.get_cog

scanner = bot.get_cog('InternetScanner')

# Scan for exposures
findings = scanner.scan_for_exposures()
print(f"Exposures found: {len(findings['exposed_services'])}")
for exposure in findings['exposed_services']:
    scanner.add_exposure(exposure)
    print(f"  - {exposure['type']}: {exposure['description']}")


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT COMMANDS FOR OWNERS
# ═══════════════════════════════════════════════════════════════════════════════

# In cogs/core/dm_command_handler.py, add these:

@commands.command(name='eventstats')
@commands.is_owner()
async def event_stats(ctx):
    """View event router statistics"""
    from cogs.architecture.event_router import event_router
    
    stats = event_router.get_stats()
    
    embed = discord.Embed(
        title="📊 Event Router Stats",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Processed", value=stats['processed_events'], inline=True)
    embed.add_field(name="Dropped", value=stats['dropped_events'], inline=True)
    embed.add_field(name="Queue Size", value=stats['queue_size'], inline=True)
    
    for route, count in stats['subscribers'].items():
        embed.add_field(name=route, value=f"📋 {count} subs", inline=True)
    
    await ctx.send(embed=embed)


@commands.command(name='blastradius')
@commands.is_owner()
async def blast_radius(ctx, user_id: int):
    """Check blast radius if user compromised"""
    from cogs.graph_engine.threat_graph import threat_graph
    
    radius = threat_graph.get_blast_radius(f"user_{user_id}")
    
    embed = discord.Embed(
        title=f"💥 Blast Radius: User {user_id}",
        color=discord.Color.red()
    )
    
    embed.add_field(name="Direct Impact", value=radius['directly_affected'], inline=True)
    embed.add_field(name="Cascade Effect", value=radius['cascade_affected'], inline=True)
    embed.add_field(name="Crown Jewels at Risk", value=radius['crown_jewels_at_risk'], inline=True)
    embed.add_field(name="Risk Score", value=f"{radius['blast_radius_score']:.0%}", inline=True)
    
    await ctx.send(embed=embed)


@commands.command(name='attackpaths')
@commands.is_owner()
async def attack_paths(ctx, from_user: int, to_crown_jewel: str):
    """Find attack paths to crown jewel"""
    from cogs.graph_engine.threat_graph import threat_graph
    
    paths = threat_graph.find_paths(
        f"user_{from_user}",
        f"resource_{to_crown_jewel}"
    )
    
    embed = discord.Embed(
        title=f"🔴 Attack Paths Found: {len(paths)}",
        color=discord.Color.red()
    )
    
    for i, path in enumerate(paths[:5], 1):
        path_str = " → ".join([node.split('_')[1] for node in path])
        embed.add_field(name=f"Path {i} ({len(path)} hops)", value=path_str, inline=False)
    
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
# UPDATING EXISTING COGS TO USE v10 SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

# Example: Update anti_phishing.py

# OLD (v9):
# await signal_bus.emit(Signal(
#     signal_type=SignalType.THREAT_DETECTED,
#     ...
# ))

# NEW (v10):
async def on_message(self, message):
    if message.author.bot:
        return
    
    urls = extract_urls(message.content)
    for url in urls:
        if is_phishing(url):
            
            # Create unified event
            event = UnifiedSecurityEvent(
                event_type=EventType.THREAT_DETECTED,
                severity=EventSeverity.HIGH,
                title="Phishing URL detected",
                description=f"URL: {url}",
                context=EventContext(
                    source_module='anti_phishing',
                    source_system='discord',
                    user_id=message.author.id,
                    resource_id=message.channel.id,
                    guild_id=message.guild.id
                ),
                payload=EventPayload(
                    raw_data={'url': url, 'author': str(message.author)},
                    normalized_data={'phishing_url': url}
                )
            )
            
            # Set metrics
            event.confidence = 0.95
            event.false_positive_score = 0.01
            
            # Track entity
            event.link_entity(f"user_{message.author.id}")
            
            # Route
            await event_router.route_event(event)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING CODE
# ═══════════════════════════════════════════════════════════════════════════════

# Quick test of unified schema
async def test_event_creation():
    event = UnifiedSecurityEvent(
        event_type=EventType.THREAT_DETECTED,
        severity=EventSeverity.CRITICAL,
        title="Test Event"
    )
    
    assert event.event_id.startswith('EVT-')
    assert event.severity == EventSeverity.CRITICAL
    print("✓ Event creation works")
    
    # Test serialization
    data = event.to_dict()
    assert 'event_id' in data
    print("✓ Serialization works")
    
    # Test reconstruction
    event2 = UnifiedSecurityEvent.from_dict(data)
    assert event2.event_id == event.event_id
    print("✓ Reconstruction works")


# Test graph operations
def test_graph():
    from cogs.graph_engine.threat_graph import threat_graph
    
    # Add nodes
    threat_graph.add_node('user_1', 'user', {'name': 'John'})
    threat_graph.add_node('role_admin', 'role', {'name': 'Admin'})
    
    # Add edge
    threat_graph.add_edge('user_1', 'role_admin', 'ASSIGNED_TO')
    
    # Get stats
    stats = threat_graph.get_statistics()
    assert stats['total_nodes'] == 2
    assert stats['total_edges'] == 1
    print("✓ Graph operations work")


# Test decision making
async def test_decisions():
    orchestrator = bot.get_cog('DecisionOrchestrator')
    
    event = UnifiedSecurityEvent(
        event_type=EventType.THREAT_DETECTED,
        severity=EventSeverity.HIGH,
        title="Test"
    )
    event.confidence = 0.95
    
    decision = await orchestrator.make_decision(event)
    assert 'outcome' in decision
    assert 'reasoning' in decision
    print("✓ Decision making works")


# ═══════════════════════════════════════════════════════════════════════════════
# COMMON PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

# Pattern 1: Detect → Create Event → Route
async def security_module_pattern(threat_detected):
    if threat_detected:
        event = UnifiedSecurityEvent(
            event_type=EventType.THREAT_DETECTED,
            severity=EventSeverity.HIGH,
            title="Threat title"
        )
        await event_router.route_event(event)


# Pattern 2: Response Execution
async def execute_response(event, decision):
    if decision['outcome'] == 'AUTOMATIC_REMEDIATION':
        for action in decision.get('recommended_actions', []):
            # Execute action
            if action == 'delete_message':
                await event.payload.raw_data['message'].delete()
            elif action == 'timeout_user':
                # Timeout user
                pass
            elif action == 'escalate':
                # Send to analyst
                pass
        
        # Mark as applied
        event.automated_response_applied = True
        
        # Store event
        data_lake = bot.get_cog('DataLake')
        if data_lake:
            await data_lake.store_event(event)


# Pattern 3: Investigation Workflow
async def investigate_incident(event):
    investigator = bot.get_cog('InvestigationAssistant')
    
    # Create case
    case = investigator.create_investigation(event.event_id, event.title)
    
    # Gather evidence
    investigator.add_evidence(case['case_id'], {
        'type': 'event',
        'data': event.to_dict()
    })
    
    # Form hypothesis
    investigator.add_hypothesis(
        case['case_id'],
        f"Root cause: {event.description}",
        confidence=0.75
    )
    
    # Notify analysts
    # Send case to #investigations channel
    return case['case_id']
"""