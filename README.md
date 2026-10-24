# 🏀 Basketball Bot

A modular Python Discord bot with basketball minigames, server profiles and a **public Render status website**.

**Currently available:** /ping, /about, /shoot, /profile, /leaderboard and the read-only status website. NBA game results, standings, and other live data slash commands are **not implemented yet**. The website only probes the reachability of the publicly accessible NBA live scoreboard endpoint.

## 🌐 Status website / Render Free

The Render Web Service serves an introduction and mobile-friendly component status page, while one Discord client runs in a single background thread.

| Route | Purpose |
| --- | --- |
| \`/\` | Public landing page, feature overview, component health and recent in-memory transitions. |
| \`/api/status\` | JSON states for the website, Discord connection, MongoDB startup connection and NBA scoreboard feed. |
| \`/health\` | HTTP website liveness: returns 200 even if the Discord bot or NBA feed is down. |

NBA feed is probed every **five minutes** at the public NBA CDN scoreboard URL used by \`nba_api\`. A probe failure means **this instance could not reach or parse that feed**, not proof the whole NBA platform is down. The bot is independent of the NBA feed and should keep its existing minigame commands available. MongoDB is checked at startup; the site does not continuously monitor DB availability. This site is not an official NBA service status page.

### Deploy on Render (manual setup)

1. Merge the GitHub PR for this website.
2. On [Render](https://dashboard.render.com/), choose **New → Web Service**, connect \`sirxpl/basketball-bot\`, branch \`main\`, and select **Free**.
3. **Build Command:** \`pip install -r requirements.txt\`
4. **Start Command:** \`python web.py\` (not \`python bot.py\`)
5. **Health Check Path:** \`/health\`
6. Under **Environment**, add \`DISCORD_TOKEN\` and \`MONGODB_URI\` as private secrets; optionally \`MONGODB_DATABASE=basketball_bot\` and \`TEST_GUILD_ID=your-test-server-id\`. Never paste tokens, usernames, or credentials in source code.
7. Deploy and visit the \`onrender.com\` URL Render assigns. Check \`/health\` and \`/api/status\`. Allow time for the bot to log in and for the NBA probe to complete.

\`render.yaml\` is also included for Render Blueprint users. Only use **one instance/one process**; running multiple web workers would create multiple Discord gateway sessions for the same token. This app uses production WSGI server **Waitress**, bound to \`0.0.0.0:$PORT\` (Render sets \`PORT\`, default is 10000).

**Important Render Free limitation:** The entire web service can sleep after around 15 minutes without incoming HTTP traffic. When it sleeps, the bot is **also offline**, the status page is unavailable, and the next browser request starts a cold boot. The status page is not an uptime guarantee and cannot report an outage while the whole host is down.

### Local quick start

Install Python 3.11+ and dependencies:

\`\`\`bash
python -m venv .venv
# macOS / Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
\`\`\`

Copy \`.env.example\` to \`.env\` and fill in \`DISCORD_TOKEN\` and \`MONGODB_URI\`, then run:

- \`python web.py\` for the website and bot together (browse \`http://localhost:10000\`).
- \`python bot.py\` for a **Discord-only** process without the website.
- \`python -m unittest discover -s tests -v\` to run unit tests.

Create the Discord application at https://discord.com/developers/applications and install with the \`bot\` and \`applications.commands\` scopes and minimal send-message permissions. Message Content and Members privileged intents are not required.

### Commands

| Command | Description |
| --- | --- |
| \`/ping\` | Check Discord gateway latency. |
| \`/about\` | Learn what the bot currently supports. |
| \`/shoot\` | Take a virtual 2- or 3-point shot, cooldown 30 seconds per user/server. |
| \`/profile\` | Shooting stats, fictional points and XP. |
| \`/leaderboard\` | Top 10 players in the current server. |

The minigame is fictional and non-wagering. No money, betting, or real-world prizes.

### Project structure

\`\`\`text
bot.py                       Discord bot + slash command loading
web.py                       Render web and Discord entry point
basketball/
  config.py                  Environment variable validation
  database.py                MongoDB operations and indexes
  status.py                  In-memory component statuses and events
  nba_monitor.py             NBA CDN scoreboard reachability checks
  webapp.py                  Flask routes
  templates/index.html       Responsive public website
  static/style.css           Styling
  static/app.js              Client-side status refresh (30 seconds)
  cogs/general.py            /ping /about
  cogs/games.py              /shoot
  cogs/players.py            /profile /leaderboard
  services/shooting.py       Pure game rules
tests/                       Status, web, NBA monitor and game unit tests
render.yaml                  Optional Render Blueprint
\`\`\`

MongoDB stores per-server user profiles. Indexes are created at bot startup. Credentials must be environment variables; the \`.env\` file is git-ignored.

**Next milestone:** actual NBA /scores and /schedule commands, provider caching, more basketball games, favorites and a full Discord OAuth2 dashboard. The public introduction/status website is not the authenticated admin dashboard.

Community-made; not affiliated with the NBA or its teams.
