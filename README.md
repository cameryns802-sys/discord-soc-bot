# Discord SOC Bot System

This repository contains three main components:

- **bot/**: Discord bot with advanced security, automation, and analytics modules.
- **api/**: FastAPI backend serving dashboard data and actions.
- **soc-dashboard/**: React dashboard for real-time SOC monitoring and control.

---

## 1. Discord Bot (bot/)
- Place your Discord bot code here (see your existing bot.py and cogs).
- Run with your preferred Python environment.

```
cd bot
python bot.py
```

---

## 2. FastAPI Backend (api/)
- Serves data to the dashboard and handles operator actions.
- Endpoints: `/overview`, `/incidents`, `/operator/lockdown`, etc.
- Edit or expand `api/main.py` as needed.

### Install dependencies:
```
pip install fastapi uvicorn pydantic
```

### Run the API server:
```
uvicorn api.main:app --reload
```

---

## 3. SOC Dashboard Frontend (soc-dashboard/)
- Modern React (Vite) dashboard with Tailwind CSS.
- Fetches data from FastAPI backend at `http://localhost:8000`.

### Install dependencies:
```
cd soc-dashboard
npm install
```

### Run the dashboard:
```
npm run dev
```

---

## Folder Structure

```
/bot
    bot.py
    cogs/
    ...
/api
    main.py
/soc-dashboard
    src/
    public/
    package.json
    ...
```

---

## Connecting Everything
- Start the FastAPI backend (`uvicorn ...`) before running the dashboard.
- The dashboard will show real data from the API endpoints.
- Wire up more endpoints and actions as needed for your SOC use case.

---

## Customization
- Add more API endpoints in `api/main.py` for new dashboard panels.
- Expand the React dashboard with new panels and widgets in `src/components`.
- Integrate the Discord bot with the API for live event streaming if desired.

---

**Questions?**
Open an issue or ask for more automation and integration scripts!

## License
MIT
