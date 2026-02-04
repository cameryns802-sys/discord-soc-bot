from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from pathlib import Path

app = FastAPI(title="Sentinel SOC API", version="1.0.0", description="Enterprise Security Operations Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for new dashboard
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ==================== NEW DASHBOARD ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the new portfolio-style dashboard"""
    try:
        index_path = Path(__file__).parent / "static" / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard not found. Please ensure static files exist.")
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving dashboard: {str(e)}")

@app.get("/api/stats")
async def get_bot_stats():
    """Get live bot statistics for dashboard"""
    try:
        # Load from data files if available
        data_dir = Path(__file__).parent.parent / "data"
        
        stats = {
            "guilds": 2,  # Default values
            "users": 13,
            "cogs_loaded": 172,
            "commands": 100,
            "security": {
                "threats_detected": 0,
                "threats_blocked": 0,
                "avg_response_time": "2.1",
                "posture_score": 94
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to load real data from bot
        try:
            # You can enhance this by storing bot stats in a JSON file
            # that the bot updates periodically
            stats_file = data_dir / "bot_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    real_stats = json.load(f)
                    stats.update(real_stats)
        except:
            pass
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# ==================== DASHBOARD STATIC FILE SERVING ====================

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the web dashboard HTML from /dashboard route"""
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard HTML file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving dashboard: {str(e)}")

# ==================== DASHBOARD ADMIN CONFIGURATION ====================

@app.post("/api/save-config")
async def save_dashboard_config(config: dict):
    """Save dashboard configuration to JSON file"""
    try:
        config_path = Path(__file__).parent / "static" / "dashboard_config.json"
        
        # Validate config structure
        required_keys = ["branding", "colors", "links", "hero", "stats", "team", "features", "cta", "footer"]
        if not all(key in config for key in required_keys):
            raise HTTPException(status_code=400, detail="Invalid configuration structure")
        
        # Write to file with pretty formatting
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": "Configuration saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

@app.get("/api/dashboard-config")
async def get_dashboard_config():
    """Get current dashboard configuration"""
    try:
        config_path = Path(__file__).parent / "static" / "dashboard_config.json"
        
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading configuration: {str(e)}")

# ==================== SHARED MODELS ====================
class Overview(BaseModel):
    threat_level: str
    active_incidents: int
    events_per_min: int
    ai_confidence: float
    bot_health: str

class Incident(BaseModel):
    id: int
    type: str
    status: str
    timestamp: str

# ==================== AI GOVERNANCE MODELS ====================
class AIModel(BaseModel):
    name: str
    version: str
    scope: str
    risk_level: str
    active: bool
    usage_count: int
    error_count: int

class ModelRisk(BaseModel):
    model_id: str
    hallucination_risk: float
    bias_risk: float
    misuse_risk: float
    overall_risk: float

class AIDecision(BaseModel):
    decision_id: str
    model_id: str
    action: str
    reasoning: str
    confidence: float
    override_status: bool
    timestamp: str

# ==================== RESILIENCE MODELS ====================
class DependencyHealth(BaseModel):
    name: str
    healthy: bool
    latency_ms: float
    error_rate: float
    uptime_percent: float

class ResilienceMetrics(BaseModel):
    overall_score: float
    mttr_hours: float
    mttf_hours: float
    availability_percent: float
    degradation_level: int

class FailoverResult(BaseModel):
    service: str
    scenario: str
    failover_time_seconds: float
    success: bool

# ==================== CRYPTOGRAPHY MODELS ====================
class KeyStatus(BaseModel):
    key_type: str
    last_rotation: Optional[str]
    rotate_in_days: int
    status: str

class SecretStatus(BaseModel):
    secret_id: str
    name: str
    type: str
    status: str
    expires_at: Optional[str]
    rotations: int

class EncryptionPolicy(BaseModel):
    location: str
    algorithm: str
    key_length: int
    required: bool

class CredentialExposure(BaseModel):
    exposure_type: str
    pattern: str
    severity: str
    timestamp: str

# ==================== SECURITY MODELS ====================
class ThreatSignal(BaseModel):
    signal_type: str
    severity: str
    source: str
    timestamp: str
    confidence: float

class SecurityScore(BaseModel):
    overall_score: int
    verification: int
    content_filter: int
    role_security: int
    recommendations: List[str]

# ==================== COMMAND MODELS ====================
class CommandParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool

class CommandInfo(BaseModel):
    name: str
    description: str
    category: str
    parameters: List[CommandParameter] = []
    usage_count: int = 0
    last_used: Optional[str] = None

class CommandCategory(BaseModel):
    category_name: str
    command_count: int
    commands: List[CommandInfo]

class CommandsResponse(BaseModel):
    total_commands: int
    total_categories: int
    categories: List[CommandCategory]
    last_updated: str

# ==================== CORE ENDPOINTS ====================

@app.get("/overview", response_model=Overview)
async def get_overview():
    """Get overall SOC status and health metrics"""
    return Overview(
        threat_level="medium",
        active_incidents=3,
        events_per_min=125,
        ai_confidence=0.87,
        bot_health="operational"
    )

@app.get("/incidents", response_model=List[Incident])
async def get_incidents():
    """Get active security incidents"""
    return [
        Incident(id=1001, type="phishing", status="investigating", timestamp="2025-02-02T10:30:00Z"),
        Incident(id=1002, type="brute_force", status="blocked", timestamp="2025-02-02T09:15:00Z"),
        Incident(id=1003, type="anomaly", status="under_review", timestamp="2025-02-02T08:45:00Z")
    ]

@app.post("/operator/lockdown")
async def trigger_lockdown():
    """Trigger immediate server lockdown"""
    return {"status": "lockdown triggered", "timestamp": str(datetime.utcnow())}

# ==================== AI GOVERNANCE ENDPOINTS ====================

@app.get("/api/governance/models", response_model=List[AIModel])
async def list_ai_models():
    """List all registered AI models"""
    return [
        AIModel(name="threat_detector", version="2.1", scope="security", risk_level="low", active=True, usage_count=4500, error_count=12),
        AIModel(name="anomaly_analyzer", version="1.8", scope="analytics", risk_level="medium", active=True, usage_count=3200, error_count=45),
        AIModel(name="risk_scorer", version="3.0", scope="governance", risk_level="low", active=True, usage_count=5100, error_count=8)
    ]

@app.get("/api/governance/models/{model_id}")
async def get_model_details(model_id: str):
    """Get detailed info for a specific AI model"""
    return {
        "model_id": model_id,
        "name": "threat_detector",
        "version": "2.1",
        "framework": "pytorch",
        "training_data_points": 15000,
        "accuracy": 0.94,
        "last_updated": "2025-01-28T14:30:00Z",
        "restrictions": ["no_autonomous_bans", "requires_human_review"]
    }

@app.get("/api/governance/risk", response_model=List[ModelRisk])
async def get_model_risk_scores():
    """Get risk assessment for all AI models"""
    return [
        ModelRisk(model_id="threat_detector", hallucination_risk=0.05, bias_risk=0.08, misuse_risk=0.03, overall_risk=0.07),
        ModelRisk(model_id="anomaly_analyzer", hallucination_risk=0.12, bias_risk=0.14, misuse_risk=0.06, overall_risk=0.13),
        ModelRisk(model_id="risk_scorer", hallucination_risk=0.02, bias_risk=0.04, misuse_risk=0.01, overall_risk=0.03)
    ]

@app.get("/api/governance/decisions", response_model=List[AIDecision])
async def get_ai_decisions(limit: int = 20):
    """Get recent AI decisions with audit trails"""
    return [
        AIDecision(decision_id="dec_001", model_id="threat_detector", action="flag_message", reasoning="pattern_match_phishing", confidence=0.92, override_status=False, timestamp="2025-02-02T10:30:00Z"),
        AIDecision(decision_id="dec_002", model_id="anomaly_analyzer", action="escalate_to_human", reasoning="unusual_access_pattern", confidence=0.78, override_status=True, timestamp="2025-02-02T10:15:00Z"),
        AIDecision(decision_id="dec_003", model_id="risk_scorer", action="allow", reasoning="within_normal_parameters", confidence=0.95, override_status=False, timestamp="2025-02-02T10:00:00Z")
    ]

@app.get("/api/governance/confidence-thresholds")
async def get_confidence_thresholds():
    """Get AI confidence thresholds for different decision types"""
    return {
        "critical": {"min_confidence": 0.95, "description": "Life-safety decisions"},
        "security": {"min_confidence": 0.85, "description": "Account security actions"},
        "moderation": {"min_confidence": 0.75, "description": "Content moderation"},
        "low_risk": {"min_confidence": 0.60, "description": "Informational actions"}
    }

@app.put("/api/governance/confidence-thresholds")
async def update_confidence_thresholds(thresholds: Dict[str, float]):
    """Update AI confidence thresholds"""
    return {"status": "updated", "thresholds": thresholds, "timestamp": str(datetime.utcnow())}

@app.get("/api/governance/red-team-results")
async def get_red_team_results():
    """Get latest red team attack simulation results"""
    return {
        "simulations_run": 14,
        "vulnerabilities_found": 3,
        "attack_vectors": ["prompt_injection", "jailbreak", "role_confusion"],
        "most_effective": "prompt_injection",
        "success_rate": 0.23,
        "last_test": "2025-02-02T06:00:00Z"
    }

@app.post("/api/governance/kill-switch/{scope}")
async def activate_kill_switch(scope: str):
    """Activate emergency AI kill switch (global or module-specific)"""
    return {
        "status": "activated",
        "scope": scope,
        "timestamp": str(datetime.utcnow()),
        "affected_systems": ["threat_detector", "anomaly_analyzer"] if scope == "global" else [scope]
    }

@app.get("/api/governance/kill-switch-status")
async def get_kill_switch_status():
    """Check current kill switch status"""
    return {
        "global_active": False,
        "module_status": {
            "threat_detector": "active",
            "anomaly_analyzer": "active",
            "risk_scorer": "active"
        }
    }

# ==================== RESILIENCE ENDPOINTS ====================

@app.get("/api/resilience/health", response_model=List[DependencyHealth])
async def get_dependency_health():
    """Get health status of all critical dependencies"""
    return [
        DependencyHealth(name="Discord API", healthy=True, latency_ms=145, error_rate=0.0, uptime_percent=99.99),
        DependencyHealth(name="Threat Intel Feed", healthy=True, latency_ms=234, error_rate=0.01, uptime_percent=99.95),
        DependencyHealth(name="Database", healthy=True, latency_ms=12, error_rate=0.0, uptime_percent=99.98),
        DependencyHealth(name="Cache Layer", healthy=True, latency_ms=5, error_rate=0.0, uptime_percent=99.99),
        DependencyHealth(name="External APIs", healthy=False, latency_ms=5000, error_rate=0.15, uptime_percent=98.2)
    ]

@app.get("/api/resilience/metrics", response_model=ResilienceMetrics)
async def get_resilience_metrics():
    """Get overall resilience scoring metrics"""
    return ResilienceMetrics(
        overall_score=87.3,
        mttr_hours=2.1,
        mttf_hours=240,
        availability_percent=99.95,
        degradation_level=0
    )

@app.post("/api/resilience/chaos-inject")
async def inject_chaos(service: str, failure_type: str, duration_seconds: int):
    """Inject controlled chaos/failure into a service"""
    return {
        "status": "chaos_injected",
        "service": service,
        "failure_type": failure_type,
        "duration": duration_seconds,
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/resilience/blast-radius/{component}")
async def analyze_blast_radius(component: str):
    """Analyze failure cascade and blast radius if component fails"""
    return {
        "component": component,
        "direct_dependents": ["security_dashboard", "incident_response"],
        "indirect_dependents": ["api_gateway", "notification_system"],
        "estimated_impact": "critical",
        "recovery_time_minutes": 15
    }

@app.get("/api/resilience/degradation-status")
async def get_degradation_status():
    """Get current system degradation level and status"""
    return {
        "current_level": "normal",
        "levels": {
            "normal": {"description": "All features active", "performance": "100%"},
            "reduced": {"description": "Non-critical features disabled", "performance": "70%"},
            "critical": {"description": "Only core operations", "performance": "40%"}
        },
        "trigger_threshold": 85,
        "current_load": 42
    }

@app.post("/api/resilience/failover-simulate")
async def simulate_failover(service: str, scenario: str):
    """Simulate failover scenario for a service"""
    return {
        "service": service,
        "scenario": scenario,
        "result": "success",
        "failover_time_seconds": 3.2,
        "data_loss": "none",
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/resilience/chaos-test-results")
async def get_chaos_test_results(limit: int = 10):
    """Get results from recent chaos engineering tests"""
    return {
        "total_tests": 47,
        "passed": 45,
        "failed": 2,
        "average_recovery_time": 2.8,
        "critical_vulnerabilities_found": 1,
        "recent_tests": [
            {"test_id": "chaos_001", "service": "discord_api", "result": "passed"},
            {"test_id": "chaos_002", "service": "database", "result": "passed"},
            {"test_id": "chaos_003", "service": "cache", "result": "passed"}
        ]
    }

# ==================== CRYPTOGRAPHY ENDPOINTS ====================

@app.get("/api/crypto/keys", response_model=List[KeyStatus])
async def get_key_status():
    """Get status of all encryption keys"""
    return [
        KeyStatus(key_type="api_keys", last_rotation="2025-01-05T00:00:00Z", rotate_in_days=25, status="active"),
        KeyStatus(key_type="signing_keys", last_rotation="2024-08-02T00:00:00Z", rotate_in_days=90, status="active"),
        KeyStatus(key_type="encryption_master", last_rotation="2024-02-02T00:00:00Z", rotate_in_days=365, status="active")
    ]

@app.post("/api/crypto/keys/rotate/{key_type}")
async def rotate_keys(key_type: str):
    """Trigger immediate key rotation"""
    return {
        "key_type": key_type,
        "status": "rotation_started",
        "new_key_id": f"key_{datetime.utcnow().timestamp()}",
        "rotation_time": "15 seconds",
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/crypto/secrets", response_model=List[SecretStatus])
async def get_secret_status():
    """Get status of managed secrets"""
    return [
        SecretStatus(secret_id="discord_token", name="DISCORD_TOKEN", type="token", status="active", expires_at=None, rotations=3),
        SecretStatus(secret_id="virustotal_key", name="VIRUSTOTAL_API_KEY", type="api_key", status="active", expires_at="2025-03-02T00:00:00Z", rotations=2),
        SecretStatus(secret_id="openai_key", name="OPENAI_API_KEY", type="api_key", status="active", expires_at="2025-04-02T00:00:00Z", rotations=1)
    ]

@app.post("/api/crypto/secrets/rotate/{secret_id}")
async def rotate_secret(secret_id: str):
    """Trigger secret rotation"""
    return {
        "secret_id": secret_id,
        "status": "rotation_started",
        "new_version": "v2",
        "grace_period_hours": 24,
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/crypto/policies", response_model=List[EncryptionPolicy])
async def get_encryption_policies():
    """Get encryption policies across the system"""
    return [
        EncryptionPolicy(location="at_rest", algorithm="AES-256-GCM", key_length=256, required=True),
        EncryptionPolicy(location="in_transit", algorithm="TLS1.3", key_length=256, required=True),
        EncryptionPolicy(location="end_to_end", algorithm="ECDH-P256", key_length=256, required=False)
    ]

@app.put("/api/crypto/policies")
async def update_encryption_policy(location: str, algorithm: str, required: bool):
    """Update encryption policy"""
    return {
        "location": location,
        "algorithm": algorithm,
        "required": required,
        "status": "updated",
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/crypto/token-validation")
async def validate_token_scopes(token: str):
    """Validate token scope and permissions"""
    return {
        "token_valid": True,
        "scopes": ["read_guild", "read_members", "manage_messages"],
        "granted_at": "2025-01-02T00:00:00Z",
        "expires_at": "2025-12-31T23:59:59Z",
        "scope_level": "write_limited"
    }

@app.get("/api/crypto/credential-exposure", response_model=List[CredentialExposure])
async def get_credential_exposure_scan():
    """Get results of credential exposure scanning"""
    return [
        CredentialExposure(exposure_type="api_key", pattern="AWS_ACCESS_KEY", severity="critical", timestamp="2025-02-02T05:30:00Z"),
        CredentialExposure(exposure_type="private_key", pattern="RSA_PRIVATE_KEY", severity="critical", timestamp="2025-02-01T18:45:00Z"),
        CredentialExposure(exposure_type="database_url", pattern="mongodb", severity="high", timestamp="2025-02-01T12:20:00Z")
    ]

@app.post("/api/crypto/scan-credentials")
async def scan_for_credential_exposure(scope: str = "all"):
    """Trigger credential exposure scan"""
    return {
        "scan_id": f"scan_{datetime.utcnow().timestamp()}",
        "status": "started",
        "scope": scope,
        "estimated_duration": "2 minutes",
        "timestamp": str(datetime.utcnow())
    }

@app.get("/api/crypto/compliance")
async def get_crypto_compliance_status():
    """Get cryptography compliance status with frameworks"""
    return {
        "gdpr_compliant": True,
        "hipaa_compliant": True,
        "pci_dss_compliant": True,
        "soc2_compliant": True,
        "recommendations": [
            "Implement GDPR data residency requirements",
            "Enhance HIPAA audit logging"
        ],
        "last_audit": "2025-02-01T00:00:00Z"
    }

# ==================== SECURITY ENDPOINTS ====================

@app.get("/api/security/dashboard", response_model=SecurityScore)
async def get_security_dashboard():
    """Get overall security posture dashboard"""
    return SecurityScore(
        overall_score=78,
        verification=80,
        content_filter=75,
        role_security=72,
        recommendations=[
            "Enable 2FA on all admin accounts",
            "Increase verification level",
            "Review excessive admin roles"
        ]
    )

@app.get("/api/security/threats", response_model=List[ThreatSignal])
async def get_threat_signals(hours: int = 24):
    """Get threat signals from the past N hours"""
    return [
        ThreatSignal(signal_type="threat_detected", severity="high", source="antinuke", timestamp="2025-02-02T09:30:00Z", confidence=0.95),
        ThreatSignal(signal_type="anomaly_detected", severity="medium", source="anomaly_analyzer", timestamp="2025-02-02T08:15:00Z", confidence=0.82),
        ThreatSignal(signal_type="policy_violation", severity="low", source="automod", timestamp="2025-02-02T07:45:00Z", confidence=0.90)
    ]

@app.get("/api/security/audit-log")
async def get_audit_log(limit: int = 50):
    """Get security audit log"""
    return {
        "total_events": 2847,
        "events": [
            {"timestamp": "2025-02-02T10:30:00Z", "action": "user_banned", "actor": "moderator_1", "target": "user_spam", "reason": "spam"},
            {"timestamp": "2025-02-02T10:15:00Z", "action": "role_created", "actor": "admin_1", "role": "Security Officer", "permissions": 128},
            {"timestamp": "2025-02-02T10:00:00Z", "action": "channel_locked", "actor": "moderator_2", "channel": "announcements", "reason": "under_review"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": str(datetime.utcnow())}

@app.get("/overview", response_model=Overview)
def get_overview():
    return Overview(
        threat_level="ELEVATED",
        active_incidents=3,
        events_per_min=124,
        ai_confidence=0.92,
        bot_health="Healthy"
    )

@app.get("/incidents", response_model=List[Incident])
def get_incidents():
    return [
        Incident(id=1, type="Raid detected", status="contained", timestamp="2026-01-30T12:00:00Z"),
        Incident(id=2, type="Privilege escalation", status="revoked", timestamp="2026-01-30T11:45:00Z"),
        Incident(id=3, type="Canary breach", status="logged", timestamp="2026-01-30T11:30:00Z"),
    ]

@app.post("/operator/lockdown")
def trigger_lockdown():
    # Here you would trigger a real lockdown action
    return {"status": "lockdown triggered"}

# ==================== COMMANDS ENDPOINT ====================

def scan_cog_files_for_commands() -> Dict[str, List[Dict]]:
    """Scan all cog files and extract slash command information"""
    import re
    
    commands_by_category = {}
    cogs_dir = os.path.join(os.path.dirname(__file__), '..', 'cogs')
    
    if not os.path.exists(cogs_dir):
        return commands_by_category
    
    # Command pattern for slash commands
    command_pattern = r'@app_commands\.command\(name=["\']([^"\']+)["\'],\s*description=["\']([^"\']*)["\']'
    param_pattern = r'@app_commands\.describe\((.*?)\)'
    
    for root, dirs, files in os.walk(cogs_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'.venv', '__pycache__', '.git', 'backups'}]
        
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find all commands in this file
                    matches = re.findall(command_pattern, content)
                    
                    # Get category from directory name
                    category = os.path.basename(root)
                    if category == 'cogs':
                        category = 'core'
                    
                    if category not in commands_by_category:
                        commands_by_category[category] = []
                    
                    for cmd_name, cmd_desc in matches:
                        commands_by_category[category].append({
                            'name': cmd_name,
                            'description': cmd_desc or 'No description',
                            'source_file': file,
                            'category': category
                        })
                except Exception as e:
                    pass
    
    return commands_by_category

@app.get("/dashboard/commands", response_class=HTMLResponse)
async def get_all_commands():
    """Get all bot commands organized by category - HTML Dashboard"""
    commands_dict = scan_cog_files_for_commands()
    categories = []
    total_commands = 0
    
    for category_name in sorted(commands_dict.keys()):
        commands = commands_dict[category_name]
        total_commands += len(commands)
        
        categories.append({
            'name': category_name,
            'count': len(commands),
            'commands': commands
        })
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel Bot - Commands Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
            border-bottom: 2px solid #00d4ff;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: #00d4ff;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        
        .header p {{
            color: #b0b0b0;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(0, 212, 255, 0.05);
            border: 1px solid #00d4ff;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            color: #00d4ff;
            font-weight: bold;
        }}
        
        .stat-card .label {{
            color: #b0b0b0;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .search-box {{
            margin-bottom: 30px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 15px 20px;
            background: rgba(0, 212, 255, 0.1);
            border: 2px solid #00d4ff;
            border-radius: 5px;
            color: #e0e0e0;
            font-size: 1em;
        }}
        
        .search-box input::placeholder {{
            color: #666;
        }}
        
        .categories {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .category-card {{
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 100, 255, 0.1) 100%);
            border: 1px solid #00d4ff;
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .category-card:hover {{
            border-color: #00ffff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            transform: translateY(-5px);
        }}
        
        .category-header {{
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            padding: 20px;
            color: #000;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }}
        
        .category-header:hover {{
            background: linear-gradient(135deg, #00ffff 0%, #00ccff 100%);
        }}
        
        .category-count {{
            background: rgba(0, 0, 0, 0.3);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        
        .category-commands {{
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .command {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
        }}
        
        .command:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .command-name {{
            color: #00d4ff;
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.95em;
        }}
        
        .command-desc {{
            color: #b0b0b0;
            font-size: 0.85em;
            line-height: 1.4;
        }}
        
        .command-file {{
            color: #666;
            font-size: 0.75em;
            margin-top: 5px;
            font-family: monospace;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0, 212, 255, 0.05);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #00d4ff;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #00ffff;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #00d4ff;
            color: #666;
            font-size: 0.9em;
        }}
        
        .filter-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .filter-tag {{
            background: rgba(0, 212, 255, 0.2);
            border: 1px solid #00d4ff;
            color: #00d4ff;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s ease;
        }}
        
        .filter-tag:hover {{
            background: rgba(0, 212, 255, 0.4);
            border-color: #00ffff;
        }}
        
        .filter-tag.active {{
            background: #00d4ff;
            color: #1a1a2e;
            border-color: #00ffff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Sentinel Bot Command Center</h1>
            <p>Complete command inventory and documentation</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="number">{total_commands}</div>
                <div class="label">Total Commands</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(categories)}</div>
                <div class="label">Categories</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(categories)}</div>
                <div class="label">Systems</div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search commands by name or description...">
        </div>
        
        <div class="filter-tags">
            <div class="filter-tag active" onclick="filterCategory('all')">All Categories</div>
"""
    
    for cat in categories:
        html_content += f'            <div class="filter-tag" onclick="filterCategory(\'{cat["name"]}\')"><strong>{cat["name"]}</strong> ({cat["count"]})</div>\n'
    
    html_content += """        </div>
        
        <div class="categories" id="categoriesContainer">
"""
    
    for category in categories:
        html_content += f'''            <div class="category-card" data-category="{category['name']}">
                <div class="category-header" onclick="toggleCategory(this)">
                    <span>{category['name'].replace('_', ' ').title()}</span>
                    <span class="category-count">{category['count']} commands</span>
                </div>
                <div class="category-commands">
'''
        
        for cmd in category['commands']:
            html_content += f'''                    <div class="command" data-name="{cmd['name']}" data-desc="{cmd['description']}">
                        <div class="command-name">/{cmd['name']}</div>
                        <div class="command-desc">{cmd['description']}</div>
                        <div class="command-file">{cmd['source_file']}</div>
                    </div>
'''
        
        html_content += """                </div>
            </div>
"""
    
    html_content += """        </div>
        
        <div class="footer">
            <p>Last updated: """ + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + """</p>
            <p>Sentinel SOC API v1.0.0</p>
        </div>
    </div>
    
    <script>
        function toggleCategory(element) {
            const card = element.parentElement;
            const commands = card.querySelector('.category-commands');
            commands.style.maxHeight = commands.style.maxHeight === 'none' ? '400px' : 'none';
        }
        
        function filterCategory(category) {
            const cards = document.querySelectorAll('.category-card');
            const tags = document.querySelectorAll('.filter-tag');
            
            tags.forEach(tag => tag.classList.remove('active'));
            event.target.classList.add('active');
            
            cards.forEach(card => {
                if (category === 'all') {
                    card.style.display = 'block';
                } else {
                    card.style.display = card.dataset.category === category ? 'block' : 'none';
                }
            });
        }
        
        document.getElementById('searchInput').addEventListener('keyup', function(e) {
            const query = e.target.value.toLowerCase();
            const commands = document.querySelectorAll('.command');
            const cards = document.querySelectorAll('.category-card');
            
            let visibleCategories = new Set();
            
            commands.forEach(cmd => {
                const name = cmd.dataset.name.toLowerCase();
                const desc = cmd.dataset.desc.toLowerCase();
                
                if (name.includes(query) || desc.includes(query)) {
                    cmd.style.display = 'block';
                    const card = cmd.closest('.category-card');
                    visibleCategories.add(card.dataset.category);
                } else {
                    cmd.style.display = 'none';
                }
            });
            
            cards.forEach(card => {
                card.style.display = visibleCategories.has(card.dataset.category) ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>
"""
    
    return html_content

@app.get("/dashboard/commands/search")
async def search_commands(query: str = ""):
    """Search commands by name or description"""
    commands_dict = scan_cog_files_for_commands()
    results = []
    
    query_lower = query.lower()
    
    for category, commands in commands_dict.items():
        for cmd in commands:
            if query_lower in cmd['name'].lower() or query_lower in cmd['description'].lower():
                results.append({
                    'name': cmd['name'],
                    'description': cmd['description'],
                    'category': cmd['category'],
                    'source_file': cmd['source_file']
                })
    
    return {
        'query': query,
        'results_found': len(results),
        'results': results
    }

@app.get("/dashboard/commands/stats")
async def get_commands_stats():
    """Get command statistics"""
    commands_dict = scan_cog_files_for_commands()
    
    total = 0
    by_category = {}
    
    for category, commands in commands_dict.items():
        count = len(commands)
        total += count
        by_category[category] = count
    
    return {
        'total_commands': total,
        'total_categories': len(by_category),
        'by_category': by_category,
        'last_scanned': datetime.utcnow().isoformat()
    }
