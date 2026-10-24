"use strict";
const names={operational:"Operational",degraded:"Degraded",offline:"Offline",starting:"Starting",checking:"Checking",unknown:"Unknown",temporary:"In-memory",disabled:"Paused"};
const parts=[["website","🌐","Website"],["discord","🤖","Discord bot"],["database","🗃️","Database"],["nba","🏀","NBA scoreboard"],["schedule","🗓️","NBA schedule"]];
let games=[], filter="all", updating=false;
function node(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=String(text);return x;}
function stamp(value){if(!value)return "Not checked";const d=new Date(value);return isNaN(d.getTime())?"Not checked":d.toLocaleString(undefined,{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"});}
function state(s){return names[s]?s:"unknown";}
function drawHealth(data){
  const overall=data.overall||"checking";
  const summary={operational:"All operational",degraded:"Needs attention",checking:"Checking…",testing:"Testing mode",dashboard_only:"Dashboard only"};
  document.getElementById("dash-system").textContent=summary[overall]||"Checking…";
  document.getElementById("dash-system-detail").textContent=overall==="dashboard_only"?"Discord bot deliberately paused":overall==="degraded"?"Some connected services have issues":"Checked "+stamp(data.generated_at);
  const discord=data.components&&data.components.discord;
  document.getElementById("dash-discord").textContent=discord?names[state(discord.state)]:"Unknown";
  const root=document.getElementById("dash-services");root.replaceChildren();
  parts.forEach(function(part){
    const item=data.components&&data.components[part[0]];if(!item)return;
    const card=node("article","dash-service-card");card.setAttribute("role","listitem");
    const head=node("div","dash-service-head");
    head.append(node("span","dash-service-icon",part[1]),node("span","state-pill "+state(item.state),names[state(item.state)]));
    card.append(head,node("h3","",part[2]),node("p","",item.message||"No details"),node("div","dash-service-footer","Checked: "+stamp(item.checked_at||item.updated_at)));
    root.appendChild(card);
  });
  const history=document.getElementById("dash-activity");history.replaceChildren();
  if(!data.events||!data.events.length){history.appendChild(node("p","activity-empty","No recent changes recorded."));return;}
  data.events.slice(0,12).forEach(function(evt){
    const row=node("div","event"),dot=node("span","event-indicator "+state(evt.state)),text=node("div","event-main");
    dot.setAttribute("aria-hidden","true");
    text.append(node("strong","",(evt.component||"Service")+" · "+names[state(evt.state)]),node("p","",evt.message||"Updated"));
    row.append(dot,text,node("time","",stamp(evt.at)));history.appendChild(row);
  });
}
function drawGames(){
  const list=document.getElementById("dash-games");list.replaceChildren();
  const now=new Date(),week=new Date(now.getTime()+7*86400000);
  const visible=games.filter(function(g){
    const t=new Date(g.start_utc);
    return !isNaN(t.getTime())&&t>=now&&(filter==="all"||(filter==="today"&&t.toDateString()===now.toDateString())||(filter==="week"&&t<=week));
  });
  if(!visible.length){list.appendChild(node("p","empty-dashboard",games.length?"No matchups for this filter.":"No upcoming matchups are available right now."));return;}
  visible.forEach(function(g){
    const card=node("article","matchup-card"),top=node("div","matchup-top"),teams=node("div","matchup-teams"),footer=node("div","matchup-footer");
    const when=new Date(g.start_utc);
    top.append(node("span","matchup-date",when.toLocaleDateString(undefined,{weekday:"short",month:"short",day:"numeric"})+" · "+when.toLocaleTimeString(undefined,{hour:"numeric",minute:"2-digit"})),node("span","matchup-status",g.status||"Scheduled"));
    const away=node("div","matchup-team"),home=node("div","matchup-team");
    away.append(node("span","team-code",g.away_abbr||"NBA"),node("span","team-name",g.away||"Away"));
    home.append(node("span","team-code",g.home_abbr||"NBA"),node("span","team-name",g.home||"Home"));
    teams.append(away,node("span","matchup-at","@"),home);
    footer.append(node("span","",g.label||"NBA game"),node("span","",g.arena||"Venue TBA"));
    card.append(top,teams,footer);list.appendChild(card);
  });
}
function drawSchedule(data){
  games=Array.isArray(data.games)?data.games:[];
  document.getElementById("dash-game-count").textContent=String(games.length);
  document.getElementById("games-updated").textContent="Schedule "+(names[state(data.state)])+(data.updated_at?" · "+stamp(data.updated_at):"");
  document.getElementById("dash-schedule-notice").textContent=data.state==="degraded"?
    (data.stale?"NBA feed unavailable: showing cached games. Verify on NBA.com.":"NBA schedule feed unavailable from this server. Check NBA.com."):
    "Game times are displayed in your device's local timezone. Matchups and times may change.";
  drawGames();
}
async function refresh(){
  if(updating)return;updating=true;
  const button=document.getElementById("dash-refresh");button.disabled=true;
  try{
    const responses=await Promise.all([fetch("/api/status",{cache:"no-store"}),fetch("/api/schedule",{cache:"no-store"})]);
    if(!responses.every(r=>r.ok))throw Error("Unavailable");
    const data=await Promise.all(responses.map(r=>r.json()));drawHealth(data[0]);drawSchedule(data[1]);
  }catch(err){
    document.getElementById("dash-system").textContent="Unavailable";
    document.getElementById("dash-system-detail").textContent="Could not refresh service status.";
    document.getElementById("dash-schedule-notice").textContent="Could not refresh NBA schedule. Try again.";
  }finally{button.disabled=false;updating=false;}
}
document.querySelectorAll(".dash-tab").forEach(function(tab){
  tab.addEventListener("click",function(){
    filter=tab.dataset.filter;
    document.querySelectorAll(".dash-tab").forEach(function(b){b.classList.toggle("active",b===tab);b.setAttribute("aria-pressed",b===tab?"true":"false");});
    drawGames();
  });
});
document.getElementById("dash-refresh").addEventListener("click",refresh);
refresh();setInterval(refresh,30000);
