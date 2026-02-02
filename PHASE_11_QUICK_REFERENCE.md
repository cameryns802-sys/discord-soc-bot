# 🎯 PHASE 11: QUICK COMMAND REFERENCE

## 📊 SIEM Log Systems

### Log Normalization
```
!normalize_event <EVENT_TYPE> <key=value pairs>
!query_logs <key=value filters>
!log_taxonomy
!log_stats
```

### Sentinel Query Language (SQL)
```
!sql <query>                    # Execute query
!save_query <name> <query>      # Save for reuse
!run_saved_query <name>         # Run saved query
!list_queries                   # List all queries
```

### Log Retention
```
!retention_policy set hot=7 warm=30 cold=90
!tier_stats                     # Show tier distribution
!transition_logs                # Manual tier transition
```

---

## 🎯 MITRE ATT&CK

### ATT&CK Mapper
```
!map_attack <alert_id> <technique_id> <confidence>
!attack_coverage                # Coverage by tactic
!attack_techniques              # List all techniques
!attack_heatmap                 # Most detected techniques
```

### Coverage Dashboard
```
!attack_dashboard               # Comprehensive dashboard
!coverage_report                # Detailed report
```

### Gap Analyzer
```
!gap_analysis                   # Identify blind spots
!gap_priorities                 # Prioritized gaps
!gap_report                     # Executive report
```

---

## 🔒 Zero-Trust

### Policy Engine
```
!zt_add_policy <type> <condition> <action>
!zt_list_policies               # List all policies
!zt_verify <@user>              # Verify user
!zt_violations                  # Show violations
!zt_enforce <on/off>            # Toggle enforcement
!zt_dashboard                   # Policy dashboard
```

### Trust Scoring
```
!trust_score <@user>            # View score
!trust_adjust <@user> <delta>   # Adjust score
!trust_history <@user>          # Score history
!trust_leaderboard              # Top trusted users
!trust_dashboard                # Trust dashboard
```

### Access Risk Enforcer
```
!access_risk_scan <@user>       # Scan risk
!access_enforce                 # Enforce restrictions
!access_config <threshold>      # Configure thresholds
!access_log                     # View enforcement log
!access_dashboard               # Risk dashboard
```

---

## 👔 Executive Reporting

### Board Risk Summary
```
!board_risk_summary             # Generate summary
!board_sla_metrics              # SLA metrics
!board_trends                   # Quarterly trends
!board_record_metric <metric> <value>
!board_export                   # Export report
```

### Executive Briefing
```
!exec_briefing                  # Generate briefing
!exec_add_threat <name> <severity> <description>
!exec_threat_trends             # Analyze trends
!exec_resolve_threat <id>       # Resolve threat
!exec_threat_dashboard          # Threat dashboard
```

### Quarterly Reports
```
!quarterly_report <quarter>     # Generate report
!quarterly_compliance <metric> <status>
!quarterly_investment <recommendation>
!quarterly_compare <Q1> <Q2>    # Compare quarters
!quarterly_dashboard            # Quarterly dashboard
```

---

## 🔍 Threat Attribution

### Attribution Model
```
!attr_create <case_id> <actor> <confidence>
!attr_add_evidence <case_id> <type> <description>
!attr_hypothesis <case_id> <hypothesis> <confidence>
!attr_view <case_id>            # View details
!attr_list                      # List all
!attr_dashboard                 # Dashboard
```

### False Flag Detection
```
!falseflag_analyze <case_id>    # Analyze for false flags
!falseflag_add_indicator <case_id> <indicator> <evidence>
!falseflag_create_detection <case_id> <confidence>
!falseflag_list                 # List all detections
!falseflag_dashboard            # Dashboard
```

---

## 🟣 Purple Team

### Purple Team Simulator
```
!purple_simulate <scenario>     # Start simulation
!purple_scenarios               # List scenarios
!purple_history                 # View history
!purple_dashboard               # Dashboard
```

**Scenarios:** Ransomware, Phishing, APT, Insider, DDoS, SupplyChain, DataExfil, Credential

### Defense Efficacy
```
!defense_score <sim_id>         # Calculate score
!defense_metrics <sim_id>       # View metrics
!defense_leaderboard            # Top defenders
!defense_dashboard              # Dashboard
```

---

## ⚖️ Legal/Forensics

### Legal Hold Manager
```
!legalhold_create <case_id> <reason>
!legalhold_add_evidence <hold_id> <evidence_type> <description>
!legalhold_verify <hold_id>     # Verify integrity
!legalhold_list                 # List all holds
!legalhold_dashboard            # Dashboard
```

### Court Admissible Exporter
```
!court_export <hold_id>         # Export for court
!court_verify_export <export_id> # Verify export
!court_chain_custody <export_id> # Chain of custody
!court_dashboard                # Dashboard
```

---

## 👥 SOC Health

### Fatigue Predictor
```
!fatigue_log_shift <analyst_id> <hours> <alerts>
!fatigue_predict <analyst_id>   # Predict fatigue
!fatigue_team_status            # Team status
!fatigue_dashboard              # Dashboard
```

### Alert Noise Optimizer
```
!noise_log_alert <alert_id> <true/false>
!noise_suppress <rule_name> <condition>
!noise_analyze                  # Analyze noise
!noise_suppressions             # List rules
!noise_dashboard                # Dashboard
```

---

## 📦 Supply Chain

### Supply Chain Risk
```
!supply_add_vendor <name> <trust_score>
!supply_alert <vendor_name> <severity> <description>
!supply_risk_report             # Generate report
!supply_vendors                 # List vendors
!supply_dashboard               # Dashboard
```

### Dependency Monitor
```
!dep_add <name> <version>       # Add dependency
!dep_cve <dep_name> <cve_id> <severity> <description>
!dep_scan                       # Scan for CVEs
!dep_cves                       # List all CVEs
!dep_dashboard                  # Dashboard
```

---

## 📈 Quick Stats

**Total New Commands:** 85+  
**Total New Systems:** 22  
**Total New Code:** 5,200+ lines  
**Bot Total Commands:** 285+  
**Bot Total Systems:** 84

---

## 🚀 Example Workflows

### **Workflow 1: SIEM Investigation**
```bash
# 1. Query logs for security alerts in last 24h
!sql event.type == "security_alert" WHERE time > -24h

# 2. Check alert noise
!noise_analyze

# 3. Map alert to ATT&CK
!map_attack ALERT-001 T1078 high

# 4. Check coverage gaps
!gap_analysis
```

### **Workflow 2: Executive Briefing**
```bash
# 1. Generate board risk summary
!board_risk_summary

# 2. Add active threat
!exec_add_threat "Ransomware Campaign" CRITICAL "Targeting healthcare"

# 3. Generate quarterly report
!quarterly_report Q1-2026

# 4. Export for board meeting
!board_export
```

### **Workflow 3: Purple Team Exercise**
```bash
# 1. Start ransomware simulation
!purple_simulate Ransomware

# 2. Check defense score
!defense_score SIM-001

# 3. Check ATT&CK coverage
!attack_dashboard

# 4. Identify gaps
!gap_priorities
```

### **Workflow 4: Legal Investigation**
```bash
# 1. Create legal hold
!legalhold_create CASE-2026-001 "Data breach investigation"

# 2. Add evidence
!legalhold_add_evidence HOLD-001 message_log "Chat logs 2026-02-01"

# 3. Verify integrity
!legalhold_verify HOLD-001

# 4. Export for court
!court_export HOLD-001
```

### **Workflow 5: SOC Health Check**
```bash
# 1. Check analyst fatigue
!fatigue_team_status

# 2. Predict burnout
!fatigue_predict analyst_123

# 3. Optimize alert noise
!noise_analyze

# 4. Check trust scores
!trust_leaderboard
```

---

**Phase 11: SIEM-Grade Enterprise Expansion ✅**  
**Ready for deployment to production Discord servers** 🚀
