# 🏀 Basketball Bot

Discord basketball minigames today; NBA data, team tracking and notifications in later releases.

**Status:** Foundation / early development. Real NBA scores, standings, player data, and dashboard are **not implemented yet**. No made-up live results.

## Included slash commands

| Command | Description |
| --- | --- |
| /ping | Check bot latency. |
| /about | View project information. |
| /shoot | Attempt a 2- or 3-point virtual basketball shot. 30-second cooldown per user and server. |
| /profile | View your points, XP, shooting attempts, and accuracy. |
| /leaderboard | Top 10 scorers in the current server. |

The shooting minigame awards **fictional points and XP only**. There is no gambling, betting, or real-money exchange.

## Project structure

```text
bot.py                          # Discord client, startup, slash command syncing
basketball/
  config.py                     # Environment configuration
  database.py                   # Async MongoDB and indexes
  cogs/
    general.py                  # /ping, /about
    players.py                  # /profile, /leaderboard
    games.py                    # /shoot
  services/
    shooting.py                 # Pure and testable game rules
tests/test_shooting.py          # Standard-library unit tests
```

## First-time setup

1. Install **Python 3.11 or newer** and create a Discord application/bot in the Discord Developer Portal.
2. Invite your bot with the **bot** and **applications.commands** OAuth2 scopes. Grant only necessary permissions (e.g. Send Messages and Embed Links). No Message Content or Members privileged intents are needed.
3. Create a free MongoDB Atlas deployment (or use another compatible MongoDB server). Create a database user and configure Atlas network access to allow your host to connect.
4. Make a virtual environment and install dependencies:

```sh
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

5. Copy `.env.example` to `.env` and configure `DISCORD_TOKEN` and `MONGODB_URI`. For faster testing, set `TEST_GUILD_ID` to your Discord server ID.
6. Start it:

```sh
python bot.py
```

**Never commit your bot token, MongoDB URI/password, or local .env file.** Keep them in your deployment's secret environment variables. Rotate anything accidentally exposed.

## Deploy on Railway / Render

- Runtime: **Python 3.11+**
- Install/build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Secret environment variables: `DISCORD_TOKEN`, `MONGODB_URI`
- Optional variables: `MONGODB_DATABASE`, `TEST_GUILD_ID`

Use a worker/background service where available: this is a Discord gateway bot, **not** an HTTP web server. Do not expect an HTTP health endpoint. On hosts where worker services require a paid tier, check the hosting plan before deploying.

## Database

The bot creates indexes at startup. The `players` collection stores one profile **per guild and user**, with shots, made shots, fictional points, XP and creation time. `guild_settings` is reserved for future notification settings. The application fails fast with a clear error if MongoDB cannot be reached, rather than running with lost data.

## Command synchronization

- With `TEST_GUILD_ID`: commands sync to the specified development server for quick testing.
- Without it: global commands sync at startup; it may take time for new commands to appear.
- **Important:** switching from global to test-guild sync does not remove previously published global commands. Clean up global registrations separately if necessary.

## Tests

```sh
python -m unittest discover -s tests -v
```

CI also compiles Python files and runs those tests.

## Next features (not yet shipped)

- Real NBA data provider integration: live scores, schedules, team rosters and standings.
- Saved favorite NBA teams and game notification channels.
- More minigames, achievements, moderation/configuration commands.
- OAuth2 web dashboard with server-level administration.

Built for community basketball fun; not affiliated with the NBA or its teams.
