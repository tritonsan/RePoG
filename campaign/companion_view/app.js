"use strict";

const STATE_URL = "companion_view_state.json";
const POLL_MS = 8000;
const elements = {
  connection: document.querySelector("#connection-status"),
  inactive: document.querySelector("#inactive"),
  companion: document.querySelector("#companion"),
  portraitWrap: document.querySelector("#portrait-wrap"),
  portrait: document.querySelector("#portrait"),
  name: document.querySelector("#companion-name"),
  pronouns: document.querySelector("#pronouns"),
  tagline: document.querySelector("#tagline"),
  clock: document.querySelector("#clock"),
  statusSection: document.querySelector("#status-section"),
  status: document.querySelector("#shared-status"),
  sharedAt: document.querySelector("#shared-at"),
  cardsSection: document.querySelector("#cards-section"),
  cards: document.querySelector("#shared-cards"),
};

let appliedRevision = null;
let pollTimer = null;
let clockTimer = null;
let clockConfig = null;
let requestInFlight = false;

function text(node, value) {
  node.textContent = typeof value === "string" ? value : "";
}

function formatSharedTime(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function renderClock() {
  if (!clockConfig) return;
  try {
    const time = new Intl.DateTimeFormat(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: clockConfig.timezone,
    }).format(new Date());
    text(elements.clock, `${clockConfig.label} · ${time}`);
    elements.clock.hidden = false;
  } catch (_error) {
    elements.clock.hidden = true;
  }
}

function startClock(config) {
  if (clockTimer !== null) window.clearInterval(clockTimer);
  clockTimer = null;
  clockConfig = config && typeof config === "object" ? config : null;
  elements.clock.hidden = true;
  if (!clockConfig) return;
  renderClock();
  clockTimer = window.setInterval(renderClock, 30000);
}

function renderPortrait(portrait) {
  const usable = portrait && typeof portrait.asset === "string" && typeof portrait.alt === "string";
  elements.portraitWrap.hidden = !usable;
  if (!usable) {
    elements.portrait.removeAttribute("src");
    elements.portrait.alt = "";
    return;
  }
  elements.portrait.src = portrait.asset;
  elements.portrait.alt = portrait.alt;
}

function renderStatus(status) {
  const usable = status && typeof status.text === "string" && status.text.length > 0;
  elements.statusSection.hidden = !usable;
  if (!usable) return;
  text(elements.status, status.text);
  const formatted = formatSharedTime(status.shared_at);
  text(elements.sharedAt, formatted);
  elements.sharedAt.dateTime = typeof status.shared_at === "string" ? status.shared_at : "";
  elements.sharedAt.hidden = !formatted;
}

function renderCards(cards) {
  elements.cards.replaceChildren();
  const safeCards = Array.isArray(cards) ? cards.slice(0, 3) : [];
  elements.cardsSection.hidden = safeCards.length === 0;
  for (const card of safeCards) {
    const item = document.createElement("li");
    item.className = "shared-card";
    const kind = document.createElement("p");
    kind.className = "card-type";
    text(kind, card.type);
    const title = document.createElement("h3");
    text(title, card.title);
    const body = document.createElement("p");
    text(body, card.text);
    item.append(kind, title, body);
    elements.cards.append(item);
  }
}

function render(state) {
  if (state.enabled !== true) {
    elements.inactive.hidden = false;
    elements.companion.hidden = true;
    startClock(null);
    return;
  }
  elements.inactive.hidden = true;
  elements.companion.hidden = false;
  text(elements.name, state.identity.name);
  text(elements.pronouns, state.identity.pronouns);
  elements.pronouns.hidden = !state.identity.pronouns;
  text(elements.tagline, state.identity.tagline);
  elements.tagline.hidden = !state.identity.tagline;
  renderPortrait(state.portrait);
  startClock(state.local_clock);
  renderStatus(state.last_shared_status);
  renderCards(state.shared_cards);
}

function schedulePoll() {
  if (pollTimer !== null) window.clearTimeout(pollTimer);
  pollTimer = null;
  if (!document.hidden) pollTimer = window.setTimeout(loadState, POLL_MS);
}

async function loadState() {
  if (document.hidden || requestInFlight) {
    schedulePoll();
    return;
  }
  requestInFlight = true;
  try {
    const response = await fetch(STATE_URL, { cache: "no-cache", credentials: "same-origin" });
    if (!response.ok) throw new Error(`View state unavailable (${response.status})`);
    const state = await response.json();
    if (!Number.isInteger(state.public_surface_revision)) throw new Error("View revision is invalid");
    if (state.public_surface_revision !== appliedRevision) {
      render(state);
      appliedRevision = state.public_surface_revision;
    }
    text(elements.connection, "Shared details are current");
  } catch (_error) {
    text(elements.connection, "Shared details are temporarily unavailable");
  } finally {
    requestInFlight = false;
    schedulePoll();
  }
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    if (pollTimer !== null) window.clearTimeout(pollTimer);
    pollTimer = null;
    return;
  }
  loadState();
});

loadState();
