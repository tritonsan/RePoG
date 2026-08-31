(function () {
  "use strict";

  const contextUrl = "/api/seat/context";
  const turnUrl = "/api/seat/turn";
  const statusUrl = "/api/seat/turn-status";
  const nextUrl = "/api/seat/next-turn";
  const pauseUrl = "/api/seat/pause";

  async function requestJson(url, options = {}) {
    const response = await fetch(url, { cache: "no-store", credentials: "same-origin", ...options });
    const payload = await response.json();
    return payload;
  }

  function installStatusSurface() {
    const topbar = document.querySelector(".topbar");
    if (!topbar || document.getElementById("agentTable")) return null;
    const panel = document.createElement("section");
    panel.id = "agentTable";
    panel.className = "agent-table";
    panel.dataset.status = "unconfigured";
    panel.setAttribute("aria-label", "Agent participant seat");
    panel.innerHTML = [
      '<div class="agent-table-copy">',
      '<span class="agent-table-kicker">Agent Seat</span>',
      '<span class="agent-table-name" id="agentSeatName">No agent seated</span>',
      '<span class="agent-table-role" id="agentSeatRole">Open a beat to invite a browser agent.</span>',
      "</div>",
      '<span class="agent-table-status" id="agentSeatStatus" role="status" aria-live="polite">Not configured</span>'
    ].join("");
    topbar.insertAdjacentElement("afterend", panel);
    return panel;
  }

  function renderStatus(context) {
    const panel = installStatusSurface();
    if (!panel) return;
    const seat = context && context.seat ? context.seat : {};
    const beat = context && context.beat ? context.beat : {};
    const status = seat.status || "unconfigured";
    panel.dataset.status = status;
    document.getElementById("agentSeatName").textContent = seat.display_name || "No agent seated";
    document.getElementById("agentSeatRole").textContent = seat.role || "Open a beat to invite a browser agent.";
    const labels = {
      unconfigured: "Not configured",
      awaiting: "Awaiting agent turn",
      submitted: "Turn committed",
      resolved: "Beat resolved",
      closed: "Seat closed"
    };
    const suffix = beat.status === "open" ? " · beat open" : "";
    document.getElementById("agentSeatStatus").textContent = `${labels[status] || status}${suffix}`;
  }

  async function refreshSeat() {
    try {
      const context = await requestJson(contextUrl);
      renderStatus(context);
      return context;
    } catch (_error) {
      renderStatus({ seat: { status: "unconfigured", display_name: "Agent Seat unavailable", role: "Start the RePoG Table server to enable agent play." } });
      return null;
    }
  }

  function matchingKnowledge(context, topic, limit) {
    const perspective = context && context.perspective ? context.perspective : {};
    const query = String(topic || "").trim().toLocaleLowerCase();
    const facts = [
      ...(perspective.self_knowledge || []),
      ...(perspective.known_facts || []),
      ...(perspective.party_public_facts || [])
    ];
    const matches = query ? facts.filter((fact) => String(fact).toLocaleLowerCase().includes(query)) : facts;
    return matches.slice(0, Math.max(1, Math.min(Number(limit) || 8, 12)));
  }

  async function registerTools() {
    if (!document.modelContext || typeof document.modelContext.registerTool !== "function") return false;
    const readAnnotations = { readOnlyHint: true, untrustedContentHint: true };
    const tools = [
      {
        name: "repog.join_session",
        title: "Join the open RePoG Agent Seat",
        description: "Join the single explicitly prepared local Agent Seat. Returns the durable session and current seat state without exposing campaign files.",
        inputSchema: { type: "object", properties: {}, additionalProperties: false },
        annotations: readAnnotations,
        execute: async (_input, options) => requestJson(contextUrl, { signal: options && options.signal })
      },
      {
        name: "repog.get_next_turn",
        title: "Get the next RePoG turn",
        description: "Read the current durable session state and the character-safe brief when a new turn is ready.",
        inputSchema: { type: "object", properties: { after_revision: { type: "integer", minimum: 0 } }, additionalProperties: false },
        annotations: readAnnotations,
        execute: async (input, options) => requestJson(`${nextUrl}${Number.isInteger(input.after_revision) ? `?after_revision=${input.after_revision}` : ""}`, { signal: options && options.signal })
      },
      {
        name: "repog.get_my_perspective",
        title: "Get my RePoG perspective",
        description: "Read only the current scene, knowledge, persona anchors, and actions available to the character assigned to this Agent Seat.",
        inputSchema: { type: "object", properties: {}, additionalProperties: false },
        annotations: readAnnotations,
        execute: async (_input, options) => requestJson(contextUrl, { signal: options && options.signal })
      },
      {
        name: "repog.recall_my_knowledge",
        title: "Recall character knowledge",
        description: "Search only facts already present in this character's safe knowledge projection. It cannot inspect private campaign files.",
        inputSchema: {
          type: "object",
          properties: {
            topic: { type: "string", maxLength: 120, description: "A short topic or name to recall." },
            limit: { type: "integer", minimum: 1, maximum: 12, default: 8 }
          },
          required: ["topic"],
          additionalProperties: false
        },
        annotations: readAnnotations,
        execute: async (input, options) => {
          const context = await requestJson(contextUrl, { signal: options && options.signal });
          return { ok: true, topic: input.topic, facts: matchingKnowledge(context, input.topic, input.limit), source_revision: context.beat && context.beat.source_revision };
        }
      },
      {
        name: "repog.commit_turn",
        title: "Commit character turn",
        description: "Submit one proposed action for the active beat. This creates a pending intent; the RePoG GM still resolves all world consequences.",
        inputSchema: {
          type: "object",
          properties: {
            operation_id: { type: "string", pattern: "^[a-z0-9][a-z0-9._-]{0,63}$", description: "A stable unique id reused for an exact retry." },
            expected_scene_id: { type: "string", pattern: "^[a-z0-9][a-z0-9._-]{0,63}$" },
            expected_source_revision: { type: "integer", minimum: 0 },
            action: { type: "string", minLength: 1, maxLength: 1200 },
            approach: { type: "string", maxLength: 600 },
            speech: { type: "string", maxLength: 1200 }
          },
          required: ["operation_id", "expected_scene_id", "expected_source_revision", "action"],
          additionalProperties: false
        },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        execute: async (input, options) => {
          const payload = await requestJson(turnUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(input),
            signal: options && options.signal
          });
          await refreshSeat();
          return payload;
        }
      },
      {
        name: "repog.get_turn_status",
        title: "Get RePoG turn status",
        description: "Check whether a previously committed character turn is pending or resolved and read only character-visible consequences.",
        inputSchema: {
          type: "object",
          properties: {
            operation_id: { type: "string", pattern: "^[a-z0-9][a-z0-9._-]{0,63}$" }
          },
          required: ["operation_id"],
          additionalProperties: false
        },
        annotations: readAnnotations,
        execute: async (input, options) => requestJson(`${statusUrl}?operation_id=${encodeURIComponent(input.operation_id)}`, { signal: options && options.signal })
      },
      {
        name: "repog.pause_session",
        title: "Pause the RePoG Agent Seat",
        description: "Pause this durable Agent Seat session without resetting its turn history.",
        inputSchema: { type: "object", properties: { operation_id: { type: "string", pattern: "^[a-z0-9][a-z0-9._-]{0,63}$" }, expected_session_revision: { type: "integer", minimum: 0 } }, required: ["operation_id", "expected_session_revision"], additionalProperties: false },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        execute: async (input, options) => requestJson(pauseUrl, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input), signal: options && options.signal })
      }
    ];
    for (const tool of tools) await document.modelContext.registerTool(tool);
    return true;
  }

  async function start() {
    installStatusSurface();
    await refreshSeat();
    try {
      await registerTools();
    } catch (error) {
      console.warn("RePoG WebMCP tools could not be registered.", error);
    }
    window.setInterval(refreshSeat, 4000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
}());
