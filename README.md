# 🏀 Basketball Bot

A Discord basketball community project with a responsive public website, a Discord OAuth2 signed-in dashboard, NBA upcoming schedule data, and service health reports.

**Current mode: website + Discord bot.** Startup is restored: the bot automatically starts alongside the website when `DISCORD_TOKEN` is configured, unless `ENABLE_DISCORD_BOT=false` explicitly pauses it. The existing game commands and economy remain unchanged. MongoDB is optional and temporary stats reset after a restart.

## Features

- Public **/** page: introduction, live component statuses, NBA upcoming games and in-memory incident transitions.
- Private **/dashboard**: signed-in Discord identity, service health, up to 12 upcoming NBA games, local tipoff times, game filters and recent activity.
- **/login**, **/oauth/callback**, **/logout**: Discord OAuth2 authorization-code login using the identify scope only. Logout requires a valid CSRF token.
- Public **/api/status**: website, Discord gateway, MongoDB, NBA scoreboard and schedule feed monitoring.
- Public **/api/schedule**: cached scheduled NBA matchups within the next 21 days.
- **/health**: HTTP website liveness only; it is not proof the Discord gateway is connected.

NBA schedule data is fetched from the publicly accessible NBA CDN, with no API key. The schedule cache refreshes at most every 30 minutes and can retain previously retrieved upcoming games when the upstream feed is unavailable (clearly labeled stale). Game times are converted to the visitor's local timezone in their browser; no fabricated results. The separate NBA scoreboard monitor checks feed reachability every five minutes.

The signed-in dashboard is currently **read-only**. It does not provide server administration, Discord command control, guild permissions or economy management.

## 🔗 Pasted website links: Discord Components V2 cards

Discord's official **Component Embeds** can render custom link previews directly from website HTML. This site adds one server-rendered Discord Container with an orange accent, branded 1200 x 630 PNG image, and **real link buttons**:

- **Open Dashboard / Dashboard** — opens Discord OAuth2 account dashboard.
- **NBA Games** — jumps to the upcoming-games section on the public website.
- **Live Status** — jumps to the public health components.
- **GitHub** — opens the project source repository.

To share, paste either of these public URLs into a Discord channel:

    https://basketball-bot-6jpx.onrender.com/
    https://basketball-bot-6jpx.onrender.com/share

The website has a **Copy Discord link** button. These rich previews are defined in the website HTML; they work independently of the Discord gateway bot and do NOT need a bot token, message content intent, webhooks, or MongoDB.

**Important distinction:** Website link previews support only **link-style** buttons and media, not buttons that run Discord bot callbacks. The private /dashboard URL requires OAuth login, so send the public homepage or /share link; the embed's Dashboard button takes a user to their own login page.

The server embeds official JSON directly in HTML (less than Discord's 3,000-byte limit), plus Open Graph and Twitter Card tags for platforms that don't support Component Embeds. The branded PNG is generated at /og-preview.png without external media sources. The preview is static promotional content, not a constantly updated service health claim.

Discord may cache link previews and feature display may vary across clients. The crawler must access the Render-hosted page and PNG within Discord's fetch timeout; Render Free cold starts can occasionally prevent a preview. Use the official Embed Debugger at https://discord.com/developers/embeds if a link preview doesn't display after deployment.

Custom domain: set the optional PUBLIC_SITE_URL environment variable to a plain HTTPS origin. By default, it points to the existing Render URL. All buttons use this trusted configured origin, never the HTTP Host header.

## Restore bot startup on your existing Render Web Service

The Discord worker is restored in `web.py` and `bot.py`. `python web.py` starts the website and, when enabled, one Discord gateway worker. A gateway failure **does not stop** the public website or NBA schedule. The Render service still uses just one web-server process.

1. Merge this fix's GitHub pull request into `main`.
2. On your **existing Render Web Service**, open **Environment**. If `ENABLE_DISCORD_BOT=false` is present, **change it to `true`** or remove it to use automatic startup. **Existing Render environment variables override `render.yaml` and code defaults.**
3. Ensure `DISCORD_TOKEN` is configured privately on Render. This is the **Discord bot token** from the Bot tab, not `DISCORD_CLIENT_SECRET` from the OAuth2 tab.
4. Keep **Build** `pip install -r requirements.txt`, **Start** `python web.py`, and **Health Check Path** `/health`.
5. Let Render deploy the updated code **once**. Check its logs for `Logged in as ...`, then test `/ping`, `/about`, `/shoot`, `/profile`, and `/leaderboard` on your server.

### Gateway mode

| `ENABLE_DISCORD_BOT` | `DISCORD_TOKEN` | Result |
| --- | --- | --- |
| Unset or `auto` | Present | Bot attempts login alongside website |
| `true` | Present | Bot attempts login alongside website |
| `false` | Any | Bot remains paused; website stays available |
| Unset or `auto` | Missing | Website only; status explains token missing |
| `true` | Missing | Website works; bot reports configuration error |

Keep OAuth2 settings (`DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `SESSION_SECRET`) unchanged so the dashboard keeps working. MongoDB is not needed for testing: without `MONGODB_URI` the bot stores points and profiles in temporary memory only.

**Previous Discord rate limit:** This Render instance previously received `HTTP 429 / Cloudflare 1015` during Discord authentication. Restoring bot startup cannot bypass an upstream IP restriction. If that error reappears, set `ENABLE_DISCORD_BOT=false`, avoid repeated redeployments, and let the restriction clear.

`render.yaml` now includes `ENABLE_DISCORD_BOT=true` and the private `DISCORD_TOKEN` variable for **new Blueprint** deployments. Your existing manually created Web Service will not pick up those settings until you edit **Render → Environment**.

### Website OAuth2 setup (unchanged)

1. In Discord Developer Portal → OAuth2, register `https://basketball-bot-6jpx.onrender.com/oauth/callback` as a redirect.
2. Under Render → Environment, configure `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, and a fresh random `SESSION_SECRET` at least 32 characters long.
3. Use `https://basketball-bot-6jpx.onrender.com/dashboard` to sign in. OAuth2 uses `identify` only and is separate from bot gateway authentication.

Never commit Discord credentials or session secrets to GitHub.
## Run locally

Use Python 3.11 or newer. Install dependencies:

    python -m pip install -r requirements.txt

Copy `.env.example` to `.env`, add `DISCORD_TOKEN` to start both services, or use `ENABLE_DISCORD_BOT=false` for a website-only local run. Then start:

    python web.py

Open http://localhost:10000 . To test OAuth2 locally, register **http://localhost:10000/oauth/callback** in the Discord Developer Portal, use it for DISCORD_REDIRECT_URI and supply local client credentials and SESSION_SECRET.

Run tests:

    python -m unittest discover -s tests -v

Automated tests verify route protection, OAuth state checks, logout CSRF, bot pausing, NBA schedule parsing/cache and existing game logic, but they do not perform real Discord OAuth or external NBA CDN requests.

## Key modules

- web.py — Render website and restored Discord worker (auto with token)
- basketball/oauth.py — Discord OAuth2 identify-only code exchange
- basketball/webapp.py — Flask authentication and status/schedule routes
- basketball/schedule.py — upcoming NBA feed and cache
- basketball/nba_monitor.py — public NBA scoreboard availability probe
- basketball/status.py — thread-safe component status registry
- basketball/templates — public homepage, dashboard and OAuth error pages
- basketball/static — responsive CSS and browser-side refresh scripts
- bot.py and basketball/cogs — restored bot start entry point; original commands and gameplay unchanged

**Render Free hosting can spin down when idle.** The entire website may be temporarily inaccessible during sleep. Checking /health shows website availability, not whether Discord is currently running.

Independent community project, not affiliated with the NBA or its teams.
