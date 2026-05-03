const baseUrl = new URL("..", window.location.href);

const forecastFiles = [
  "outputs/golden-forecast-edge-appliance.json",
  "outputs/golden-forecast-financial-theft.json",
  "outputs/golden-forecast-wiper-shutdown.json"
];

const state = {
  forecasts: [],
  records: [],
  catalog: { sources: [] },
  selectedForecast: 0,
  demoFallback: false
};

const fallbackForecast = {
  forecast_id: "demo_fallback_edge_appliance",
  input_candidate_id: "cs-fixture-edge-appliance-001",
  schema_version: "world_forecast.v0.1",
  generated_at: "2026-05-02T23:45:00Z",
  strategic_frame: {
    adversary_class: "state-aligned actors",
    target_scope: "federal and defense-support edge infrastructure",
    geographic_scope: "US / Indo-Pacific",
    forecast_assumptions: ["demo fallback"],
    excluded_uses: ["targeting guidance", "exploit payloads"]
  },
  strike_windows: [
    {
      window_id: "demo_window_001",
      start_date: "2026-05-03",
      end_date: "2026-05-09",
      confidence: "medium",
      why_this_window: "Current official and chatter context clusters around near-term diplomatic and infrastructure pressure.",
      trigger_signals: ["official advisories", "sanitized chatter", "historical edge-appliance analogy"],
      historical_analogies: [
        {
          case_id: "hist_volt_typhoon",
          case_name: "Volt Typhoon pre-positioning",
          pattern_matched: "edge infrastructure access",
          time_to_burn: "months",
          source_ref_ids: ["src_context_chatter"]
        }
      ],
      source_ref_ids: ["src_context_chatter"]
    }
  ],
  strike_vectors: [
    {
      vector_id: "demo_vector_001",
      vector_class: "edge-appliance initial access and pre-positioning",
      target_sector: "federal and defense-support networks",
      likely_objective: "collection and persistence",
      non_actionable_mechanism: "High-level defensive class only; no exploit steps.",
      candidate_fit: "strong",
      why_this_vector: "Historical corpus and sanitized current records both emphasize perimeter appliances.",
      defensive_implication: "Prioritize edge-device patching, logging, and abnormal access review.",
      source_ref_ids: ["src_context_chatter"]
    }
  ],
  summary: {
    one_line: "Demo fallback forecast for edge-appliance timing pressure.",
    recommended_demo_path: "Use golden fixtures when live feeds are unavailable.",
    stage3_priority: "high",
    analyst_notes: []
  },
  source_refs: [
    {
      id: "src_context_chatter",
      label: "Sanitized chatter fixture",
      url: "sanitized://scraper-record/demo",
      date: "2026-05-02",
      supports: "demo fallback context"
    }
  ]
};

const fallbackRecords = [
  {
    record_id: "chat_fixture_001",
    observed_at: "2026-05-02T22:20:00Z",
    source_type: "telegram_public_channel",
    collection_tier: "public_chatter",
    actor_hint: "PRC-nexus",
    region_hint: "US / Indo-Pacific",
    target_sector: "US federal and defense edge infrastructure",
    vector_class: "edge-appliance access and pre-positioning",
    motive_hint: "summit-timed collection interest",
    confidence: "medium",
    summary: "Sanitized public-channel chatter notes increased discussion of federal edge-access themes around a near-term diplomatic window.",
    source_ref: {
      id: "src_chatter_fixture_001",
      label: "Sanitized chatter fixture",
      url: "sanitized://scraper-record/chat_fixture_001",
      date: "2026-05-02",
      supports: "current public chatter signal"
    },
    tags: ["edge", "appliance", "public_chatter"]
  },
  {
    record_id: "chat_fixture_002",
    observed_at: "2026-05-02T22:35:00Z",
    source_type: "onion_public_metadata",
    collection_tier: "darkweb_metadata",
    actor_hint: "ransomware/extortion ecosystem",
    region_hint: "US / global",
    target_sector: "managed file transfer and enterprise service providers",
    vector_class: "mass extortion against enterprise services",
    motive_hint: "holiday and weekend response-gap interest",
    confidence: "low",
    summary: "Sanitized metadata-only observation of public extortion-site themes around enterprise-service data exposure.",
    source_ref: {
      id: "src_chatter_fixture_002",
      label: "Sanitized metadata fixture",
      url: "sanitized://scraper-record/chat_fixture_002",
      date: "2026-05-02",
      supports: "metadata-only extortion timing signal"
    },
    tags: ["darkweb_metadata", "enterprise_services"]
  }
];

const fallbackCatalog = {
  sources: [
    { id: "cisa_kev_json", enabled: true, lane: "official_gov_feeds", source_type: "gov_feed", display_name: "CISA KEV JSON", collection: { auth_method: "none" } },
    { id: "first_epss_api", enabled: true, lane: "public_technical_chatter", source_type: "technical_api", display_name: "FIRST EPSS API", collection: { auth_method: "none" } },
    { id: "worldmonitor_bootstrap_api", enabled: false, lane: "osint_context_feeds", source_type: "osint_context", display_name: "World Monitor Bootstrap API", collection: { auth_method: "api_key_required" } },
    { id: "telegram_public_channel_metadata", enabled: false, lane: "public_social_chatter", source_type: "public_social", display_name: "Telegram Public Channel Metadata", collection: { auth_method: "not_applicable" } },
    { id: "onion_public_landing_metadata", enabled: false, lane: "high_risk_metadata_only", source_type: "high_risk_metadata", display_name: "Onion Public Landing Metadata", collection: { auth_method: "not_applicable" } }
  ]
};

init();

async function init() {
  bindTabs();
  await loadData();
  render();
}

function bindTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("is-active"));
      document.querySelectorAll(".view").forEach((view) => view.classList.remove("is-active"));
      button.classList.add("is-active");
      document.getElementById(`${button.dataset.view}View`).classList.add("is-active");
    });
  });
}

async function loadData() {
  try {
    const [catalog, chatter, ...forecasts] = await Promise.all([
      fetchJson("scraper/config/source_catalog.json"),
      fetchText("fixtures/sanitized-chatter-sample.jsonl"),
      ...forecastFiles.map(fetchJson)
    ]);
    state.catalog = catalog;
    state.records = parseJsonl(chatter);
    state.forecasts = forecasts.filter(Boolean);
  } catch (error) {
    state.demoFallback = true;
    state.catalog = fallbackCatalog;
    state.records = fallbackRecords;
    state.forecasts = [fallbackForecast];
  }
}

async function fetchJson(path) {
  const response = await fetch(new URL(path, baseUrl));
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`);
  }
  return response.json();
}

async function fetchText(path) {
  const response = await fetch(new URL(path, baseUrl));
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`);
  }
  return response.text();
}

function parseJsonl(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function render() {
  renderStatus();
  renderScore();
  renderMap();
  renderFeed();
  renderSources();
  renderForecasts();
}

function renderStatus() {
  const enabled = state.catalog.sources.filter((source) => source.enabled).length;
  const disabled = state.catalog.sources.length - enabled;
  const mode = state.demoFallback ? "Fallback demo" : "Fixture demo";
  const strip = document.getElementById("statusStrip");
  strip.innerHTML = [
    pill(mode, "green"),
    pill(`${enabled} enabled sources`, "blue"),
    pill(`${disabled} gated or disabled`, "amber"),
    pill(`${state.records.length} sanitized records`, "green")
  ].join("");
}

function renderScore() {
  const forecast = currentForecast();
  const parts = pressureParts(forecast);
  const total = Math.min(100, Object.values(parts).reduce((sum, value) => sum + value, 0));
  const ring = document.getElementById("scoreRing");
  ring.style.setProperty("--score", total);
  document.getElementById("scoreValue").textContent = String(total);
  document.getElementById("pressureLabel").textContent = pressureLabel(total);

  const colors = ["#2f7d5c", "#2d7f89", "#b87913", "#446a9b", "#b84b3f"];
  document.getElementById("scoreBreakdown").innerHTML = Object.entries(parts)
    .map(([label, value], index) => `
      <div class="metric-row">
        <strong>${escapeHtml(label)}</strong>
        <div class="bar" style="--bar-color:${colors[index % colors.length]}"><span style="--value:${value}"></span></div>
        <span>${value}</span>
      </div>
    `)
    .join("");
}

function pressureParts(forecast) {
  const officialRecords = state.records.filter((record) => record.collection_tier === "official_signal").length;
  const enabledOfficial = state.catalog.sources.filter((source) => source.enabled && source.lane === "official_gov_feeds").length;
  const chatterRecords = state.records.filter((record) => ["public_chatter", "darkweb_metadata", "technical_chatter"].includes(record.collection_tier)).length;
  const analogies = (forecast.strike_windows || []).flatMap((windowItem) => windowItem.historical_analogies || []).length;
  const windows = forecast.strike_windows || [];
  const vectors = forecast.strike_vectors || [];

  return {
    "official pressure": clampScore(enabledOfficial * 2 + officialRecords * 4, 30),
    "exploit relevance": clampScore(vectors.length * 9 + vectorFitBonus(vectors), 25),
    "chatter convergence": clampScore(chatterRecords * 8, 20),
    "historical analogy": clampScore(analogies * 5, 15),
    "timing calendar": clampScore(windows.length * 4 + confidenceBonus(windows), 10)
  };
}

function vectorFitBonus(vectors) {
  return vectors.reduce((score, vector) => score + (String(vector.candidate_fit || "").toLowerCase().includes("strong") ? 7 : 3), 0);
}

function confidenceBonus(windows) {
  return windows.reduce((score, item) => {
    const confidence = String(item.confidence || "").toLowerCase();
    if (confidence === "high") return score + 6;
    if (confidence === "medium") return score + 4;
    return score + 2;
  }, 0);
}

function clampScore(value, max) {
  return Math.max(0, Math.min(max, Math.round(value)));
}

function pressureLabel(score) {
  if (score >= 78) return "Elevated";
  if (score >= 54) return "Watch";
  return "Baseline";
}

function renderMap() {
  const regions = buildRegions();
  const top = regions.slice().sort((a, b) => b.heat - a.heat)[0];
  document.getElementById("topRegion").textContent = top ? top.name : "Regional Heat";
  document.getElementById("regionGrid").innerHTML = regions
    .map((region) => `
      <div class="region-cell" style="--heat:${region.heat}; --heat-color:${region.color}">
        <strong>${escapeHtml(region.name)}</strong>
        <span>${escapeHtml(region.note)}</span>
        <span>${region.heat}/100</span>
      </div>
    `)
    .join("");
}

function buildRegions() {
  const buckets = [
    { name: "North America", keys: ["us", "united states", "federal"], color: "#2f7d5c" },
    { name: "Europe", keys: ["eu", "europe", "russia", "ukraine"], color: "#446a9b" },
    { name: "Indo-Pacific", keys: ["indo-pacific", "prc", "china", "taiwan"], color: "#b87913" },
    { name: "Middle East", keys: ["middle east", "iran", "red sea", "israel"], color: "#b84b3f" },
    { name: "Global Infrastructure", keys: ["global", "critical infrastructure", "energy", "shipping"], color: "#2d7f89" },
    { name: "Financial System", keys: ["financial", "bank", "payments"], color: "#6f6b35" }
  ];
  const text = [
    ...state.records.map((record) => `${record.region_hint} ${record.target_sector} ${record.summary}`),
    currentForecast().strategic_frame?.geographic_scope || "",
    currentForecast().summary?.one_line || ""
  ].join(" ").toLowerCase();

  return buckets.map((bucket) => {
    const matches = bucket.keys.reduce((count, key) => count + (text.includes(key) ? 1 : 0), 0);
    const heat = clampScore(24 + matches * 18 + state.records.length * 2, 100);
    return {
      ...bucket,
      heat,
      note: matches ? `${matches} signal cluster(s) in current forecast context` : "No dominant cluster in loaded demo records"
    };
  });
}

function renderFeed() {
  const records = state.records.slice().sort((a, b) => String(b.observed_at).localeCompare(String(a.observed_at)));
  document.getElementById("feedCount").textContent = `${records.length} records`;
  document.getElementById("feedList").innerHTML = records
    .map((record) => `
      <article class="feed-item">
        <h3>${escapeHtml(record.vector_class || record.source_type)}</h3>
        <p>${escapeHtml(record.summary)}</p>
        <div class="feed-meta">
          ${pill(record.collection_tier || "unknown", colorForTier(record.collection_tier))}
          ${pill(record.source_type || "source", "blue")}
          ${pill(record.confidence || "confidence", confidenceColor(record.confidence))}
        </div>
      </article>
    `)
    .join("");
}

function renderSources() {
  const sources = state.catalog.sources || [];
  const byLane = groupBy(sources, (source) => source.lane || "uncategorized");
  const enabled = sources.filter((source) => source.enabled).length;
  document.getElementById("sourceSummary").textContent = `${enabled}/${sources.length} enabled`;
  document.getElementById("laneList").innerHTML = Object.entries(byLane)
    .map(([lane, laneSources]) => {
      const enabledCount = laneSources.filter((source) => source.enabled).length;
      return `
        <div class="lane-row">
          <div>
            <strong>${formatLabel(lane)}</strong>
            <small>${laneSources.map((source) => source.display_name || source.id).slice(0, 4).join(", ")}</small>
          </div>
          ${pill(`${enabledCount}/${laneSources.length}`, enabledCount ? "green" : "amber")}
        </div>
      `;
    })
    .join("");

  const boundary = [
    ["Open-source lanes", "Official feeds, public metadata APIs, RSS, GDELT, ReliefWeb, USGS, GDACS, GitHub, Reddit."],
    ["World Monitor", "Disabled optional API-key context lane until WORLDMONITOR_API_KEY exists outside git."],
    ["Telegram", "Disabled VM-side sanitized JSONL import only; no channel names, handles, invite links, or raw posts."],
    ["Onion", "Disabled VM-side metadata JSONL import only; no hidden-service addresses, stolen files, screenshots, or dumps."],
    ["Private integrations", "Reserved for Idan after authorization, terms review, and sanitizer contract review."]
  ];
  document.getElementById("boundaryList").innerHTML = boundary
    .map(([title, body]) => `
      <div class="boundary-row">
        <div>
          <strong>${escapeHtml(title)}</strong>
          <p>${escapeHtml(body)}</p>
        </div>
      </div>
    `)
    .join("");
}

function renderForecasts() {
  const forecasts = state.forecasts.length ? state.forecasts : [fallbackForecast];
  document.getElementById("forecastNav").innerHTML = forecasts
    .map((forecast, index) => `
      <button class="forecast-card ${index === state.selectedForecast ? "is-active" : ""}" type="button" data-forecast-index="${index}">
        <h3>${escapeHtml(forecast.input_candidate_id || forecast.forecast_id)}</h3>
        <div class="subline">
          ${pill(`${(forecast.strike_windows || []).length} windows`, "blue")}
          ${pill(`${(forecast.strike_vectors || []).length} vectors`, "green")}
        </div>
        <p>${escapeHtml(forecast.summary?.one_line || "Forecast")}</p>
      </button>
    `)
    .join("");
  document.querySelectorAll("[data-forecast-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedForecast = Number(button.dataset.forecastIndex);
      renderForecasts();
      renderScore();
      renderMap();
    });
  });
  renderForecastDetail(forecasts[state.selectedForecast] || forecasts[0]);
}

function renderForecastDetail(forecast) {
  const windows = forecast.strike_windows || [];
  const vectors = forecast.strike_vectors || [];
  const refs = forecast.source_refs || [];
  document.getElementById("forecastDetail").innerHTML = `
    <p class="kicker">${escapeHtml(forecast.schema_version || "world_forecast")}</p>
    <h2>${escapeHtml(forecast.input_candidate_id || forecast.forecast_id)}</h2>
    <p>${escapeHtml(forecast.summary?.one_line || "")}</p>
    <div class="detail-grid">
      ${windows.map(renderWindow).join("")}
      ${vectors.map(renderVector).join("")}
    </div>
    <div class="detail-section">
      <h3>Source Citations</h3>
      <div class="source-list">
        ${refs.slice(0, 8).map(renderSource).join("")}
      </div>
    </div>
  `;
}

function renderWindow(item) {
  const analogies = (item.historical_analogies || []).map((analogy) => analogy.case_name).slice(0, 2).join(", ");
  return `
    <article class="window-row">
      <h3>${escapeHtml(item.start_date)} to ${escapeHtml(item.end_date)}</h3>
      <div class="subline">${pill(item.confidence || "confidence", confidenceColor(item.confidence))}</div>
      <p>${escapeHtml(item.why_this_window || "")}</p>
      <p>${escapeHtml(analogies || "No analogy listed")}</p>
    </article>
  `;
}

function renderVector(item) {
  return `
    <article class="vector-row">
      <h3>${escapeHtml(item.vector_class || "Strike vector")}</h3>
      <div class="subline">${pill(item.candidate_fit || "fit", "green")}</div>
      <p>${escapeHtml(item.defensive_implication || item.why_this_vector || "")}</p>
    </article>
  `;
}

function renderSource(ref) {
  const safeUrl = String(ref.url || "");
  const link = safeUrl.startsWith("https://")
    ? `<a href="${escapeAttribute(safeUrl)}" target="_blank" rel="noreferrer">${escapeHtml(ref.label || ref.id)}</a>`
    : `<strong>${escapeHtml(ref.label || ref.id)}</strong>`;
  return `
    <article class="source-row">
      ${link}
      <p>${escapeHtml(ref.supports || "")}</p>
    </article>
  `;
}

function currentForecast() {
  return state.forecasts[state.selectedForecast] || state.forecasts[0] || fallbackForecast;
}

function groupBy(items, keyFn) {
  return items.reduce((groups, item) => {
    const key = keyFn(item);
    groups[key] = groups[key] || [];
    groups[key].push(item);
    return groups;
  }, {});
}

function pill(text, color = "") {
  return `<span class="pill ${escapeAttribute(color)}">${escapeHtml(text)}</span>`;
}

function colorForTier(tier) {
  if (tier === "official_signal") return "green";
  if (tier === "darkweb_metadata") return "red";
  if (tier === "public_chatter") return "amber";
  if (tier === "technical_chatter") return "blue";
  return "";
}

function confidenceColor(confidence) {
  const value = String(confidence || "").toLowerCase();
  if (value === "high") return "green";
  if (value === "medium") return "amber";
  return "red";
}

function formatLabel(value) {
  return escapeHtml(String(value).replaceAll("_", " "));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}
