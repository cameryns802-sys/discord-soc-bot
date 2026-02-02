"""
Remediation Recommender: Generate tailored remediation plans and training prompts.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class RemediationRecommenderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/remediation.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"remediation_plans": {}, "training_prompts": {}, "counter": 1}

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def generate_remediation_plan(self, incident_type: str, severity: str, findings: dict) -> str:
        """Generate tailored remediation plan based on incident."""
        
        plan_templates = {
            "phishing": """
# REMEDIATION PLAN: Phishing Incident
**Plan ID:** {plan_id}
**Incident Type:** Phishing Campaign
**Severity:** {severity}
**Generated:** {timestamp}

## EXECUTIVE SUMMARY
This remediation plan addresses gaps identified during phishing incident response and provides actionable steps to prevent recurrence.

## IMMEDIATE ACTIONS (0-24 hours) ✅

### 1. Verify Containment
- [ ] Confirm all malicious emails quarantined
- [ ] Verify sender domain/IP blocked at gateway
- [ ] Check no additional similar emails in queues
- [ ] Review spam filter effectiveness

### 2. User Account Security
- [ ] Force password resets completed for all affected users
- [ ] Enable MFA for accounts that clicked links
- [ ] Review recent activity for affected accounts
- [ ] Monitor for suspicious login attempts

### 3. Communication
- [ ] Send organization-wide phishing awareness alert
- [ ] Notify affected users individually
- [ ] Update security team on status
- [ ] Prepare executive briefing

## SHORT-TERM ACTIONS (1-7 days) 🔧

### 1. Technical Controls
- [ ] **Email Gateway:** Update phishing detection rules
  - Add sender patterns to blocklist
  - Enhance link analysis capabilities
  - Configure stricter attachment policies
  
- [ ] **User Awareness Systems:** Deploy banners for external emails
  - "[EXTERNAL]" tag in subject lines
  - Warning banners for links clicking
  - Hover-to-preview URL capabilities

- [ ] **SIEM/Monitoring:** Create alerts for similar patterns
  - Alert on bulk external emails with links
  - Monitor for credential-harvesting sites
  - Track email engagement metrics

### 2. User Training
- [ ] Schedule mandatory phishing awareness training
- [ ] Deploy simulated phishing campaign
- [ ] Create easy-to-reference reporting procedures
- [ ] Reward users who report phishing promptly

### 3. Process Improvements
- [ ] Review and update phishing response playbook
- [ ] Document lessons learned from this incident
- [ ] Update escalation procedures if needed
- [ ] Create quick reference guide for users

## LONG-TERM ACTIONS (1-4 weeks) 🛡️

### 1. Technology Enhancements
- [ ] **Email Security:** Evaluate advanced email protection solutions
  - AI-powered phishing detection
  - Sandbox for suspicious attachments
  - URL reputation checking
  
- [ ] **Authentication:** Enforce MFA organization-wide
  - Phase 1: Critical systems (Week 1)
  - Phase 2: Email and collaboration tools (Week 2)
  - Phase 3: All applications (Week 3-4)

- [ ] **Monitoring:** Enhance detection capabilities
  - User behavior analytics
  - Anomalous login detection
  - Credential stuffing alerts

### 2. Organizational Security Culture
- [ ] Conduct quarterly phishing simulations
- [ ] Create security champions program
- [ ] Establish easy reporting mechanisms
- [ ] Implement security awareness metrics

### 3. Vendor/Third-Party Management
- [ ] Review email security vendor SLAs
- [ ] Assess need for managed security services
- [ ] Evaluate threat intelligence feeds
- [ ] Consider security awareness platform

## PREVENTION STRATEGIES

### Technical Preventive Controls
1. **Email Authentication:** SPF, DKIM, DMARC enforcement
2. **Link Protection:** URL rewriting and sandboxing
3. **Attachment Scanning:** Deep content inspection
4. **User Reporting:** One-click phishing report button

### Administrative Preventive Controls
1. **Policy Updates:** Acceptable use and email policies
2. **Training Program:** Ongoing security awareness
3. **Incident Response:** Updated procedures
4. **Metrics:** Track and report phishing trends

### Monitoring & Detection
1. **Alert Tuning:** Refine email security alerts
2. **User Reports:** Encourage and track reporting
3. **Threat Intel:** Subscribe to phishing feeds
4. **Regular Testing:** Monthly simulated attacks

## SUCCESS METRICS

### Immediate (30 days)
- ✅ 100% of affected users' credentials reset
- ✅ Phishing detection rules updated
- ✅ Organization-wide training completed
- ✅ Zero similar phishing emails in 30 days

### Short-term (90 days)
- 📊 <5% click rate on simulated phishing
- 📊 >80% user reporting within 15 minutes
- 📊 MFA adoption >90%
- 📊 Email gateway blocking >95% phishing

### Long-term (6 months)
- 🎯 Phishing click rate <1%
- 🎯 Average time-to-report <5 minutes
- 🎯 100% MFA coverage
- 🎯 Zero successful phishing compromises

## FOLLOW-UP AUDIT

**Scheduled Date:** {audit_date}

Audit will verify:
1. All remediation actions completed
2. Controls operating effectively
3. Training effectiveness measured
4. No recurrence of similar incidents

## BUDGET CONSIDERATIONS

**Estimated Costs:**
- Email security enhancement: $5,000-$15,000
- Security awareness platform: $3,000-$10,000 annually
- Training materials/time: $2,000-$5,000
- MFA rollout: $1,000-$3,000

**Total Estimated:** $11,000 - $33,000

**ROI:** Prevention of one significant breach saves $100K+ in incident response, legal, and reputational costs.

## OWNERSHIP & ACCOUNTABILITY

| Action Item | Owner | Status | Due Date |
|-------------|-------|--------|----------|
| Email gateway updates | IT Security | ⏳ In Progress | Day 3 |
| User password resets | IT Operations | ✅ Complete | Day 1 |
| Training deployment | Security Awareness | ⏳ Scheduled | Week 2 |
| MFA rollout | IT Security | 📋 Planned | Week 3-4 |
| Follow-up audit | SOC Manager | 📋 Planned | Month 3 |

---
*This remediation plan should be reviewed and approved by security leadership before implementation*
""",
            "malware": """
# REMEDIATION PLAN: Malware Incident
**Plan ID:** {plan_id}
**Incident Type:** Malware Infection
**Severity:** {severity}
**Generated:** {timestamp}

## EXECUTIVE SUMMARY
This plan addresses malware containment, eradication, and preventive measures to reduce future risk.

## IMMEDIATE ACTIONS (0-24 hours) 🚨

### 1. Verify Eradication
- [ ] Confirm malware removed from all affected systems
- [ ] Verify no persistence mechanisms remain (registry, scheduled tasks)
- [ ] Check for lateral movement to other systems
- [ ] Validate systems clean via multiple AV scans

### 2. Network Security
- [ ] Block malware C2 servers at firewall
- [ ] Review and update IDS/IPS signatures
- [ ] Monitor for beaconing or callback attempts
- [ ] Isolate affected network segment if needed

### 3. Evidence Preservation
- [ ] Collect forensic images of affected systems
- [ ] Preserve memory dumps and logs
- [ ] Document malware variants and IOCs
- [ ] Share IOCs with threat intel community

## SHORT-TERM ACTIONS (1-7 days) 🔧

### 1. Endpoint Security Enhancement
- [ ] **EDR/Antivirus:** Update all signatures and definitions
- [ ] **Behavioral Detection:** Enable advanced threat detection
- [ ] **Application Whitelisting:** Implement for critical systems
- [ ] **Patch Management:** Accelerate patching schedule

### 2. User Education
- [ ] Train users on malware risks (email attachments, downloads)
- [ ] Demonstrate safe browsing practices
- [ ] Emphasize importance of updates
- [ ] Create incident reporting procedures

### 3. Access Controls
- [ ] Review and restrict local admin rights
- [ ] Implement principle of least privilege
- [ ] Disable unnecessary services and protocols
- [ ] Harden configurations per CIS benchmarks

## LONG-TERM ACTIONS (1-4 weeks) 🛡️

### 1. Technology Improvements
- [ ] **EDR Solution:** Deploy advanced endpoint detection and response
- [ ] **Email Security:** Sandbox suspicious attachments
- [ ] **Web Filtering:** Block malicious domains and categories
- [ ] **Backup Strategy:** Implement immutable backups

### 2. Vulnerability Management
- [ ] Conduct full vulnerability assessment
- [ ] Prioritize patching critical vulnerabilities
- [ ] Establish monthly patch cycle
- [ ] Implement vulnerability scanning automation

### 3. Incident Response Capabilities
- [ ] Update malware response playbooks
- [ ] Conduct tabletop exercise
- [ ] Acquire additional forensics tools
- [ ] Train team on malware analysis

## PREVENTION STRATEGIES

### Technical Controls
1. **Endpoint Protection:** EDR with behavioral analysis
2. **Network Segmentation:** Limit lateral movement
3. **Email Security:** Attachment sandboxing
4. **Web Filtering:** Block known malicious sites
5. **Patch Management:** Automated, regular patching

### Administrative Controls
1. **Policy:** Acceptable use, device management
2. **Training:** Quarterly security awareness
3. **Access Control:** Least privilege enforcement
4. **Change Management:** Controlled system changes

## SUCCESS METRICS

### 30 Days
- ✅ Zero malware detections on remediated systems
- ✅ EDR deployed to 100% of endpoints
- ✅ Critical vulnerabilities patched

### 90 Days
- 📊 <1 malware incident per month
- 📊 Mean time to detection <5 minutes
- 📊 Patch compliance >95%

### 6 Months
- 🎯 Zero successful malware infections
- 🎯 100% EDR coverage with active monitoring
- 🎯 Vulnerability backlog cleared

## ESTIMATED COSTS
- EDR solution: $15-$30 per endpoint/year
- Forensics tools: $5,000-$10,000
- Training: $2,000-$5,000
- **Total:** $10,000 - $20,000

---
*Review and approve before implementation*
""",
            "data_breach": """
# REMEDIATION PLAN: Data Breach
**Plan ID:** {plan_id}
**Incident Type:** Data Breach / Exfiltration
**Severity:** {severity}
**Generated:** {timestamp}

## EXECUTIVE SUMMARY
Comprehensive remediation plan addressing data breach response, regulatory compliance, and prevention.

## IMMEDIATE ACTIONS (0-72 hours) 🚨

### 1. Legal & Regulatory Compliance
- [ ] Notify legal team immediately
- [ ] Assess GDPR/CCPA notification requirements
- [ ] Prepare breach notification drafts
- [ ] Coordinate with data protection officer
- [ ] Document timeline for regulatory reporting

### 2. Containment Verification
- [ ] Confirm unauthorized access terminated
- [ ] Revoke compromised credentials
- [ ] Block exfiltration channels
- [ ] Verify no ongoing data access

### 3. Impact Assessment
- [ ] Identify all affected data categories
- [ ] Determine number of individuals impacted
- [ ] Classify data sensitivity (PII, PHI, financial)
- [ ] Assess business and reputational impact

## SHORT-TERM ACTIONS (1-14 days) 🔧

### 1. Notifications
- [ ] **Internal:** Executive team, board, legal, PR
- [ ] **Regulatory:** Notify authorities within 72 hours (GDPR)
- [ ] **Customers:** Prepare and send breach notifications
- [ ] **Media:** Coordinate public response with PR team

### 2. Technical Remediation
- [ ] **Access Controls:** Review and enhance authentication
- [ ] **Data Protection:** Encrypt sensitive data at rest
- [ ] **Monitoring:** Deploy DLP and data access monitoring
- [ ] **Logging:** Enable comprehensive audit logging

### 3. Forensics & Root Cause
- [ ] Complete forensic investigation
- [ ] Identify attack vector and timeline
- [ ] Document evidence and findings
- [ ] Determine how breach occurred

## LONG-TERM ACTIONS (2-12 weeks) 🛡️

### 1. Data Security Program
- [ ] **Data Inventory:** Catalog all sensitive data
- [ ] **Classification:** Implement data classification scheme
- [ ] **Encryption:** Encrypt data at rest and in transit
- [ ] **DLP:** Deploy data loss prevention tools
- [ ] **Access Governance:** Role-based access controls

### 2. Technical Enhancements
- [ ] **Zero Trust:** Implement zero-trust architecture
- [ ] **Network Segmentation:** Isolate sensitive data
- [ ] **CASB:** Cloud access security broker for SaaS
- [ ] **SIEM:** Centralized logging and alerting

### 3. Organizational Improvements
- [ ] Update data handling policies
- [ ] Mandatory privacy and security training
- [ ] Establish data breach response team
- [ ] Conduct annual data protection audits

## PREVENTION STRATEGIES

### Technical Preventive Controls
1. **Encryption:** All sensitive data encrypted
2. **Access Controls:** Strong authentication (MFA)
3. **Data Loss Prevention:** Monitor and block exfiltration
4. **Network Security:** Segment and monitor data flows
5. **Monitoring:** Real-time data access alerts

### Administrative Controls
1. **Data Governance:** Classification and handling policies
2. **Training:** Annual privacy and security training
3. **Vendor Management:** Third-party data security requirements
4. **Incident Response:** Updated breach response procedures

## SUCCESS METRICS

### 30 Days
- ✅ All affected individuals notified
- ✅ Regulatory notifications complete
- ✅ Root cause identified and fixed
- ✅ Enhanced monitoring deployed

### 90 Days
- 📊 100% sensitive data encrypted
- 📊 DLP deployed and tuned
- 📊 Zero unauthorized data access
- 📊 Privacy training completed

### 6 Months
- 🎯 Zero data breaches
- 🎯 <5 DLP policy violations per month
- 🎯 99.9% access logging coverage
- 🎯 Annual security audit passed

## BUDGET CONSIDERATIONS

**Estimated Costs:**
- DLP solution: $25,000-$50,000
- Encryption tools: $10,000-$20,000
- SIEM/logging: $15,000-$30,000
- Legal/consulting: $50,000-$150,000
- Customer notifications: $10,000-$50,000
- Credit monitoring (if applicable): $100,000-$500,000

**Total Estimated:** $210,000 - $800,000

**Note:** Costs vary significantly based on breach scope and regulatory requirements.

## REGULATORY COMPLIANCE

### GDPR Requirements
- [ ] Notify supervisory authority within 72 hours
- [ ] Notify affected individuals without undue delay
- [ ] Document breach in compliance register
- [ ] Assess need for data protection impact assessment

### CCPA Requirements
- [ ] Determine if 500+ California residents affected
- [ ] Notify California Attorney General if threshold met
- [ ] Provide free credit monitoring if unencrypted data exposed
- [ ] Update privacy policy with incident details

## OWNERSHIP

| Action | Owner | Due Date |
|--------|-------|----------|
| Legal notifications | Legal Team | Day 2 |
| Technical remediation | CISO | Week 2 |
| Customer notifications | Customer Success + Legal | Week 1 |
| DLP deployment | IT Security | Month 1 |
| Training program | Security Awareness | Month 2 |

---
*Critical: Legal review required before any external communications*
"""
        }
        
        template = plan_templates.get(incident_type.lower(), "# Remediation Plan\n\nCustom plan for {incident_type} - {severity}")
        
        plan_id = f"REM-{self.data['counter']:05d}"
        audit_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        return template.format(
            plan_id=plan_id,
            severity=severity,
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            audit_date=audit_date
        )

    def generate_training_prompt(self, topic: str, audience: str) -> dict:
        """Generate security training content."""
        prompts = {
            "phishing_awareness": {
                "title": "Recognizing and Reporting Phishing Emails",
                "audience": audience,
                "duration": "15 minutes",
                "content": """
## Learning Objectives
By the end of this training, you will be able to:
1. Identify common phishing email indicators
2. Understand the risks of phishing attacks
3. Know how to report suspicious emails
4. Protect your credentials and data

## What is Phishing?
Phishing is a cyberattack where attackers impersonate legitimate organizations to steal credentials, personal information, or money.

## Red Flags to Watch For 🚩

### 1. Suspicious Sender
- Misspelled domain names (micros0ft.com instead of microsoft.com)
- Free email accounts (gmail, yahoo) for business communications
- Sender name doesn't match email address

### 2. Urgent Language
- "URGENT: Your account will be suspended!"
- "Immediate action required"
- "Click within 24 hours or lose access"

### 3. Generic Greetings
- "Dear Customer" instead of your name
- No personalization
- Generic company references

### 4. Suspicious Links
- Hover over links to see real destination
- Shortened URLs (bit.ly, tinyurl)
- Domains similar but not exact

### 5. Unexpected Attachments
- Unsolicited attachments
- Unusual file types (.exe, .zip)
- Password-protected attachments

### 6. Requests for Sensitive Information
- Asking for passwords or credentials
- Requesting financial information
- Multi-factor authentication codes

## Real Examples

### Example 1: Fake IT Support
```
From: IT Support <support@company-security.com>
Subject: URGENT: Verify Your Account

Your email account will be suspended due to security concerns.
Click here to verify: http://verify-account-now.com

[Verify Now Button]
```

🚩 Red Flags: Urgent language, suspicious domain, request to verify

### Example 2: CEO Fraud
```
From: CEO <ceo@gmail.com>
Subject: Need urgent help

I'm in a meeting and need you to purchase gift cards.
Reply with the card numbers immediately.

- CEO Name
```

🚩 Red Flags: Personal email for business, unusual request, urgency

## What Should You Do?

### If You Receive a Suspicious Email:
1. ✅ **DON'T click** any links or attachments
2. ✅ **DON'T reply** to the email
3. ✅ **DON'T provide** any information
4. ✅ **DO report** it using !report command or forward to security@company.com
5. ✅ **DO delete** the email after reporting

### If You Clicked a Phishing Link:
1. 🚨 **Immediately** disconnect from network
2. 🚨 **Don't enter** credentials if you haven't yet
3. 🚨 **Report** to IT Security immediately
4. 🚨 **Change password** from a different device
5. 🚨 **Enable MFA** if not already active

## Quiz Time! 🎯

**Question 1:** Which of these is a red flag?
A) Email from your manager's company address
B) Email from "CEO" using gmail.com
C) Email with your full name
D) Expected document from colleague

**Answer:** B - Personal email for business communication

**Question 2:** What should you do with a suspicious email?
A) Click to see if it's real
B) Reply to confirm it's legitimate
C) Report it immediately
D) Ignore it

**Answer:** C - Report it immediately

## Remember: When in Doubt, Report! 📧

It's better to report 100 false alarms than miss 1 real phishing email.

**How to Report:**
- Use !report command in Slack
- Forward to: security@company.com
- Call IT Security: x1234

## Additional Resources
- Phishing examples: [internal link]
- Reporting guide: [internal link]
- Security policies: [internal link]

---
*Questions? Contact Security Awareness Team*
""",
                "quiz_questions": [
                    {
                        "question": "What is the best way to verify a suspicious email claiming to be from your bank?",
                        "options": ["A) Click the link in the email", "B) Reply and ask if it's legitimate", "C) Call the bank using a number from their official website", "D) Check if others received it"],
                        "correct": "C",
                        "explanation": "Always use official contact information, never links or numbers from suspicious emails."
                    },
                    {
                        "question": "Which is NOT a common phishing indicator?",
                        "options": ["A) Urgent language requiring immediate action", "B) Request for password or credentials", "C) Email contains your full name", "D) Suspicious sender domain"],
                        "correct": "C",
                        "explanation": "Knowing your name doesn't make an email legitimate. Phishers can find names easily."
                    }
                ]
            },
            "password_security": {
                "title": "Creating Strong Passwords and Using MFA",
                "audience": audience,
                "duration": "10 minutes",
                "content": """
## Why Password Security Matters
Weak passwords are the #1 cause of account compromises. Strong passwords + MFA = Strong security.

## Creating Strong Passwords

### DO's ✅
- Use 12+ characters minimum
- Mix uppercase, lowercase, numbers, symbols
- Use unique passwords for each account
- Use a password manager
- Use passphrases: "Coffee!Morning@Sunrise2025"

### DON'Ts ❌
- Don't use dictionary words
- Don't use personal information (birthdate, names)
- Don't reuse passwords across accounts
- Don't share passwords
- Don't write passwords on sticky notes

## Multi-Factor Authentication (MFA)

### What is MFA?
Extra layer of security requiring:
1. Something you know (password)
2. Something you have (phone, token)
3. Something you are (fingerprint)

### Why MFA Matters
99.9% of automated attacks are blocked by MFA!

### Enable MFA Everywhere
- Work accounts: REQUIRED
- Email: Strongly recommended
- Banking: Strongly recommended
- Social media: Recommended

## Password Manager Benefits
✅ Generate strong, unique passwords
✅ Remember passwords for you
✅ Auto-fill login forms
✅ Encrypted storage
✅ Works across devices

---
*Enable MFA today!*
"""
            }
        }
        
        return prompts.get(topic, {"title": f"Training: {topic}", "content": "Custom training content"})

    @commands.command(name="generate_remediation")
    async def generate_remediation(self, ctx, incident_type: str, severity: str = "HIGH"):
        """Generate remediation plan for incident type."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        await ctx.send(f"📋 Generating remediation plan for **{incident_type}** ({severity})...")
        
        plan_text = self.generate_remediation_plan(incident_type, severity, {})
        
        plan_id = f"REM-{self.data['counter']:05d}"
        self.data['remediation_plans'][plan_id] = {
            "plan_id": plan_id,
            "incident_type": incident_type,
            "severity": severity,
            "generated_by": str(ctx.author.id),
            "generated_at": datetime.utcnow().isoformat(),
            "content": plan_text
        }
        self.data['counter'] += 1
        self.save_data(self.data)
        
        # Save plan
        plan_file = f"data/remediation/{plan_id}_{incident_type}.md"
        os.makedirs(os.path.dirname(plan_file), exist_ok=True)
        with open(plan_file, 'w') as f:
            f.write(plan_text)
        
        embed = discord.Embed(
            title=f"📋 Remediation Plan: {plan_id}",
            description=f"Comprehensive remediation plan for {incident_type} incident",
            color=discord.Color.green()
        )
        embed.add_field(name="Incident Type", value=incident_type, inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Phases", value="Immediate → Short-term → Long-term", inline=True)
        embed.add_field(name="File", value=f"`{plan_file}`", inline=False)
        
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(plan_file))

    @commands.command(name="generate_training")
    async def generate_training(self, ctx, topic: str, audience: str = "all_staff"):
        """Generate security training content."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        await ctx.send(f"📚 Generating training content: **{topic}** for {audience}...")
        
        training_content = self.generate_training_prompt(topic, audience)
        
        training_id = f"TRAIN-{self.data['counter']:04d}"
        self.data['training_prompts'][training_id] = {
            "training_id": training_id,
            "topic": topic,
            "audience": audience,
            "generated_by": str(ctx.author.id),
            "generated_at": datetime.utcnow().isoformat(),
            "content": training_content
        }
        self.data['counter'] += 1
        self.save_data(self.data)
        
        # Save training
        training_file = f"data/training/{training_id}_{topic}.md"
        os.makedirs(os.path.dirname(training_file), exist_ok=True)
        with open(training_file, 'w') as f:
            f.write(f"# {training_content['title']}\n\n")
            f.write(f"**Audience:** {training_content['audience']}\n")
            f.write(f"**Duration:** {training_content.get('duration', 'Self-paced')}\n\n")
            f.write(training_content['content'])
        
        embed = discord.Embed(
            title=f"📚 Training Generated: {training_id}",
            description=training_content['title'],
            color=discord.Color.blue()
        )
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Audience", value=audience, inline=True)
        embed.add_field(name="Duration", value=training_content.get('duration', 'Self-paced'), inline=True)
        embed.add_field(name="File", value=f"`{training_file}`", inline=False)
        
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(training_file))

    @commands.command(name="audit_plan")
    async def audit_plan(self, ctx, plan_id: str):
        """Schedule follow-up audit for remediation plan."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if plan_id not in self.data['remediation_plans']:
            await ctx.send("❌ Remediation plan not found.")
            return
        
        plan = self.data['remediation_plans'][plan_id]
        plan['audit_scheduled'] = True
        plan['audit_date'] = (datetime.utcnow().replace(day=1) + timedelta(days=90)).isoformat()
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"📅 Follow-up Audit Scheduled: {plan_id}",
            description="Verification audit scheduled to ensure remediation effectiveness",
            color=discord.Color.orange()
        )
        embed.add_field(name="Audit Date", value=plan['audit_date'][:10], inline=True)
        embed.add_field(name="Plan Type", value=plan['incident_type'], inline=True)
        embed.add_field(name="Audit Scope", value="• Verify all actions completed\n• Test control effectiveness\n• Measure success metrics\n• Document findings", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RemediationRecommenderCog(bot))
