"use strict";

const STATE_NAMES = {
  operational: "Operational",
  degraded: "Degraded",
  offline: "Offline",
  checking: "Checking",
  starting: "Starting",
  unknown: "Unknown"
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
    checking: ["Some services are still being checked", "Information will update as each component finishes starting or checking.", "◌"]
  };
  const info = phrases[overall] || phrases.checking;
  title.textContent = info[0];
  subtitle.textContent = info[1];
  overallIcon.textContent = info[2];
  overallIcon.className = "overall-icon " + overall;
  document.getElementById("updated-time").textContent = displayTime(data.generated_at);

  ["website", "discord", "database", "nba"].forEach(function (component) {
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
