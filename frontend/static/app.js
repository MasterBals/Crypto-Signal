const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");
const form = document.getElementById("signalForm");
const recommendation = document.getElementById("recommendation");
const timeline = document.getElementById("timeline");

const fields = {
  action: recommendation.querySelector('[data-value="action"]'),
  confidence: recommendation.querySelector('[data-value="confidence"]'),
  entry: recommendation.querySelector('[data-value="entry"]'),
  tp: recommendation.querySelector('[data-value="tp"]'),
  sl: recommendation.querySelector('[data-value="sl"]'),
  summary: recommendation.querySelector('[data-value="summary"]'),
};

const history = [];

const setStatus = (ok, message) => {
  statusDot.classList.toggle("ok", ok);
  statusText.textContent = message;
};

const renderTimeline = () => {
  timeline.innerHTML = "";
  history.slice(0, 5).forEach((item) => {
    const card = document.createElement("div");
    card.className = "timeline-card";
    card.innerHTML = `
      <h3>${item.pair} · ${item.action}</h3>
      <p>${item.summary}</p>
      <p>Konfidenz: ${item.confidence} · Zeit: ${item.time}</p>
    `;
    timeline.appendChild(card);
  });
};

const updateRecommendation = (data) => {
  fields.action.textContent = data.action;
  fields.confidence.textContent = data.confidence;
  fields.entry.textContent = data.entry;
  fields.tp.textContent = data.takeProfit;
  fields.sl.textContent = data.stopLoss;
  fields.summary.textContent = data.summary;
};

const mockSignal = (payload) => {
  const actions = ["BUY", "SELL", "HOLD"];
  const action = actions[Math.floor(Math.random() * actions.length)];
  return {
    pair: payload.pair,
    action,
    confidence: `${Math.floor(68 + Math.random() * 20)}%`,
    entry: `${payload.pair} @ ${1.08 + Math.random() * 0.2}`.slice(0, 16),
    takeProfit: "+45 Pips",
    stopLoss: "-20 Pips",
    summary: `Trend ${payload.strategy} mit ${payload.timeframe} Fokus. Risiko-Level ${payload.risk}.`,
  };
};

const checkBackend = async () => {
  try {
    const response = await fetch("/api/");
    if (response.ok) {
      setStatus(true, "Backend erreichbar");
      return;
    }
    setStatus(false, "Backend antwortet nicht");
  } catch (error) {
    setStatus(false, "Backend nicht verfügbar");
  }
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  const endpoint = payload.endpoint || "/api/signal";

  const requestBody = {
    pair: payload.pair,
    timeframe: payload.timeframe,
    strategy: payload.strategy,
    risk: Number(payload.risk),
    positions: Number(payload.positions),
    alerts: formData.get("alerts") === "on",
    macro: formData.get("macro") === "on",
    market: "forex",
  };

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error("Backend response not ok");
    }

    const data = await response.json();
    const normalized = {
      pair: payload.pair,
      action: data.action ?? "HOLD",
      confidence: data.confidence ?? "—",
      entry: data.entry ?? "—",
      takeProfit: data.takeProfit ?? data.tp ?? "—",
      stopLoss: data.stopLoss ?? data.sl ?? "—",
      summary: data.summary ?? "Backend liefert keine Zusammenfassung.",
    };

    updateRecommendation(normalized);
    history.unshift({
      ...normalized,
      time: new Date().toLocaleTimeString("de-DE"),
    });
  } catch (error) {
    const fallback = mockSignal(payload);
    updateRecommendation(fallback);
    history.unshift({
      ...fallback,
      time: new Date().toLocaleTimeString("de-DE"),
    });
  }

  renderTimeline();
});

checkBackend();
renderTimeline();
