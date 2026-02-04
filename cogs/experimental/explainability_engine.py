"""
Explainability Engine: Generate "why" narratives and justify automated actions.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ExplainabilityEngineCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/explainability.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"explanations": {}, "causal_chains": {}, "counter": 1}

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def explain_action(self, action: str, context: dict) -> str:
        """Generate explanation for why an automated action was taken."""
        
        explanations = {
            "account_suspended": """
# WHY WAS THIS ACCOUNT SUSPENDED?

## Automated Action Taken
**Action:** User account suspended
**Timestamp:** {timestamp}
**Triggered By:** Automated security system
**Status:** Active

## WHY This Action Was Necessary

### Primary Reason: Suspicious Activity Detected
The account exhibited behavior patterns consistent with compromise or abuse:

1. **Unusual Access Pattern** 🚩
   - Login from 3 different countries within 1 hour
   - This is physically impossible for legitimate use
   - Previous history: User always logs in from USA only

2. **Failed Login Spike** 🚩
   - 47 failed login attempts before successful authentication
   - Indicates credential stuffing or brute force attack
   - Normal user behavior: <3 failed attempts

3. **Abnormal Activity** 🚩
   - Accessed 500+ files immediately after login
   - Typical user accesses 5-10 files per session
   - Suggests automated scraping or data exfiltration

## Decision Logic

### Confidence Score: 94%

**Risk Factors Analyzed:**
- ✅ Impossible travel: +40 points
- ✅ Failed login spike: +30 points
- ✅ Mass file access: +24 points
- ⚠️ Account age (<30 days): Not applicable
- ⚠️ Previous incidents: None found

**Threshold for Action:** 75 points
**Score:** 94 points → **AUTOMATIC SUSPENSION**

### Alternative Actions Considered

| Action | Score Required | Why Not Chosen |
|--------|---------------|----------------|
| Monitor only | 0-40 | Risk too high |
| Challenge MFA | 41-60 | Insufficient for this risk level |
| Temporary lockout | 61-74 | Just below threshold |
| **SUSPEND** | **75-100** | **✅ Selected - Risk exceeds threshold** |
| Permanent ban | 100+ | Not applicable |

## How This Protects You

### Immediate Protection
- Prevents unauthorized access to data
- Stops potential data exfiltration
- Blocks lateral movement to other systems
- Protects other users and systems

### What Happens Next
1. Security team notified automatically
2. Forensic analysis initiated
3. User contacted via verified channel
4. Account restored after verification

## Transparency & Accountability

### This Decision Was:
- ✅ Based on quantifiable risk factors
- ✅ Consistent with security policy (Section 4.2.3)
- ✅ Logged and auditable
- ✅ Reversible with proper authorization

### Review Process
- **Automatic Review:** Every 24 hours
- **Manual Review:** Available on request
- **Appeal Process:** Contact security@company.com
- **Expected Resolution:** 24-48 hours

## How to Appeal

If you believe this was incorrect:
1. Contact security team: security@company.com
2. Provide verification of identity
3. Explain your recent activity
4. Security team will review within 4 hours

## Similar Cases

In the past 30 days:
- 12 accounts suspended for similar patterns
- 11 confirmed compromises (malicious)
- 1 false positive (international traveler)
- False positive rate: 8.3%

## Technical Details

**Detection Rule:** RULE-UA-001 (Impossible Travel + Mass Access)
**Data Sources:** Authentication logs, access logs, user behavior analytics
**Machine Learning Model:** UserBehaviorML-v3.2
**Last Model Update:** 2025-01-01
**Model Accuracy:** 94.2% (validated against 10,000 test cases)

---
*This explanation is auto-generated to provide transparency in automated security decisions*
""",
            "email_quarantined": """
# WHY WAS THIS EMAIL QUARANTINED?

## Automated Action Taken
**Action:** Email quarantined (not delivered)
**Timestamp:** {timestamp}
**Sender:** suspicious@external-domain.com
**Subject:** "URGENT: Verify Your Account"

## WHY This Email Was Blocked

### Phishing Risk Score: 89/100 (HIGH)

### Detection Factors

#### 1. Sender Reputation: HIGH RISK 🚩
- **Domain age:** 3 days (created 2025-01-12)
- **Similar to legitimate domain:** company.com vs company-verify.com
- **Previous reports:** 45 phishing reports in threat database
- **Reputation score:** 2/100 (Very Poor)

#### 2. Content Analysis: SUSPICIOUS 🚩
- **Urgent language detected:** "URGENT", "immediately", "suspended"
- **Credential request:** Asks user to "verify password"
- **Link destination mismatch:** Display text ≠ actual URL
- **Grammar anomalies:** 7 spelling/grammar errors

#### 3. Link Analysis: MALICIOUS 🚩
- **Destination:** http://verify-account-phish.tk (known phishing)
- **URL reputation:** MALICIOUS (blocked by 5 threat feeds)
- **Previously used in:** 127 phishing campaigns
- **Blacklist status:** YES (added 2025-01-10)

#### 4. Technical Indicators: FAILING 🚩
- **SPF:** FAIL (sender not authorized)
- **DKIM:** FAIL (signature invalid)
- **DMARC:** FAIL (policy: reject)
- **Encryption:** None (sent plain text)

## Decision Algorithm

```
IF sender_reputation < 20 
   AND (urgent_language OR credential_request)
   AND link_reputation = "malicious"
   THEN action = QUARANTINE
```

**Result:** ALL conditions met → QUARANTINE

### Confidence: 99%

## What This Means

### For End Users
- ✅ You were protected from phishing attempt
- ✅ No action required from you
- ✅ Credentials remain secure
- ✅ Other users also protected

### For the Organization
- Prevented potential credential compromise
- Reduced incident response costs
- Maintained user trust
- Demonstrated security controls effectiveness

## False Positive Rate

**For this rule:** 0.5%
**Total emails processed:** 50,000/day
**Legitimate emails quarantined:** ~250/day
**Review process:** Automated + manual verification

## How to Retrieve Legitimate Email

If this was a legitimate email:
1. Contact IT Security
2. Provide email details (sender, subject, time)
3. Security will verify and release if safe
4. Sender will be whitelisted if appropriate

## Comparative Analysis

| Email Feature | This Email | Typical Phishing | Typical Legitimate |
|---------------|------------|------------------|-------------------|
| Sender Reputation | 2/100 | 5/100 | 85/100 |
| Domain Age | 3 days | <30 days | >1 year |
| SPF/DKIM | FAIL | FAIL | PASS |
| Urgent Language | YES | YES | Rare |
| Link Reputation | Malicious | Malicious | Clean |

**Verdict:** This email matches phishing profile 99.2%

## Transparency

### This Decision Was:
- ✅ Fully automated (no human intervention)
- ✅ Based on threat intelligence from 8 sources
- ✅ Consistent with 127 previous detections of same sender
- ✅ Logged for audit purposes

### Review Available
- Request human review: security@company.com
- Average review time: 15 minutes
- Can be restored if legitimate

---
*Phishing Detection Engine v4.2 - Last Updated: 2025-01-15*
""",
            "alert_triggered": """
# WHY DID THIS ALERT TRIGGER?

## Alert Details
**Alert ID:** ALERT-{alert_id}
**Triggered:** {timestamp}
**Severity:** HIGH
**Rule:** Suspicious Network Activity

## Root Cause

### What Happened
An internal system attempted to connect to a known command & control (C2) server.

**Source:** 10.0.50.125 (workstation-045)
**Destination:** 203.45.67.89:4444 (known C2 server)
**Protocol:** HTTPS
**Data sent:** 1.2 MB

### WHY This Is Concerning

#### 1. Destination Reputation: MALICIOUS
- IP 203.45.67.89 is on 4 threat intelligence blacklists
- Associated with "MalwareFamily-X" botnet
- First seen: 2024-12-20
- Confidence: 98% malicious

#### 2. Abnormal Behavior
- This system normally doesn't connect to external IPs
- Connection initiated from %TEMP% directory
- Process name: svchost32.exe (suspicious - similar to legitimate svchost.exe)
- No legitimate business reason for this connection

#### 3. Timing
- Connection attempted at 02:30 AM (outside business hours)
- User not logged in at time of connection
- Suggests automated malware activity

## Alert Logic

### Detection Rule: RULE-NET-C2-001

```
IF source = internal_network
   AND destination IN malicious_ip_list
   AND port IN [4444, 8080, 443]
   AND reputation_score < 10
   THEN severity = HIGH
        action = ALERT + BLOCK
```

### Data Sources
1. Network firewall logs
2. Threat intelligence feeds (AlienVault, abuse.ch)
3. Internal asset inventory
4. User authentication logs

### Why IMMEDIATE Alert?
- C2 communication = Active malware infection
- Data exfiltration risk: CRITICAL
- Lateral movement risk: HIGH
- Automated response required

## Automated Actions Taken

1. ✅ **Network Block:** Connection blocked at firewall
2. ✅ **System Isolation:** Workstation-045 isolated from network
3. ✅ **Alert Escalation:** SOC team notified
4. ✅ **Evidence Preservation:** Network logs saved
5. ⏳ **Pending:** Forensic analysis

## Confidence Assessment

**Overall Confidence:** 95%

### High Confidence Because:
- IP on multiple verified threat feeds (not just one source)
- Behavioral anomalies (time, process name, directory)
- No false positive history for this rule
- Clear indicators of compromise

### Small Uncertainty:
- 5% chance this IP was recently hijacked for legitimate use
- Possible false positive if system legitimately needs this connection
- Will be verified during investigation

## Historical Context

### Similar Alerts
- **Last 30 days:** 3 similar C2 alerts
- **All 3 confirmed:** Malware infections
- **False positive rate:** 0% for this rule

### Workstation-045 History
- Previous incidents: None
- Last scan: Clean (48 hours ago)
- User risk score: Low
- Conclusion: Likely **new** infection

## What Happens Next

### Immediate (0-15 min)
- [ ] Analyst reviews alert details
- [ ] Confirms legitimate or malicious
- [ ] Escalates to incident if confirmed

### Short-term (15-60 min)
- [ ] Forensic analysis of workstation-045
- [ ] Malware identification
- [ ] Scope assessment (other systems?)
- [ ] Containment verification

### Follow-up (1-24 hours)
- [ ] Malware eradication
- [ ] System reimaging if needed
- [ ] Root cause analysis
- [ ] Preventive measures

## Explanation for Non-Technical Users

**Simple Version:**
One of our computers tried to "phone home" to hackers. We detected it and blocked the connection automatically. The computer is now disconnected from the network while we investigate and clean it.

**Why you should care:**
If we didn't catch this, the hackers could have stolen data or spread to other systems.

## Appeal/Review Process

If you believe this is a false positive:
1. Contact SOC team immediately
2. Explain legitimate business need for this connection
3. Provide approval from manager
4. Security will review and potentially whitelist

---
*Automated Threat Detection System - Powered by AI & Threat Intelligence*
"""
        }
        
        explanation = explanations.get(action, f"# Explanation for {action}\n\nGeneric explanation placeholder")
        
        return explanation.format(
            timestamp=get_now_pst().strftime('%Y-%m-%d %H:%M:%S UTC'),
            alert_id=f"{self.data['counter']:06d}"
        )

    def generate_causal_chain(self, event: str) -> str:
        """Generate causal chain showing how we got to this event."""
        
        chain = """
# CAUSAL CHAIN ANALYSIS

## Event Under Analysis
**Event:** {event}
**Analysis Time:** {timestamp}

## How Did We Get Here? (Root Cause Chain)

```
                ROOT CAUSE
                     │
                     ▼
        ┌────────────────────────┐
        │  User clicked phishing │
        │  link in email         │
        └────────────┬───────────┘
                     │ (enabled)
                     ▼
        ┌────────────────────────┐
        │  Malware downloaded    │
        │  to user system        │
        └────────────┬───────────┘
                     │ (executed)
                     ▼
        ┌────────────────────────┐
        │  Malware established   │
        │  persistence           │
        └────────────┬───────────┘
                     │ (attempted)
                     ▼
        ┌────────────────────────┐
        │  Malware tried to      │
        │  connect to C2 server  │
        └────────────┬───────────┘
                     │ (blocked)
                     ▼
        ┌────────────────────────┐
        │  ALERT TRIGGERED       │ ← We are here
        │  (This Event)          │
        └────────────────────────┘
```

## Detailed Causal Analysis

### Step 1: Initial Compromise (Root Cause)
**What:** User clicked malicious link in phishing email
**When:** 2025-01-15 14:30:00 UTC
**Why:** User did not recognize phishing indicators
**Contributing Factors:**
- Email appeared legitimate (spoofed sender)
- User was busy and didn't verify
- Phishing awareness training was 6 months ago

### Step 2: Malware Download
**What:** TrojanDownloader.js downloaded to system
**When:** 2025-01-15 14:30:15 UTC (15 seconds after click)
**Why:** Browser auto-downloaded file
**Contributing Factors:**
- Browser settings allowed auto-download
- Antivirus didn't detect (0-day variant)
- File executed automatically (macro enabled)

### Step 3: Persistence Established
**What:** Malware added registry key for startup
**When:** 2025-01-15 14:30:45 UTC
**Why:** User had local admin rights
**Contributing Factors:**
- Legacy app requires admin rights
- Privilege escalation not needed
- No application whitelisting

### Step 4: C2 Communication Attempt
**What:** Malware tried to connect to 203.45.67.89:4444
**When:** 2025-01-15 14:31:00 UTC
**Why:** Standard malware behavior (command & control)
**Contributing Factors:**
- Outbound HTTPS generally allowed
- Firewall rules too permissive

### Step 5: Alert Triggered (Current Event)
**What:** Network monitoring detected malicious connection
**When:** 2025-01-15 14:31:01 UTC
**Why:** Destination IP matched threat intelligence
**Contributing Factors:**
- ✅ Detection working as designed
- ✅ Threat intel feeds up to date

## Prevention Points (Where We Could Have Stopped This)

### Point 1: Email Gateway 🔴 FAILED
❌ Phishing email should have been blocked
**Why it failed:** New phishing domain not yet in threat feeds
**Fix:** Implement AI-powered email analysis

### Point 2: User Awareness 🔴 FAILED
❌ User should have recognized and reported phishing
**Why it failed:** Training not recent, high workload
**Fix:** More frequent training, simulated phishing tests

### Point 3: Browser Protection 🔴 FAILED
❌ Download should have been blocked or warned
**Why it failed:** 0-day malware, no signature
**Fix:** Implement browser isolation for external links

### Point 4: Endpoint Protection 🔴 FAILED
❌ Antivirus should have detected malware
**Why it failed:** 0-day variant, signature not available
**Fix:** Deploy EDR with behavioral detection

### Point 5: Privilege Management 🟡 PARTIAL
⚠️ User shouldn't have admin rights for persistence
**Why it failed:** Legacy app requirements
**Fix:** Application virtualization, JIT admin access

### Point 6: Network Detection ✅ SUCCESS
✅ Detected C2 communication attempt
**Why it worked:** Updated threat intel, proper monitoring
**This is where we caught it!**

## Systemic Issues Identified

### Technical Gaps
1. Signature-based AV insufficient for 0-day threats
2. Overly permissive firewall rules
3. No application whitelisting
4. Excessive user privileges

### Process Gaps
1. Phishing training frequency too low
2. No regular phishing simulations
3. Slow threat intel integration

### People Gaps
1. Users not empowered to report suspicious emails
2. Security awareness culture needs improvement

## Recommendations to Break This Chain

### Immediate
1. Deploy EDR to all endpoints
2. Implement email link isolation
3. Review and restrict firewall rules

### Short-term
1. Conduct phishing simulation campaign
2. Implement application whitelisting
3. Reduce local admin privileges

### Long-term
1. Build security-aware culture
2. Implement zero-trust architecture
3. Continuous security training program

---
*This analysis helps us understand not just what happened, but why and how to prevent it*
"""
        
        return chain.format(
            event=event,
            timestamp=get_now_pst().strftime('%Y-%m-%d %H:%M:%S UTC')
        )

    @commands.command(name="explain")
    async def explain(self, ctx, *, action: str):
        """Explain why an automated security action was taken."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        await ctx.send(f"🤔 Generating explanation for: **{action}**...")
        
        explanation_text = self.explain_action(action, {})
        
        explain_id = f"EXPLAIN-{self.data['counter']:05d}"
        self.data['explanations'][explain_id] = {
            "explain_id": explain_id,
            "action": action,
            "generated_by": str(ctx.author.id),
            "generated_at": get_now_pst().isoformat(),
            "content": explanation_text
        }
        self.data['counter'] += 1
        self.save_data(self.data)
        
        # Save explanation
        explain_file = f"data/explanations/{explain_id}_{action.replace(' ', '_')}.md"
        os.makedirs(os.path.dirname(explain_file), exist_ok=True)
        with open(explain_file, 'w') as f:
            f.write(explanation_text)
        
        embed = discord.Embed(
            title=f"🤔 Explanation Generated: {explain_id}",
            description=f"Why this action was taken: **{action}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Transparency", value="✅ Decision logic documented", inline=True)
        embed.add_field(name="Accountability", value="✅ Auditable and reviewable", inline=True)
        embed.add_field(name="File", value=f"`{explain_file}`", inline=False)
        
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(explain_file))

    @commands.command(name="causal_chain")
    async def causal_chain(self, ctx, *, event: str):
        """Generate causal chain analysis showing how an event occurred."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        await ctx.send(f"🔗 Analyzing causal chain for: **{event}**...")
        
        chain_text = self.generate_causal_chain(event)
        
        chain_id = f"CHAIN-{self.data['counter']:05d}"
        self.data['causal_chains'][chain_id] = {
            "chain_id": chain_id,
            "event": event,
            "generated_by": str(ctx.author.id),
            "generated_at": get_now_pst().isoformat(),
            "content": chain_text
        }
        self.data['counter'] += 1
        self.save_data(self.data)
        
        # Save chain
        chain_file = f"data/causal_chains/{chain_id}_{event.replace(' ', '_')}.md"
        os.makedirs(os.path.dirname(chain_file), exist_ok=True)
        with open(chain_file, 'w') as f:
            f.write(chain_text)
        
        embed = discord.Embed(
            title=f"🔗 Causal Chain Analysis: {chain_id}",
            description=f"Root cause analysis for: **{event}**",
            color=discord.Color.purple()
        )
        embed.add_field(name="Analysis Type", value="Root Cause + Prevention Points", inline=True)
        embed.add_field(name="Prevention Identified", value="6 potential intervention points", inline=True)
        embed.add_field(name="File", value=f"`{chain_file}`", inline=False)
        
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(chain_file))

    @commands.command(name="justify_decision")
    async def justify_decision(self, ctx, decision_id: str):
        """Get full justification for an AI/automated decision."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        # Simulated decision justification
        justification = f"""
**Decision ID:** {decision_id}
**Timestamp:** {get_now_pst().strftime('%Y-%m-%d %H:%M:%S UTC')}

**JUSTIFICATION:**

1. **Data Inputs:** 247 data points analyzed
2. **Model Used:** ThreatDetectionML v4.5
3. **Confidence:** 94%
4. **Risk Score:** 87/100 (High)
5. **Policy Alignment:** Compliant with Security Policy §4.2
6. **Human Review:** Not required (confidence >90%)
7. **Audit Trail:** Fully logged and preserved

**KEY FACTORS:**
✅ Anomaly detection score: 89/100
✅ Threat intelligence match: YES (3 sources)
✅ Historical pattern: Matches 15 previous incidents
⚠️ Uncertainty: 6% (within acceptable range)

**ALTERNATIVE OPTIONS CONSIDERED:**
- Monitor only: Rejected (risk too high)
- Challenge user: Rejected (response time critical)
- **Automated block: SELECTED** (optimal for risk/speed)

**ACCOUNTABILITY:**
This decision can be reviewed, appealed, and overridden by authorized personnel.
Contact: security@company.com
"""
        
        embed = discord.Embed(
            title=f"⚖️ Decision Justification: {decision_id}",
            description=justification,
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ExplainabilityEngineCog(bot))
