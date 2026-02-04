# 🎨 Visual Customization Guide

## What Can You Change? (Visual Reference)

This guide shows exactly what each admin panel setting controls on your dashboard.

---

## 🏠 Dashboard Layout Map

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                                │
│  [🛡️ Logo Emoji]  [Bot Name]                    [Links]    │ ← Branding Tab
│  configurable        configurable                configurable│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     HERO SECTION                             │
│                                                               │
│        [Badge Text - Tagline]                                │ ← Branding Tab
│                                                               │
│            [🛡️ Bot Name]                                     │ ← Branding Tab
│                                                               │
│         [Description Text]                                    │ ← Branding Tab
│                                                               │
│     [Subtitle with Features List]                            │ ← Branding Tab
│                                                               │
│  [Add to Discord Button]  [View Features Button]             │ ← Links Tab
│   configurable link         configurable link                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   STATISTICS SECTION                         │
│                                                               │
│  [Server Count]  [User Count]  [Cogs]  [Commands]           │ ← Statistics Tab
│   configurable    configurable  config   config              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    FEATURES SECTION                          │
│                                                               │
│  [Feature 1]  [Feature 2]  [Feature 3]  [Feature 4]         │
│   🎣 icon     🚨 icon     🦠 icon      📊 icon              │ ← Features Tab
│   Title       Title       Title        Title                 │ (all editable)
│   Desc        Desc        Desc         Desc                  │
│   [Tags]      [Tags]      [Tags]       [Tags]               │
│                                                               │
│  [Feature 5]  [Feature 6]  [Feature 7]  [Feature 8]         │
│   🎯 icon     🔍 icon     🤖 icon      📋 icon              │
│   Title       Title       Title        Title                 │
│   Desc        Desc        Desc         Desc                  │
│   [Tags]      [Tags]      [Tags]       [Tags]               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      TEAM SECTION                            │
│                                                               │
│  [Member 1]   [Member 2]   [Member 3]                       │
│   Avatar      Avatar       Avatar                            │ ← Team Tab
│   Name        Name         Name                              │ (add/edit/remove)
│   Role        Role         Role                              │
│   Badges      Badges       Badges                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    CTA SECTION                               │
│                                                               │
│         [CTA Title - Ready to Secure?]                       │ ← Stored in config
│         [CTA Subtitle - Join thousands...]                   │ ← (not yet rendered)
│                                                               │
│  [Add to Discord]  [Join Support Server]                     │
│   configurable       configurable                            │ ← Links Tab
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       FOOTER                                 │
│                                                               │
│  [Description - Enterprise-grade security...]                │ ← Branding Tab
│                                                               │
│  [GitHub]  [Documentation]  [Support]  [Terms]  [Privacy]   │ ← Links Tab
│   config     config          config     config   config      │
│                                                               │
│           [Copyright © 2026...]                              │ ← Stored in config
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Color Application Map

```
Primary Color (#5865F2 by default):
├── All buttons (CTA, features, navigation)
├── Links and hyperlinks
├── Hero badge background
├── Section accents
└── Active states

Primary Dark (#4752C4):
├── Button hover states
├── Link hover states
└── Interactive element hover

Secondary Color (#57F287):
├── Success indicators
├── Positive stats
├── Achievement badges
└── Completion markers

Danger Color (#ED4245):
├── Error messages
├── Warning indicators
├── Critical alerts
└── Negative stats

Warning Color (#FEE75C):
├── Caution notices
├── Pending states
├── Information badges
└── Attention markers
```

---

## 📝 Branding Tab Controls

### 1. Bot Name
```
Appears in:
├── Header logo text
├── Hero title
├── Footer branding
└── Page title

Example: "Sentinel SOC" → "My Security Bot"
```

### 2. Logo Emoji
```
Appears in:
├── Header logo icon
├── Hero section
├── Footer icon
└── Favicon (browser tab)

Example: 🛡️ → 🔐 or 🤖 or 🦅
```

### 3. Tagline
```
Appears in:
└── Hero badge (top of hero section)

Example: "Enterprise-Grade Security Platform"
         → "Advanced Discord Security"
```

### 4. Description
```
Appears in:
└── Hero main subtitle

Example: "Advanced Security Operations Center for Discord"
         → "Protecting Your Community 24/7"
```

### 5. Subtitle (Feature List)
```
Appears in:
└── Hero detailed features line

Example: "100+ Security Modules | Real-Time Threat Detection | Automated Response"
         → "AI-Powered Protection | 24/7 Monitoring | Instant Response"
```

---

## 🎨 Colors Tab Controls

### Visual Impact of Each Color

```
PRIMARY COLOR
────────────────────────────────────────────────────────
Before: [Button]  After: [Button]
        #5865F2          #your-color

Effects:
• All CTA buttons
• Navigation highlights
• Link colors
• Feature card accents
• Stats highlights
```

```
PRIMARY DARK (Hover State)
────────────────────────────────────────────────────────
Before: [Button Hover]  After: [Button Hover]
        #4752C4                #your-dark-color

Effects:
• Button hover states
• Link hover effects
• Interactive elements hover
• Active menu items
```

```
SECONDARY COLOR
────────────────────────────────────────────────────────
Before: ✅ Success  After: ✅ Success
        #57F287            #your-secondary

Effects:
• Success messages
• Positive indicators
• Achievement badges
• Completion states
```

```
DANGER COLOR
────────────────────────────────────────────────────────
Before: ❌ Error  After: ❌ Error
        #ED4245          #your-danger

Effects:
• Error messages
• Warning states
• Critical alerts
• Failed actions
```

```
WARNING COLOR
────────────────────────────────────────────────────────
Before: ⚠️ Warning  After: ⚠️ Warning
        #FEE75C            #your-warning

Effects:
• Caution notices
• Pending states
• Information badges
• Attention markers
```

---

## 🔗 Links Tab Controls

### Link Mapping

```
Discord Invite Link
├── Hero "Add to Discord" button
├── CTA "Add to Discord" button
└── Footer "Invite Bot" link

Support Server Link
├── Hero "Join Server" button (if visible)
├── CTA "Join Support" button
└── Footer "Support" link

GitHub Repository
└── Footer "GitHub" link

Documentation Path
└── Footer "Docs" link

API Reference Path
└── Footer "API" link

Terms Path
└── Footer "Terms" link

Privacy Path
└── Footer "Privacy" link
```

---

## 👥 Team Tab Controls

### Team Member Card Structure

```
┌─────────────────────────────┐
│     [Avatar Image]          │ ← Avatar URL
│                              │
│     Name Here                │ ← Name field
│     Role/Title               │ ← Role field
│                              │
│  [Badge1] [Badge2] [Badge3] │ ← Badges (comma-separated)
│                              │
│  Projects: Project Name      │ ← Projects (auto-set)
└─────────────────────────────┘

Controls:
• ➕ Add Team Member    → Creates new card
• ✏️ Edit inline       → Change any field
• 🗑️ Remove           → Deletes card
```

### Team Section Layout

```
Current:
[Member 1] [Member 2] [Member 3]

Can become:
[Member 1] [Member 2] [Member 3] [Member 4] [Member 5]

Or simplified:
[Member 1] [Member 2]

Fully flexible - add as many or as few as you want!
```

---

## ✨ Features Tab Controls

### Feature Card Structure

```
┌─────────────────────────────┐
│         🎣 Icon              │ ← Icon (emoji)
│                              │
│      Feature Title           │ ← Title
│                              │
│  Detailed description text   │ ← Description
│  explaining what this        │   (textarea)
│  feature does...             │
│                              │
│  [Tag1] [Tag2] [Tag3]       │ ← Tags (comma-separated)
└─────────────────────────────┘
```

### Current 8 Features

```
1. 🎣 Anti-Phishing
   Title: Anti-Phishing
   Desc: Real-time detection and blocking of phishing attempts...
   Tags: Real-Time, AI-Powered, URL Scanning

2. 🚨 Anti-Raid System
   Title: Anti-Raid System
   Desc: Automated detection and prevention of mass join/raid attacks...
   Tags: Automated, Pattern Detection, Mass Ban

3. 🦠 Malware Detection
   Title: Malware Detection
   Desc: Multi-layer malware scanning for file attachments...
   Tags: File Scanning, Multi-Layer, Ransomware Protection

4. 📊 Security Dashboard
   Title: Security Dashboard
   Desc: Real-time security metrics and threat visualization...
   Tags: Real-Time, Analytics, Executive Reporting

5. 🎯 Threat Drills
   Title: Threat Drills
   Desc: 8 simulation scenarios for team training...
   Tags: Training, Simulation, 8 Scenarios

6. 🔍 Threat Intelligence
   Title: Threat Intelligence
   Desc: IOC tracking, threat actor profiling...
   Tags: IOC Tracking, Threat Feeds, Attribution

7. 🤖 AI Governance
   Title: AI Governance
   Desc: Human-in-the-loop AI decisions with confidence scoring...
   Tags: AI Safety, Human Oversight, Transparency

8. 📋 Compliance
   Title: Compliance
   Desc: GDPR, SOC2, and ISO27001 compliance monitoring...
   Tags: GDPR, SOC2, Audit Trails
```

---

## 📊 Statistics Tab Controls

### Statistics Display

```
┌─────────────────────────────────────────┐
│          Live Statistics                │
│                                          │
│   [Servers: 2]     [Users: 13]         │ ← Default values
│   [Cogs: 172]      [Commands: 100]     │ ← Display totals
│                                          │
│   Show Live Stats: [✓] ON / [ ] OFF    │ ← Toggle
└─────────────────────────────────────────┘

Controls:
• Show Live Statistics → Enable/disable live data fetching
• Default Servers      → Fallback value if API unavailable
• Default Users        → Fallback value if API unavailable
• Total Cogs          → Display total (from bot)
• Total Commands      → Display total (from bot)
```

---

## 🎯 Quick Reference: What Changes What

### To Change Bot Identity
```
Tab: Branding
• Bot Name      → All branding text
• Logo Emoji    → All logo icons
• Tagline       → Hero badge
```

### To Change Look & Feel
```
Tab: Colors
• Primary       → Main theme color
• Primary Dark  → Hover states
• Secondary     → Success indicators
• Danger        → Error states
• Warning       → Caution indicators
```

### To Update External Links
```
Tab: Links
• Discord Invite → All "Add to Discord" buttons
• Support Server → All support links
• GitHub         → Repository link
• Documentation  → Help link
```

### To Showcase Your Team
```
Tab: Team
• Add members    → Click ➕
• Edit members   → Change fields inline
• Remove members → Click 🗑️
```

### To Highlight Features
```
Tab: Features
• Edit any of 8 feature cards
• Change icon, title, description, tags
• All fields editable
```

### To Configure Stats
```
Tab: Statistics
• Toggle live stats on/off
• Set default fallback values
• Configure display totals
```

---

## 💡 Pro Tips

### Color Selection
```
✅ DO:
• Use high contrast colors
• Test on different screens
• Match your Discord server theme
• Keep accessibility in mind

❌ DON'T:
• Use colors that are too similar
• Make text hard to read
• Use too many bright colors
• Forget about colorblind users
```

### Branding Guidelines
```
✅ DO:
• Keep names concise (2-4 words)
• Use clear, professional language
• Match your brand identity
• Be consistent across platforms

❌ DON'T:
• Use overly long names
• Include special characters
• Change too frequently
• Use confusing terminology
```

### Link Best Practices
```
✅ DO:
• Test all links before saving
• Use https:// for security
• Keep URLs simple and memorable
• Update when links change

❌ DON'T:
• Use shortened URLs (looks suspicious)
• Link to external sites unnecessarily
• Forget to update broken links
• Use localhost in production
```

---

## 🎨 Color Preset Reference

Copy these color codes for instant themes:

### Discord Theme (Default)
```
Primary:      #5865F2  ████ (Discord Blurple)
Primary Dark: #4752C4  ████ (Darker Blurple)
Secondary:    #57F287  ████ (Discord Green)
Danger:       #ED4245  ████ (Discord Red)
Warning:      #FEE75C  ████ (Discord Yellow)
```

### GitHub Theme
```
Primary:      #238636  ████ (GitHub Green)
Primary Dark: #1a7f37  ████ (Darker Green)
Secondary:    #58a6ff  ████ (GitHub Blue)
Danger:       #f85149  ████ (GitHub Red)
Warning:      #d29922  ████ (GitHub Orange)
```

### Cyberpunk Theme
```
Primary:      #00F5FF  ████ (Cyan)
Primary Dark: #00D8E8  ████ (Dark Cyan)
Secondary:    #FF10F0  ████ (Magenta)
Danger:       #FF003C  ████ (Neon Red)
Warning:      #FFE400  ████ (Electric Yellow)
```

### Professional Blue
```
Primary:      #0066CC  ████ (Corporate Blue)
Primary Dark: #0052A3  ████ (Navy)
Secondary:    #00AA55  ████ (Success Green)
Danger:       #CC0000  ████ (Alert Red)
Warning:      #FF9900  ████ (Caution Orange)
```

### Dark Purple
```
Primary:      #7C3AED  ████ (Purple)
Primary Dark: #6D28D9  ████ (Deep Purple)
Secondary:    #10B981  ████ (Emerald)
Danger:       #EF4444  ████ (Red)
Warning:      #F59E0B  ████ (Amber)
```

---

## ✅ Checklist: First-Time Setup

### Essential Customizations

```
□ Change bot name (Branding tab)
□ Choose logo emoji (Branding tab)
□ Update tagline (Branding tab)
□ Write description (Branding tab)
□ Set primary color (Colors tab)
□ Set other colors (Colors tab)
□ Add Discord invite link (Links tab)
□ Add support server link (Links tab)
□ Add GitHub repository (Links tab)
□ Add at least 1 team member (Team tab)
□ Review all 8 features (Features tab)
□ Configure statistics (Statistics tab)
□ Test all links work
□ Check mobile view
□ Share with your community!
```

---

**This visual guide shows every customizable element in your dashboard!** 🎨

For step-by-step instructions, see: `ADMIN_PANEL_GUIDE.md`
