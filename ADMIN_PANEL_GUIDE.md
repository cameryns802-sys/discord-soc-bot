# Dashboard Admin Panel - Quick Start Guide

## 🎯 Overview

The admin panel allows you to customize **every aspect** of your Sentinel SOC dashboard without editing code. Changes are made through a visual web interface with instant preview.

## 🚀 Access the Admin Panel

1. Start your dashboard server:
   ```bash
   python test_dashboard.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/static/admin.html
   ```

3. The admin panel will load automatically

## 📋 Admin Panel Sections

### 1. 🎨 Branding & Identity

Customize your bot's visual identity:

- **Bot Name**: Updates header, hero section, and footer
- **Logo Emoji**: Changes the emoji shown in all logo instances
- **Tagline**: Appears in the hero badge section
- **Description**: Main description in hero section
- **Subtitle**: Detailed feature list in hero section

**Example**:
- Bot Name: "My Security Bot"
- Logo Emoji: 🔐
- Tagline: "Advanced Discord Security"

### 2. 🎨 Color Theme

Full control over dashboard colors with live preview:

- **Primary Color**: Main accent color (buttons, links)
- **Primary Dark**: Hover states for buttons
- **Secondary Color**: Success indicators, highlights
- **Danger Color**: Error states, warnings
- **Warning Color**: Caution indicators

**Features**:
- Color picker with live preview swatches
- "Reset to Defaults" button (Discord colors)
- Real-time preview updates

**Tips**:
- Use Discord's colors: Primary `#5865F2`, Secondary `#57F287`
- Keep contrast high for readability
- Test on different screens

### 3. 🔗 Links & URLs

Update all external links:

- **Discord Invite Link**: Bot invite and CTA buttons
- **Support Server**: Footer and support links
- **GitHub Repository**: Source code link
- **Documentation**: Help and guides path
- **API Reference**: API documentation path

**Important**: 
- Use full URLs for external links (include `https://`)
- Use relative paths for internal pages (e.g., `/docs`)

### 4. 👥 Team Members

Manage your team showcase:

**For Each Member**:
- Name
- Role/Title
- Avatar URL (Discord CDN or external)
- Badges (comma-separated, e.g., "Python, Security, DevOps")
- Projects (automatically set to "Sentinel SOC Bot")

**Actions**:
- ➕ **Add Team Member**: Click button to add new member
- ✏️ **Edit Member**: Change any field inline
- 🗑️ **Remove Member**: Delete member card

**Tips**:
- Use Discord avatar URLs for consistency
- Keep badges concise (3-5 per person)
- Use professional titles

### 5. ✨ Features Showcase

Customize all 8 feature cards:

**For Each Feature**:
- **Icon**: Emoji representing the feature
- **Title**: Feature name
- **Description**: Detailed explanation (100-200 chars)
- **Tags**: Key highlights (comma-separated)

**Current Features**:
1. 🎣 Anti-Phishing
2. 🚨 Anti-Raid System
3. 🦠 Malware Detection
4. 📊 Security Dashboard
5. 🎯 Threat Drills
6. 🔍 Threat Intelligence
7. 🤖 AI Governance
8. 📋 Compliance

**Tips**:
- Choose clear, relevant emojis
- Keep titles short (2-4 words)
- Use action-oriented descriptions
- Tags should be 2-4 words each

### 6. 📊 Statistics Settings

Configure statistics display:

- **Show Live Statistics**: Toggle real-time stats on/off
- **Default Servers**: Fallback value if no live data
- **Default Users**: Fallback value if no live data
- **Total Cogs**: Number of bot modules to display
- **Total Commands**: Number of commands to display

**When to Use**:
- Disable live stats if bot is offline
- Set realistic default values for demos
- Update totals when adding new cogs/commands

## 💾 Saving Changes

### How to Save

1. Make your changes in any section
2. Click the **💾 Save** button in that section
3. Wait for success message: "✅ Success! Changes saved successfully"
4. Click "View Dashboard →" to preview changes

### Important Notes

- **Each section saves independently** - save after editing each tab
- Changes apply immediately to config file
- Dashboard updates on next page load (refresh browser)
- Config file is saved to: `api/static/dashboard_config.json`

### Troubleshooting Save Issues

If save fails:
1. Check console for errors (F12 → Console tab)
2. Verify server is running (`python test_dashboard.py`)
3. Check file permissions on `dashboard_config.json`
4. Try smaller changes (one section at a time)

## 🔄 Workflow Example

**Complete Customization Workflow**:

1. **Start Server**:
   ```bash
   python test_dashboard.py
   ```

2. **Open Admin Panel**:
   - Navigate to `http://localhost:8000/static/admin.html`

3. **Customize Branding**:
   - Change bot name to "SecureBot"
   - Change logo to 🔒
   - Update tagline
   - Click "💾 Save Branding"
   - Wait for success message

4. **Update Colors**:
   - Click "Colors" tab
   - Change primary color to `#FF6B6B`
   - Watch preview update
   - Click "💾 Save Colors"

5. **Update Team**:
   - Click "Team" tab
   - Click "➕ Add Team Member"
   - Fill in details
   - Click "💾 Save Team"

6. **Preview Changes**:
   - Open new tab: `http://localhost:8000/`
   - Hard refresh: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)
   - Verify all changes applied

7. **Iterate**:
   - Go back to admin panel
   - Make additional changes
   - Save and refresh to preview

## 📝 Configuration File

All settings are stored in:
```
api/static/dashboard_config.json
```

### Manual Editing

You can also edit the config file directly in a text editor:

1. Open `dashboard_config.json` in VS Code
2. Make changes to JSON structure
3. Save file
4. Refresh dashboard to see changes

**Advantages**:
- Faster for bulk changes
- Better for version control diffs
- Can use find/replace

**Disadvantages**:
- No validation (must be valid JSON)
- No live preview
- Manual escaping required

### Backup Configuration

**Before making major changes**:

```bash
# Create backup
cp api/static/dashboard_config.json api/static/dashboard_config.backup.json

# Restore if needed
cp api/static/dashboard_config.backup.json api/static/dashboard_config.json
```

### Version Control

Config file is tracked in git:
```bash
# View changes
git diff api/static/dashboard_config.json

# Commit changes
git add api/static/dashboard_config.json
git commit -m "Updated dashboard branding"

# Revert changes
git checkout api/static/dashboard_config.json
```

## 🎨 Color Presets

### Discord Theme (Default)
```
Primary: #5865F2
Primary Dark: #4752C4
Secondary: #57F287
Danger: #ED4245
Warning: #FEE75C
```

### GitHub Theme
```
Primary: #238636
Primary Dark: #1a7f37
Secondary: #58a6ff
Danger: #f85149
Warning: #d29922
```

### Cyberpunk Theme
```
Primary: #00F5FF
Primary Dark: #00D8E8
Secondary: #FF10F0
Danger: #FF003C
Warning: #FFE400
```

### Corporate Blue
```
Primary: #0066CC
Primary Dark: #0052A3
Secondary: #00AA55
Danger: #CC0000
Warning: #FF9900
```

## 🔧 Advanced Customization

### Adding Custom Sections

The config file structure allows custom sections:

```json
{
  "custom": {
    "announcement": "New feature released!",
    "maintenance_mode": false
  }
}
```

Access in JavaScript:
```javascript
if (dashboardConfig.custom?.maintenance_mode) {
  showMaintenanceBanner();
}
```

### Dynamic Content

Update config programmatically:

```python
import json

# Load config
with open('api/static/dashboard_config.json', 'r') as f:
    config = json.load(f)

# Update values
config['stats']['default_guilds'] = 150
config['branding']['name'] = "Updated Name"

# Save config
with open('api/static/dashboard_config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

## 🐛 Troubleshooting

### Admin Panel Won't Load

**Symptoms**: Blank page or 404 error

**Solutions**:
1. Verify server is running
2. Check URL: `http://localhost:8000/static/admin.html` (note `/static/`)
3. Check console (F12) for JavaScript errors
4. Clear browser cache (Ctrl + Shift + Delete)

### Changes Not Appearing

**Symptoms**: Saved changes but dashboard looks the same

**Solutions**:
1. **Hard refresh** dashboard: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache completely
3. Check if `dashboard_config.json` was actually updated (open in editor)
4. Restart dashboard server
5. Check browser console for loading errors

### Save Button Not Working

**Symptoms**: Click save but no success message

**Solutions**:
1. Open browser console (F12 → Console)
2. Look for error messages
3. Verify server is responding: `http://localhost:8000/api/stats`
4. Check server terminal for error logs
5. Restart server if needed

### Colors Not Applying

**Symptoms**: Changed colors but dashboard still uses old colors

**Solutions**:
1. Hard refresh (Ctrl + F5)
2. Check if dynamic theme style element exists (F12 → Elements → `<style id="dynamic-theme">`)
3. Clear all browser data for localhost
4. Check for CSS caching issues
5. Verify color values are valid hex codes (#RRGGBB)

### Team/Features Not Updating

**Symptoms**: Changes to team or features not visible

**Solutions**:
1. These sections require dashboard code update to render
2. Currently config loads branding, colors, links
3. Team/features section rendering coming in next update
4. For now, values are stored but not yet displayed

## 📚 Related Documentation

- **Dashboard Setup**: `DASHBOARD_README.md`
- **Bot Documentation**: `README.md`
- **API Reference**: `http://localhost:8000/api/docs`

## 🆘 Getting Help

### Common Issues

**Q: Can I add more than 8 features?**
A: Yes! Edit `dashboard_config.json` directly and add more feature objects to the array. Dashboard will render all of them.

**Q: Can I change the background colors?**
A: Currently, only accent colors are customizable. Background colors require CSS editing in `api/static/css/style.css`.

**Q: Will my changes persist after bot restart?**
A: Yes! All changes are saved to `dashboard_config.json` which persists across restarts.

**Q: Can multiple people edit the config at once?**
A: No. Last save wins. Use git for collaboration and version control.

**Q: How do I reset everything to defaults?**
A: Delete `dashboard_config.json` and restart server. It will regenerate with default values.

### Support

If you need help:
1. Check console logs (F12 → Console)
2. Check server terminal output
3. Verify all files exist in correct locations
4. Check that ports aren't blocked (8000)

## ✅ Best Practices

1. **Always test changes**: Preview before announcing updates
2. **Use version control**: Commit config changes regularly
3. **Keep backups**: Copy config before major changes
4. **Use consistent branding**: Match your server's theme
5. **Optimize images**: Use CDN links, avoid large avatars
6. **Validate URLs**: Test all links after updating
7. **Mobile test**: Check dashboard on mobile devices
8. **Accessibility**: Keep good color contrast ratios
9. **Professional tone**: Use clear, concise descriptions
10. **Regular updates**: Keep team and features current

## 🎉 You're Ready!

You now have complete control over your dashboard appearance and content. Start customizing and make it your own! 🚀
