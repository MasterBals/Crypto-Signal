const statusIndicator = document.getElementById("status-indicator");
const statusText = document.getElementById("status-text");
const lastRun = document.getElementById("last-run");
const refreshButton = document.getElementById("refresh");
const emptyState = document.getElementById("empty-state");
const table = document.getElementById("results-table");
const tableBody = table.querySelector("tbody");

const state = {
  loading: false,
};

const setStatus = (mode, message) => {
  statusIndicator.className = `indicator ${mode}`;
  statusText.textContent = message;
};

const setLoading = (loading) => {
  state.loading = loading;
  refreshButton.disabled = loading;
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return value;
};

const renderRows = (results) => {
  tableBody.innerHTML = "";
  const rows = [];

  Object.entries(results).forEach(([exchange, markets]) => {
    Object.entries(markets).forEach(([pair, payload]) => {
      const decision = payload.decision || {};
      rows.push({
        exchange,
        pair,
        signal: decision.signal || "neutral",
        confidence: decision.confidence || 0,
        timeframe: decision.timeframe || "n/a",
        scenario: decision.scenario || "n/a",
        zone: decision.zone || "n/a",
      });
    });
  });

  if (!rows.length) {
    emptyState.classList.remove("hidden");
    table.classList.add("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  table.classList.remove("hidden");

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${formatValue(row.exchange)}</td>
      <td>${formatValue(row.pair)}</td>
      <td>${formatValue(row.signal)}</td>
      <td>${formatValue(row.confidence)}</td>
      <td>${formatValue(row.timeframe)}</td>
      <td>${formatValue(row.scenario)}</td>
      <td>${formatValue(row.zone)}</td>
    `;
    tableBody.appendChild(tr);
  });
};

const fetchResults = async () => {
  try {
    setLoading(true);
    setStatus("idle", "Aktualisiere...");
    const response = await fetch("/api/results");
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const data = await response.json();
    if (!data.results) {
      setStatus("error", "Keine Ergebnisse vorhanden");
      renderRows({});
      return;
    }
    renderRows(data.results);
    lastRun.textContent = `Letzter Lauf: ${formatValue(data.last_run)}`;
    setStatus("ok", "Daten aktuell");
  } catch (error) {
    console.error(error);
    setStatus("error", "Backend nicht erreichbar");
  } finally {
    setLoading(false);
  }
};

refreshButton.addEventListener("click", fetchResults);

fetchResults();
setInterval(fetchResults, 30000);
