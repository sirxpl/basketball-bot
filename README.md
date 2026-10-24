# 🏀 Basketball Bot

A Discord basketball community project with a responsive public website, a Discord OAuth2 signed-in dashboard, NBA upcoming schedule data, and service health reports.

**Current mode: website-only.** The Discord gateway bot is deliberately paused because Discord returned HTTP 429 / Cloudflare 1015 to its login attempt. This release does not change the economy, shooting minigames, profiles, or slash commands, and it does not require MongoDB. Those commands are unavailable while the gateway is paused.

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

## Setup: existing Render Web Service

1. Merge the dashboard PR into the main branch of https://github.com/sirxpl/basketball-bot .
2. In Render, keep the existing Web Service (Free for testing). Build command: **pip install -r requirements.txt**. Start command: **python web.py**. HTTP health-check path: **/health**.
3. Open **Render → basketball-bot → Environment**. Add **ENABLE_DISCORD_BOT=false**. This option defaults to false, so a previously saved DISCORD_TOKEN is **never used automatically** by the web entrypoint. You may remove the DISCORD_TOKEN environment variable until Discord's restriction is resolved.
4. Visit https://discord.com/developers/applications and open the Basketball Bot application.
5. In **OAuth2**, copy the **Client ID (Application ID)** and **Client Secret**. Register the following exact redirect URI under OAuth2 **Redirects**:

    https://basketball-bot-6jpx.onrender.com/oauth/callback

6. Add the following environment variables under the same Render service:

| Name | Value |
| --- | --- |
| ENABLE_DISCORD_BOT | false |
| DISCORD_CLIENT_ID | The application's Client ID from Discord |
| DISCORD_CLIENT_SECRET | The private OAuth2 client secret from Discord |
| DISCORD_REDIRECT_URI | https://basketball-bot-6jpx.onrender.com/oauth/callback |
| SESSION_SECRET | A freshly generated random string of at least 32 characters |

7. To generate SESSION_SECRET locally, run this Python command and paste its output **only** into Render (never into GitHub or chat):

    python -c "import secrets; print(secrets.token_hex(32))"

8. Save and deploy once. Open https://basketball-bot-6jpx.onrender.com and click **Login with Discord**, or visit **/dashboard** directly. If OAuth2 isn't configured yet, the public website still works and the private dashboard displays a configuration notice.

**Important:** Discord OAuth2 token exchange also talks to Discord's API. The Render hosting IP restriction *might* also block OAuth login. A sign-in error does not disable the public NBA schedule or status website. Wait for the restriction to resolve rather than repeatedly restarting the bot.

**OAuth credentials are NOT the Discord bot token.** Only the identify permission is requested; this does not install the bot or grant server administrative access. OAuth bearer tokens are not placed in browser sessions. Users are authenticated with secure, signed HTTP-only cookies; sessions expire after 12 hours.

## Future Discord bot use

- **ENABLE_DISCORD_BOT=false** means that starting **python web.py** does not construct a Discord client or use the Discord bot token.
- Once the Discord rate limit is resolved, you can explicitly set **ENABLE_DISCORD_BOT=true** and configure **DISCORD_TOKEN** in Render to turn the legacy Discord worker back on. This is NOT needed now.
- **MONGODB_URI** remains optional for temporary game stats. Persistent stats can be added later without changing the web OAuth features.
- Running **python bot.py** directly also respects ENABLE_DISCORD_BOT=false and exits without logging in. Explicitly set ENABLE_DISCORD_BOT=true only after the Discord rate limit is resolved.

## Run locally

Use Python 3.11 or newer. Install dependencies:

    python -m pip install -r requirements.txt

Copy .env.example to .env, keep ENABLE_DISCORD_BOT=false, then start:

    python web.py

Open http://localhost:10000 . To test OAuth2 locally, register **http://localhost:10000/oauth/callback** in the Discord Developer Portal, use it for DISCORD_REDIRECT_URI and supply local client credentials and SESSION_SECRET.

Run tests:

    python -m unittest discover -s tests -v

Automated tests verify route protection, OAuth state checks, logout CSRF, bot pausing, NBA schedule parsing/cache and existing game logic, but they do not perform real Discord OAuth or external NBA CDN requests.

## Key modules

- web.py — Render website and optional, explicitly enabled Discord worker
- basketball/oauth.py — Discord OAuth2 identify-only code exchange
- basketball/webapp.py — Flask authentication and status/schedule routes
- basketball/schedule.py — upcoming NBA feed and cache
- basketball/nba_monitor.py — public NBA scoreboard availability probe
- basketball/status.py — thread-safe component status registry
- basketball/templates — public homepage, dashboard and OAuth error pages
- basketball/static — responsive CSS and browser-side refresh scripts
- bot.py and basketball/cogs — unchanged Discord commands and minigame logic

**Render Free hosting can spin down when idle.** The entire website may be temporarily inaccessible during sleep. Checking /health shows website availability, not whether Discord is currently running.

Independent community project, not affiliated with the NBA or its teams.
