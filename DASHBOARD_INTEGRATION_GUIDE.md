# Web Dashboard Integration Guide

## Overview

You now have a complete web-based dashboard system that pulls real-time data from your Discord bot's security and moderation cogs:

1. **Web Dashboard API** (`api/web_dashboard.py`) - REST endpoints that aggregate cog data
2. **Website Dashboard** (`api/dashboard.html`) - Beautiful web UI for monitoring

## Integration Steps

### Step 1: Update `api/main.py`

Add the following imports at the top of your `api/main.py`:

```python
from api.web_dashboard import router as dashboard_router, set_bot_instance
```

Then in your app setup, add this line to include the router:

```python
app.include_router(dashboard_router)
```

### Step 2: Inject Bot Instance

In your bot startup (in `bot.py`), after the bot is initialized:

```python
# At the end of main() function, before starting the bot:
if API_ENVIRONMENT != 'development':
    from api.web_dashboard import set_bot_instance
    set_bot_instance(bot)
```

### Step 3: Serve the HTML Dashboard

Option A: Add this endpoint to `api/main.py`:

```python
@app.get("/dashboard")
async def serve_dashboard():
    with open('api/dashboard.html', 'r') as f:
        return HTMLResponse(content=f.read())
```

Option B: Serve the HTML directly from a static folder:
- Place `api/dashboard.html` in a `static/` directory
- Configure FastAPI to serve static files

### Step 4: Update CORS (if needed)

Make sure your FastAPI app has CORS enabled for the dashboard.html to call the API:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing

After integration:

1. **Start your bot** - Ensure `bot.py` is running and the API is active
2. **Visit the dashboard** - Open `http://127.0.0.1:8000/dashboard.html` in your browser
3. **Check API endpoints** - Test individual endpoints:
   - `http://127.0.0.1:8000/api/dashboard/overview`
   - `http://127.0.0.1:8000/api/dashboard/security`
   - `http://127.0.0.1:8000/api/dashboard/incidents`

## API Endpoints Available

| Endpoint | Purpose | Data |
|----------|---------|------|
| `/api/dashboard/overview` | Bot status & system metrics | Bot info, guilds, users, cogs, commands, memory, CPU, ping |
| `/api/dashboard/security` | Security systems & threat intel | IOCs by severity, detection stats, systems status |
| `/api/dashboard/incidents` | Recent security incidents | Incidents from signal bus, severity, confidence |
| `/api/dashboard/cogs` | Loaded cogs information | Cog names, modules, status |
| `/api/dashboard/stats` | System statistics | Memory, CPU, Discord latency, uptime |
| `/api/dashboard/moderation` | Moderation actions | Warnings, timeouts, kicks, bans |
| `/api/dashboard/compliance` | Compliance status | Framework compliance, policy status |
| `/api/dashboard/activity` | Activity log | Historical events |
| `/api/dashboard/health` | System health score | Overall health (0-100), component status |

## Dashboard Features

### Tabs:
1. **Overview** - Bot status, system info, threat level, quick stats
2. **Security** - Threat intel, detection stats, security systems status
3. **Incidents** - Real-time list of security incidents with severity
4. **Cogs** - Loaded cogs and command counts
5. **Moderation** - Moderation action statistics
6. **Compliance** - Framework and policy compliance status
7. **Health** - Memory, CPU, and connectivity status

### Real-Time Features:
- Auto-refresh every 30 seconds
- Header stats update every 10 seconds
- Color-coded threat levels and severity indicators
- Responsive design (mobile-friendly at 768px)
- Smooth animations and transitions

## Customization

### Adding New Data to Dashboard:
1. Add a new API endpoint in `web_dashboard.py`
2. Add a new tab in the HTML `<div id="new-tab" class="tab-content">`
3. Add a new nav button for the tab
4. Create a `loadNewTab()` function in JavaScript
5. Add the tab switch case in `loadTabData()`

### Changing Colors:
Edit the CSS variables in `dashboard.html`:
```css
:root {
    --primary: #1a1f35;
    --secondary: #0f1419;
    --accent: #00d4ff;
    --danger: #ff4757;
    --warning: #ffa502;
    --success: #2ed573;
}
```

### Adjusting Auto-Refresh Rate:
In dashboard.html JavaScript:
```javascript
// Change this value (milliseconds)
setInterval(() => {
    updateTimestamp();
    loadTabData(currentTab);
}, 30000);  // Change from 30000 to desired interval
```

## Troubleshooting

### Dashboard shows "Loading..." but data won't load:
- Check browser console (F12) for CORS errors
- Verify API server is running on http://127.0.0.1:8000
- Confirm `set_bot_instance(bot)` was called in bot.py

### API returns 500 errors:
- Check bot.py console for errors
- Verify all referenced cogs are loaded
- Check that bot instance is properly injected

### Headers show "--" values:
- Bot startup may not be complete
- Verify bot.py is running without errors
- Check that cogs are initialized

## Next Steps

1. ✅ Integrate web_dashboard.py into api/main.py
2. ✅ Inject bot instance in bot.py startup
3. ✅ Test API endpoints individually
4. ✅ Test dashboard in browser
5. 🔄 Monitor dashboard usage and performance
6. 🔄 Add more cog data as needed
7. 🔄 Create dashboard alerts/notifications
8. 🔄 Export dashboard data to file/database

## Support

For issues or questions:
1. Check the bot.py console for errors
2. Review API endpoint responses in browser dev tools
3. Verify all cogs are properly loaded
4. Check CORS configuration if cross-origin errors appear
