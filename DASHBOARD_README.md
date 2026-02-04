# 🛡️ Sentinel SOC Bot - Dashboard

A professional, portfolio-style dashboard for showcasing the Sentinel Security Operations Center Discord bot.

## Features

### 🎨 Modern Design
- **Discord-inspired theme** with custom color palette
- **Responsive layout** that works on all devices
- **Smooth animations** and scroll effects
- **Card-based design** for clean organization
- **Glass morphism effects** for modern UI

### 📊 Live Statistics
- Real-time server and user counts
- Security metrics (threats detected/blocked)
- System health indicators
- Recent activity feed
- Performance monitoring

### 🔐 Security Showcase
- **Core Security Systems** (8 feature cards):
  - Anti-Phishing Detection
  - Anti-Raid System
  - Malware Detection
  - Security Dashboard
  - Threat Drills
  - Threat Intelligence
  - AI Governance
  - Compliance Monitoring

- **Advanced Modules** (172 security cogs):
  - Core Security (45 cogs)
  - SOC Operations (38 cogs)
  - Threat Intelligence (22 cogs)
  - Compliance & Governance (18 cogs)
  - AI & Automation (25 cogs)
  - Analytics & Reporting (24 cogs)

### 👥 Team Section
- Team member profiles
- Role assignments
- Skill badges
- Project associations

### ⚡ Interactive Elements
- Smooth scroll navigation
- Animated statistics counters
- Auto-updating activity feed
- Scroll-triggered animations
- Particle effects (optional)

## File Structure

```
api/
├── main.py                  # FastAPI backend with endpoints
└── static/
    ├── index.html          # Main dashboard HTML
    ├── css/
    │   └── style.css       # All styling and animations
    └── js/
        └── main.js         # Interactive features and API calls
```

## Setup & Deployment

### Local Development

1. **Ensure FastAPI is running**:
   ```bash
   # Bot automatically starts FastAPI on port 8000
   python bot.py
   ```

2. **Access dashboard**:
   - Main dashboard: http://localhost:8000/
   - API docs: http://localhost:8000/docs
   - Stats endpoint: http://localhost:8000/api/stats

### Production Deployment

#### Option 1: Deploy with Bot (Recommended)
The dashboard is served by the bot's FastAPI instance:
- Runs on same server as Discord bot
- Port: 8000 (configurable via environment variables)
- Auto-starts when bot starts

#### Option 2: Static Hosting (Netlify/Vercel/GitHub Pages)
If you want to host the dashboard separately:

1. **Copy static files**:
   ```bash
   cp -r api/static/* ./dashboard-deploy/
   ```

2. **Update API URLs** in `main.js`:
   ```javascript
   const API_BASE_URL = 'https://your-bot-api.com';
   ```

3. **Deploy to hosting platform**:
   - **Netlify**: Drag & drop the `static` folder
   - **GitHub Pages**: Push to `gh-pages` branch
   - **Vercel**: Connect repo and deploy

## API Endpoints

### GET `/`
Serves the main dashboard HTML

### GET `/api/stats`
Returns live bot statistics:
```json
{
  "guilds": 2,
  "users": 13,
  "cogs_loaded": 172,
  "commands": 100,
  "security": {
    "threats_detected": 150,
    "threats_blocked": 145,
    "avg_response_time": "2.1",
    "posture_score": 94
  },
  "timestamp": "2026-02-02T12:00:00"
}
```

## Customization

### Update Bot Information

**HTML** (`index.html`):
- Line 21: Update Discord invite link
- Line 145: Update server invite URLs
- Line 623: Update team member information
- Line 705: Update footer links

**CSS** (`style.css`):
- Lines 7-16: Customize color palette
- Lines 32-35: Adjust spacing and sizing

**JavaScript** (`main.js`):
- Lines 73-81: Update demo data values
- Lines 88-93: Customize activity feed messages

### Add Real-Time Data

To enable live statistics from your bot:

1. **Create stats updater in bot**:
   ```python
   # Add to bot.py or a new cog
   import json
   from pathlib import Path
   
   async def update_bot_stats():
       stats = {
           "guilds": len(bot.guilds),
           "users": sum(g.member_count for g in bot.guilds),
           "cogs_loaded": len(bot.cogs),
           "commands": len(list(bot.tree._get_all_commands())),
           "security": {
               "threats_detected": get_threat_count(),
               "threats_blocked": get_blocked_count(),
               "avg_response_time": "2.1",
               "posture_score": calculate_security_score()
           }
       }
       
       Path("data/bot_stats.json").write_text(json.dumps(stats))
   
   # Run every 30 seconds
   @tasks.loop(seconds=30)
   async def update_stats_task():
       await update_bot_stats()
   ```

2. **API will automatically read from `data/bot_stats.json`**

### Branding

Replace placeholders:
- `your-invite` → Your Discord invite code
- `your-repo` → Your GitHub repository
- Default avatars → Your team's Discord avatars
- Add your bot's logo/icon

## Performance

### Optimizations
- CSS minification ready
- Image optimization recommended
- Lazy loading for heavy content
- API response caching (30s default)
- Efficient animations (GPU-accelerated)

### Monitoring
- Console logs show API status
- Fallback to demo data if API unavailable
- Error handling for all fetch operations

## Browser Support
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers
- ⚠️ IE11 not supported (uses modern CSS/JS)

## Security Considerations

### Production Checklist
- [ ] Update CORS origins in `main.py` (currently allows all)
- [ ] Set proper Discord invite link expiration
- [ ] Review API rate limiting
- [ ] Enable HTTPS in production
- [ ] Sanitize any user-generated content
- [ ] Set up proper error logging

### Privacy
- No user data collection
- No tracking scripts
- No cookies (except Discord invite)
- API stats are aggregate/anonymous

## Troubleshooting

### Dashboard not loading
- Check FastAPI is running: http://localhost:8000/docs
- Verify static files exist: `api/static/index.html`
- Check browser console for errors

### Statistics not updating
- Verify API endpoint: http://localhost:8000/api/stats
- Check `data/bot_stats.json` exists
- Review console logs for API errors

### Styling issues
- Hard refresh browser (Ctrl+Shift+R)
- Clear cache
- Verify CSS file loaded in Network tab

## Contributing

To add new features:
1. Add HTML structure in `index.html`
2. Style in `style.css`
3. Add interactivity in `main.js`
4. Update API endpoints if needed
5. Test on multiple devices

## License

Part of Sentinel SOC Bot. All rights reserved.

## Credits

- **Design Inspiration**: botportfolios.netlify.app
- **Framework**: FastAPI + Vanilla JS
- **Icons**: Unicode emoji
- **Fonts**: Google Fonts (Inter)
- **Color Scheme**: Discord-inspired palette

---

**Version**: 1.0.0  
**Last Updated**: February 2, 2026  
**Maintained By**: Sentinel SOC Team
