"use strict";

const STATE_NAMES = {
  operational: "Operational",
  degraded: "Degraded",
  offline: "Offline",
  checking: "Checking",
  starting: "Starting",
  unknown: "Unknown",
  temporary: "In-memory",
  disabled: "Paused"
};

function displayTime(input) {
  if (!input) return "Not checked";
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return "Not checked";
  return d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function showStatus(data) {
  const overall = data.overall || "checking";
  const title = document.getElementById("overall-title");
  const subtitle = document.getElementById("overall-subtitle");
  const overallIcon = document.getElementById("overall-icon");
  const phrases = {
    operational: ["All monitored systems operational", "The website, Discord bot, database startup check, and NBA scoreboard feed are reporting normally.", "✓"],
    degraded: ["Some services are experiencing issues", "Check the individual components below for details.", "!"],
    checking: ["Some services are still being checked", "Information will update as each component finishes starting or checking.", "◌"],
    testing: ["Temporary testing mode", "No MongoDB required: player stats will reset when this service restarts.", "◎"],
    dashboard_only: ["Dashboard-only mode is active", "Discord bot token login is intentionally paused. Public NBA and status services are still available.", "◎"]
  };
  const info = phrases[overall] || phrases.checking;
  title.textContent = info[0];
  subtitle.textContent = info[1];
  overallIcon.textContent = info[2];
  overallIcon.className = "overall-icon " + overall;
  document.getElementById("updated-time").textContent = displayTime(data.generated_at);

  ["website", "discord", "database", "nba", "schedule"].forEach(function (component) {
    const row = data.components && data.components[component];
    if (!row) return;
    const state = STATE_NAMES[row.state] ? row.state : "unknown";
    const badge = document.getElementById("badge-" + component);
    badge.textContent = STATE_NAMES[state];
    badge.className = "state-pill " + state;
    document.getElementById("message-" + component).textContent = row.message || "No details are available.";
    document.getElementById("date-" + component).textContent = displayTime(row.checked_at || row.updated_at);
  });

  const feed = document.getElementById("event-list");
  feed.replaceChildren();
  if (!Array.isArray(data.events) || data.events.length === 0) {
    const empty = document.createElement("p");
    empty.className = "activity-empty";
    empty.textContent = "No status transitions have been recorded since this instance started.";
    feed.appendChild(empty);
    return;
  }

  data.events.slice(0, 12).forEach(function (evt) {
    const item = document.createElement("div");
    item.className = "event";
    const dot = document.createElement("span");
    dot.className = "event-indicator " + (STATE_NAMES[evt.state] ? evt.state : "unknown");
    dot.setAttribute("aria-hidden", "true");

    const body = document.createElement("div");
    body.className = "event-main";
    const headline = document.createElement("strong");
    headline.textContent = (evt.component || "Service") + " · " + (STATE_NAMES[evt.state] || "Updated");
    const desc = document.createElement("p");
    desc.textContent = evt.message || "Status changed";
    body.append(headline, desc);

    const time = document.createElement("time");
    time.textContent = displayTime(evt.at);
    item.append(dot, body, time);
    feed.appendChild(item);
  });
}

let requesting = false;
async function refreshStatus() {
  if (requesting) return;
  requesting = true;
  const button = document.getElementById("refresh-status");
  button.disabled = true;
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Status unavailable");
    showStatus(await response.json());
  } catch (_) {
    document.getElementById("overall-title").textContent = "Website status unavailable";
    document.getElementById("overall-subtitle").textContent = "Could not retrieve current component health. Try refreshing again.";
    document.getElementById("overall-icon").className = "overall-icon degraded";
    document.getElementById("overall-icon").textContent = "!";
  } finally {
    requesting = false;
    button.disabled = false;
  }
}
document.getElementById("refresh-status").addEventListener("click", refreshStatus);
refreshStatus();
setInterval(refreshStatus, 30000);


function publicScheduleNode(tag, cls, content) {
  const element = document.createElement(tag);
  if (cls) element.className = cls;
  if (content !== undefined) element.textContent = String(content);
  return element;
}
async function refreshPublicSchedule() {
  const container = document.getElementById("public-schedule");
  if (!container) return;
  try {
    const response = await fetch("/api/schedule", {cache:"no-store"});
    if (!response.ok) throw Error("Unavailable");
    const data = await response.json();
    container.replaceChildren();
    const list = Array.isArray(data.games) ? data.games.slice(0, 8) : [];
    if (!list.length) {
      container.appendChild(publicScheduleNode("p", "activity-empty",
        data.state === "checking" ? "Checking the NBA schedule feed…" :
        "No upcoming games are currently available from this server."));
    } else {
      list.forEach(function (game) {
        const card = publicScheduleNode("article", "public-schedule-card");
        const when = new Date(game.start_utc);
        const date = isNaN(when.getTime()) ? "Time unavailable" :
          when.toLocaleString(undefined, {weekday:"short",month:"short",day:"numeric",hour:"numeric",minute:"2-digit"});
        card.append(
          publicScheduleNode("span", "public-game-time", date),
          publicScheduleNode("h3", "", (game.away || "Away") + " @ " + (game.home || "Home")),
          publicScheduleNode("p", "", (game.label || "Scheduled") + " · " + (game.arena || "Venue TBA"))
        );
        container.appendChild(card);
      });
    }
    const notice=document.getElementById("schedule-notice");
    if (data.state === "degraded") {
      notice.textContent = data.stale ?
        "The NBA schedule feed is temporarily unavailable. Displaying cached games; verify on NBA.com." :
        "NBA schedule could not be loaded from this server. Please check NBA.com directly.";
    }
  } catch (_) {
    container.replaceChildren(publicScheduleNode("p","activity-empty","Could not load the NBA schedule. Try refreshing."));
  }
}
refreshPublicSchedule();
setInterval(refreshPublicSchedule, 60000);


// Share the canonical public link, not the authenticated /dashboard URL.
const shareButton=document.getElementById("copy-discord-link");
if (shareButton) {
  shareButton.addEventListener("click", async function () {
    const url=shareButton.dataset.url;
    try {
      await navigator.clipboard.writeText(url);
      shareButton.textContent="Link copied! Paste it into Discord 🏀";
    } catch (_) {
      window.prompt("Copy this public link and paste it into Discord:",url);
    }
  });
}
