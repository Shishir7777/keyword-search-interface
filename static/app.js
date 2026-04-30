const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const resultsEl = document.querySelector("#results");
const statusEl = document.querySelector("#status");
const modeButtons = document.querySelectorAll(".mode-button");

let currentMode = "local";

function setMode(mode) {
  currentMode = mode;
  modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  queryInput.placeholder = mode === "local" ? "Search song lyrics" : "Search the web";
  if (queryInput.value.trim()) {
    runSearch();
  }
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderLocalResult(result) {
  return `
    <article class="result-item">
      <a class="result-title" href="/song/${result.id}">${escapeHtml(result.title)}</a>
      <div class="result-url">Rank ${escapeHtml(result.rank || "N/A")} · ${escapeHtml(result.year || "Unknown year")} · ${escapeHtml(result.artist || "Unknown artist")}</div>
      <p class="result-snippet">${result.snippet || ""}</p>
    </article>
  `;
}

function renderWebResult(result) {
  return `
    <article class="result-item">
      <a class="result-title" href="${escapeHtml(result.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(result.title)}</a>
      <div class="result-url">${escapeHtml(result.displayUrl || result.url)}</div>
      <p class="result-snippet">${escapeHtml(result.snippet || "")}</p>
    </article>
  `;
}

async function runSearch() {
  const query = queryInput.value.trim();
  resultsEl.innerHTML = "";

  if (!query) {
    statusEl.textContent = "Enter keywords to search.";
    return;
  }

  statusEl.textContent = "Searching...";
  const params = new URLSearchParams({ mode: currentMode, q: query, limit: "10" });

  try {
    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();

    if (data.error) {
      statusEl.textContent = data.error;
      return;
    }

    const results = data.results || [];
    statusEl.textContent = `${results.length} result${results.length === 1 ? "" : "s"} for "${query}"`;
    resultsEl.innerHTML = results
      .map((result) => currentMode === "local" ? renderLocalResult(result) : renderWebResult(result))
      .join("");
  } catch (error) {
    statusEl.textContent = `Search failed: ${error.message}`;
  }
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch();
});
