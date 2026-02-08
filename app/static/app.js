let refreshSeconds = 300;
let refreshTimer = null;

function fmtTs(epoch) {
  const d = new Date(epoch * 1000);
  return d.toLocaleString();
}

function fmtHours(value) {
  if (value === null || value === undefined) return "-";
  return `${value}h`;
}

function clsSent(x) {
  if (x >= 0.15) return "sent-pos";
  if (x <= -0.15) return "sent-neg";
  return "sent-neu";
}

function setBadge(actionEl, action) {
  actionEl.textContent = action;
  actionEl.style.color = "#e5e7eb";
  if (action.includes("BUY")) actionEl.style.background = "rgba(22,163,74,0.18)";
  else if (action.includes("SELL")) actionEl.style.background = "rgba(220,38,38,0.18)";
  else actionEl.style.background = "rgba(245,158,11,0.18)";
}

let chart;
let candleSeries;

function initChart() {
  const el = document.getElementById("chart");
  chart = LightweightCharts.createChart(el, {
    layout: { background: { type: "solid", color: "transparent" }, textColor: "#e5e7eb" },
    grid: {
      vertLines: { color: "rgba(31,41,55,0.6)" },
      horzLines: { color: "rgba(31,41,55,0.6)" },
    },
    rightPriceScale: { borderColor: "rgba(31,41,55,0.8)" },
    timeScale: { borderColor: "rgba(31,41,55,0.8)" },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  });
  candleSeries = chart.addCandlestickSeries();
  window.addEventListener("resize", () => chart.resize(el.clientWidth, el.clientHeight));
  chart.resize(el.clientWidth, el.clientHeight);
}

function renderNews(items) {
  const root = document.getElementById("news");
  if (!items || items.length === 0) {
    root.innerHTML =
      '<div class="news-item"><div class="news-meta">Keine passenden News gefunden oder RSS temporaer nicht erreichbar.</div></div>';
    return;
  }
  root.innerHTML = items
    .map(
      (it) =>
        `<div class="news-item">
          <a class="news-title" href="${it.link || "#"}" target="_blank" rel="noreferrer">${it.title}</a>
          <div class="news-meta">
            <span>${it.source || "rss"}</span>
            <span class="${clsSent(it.sentiment)}">Sentiment: ${Number(it.sentiment).toFixed(2)}</span>
          </div>
        </div>`,
    )
    .join("");
}

function updateRefresh(seconds) {
  if (!seconds || Number.isNaN(Number(seconds))) return;
  const next = Number(seconds);
  if (next <= 0 || next === refreshSeconds) return;
  refreshSeconds = next;
  document.getElementById("refresh").textContent = `${refreshSeconds}`;
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
  refreshTimer = setInterval(tick, refreshSeconds * 1000);
}

async function fetchState() {
  const r = await fetch("/api/state", { cache: "no-store" });
  if (!r.ok) throw new Error("API Fehler");
  return await r.json();
}

function renderState(s) {
  const currency = s.meta.display_currency || "";
  document.getElementById("updated").textContent = `Update: ${fmtTs(s.updated_epoch)}`;
  document.getElementById("price").textContent = `Preis: ${s.market.price} ${currency}`;

  document.getElementById("meta").textContent = `${s.meta.pair} | Interval: ${s.meta.interval}`;
  document.getElementById("refresh").textContent = `${s.meta.refresh_seconds}`;

  updateRefresh(s.meta.refresh_seconds);

  const sig = s.signal;
  setBadge(document.getElementById("action"), sig.action);
  document.getElementById("confidence").textContent = `${sig.confidence}%`;
  document.getElementById("success").textContent = `${sig.success_chance}%`;
  document.getElementById("entry").textContent = sig.entry ?? "-";
  document.getElementById("sl").textContent = sig.stop_loss ?? "-";
  document.getElementById("tp").textContent = sig.take_profit ?? "-";
  document.getElementById("score").textContent = sig.score;
  document.getElementById("entry-eta").textContent = fmtHours(sig.expected_entry_hours);
  document.getElementById("tp-eta").textContent = fmtHours(sig.expected_tp_hours);
  document.getElementById("reason").textContent = sig.reason;

  const ind = s.indicators || {};
  document.getElementById("rsi").textContent = ind.rsi14?.toFixed?.(1) ?? "-";
  document.getElementById("ema20").textContent = ind.ema20?.toFixed?.(4) ?? "-";
  document.getElementById("ema50").textContent = ind.ema50?.toFixed?.(4) ?? "-";
  document.getElementById("macdh").textContent = ind.macd_hist?.toFixed?.(4) ?? "-";
  document.getElementById("atr").textContent = ind.atr14?.toFixed?.(4) ?? "-";

  const tv = s.tradingview_ta?.recommendation;
  document.getElementById("tv").textContent = tv
    ? `TradingView-TA: ${tv}`
    : "TradingView-TA: nicht verfuegbar (optional)";

  const candles = s.chart?.candles || [];
  if (candles.length > 0) {
    candleSeries.setData(candles);
    chart.timeScale().fitContent();
  }

  renderNews(s.news);
}

async function tick() {
  try {
    const s = await fetchState();
    renderState(s);
  } catch (e) {
    console.error(e);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  initChart();
  await tick();
  refreshTimer = setInterval(tick, refreshSeconds * 1000);
});
