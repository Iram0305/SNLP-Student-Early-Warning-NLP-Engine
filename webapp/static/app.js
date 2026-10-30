/* Student Early-Warning Engine: local web app front end.
   Plain JavaScript, no libraries, so it works offline. */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const nice = (label) => String(label).replace(/_/g, " ");

const CAT_COLOURS = {
  "Academic difficulty": "#818cf8",
  "Financial difficulty": "#fbbf24",
  "Personal/Mental health": "#c084fc",
  "Harassment/Safety": "#f87171",
  "Administrative": "#60a5fa",
  "No_Concern": "#34d399",
};
const URG_COLOURS = { High: "#f87171", Medium: "#fbbf24", Low: "#60a5fa", No_Concern: "#34d399" };
const CATEGORIES = Object.keys(CAT_COLOURS);
const URGENCIES = Object.keys(URG_COLOURS);

const EXAMPLES = {
  "Financial pressure": "I have not been able to pay my tuition fees this semester and I am worried I will be removed from the rolls.",
  "Routine request": "Could you share the slides from today's Machine Learning lecture?",
  "Feeling overwhelmed": "I've been feeling extremely overwhelmed and hopeless lately and I don't know who to talk to.",
  "Safety concern": "A senior student has been repeatedly harassing me online and I do not feel safe on campus anymore.",
  "Falling behind": "I have missed the last three weeks of Statistics due to a family emergency and I am at risk of failing.",
  "Records request": "Could you tell me the process for requesting a bonafide certificate?",
  "Course review": "Great professor, the lectures were clear and the assignments were fair. I would take this course again.",
};

async function api(path, body) {
  const opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

function toast(msg, colour = "var(--accent)", ms = 3200) {
  const t = document.createElement("div");
  t.className = "toast";
  t.style.setProperty("--c", colour);
  t.innerHTML = msg;
  $("#toasts").appendChild(t);
  setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 300); }, ms);
}

function countUp(node, target, ms = 900, decimals = 0) {
  const start = performance.now();
  const step = (now) => {
    const p = Math.min(1, (now - start) / ms);
    const eased = 1 - Math.pow(1 - p, 3);
    node.textContent = (target * eased).toFixed(decimals);
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* Ripple on every button-like click */
document.addEventListener("pointerdown", (e) => {
  const b = e.target.closest(".btn, .icon-btn, .chip, .seg button");
  if (!b) return;
  const r = b.getBoundingClientRect();
  const size = Math.max(r.width, r.height);
  const s = document.createElement("span");
  s.className = "ripple";
  s.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - r.left - size / 2}px;top:${e.clientY - r.top - size / 2}px`;
  if (getComputedStyle(b).position === "static") b.style.position = "relative";
  b.style.overflow = "hidden";
  b.appendChild(s);
  setTimeout(() => s.remove(), 600);
});

/* ------------------------------------------------------------------ theme */
const root = document.documentElement;
try { const saved = localStorage.getItem("ews-theme"); if (saved) root.dataset.theme = saved; } catch (_) {}
$("#themeBtn").addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
  try { localStorage.setItem("ews-theme", root.dataset.theme); } catch (_) {}
});

/* ------------------------------------------------------------------- tabs */
const loaded = {};
function moveInk() {
  const active = $(".tab.active");
  const ink = $("#tabInk");
  ink.style.width = active.offsetWidth + "px";
  ink.style.transform = `translateX(${active.offsetLeft}px)`;
}
async function showTab(name) {
  const btn = $(`.tab[data-tab="${name}"]`);
  if (!btn) return;
  const current = $(".panel.active");
  const next = $(`#tab-${name}`);
  $$(".tab").forEach((t) => t.classList.toggle("active", t === btn));
  moveInk();
  if (current !== next) {
    if (current) {
      current.classList.add("leaving");
      current.classList.remove("active");
      await sleep(200);
      current.classList.remove("leaving");
    }
    next.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  history.replaceState(null, "", "#" + name);
  if (!loaded[name] && LOADERS[name]) { loaded[name] = true; LOADERS[name](); }
}
$$(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
window.addEventListener("resize", moveInk);

/* ------------------------------------------------------------ model status */
let modelReady = false;
async function pollStatus() {
  const pill = $("#statusPill");
  try {
    const s = await api("/api/status");
    if (s.error) {
      pill.className = "status-pill error";
      $("#statusText").textContent = "Model error";
      pill.title = s.error;
      return;
    }
    if (s.ready) {
      if (!modelReady) toast(`Model ready <span class="muted">(loaded in ${s.loaded_in}s)</span>`, "var(--ok)");
      modelReady = true;
      pill.className = "status-pill ready";
      $("#statusText").textContent = "Model ready";
      pill.title = s.model;
      setTimeout(pollStatus, 15000);
      return;
    }
    pill.className = "status-pill loading";
    $("#statusText").textContent = "Loading model…";
    setTimeout(pollStatus, 1500);
  } catch (_) {
    pill.className = "status-pill offline";
    $("#statusText").textContent = "Server offline";
    modelReady = false;
    setTimeout(pollStatus, 5000);
  }
}

function setLoading(btn, on) {
  btn.classList.toggle("loading", on);
  btn.disabled = on;
}

/* ============================================================== ANALYSE */
const msgInput = $("#msgInput");
const chips = $("#exampleChips");
Object.entries(EXAMPLES).forEach(([label, text]) => {
  const c = document.createElement("button");
  c.className = "chip";
  c.textContent = label;
  c.addEventListener("click", () => {
    $$(".chip", chips).forEach((x) => x.classList.remove("picked"));
    c.classList.add("picked");
    typeInto(msgInput, text);
  });
  chips.appendChild(c);
});

let typing = 0;
async function typeInto(area, text) {
  const id = ++typing;
  area.value = "";
  for (let i = 0; i < text.length; i += 3) {
    if (id !== typing) return;
    area.value = text.slice(0, i + 3);
    updateCount();
    await sleep(6);
  }
  area.value = text;
  updateCount();
}
function updateCount() { $("#charCount").textContent = `${msgInput.value.length} characters`; }
msgInput.addEventListener("input", () => { typing++; updateCount(); $$(".chip", chips).forEach((x) => x.classList.remove("picked")); });
msgInput.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.ctrlKey) runAnalyse(); });
$("#clearBtn").addEventListener("click", () => {
  typing++;
  msgInput.value = "";
  updateCount();
  resetTrace();
  const area = $("#resultArea");
  area.style.transition = "opacity .3s";
  area.style.opacity = 0;
  setTimeout(() => { area.innerHTML = ""; area.style.opacity = 1; }, 300);
});
$("#analyseBtn").addEventListener("click", runAnalyse);

function resetTrace() { $$("#trace li").forEach((li) => li.classList.remove("active", "done")); }
async function stepTrace(i) {
  const items = $$("#trace li");
  if (i > 0) { items[i - 1].classList.remove("active"); items[i - 1].classList.add("done"); }
  if (items[i]) items[i].classList.add("active");
}

async function runAnalyse() {
  const text = msgInput.value.trim();
  if (!text) { toast("Type or pick a message first.", "var(--warn)"); msgInput.focus(); return; }
  if (!modelReady) { toast("The model is still loading. Give it a few seconds.", "var(--warn)"); return; }
  const btn = $("#analyseBtn");
  setLoading(btn, true);
  resetTrace();

  // Animate the trace while the request runs; the final steps finish once the answer arrives.
  const request = api("/api/analyze", { text });
  let failed = false;
  request.catch(() => { failed = true; });
  for (let i = 0; i < 4 && !failed; i++) { await stepTrace(i); await sleep(260); }
  try {
    const r = await request;
    await stepTrace(4); await sleep(220);
    await stepTrace(5); await sleep(200);
    $$("#trace li")[5].classList.replace("active", "done");
    renderResult(r);
  } catch (err) {
    resetTrace();
    toast(esc(err.message), "var(--bad)", 5000);
  } finally {
    setLoading(btn, false);
  }
}

function confWords(s) {
  if (s >= 0.85) return "High confidence";
  if (s >= 0.65) return "Moderate confidence";
  if (s >= 0.5) return "Low confidence";
  return "Very low confidence";
}

function metricCard(label, value, score, colour) {
  return `
    <div class="card res-card" style="--c:${colour}">
      <div class="label">${label}</div>
      <div class="value">${esc(nice(value))}</div>
      <div class="meter"><span data-w="${Math.round(score * 100)}"></span></div>
      <div class="meter-row"><span>${confWords(score)}</span><b class="cnt" data-v="${score}">0.00</b></div>
    </div>`;
}

function highlightJson(obj) {
  return esc(JSON.stringify(obj, null, 2))
    .replace(/(&quot;[^&]*?&quot;)(\s*:)/g, '<span class="j-key">$1</span>$2')
    .replace(/:\s(&quot;.*?&quot;)/g, ': <span class="j-str">$1</span>')
    .replace(/:\s(-?\d+(?:\.\d+)?)/g, ': <span class="j-num">$1</span>')
    .replace(/:\s(true|false|null)/g, ': <span class="j-bool">$1</span>');
}

function renderResult(r) {
  const contract = {
    input_id: r.input_id, category: r.category, category_confidence: r.category_confidence,
    urgency: r.urgency, urgency_confidence: r.urgency_confidence, recommended_action: r.recommended_action,
  };
  const area = $("#resultArea");
  area.innerHTML = `
    <div class="result-grid">
      ${metricCard("Concern type", r.category, r.category_confidence, CAT_COLOURS[r.category] || "var(--accent)")}
      ${metricCard("Urgency", r.urgency, r.urgency_confidence, URG_COLOURS[r.urgency] || "var(--accent)")}
      <div class="card res-card wide" style="--c:var(--accent-2)">
        <div class="label">Recommended next step</div>
        <div class="action-title">${esc(r.recommended_action)}</div>
        <div class="muted">${esc(r.guidance)}</div>
        <div class="timing"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>${esc(r.timing)}</div>
        ${r.needs_review ? `<div class="caution"><b>Read this one manually.</b> The model is not confident about this message (a confidence below 0.5), which usually means the wording is ambiguous or unlike anything in the training data. Treat the result as a weak signal only.</div>` : ""}
      </div>
      <div class="card res-card wide json" style="--c:var(--accent-3)">
        <details class="json">
          <summary>Structured output (what another system receives) <span class="muted small">· ${r.elapsed_ms} ms</span></summary>
          <pre class="json-out">${highlightJson(contract)}</pre>
        </details>
      </div>
    </div>`;
  requestAnimationFrame(() => {
    $$(".meter span", area).forEach((s) => (s.style.width = s.dataset.w + "%"));
    $$(".cnt", area).forEach((n) => setTimeout(() => countUp(n, +n.dataset.v, 1000, 2), 250));
  });
  setTimeout(() => area.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
}

/* ================================================================ BATCH */
let batchFormat = "auto";
let batchData = null;
let batchFilter = "all";

$$("#formatSeg button").forEach((b) => b.addEventListener("click", () => {
  $$("#formatSeg button").forEach((x) => x.classList.toggle("active", x === b));
  batchFormat = b.dataset.fmt;
}));
$$("#filterSeg button").forEach((b) => b.addEventListener("click", () => {
  $$("#filterSeg button").forEach((x) => x.classList.toggle("active", x === b));
  batchFilter = b.dataset.filter;
  renderTable();
}));

$("#sampleBtn").addEventListener("click", async () => {
  const btn = $("#sampleBtn");
  setLoading(btn, true);
  try {
    const data = await api("/api/sample-batch");
    $("#batchInput").value = JSON.stringify(data, null, 2);
    toast(`Loaded ${data.items.length} Group 5 feedback comments.`);
  } catch (err) { toast(esc(err.message), "var(--bad)"); }
  setLoading(btn, false);
});

$("#fileInput").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  $("#batchInput").value = await file.text();
  toast(`Loaded <b>${esc(file.name)}</b>`);
  e.target.value = "";
});

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); rows.push(row); row = []; cell = "";
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some((x) => x.trim()));
}

function parseBatch(raw) {
  const text = raw.trim();
  let fmt = batchFormat;
  if (fmt === "auto") {
    if (text.startsWith("{") || text.startsWith("[")) fmt = "json";
    else if (/^[^\n]*\btext\b[^\n]*,|,[^\n]*\btext\b/i.test(text.split("\n")[0])) fmt = "csv";
    else fmt = "lines";
  }
  if (fmt === "json") {
    let data = JSON.parse(text);
    if (!Array.isArray(data)) data = data.items || data.feedback || data.results || [];
    return data.map((d, i) => (typeof d === "string" ? { id: `ITEM${String(i + 1).padStart(3, "0")}`, text: d } : { id: d.id ?? d.feedback_id ?? null, text: d.text ?? d.feedback ?? d.comment ?? "" }));
  }
  if (fmt === "csv") {
    const [head, ...rows] = parseCsv(text);
    const cols = head.map((h) => h.trim().toLowerCase());
    const ti = ["text", "feedback", "comment"].map((c) => cols.indexOf(c)).find((i) => i >= 0);
    const ii = ["id", "feedback_id"].map((c) => cols.indexOf(c)).find((i) => i >= 0);
    if (ti === undefined) throw new Error('CSV needs a "text", "feedback" or "comment" column.');
    return rows.map((r) => ({ id: ii === undefined ? null : r[ii], text: r[ti] || "" }));
  }
  return text.split(/\r?\n/).filter((l) => l.trim()).map((l) => ({ id: null, text: l.trim() }));
}

$("#batchBtn").addEventListener("click", async () => {
  let items;
  try { items = parseBatch($("#batchInput").value).filter((i) => i.text.trim()); }
  catch (err) { toast("Could not read the input: " + esc(err.message), "var(--bad)", 5000); return; }
  if (!items.length) { toast("Add some messages first, or load the Group 5 sample.", "var(--warn)"); return; }
  if (!modelReady) { toast("The model is still loading. Give it a few seconds.", "var(--warn)"); return; }
  const btn = $("#batchBtn");
  setLoading(btn, true);
  $("#batchProgress").classList.add("run");
  try {
    batchData = await api("/api/batch", { items });
    renderDashboard();
    toast(`Analysed <b>${batchData.summary.total}</b> messages.`, "var(--ok)");
  } catch (err) { toast(esc(err.message), "var(--bad)", 5000); }
  $("#batchProgress").classList.remove("run");
  setLoading(btn, false);
});

function renderDashboard() {
  const d = batchData;
  const dash = $("#dashboard");
  dash.classList.remove("hidden");
  dash.style.animation = "none"; void dash.offsetWidth; dash.style.animation = "";

  const tiles = [
    ["Messages analysed", d.summary.total, "var(--accent)"],
    ["Support signals", d.summary.support_signals, "var(--ok)"],
    ["High urgency signals", d.summary.high_urgency, "var(--bad)"],
    ["Low confidence (<0.5)", d.summary.low_confidence, "var(--warn)"],
  ];
  $("#tiles").innerHTML = tiles.map(([l, v, c]) => `<div class="tile" style="--c:${c}"><div class="glow"></div><div class="label">${l}</div><div class="num" data-v="${v}">0</div></div>`).join("");
  $$("#tiles .num").forEach((n) => countUp(n, +n.dataset.v, 900));

  const max = Math.max(1, ...Object.values(d.category_counts));
  $("#catBars").innerHTML = CATEGORIES.map((c) => {
    const v = d.category_counts[c] || 0;
    return `<div class="bar-row" style="--c:${CAT_COLOURS[c]}"><span>${nice(c)}</span><div class="bar-track"><span data-w="${(v / max) * 100}"></span></div><b>${v}</b></div>`;
  }).join("");

  const total = Math.max(1, d.summary.total);
  const R = 70, C = 2 * Math.PI * R;
  let offset = 0;
  const arcs = URGENCIES.map((u) => {
    const v = d.urgency_counts[u] || 0;
    const len = (v / total) * C;
    const arc = `<circle r="${R}" cx="90" cy="90" stroke="${URG_COLOURS[u]}" stroke-dasharray="0 ${C}" data-len="${len}" stroke-dashoffset="${-offset}"></circle>`;
    offset += len;
    return arc;
  }).join("");
  $("#urgDonut").innerHTML = `<svg viewBox="0 0 180 180"><circle r="${R}" cx="90" cy="90" stroke="var(--surface-2)"></circle>${arcs}</svg>
    <div class="legend">${URGENCIES.map((u) => `<div><span style="--c:${URG_COLOURS[u]}"></span>${nice(u)}: <b>${d.urgency_counts[u] || 0}</b></div>`).join("")}</div>`;

  requestAnimationFrame(() => setTimeout(() => {
    $$("#catBars .bar-track span").forEach((s) => (s.style.width = s.dataset.w + "%"));
    $$("#urgDonut circle[data-len]").forEach((c) => c.setAttribute("stroke-dasharray", `${c.dataset.len} ${C}`));
  }, 60));

  renderTable();
  setTimeout(() => dash.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
}

function renderTable() {
  if (!batchData) return;
  let rows = batchData.results;
  if (batchFilter === "flagged") rows = rows.filter((r) => r.support_signal);
  if (batchFilter === "review") rows = rows.filter((r) => Math.min(r.category_confidence, r.urgency_confidence) < 0.5);
  const conf = (v) => `<span class="conf ${v < 0.5 ? "low" : ""}">${v.toFixed(2)}</span>`;
  $("#resultsTable").innerHTML = `
    <thead><tr><th>ID</th><th>Message</th><th>Category</th><th>Conf.</th><th>Urgency</th><th>Conf.</th><th>Signal</th></tr></thead>
    <tbody>${rows.map((r, i) => `
      <tr style="animation-delay:${Math.min(i * 25, 600)}ms">
        <td><code>${esc(r.input_id)}</code></td>
        <td class="txt">${esc(r.text)}</td>
        <td><span class="badge" style="--c:${CAT_COLOURS[r.category]}">${esc(nice(r.category))}</span></td>
        <td>${conf(r.category_confidence)}</td>
        <td><span class="badge" style="--c:${URG_COLOURS[r.urgency]}">${esc(nice(r.urgency))}</span></td>
        <td>${conf(r.urgency_confidence)}</td>
        <td>${r.support_signal ? '<span class="flag">● yes</span>' : '<span class="muted">-</span>'}</td>
      </tr>`).join("") || '<tr><td colspan="7" class="muted">Nothing matches this filter.</td></tr>'}
    </tbody>`;
}

function download(name, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const FIELDS = ["input_id", "text", "category", "category_confidence", "urgency", "urgency_confidence", "recommended_action", "support_signal"];
$("#dlCsv").addEventListener("click", () => {
  if (!batchData) return;
  const q = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const csv = [FIELDS.join(","), ...batchData.results.map((r) => FIELDS.map((f) => q(r[f])).join(","))].join("\n");
  download("triage results.csv", csv, "text/csv");
  toast("Downloaded CSV");
});
$("#dlJson").addEventListener("click", () => {
  if (!batchData) return;
  const out = { model_version: "mpnet-week4", advisory_only: true, summary: batchData.summary, results: batchData.results };
  download("triage results.json", JSON.stringify(out, null, 2), "application/json");
  toast("Downloaded JSON");
});

/* ============================================================= PIPELINE */
const ICONS = {
  data: '<path d="M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  split: '<path d="M16 3h5v5M8 3H3v5M21 3l-7 7M3 3l7 7M12 22v-8"/>',
  plus: '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
  vec: '<path d="M4 20L20 4M20 4h-6M20 4v6"/><circle cx="6" cy="18" r="2"/>',
  brain: '<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 3 3h0V3z"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-3 3h0V3z"/>',
  chart: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
  api: '<path d="M8 9l-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/>',
  people: '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M15 14.5c3 0 6 2 6 5"/>',
};

const STAGES = [
  { n: "01", t: "Synthetic data", s: "Templates + slot filling", ic: "data", c: "#818cf8",
    d: "No real student messages exist that we could legally use, so the dataset is generated from hand-written templates for every category × urgency pair, with slots such as course names filled at random.",
    pts: ["6 categories × 4 urgency levels", "Fixed random seed for reproducibility", "Each row: id, text, category, urgency, recommended_action"],
    files: ["src/preprocessing/generate_dataset.py"] },
  { n: "02", t: "Clean & split", s: "70 / 15 / 15 stratified", ic: "split", c: "#a78bfa",
    d: "Whitespace is normalised and duplicates dropped. The data is then split into train, validation and test sets, stratified on category so each split has the same mix.",
    pts: ["Validation set is used for model choices", "Test set is used once for final scores", "random_state=42 everywhere"],
    files: ["src/preprocessing/preprocess.py"] },
  { n: "03", t: "Review-style examples", s: "Week 7 data fix", ic: "plus", c: "#c084fc",
    d: "Group 5's real course reviews were over-flagged (32 of 38) as concerns, because the model had never seen an ordinary course review. We added 40 review-style No_Concern examples and retrained. Afterwards only 3 of 38 were support signals.",
    pts: ["28 train / 6 val / 6 test added", "Splits are now 187 / 40 / 41", "Error-driven data improvement"],
    files: ["src/preprocessing/add_review_examples.py"] },
  { n: "04", t: "Sentence embeddings", s: "MiniLM → MPNet", ic: "vec", c: "#22d3ee",
    d: "Each message becomes a dense vector that captures meaning. Week 3 used all-MiniLM-L6-v2 (384 numbers). Week 4 moved to all-mpnet-base-v2 (768 numbers), a stronger encoder. Vectors are cached to disk so training is fast.",
    pts: ["Pre-trained transformer, no fine-tuning", "Similar meaning → nearby vectors", "Cached in src/models/embeddings_v2/"],
    files: ["src/models/embed.py", "src/models/embed_v2.py"] },
  { n: "05", t: "Classifier selection", s: "LogReg vs linear SVM", ic: "brain", c: "#60a5fa",
    d: "Two separate classifiers are trained on the embeddings: one for category, one for urgency. For each, Logistic Regression and a linear SVM are compared on the validation set by macro F1 and the better one is saved.",
    pts: ["class_weight='balanced' for uneven classes", "Macro F1 so every class counts equally", "Saved as week4_category / week4_urgency .joblib"],
    files: ["src/models/baseline.py", "src/models/improved_model.py", "src/models/improved_model_v2.py"] },
  { n: "06", t: "Evaluation", s: "Reports + error analysis", ic: "chart", c: "#34d399",
    d: "Every model is scored on the same test set with precision, recall and F1, plus a confusion matrix. Error analysis lists every mistake and checks that the model is less confident when it is wrong, which justifies the 0.5 human-review threshold.",
    pts: ["Baseline vs Week 3 vs Week 4 comparison", "Urgency errors are between adjacent levels", "Confidence on correct ≫ confidence on wrong"],
    files: ["src/evaluation/compare_all_models.py", "src/evaluation/error_analysis.py"] },
  { n: "07", t: "Reusable asset", s: "analyze_message() + API", ic: "api", c: "#fbbf24",
    d: "Everything is wrapped behind one function, analyze_message(text), which returns a fixed JSON contract. A FastAPI service exposes it over HTTP so any team can call it, and this web app uses it too.",
    pts: ["Input: text (+ optional id)", "Output: category, urgency, confidences, action", "REST endpoints for single and batch use"],
    files: ["src/models/pipeline_v2.py", "src/api/app.py", "webapp/server.py"] },
  { n: "08", t: "Integration & review", s: "Group 5 → dashboard → human", ic: "people", c: "#f87171",
    d: "Group 5 sends course feedback as JSON. We triage it, apply the support-signal rule (a concern with category confidence ≥ 0.5) and send a reply file back. The dashboard shows emerging concern categories. A human always makes the final decision.",
    pts: ["File handoff: group5 feedback input.json → group5 triage output.json", "advisory_only: true in every reply", "Low-confidence items routed to manual reading"],
    files: ["src/api/integration.py", "demo/run_group5.py"] },
];

function renderPipeline() {
  $("#flow").innerHTML = STAGES.map((s, i) => `
    <div class="stage" data-i="${i}" style="--c:${s.c}; animation-delay:${i * 70}ms">
      <div class="ic"><svg viewBox="0 0 24 24">${ICONS[s.ic]}</svg></div>
      <div class="n">STAGE ${s.n}</div>
      <div class="ttl">${s.t}</div>
      <div class="sub">${s.s}</div>
      <div class="flowdot" style="animation-delay:${i * 0.3}s"></div>
    </div>`).join("");
  $$(".stage").forEach((el) => el.addEventListener("click", () => selectStage(+el.dataset.i)));
  selectStage(0);
}

function selectStage(i) {
  const s = STAGES[i];
  $$(".stage").forEach((el) => el.classList.toggle("active", +el.dataset.i === i));
  $("#stageDetail").style.setProperty("--c", s.c);
  $("#stageDetail").innerHTML = `
    <div class="swap">
      <div class="label" style="color:${s.c}">Stage ${s.n}</div>
      <h3 style="font-size:1.2rem;margin-top:4px">${s.t}</h3>
      <p class="muted">${s.d}</p>
      <ul>${s.pts.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>
      <div class="files">${s.files.map((f) => `<button data-file="${f}">${f} ↗</button>`).join("")}</div>
    </div>`;
  $$("#stageDetail [data-file]").forEach((b) => b.addEventListener("click", () => openCode(b.dataset.file)));
}

function reportTable(rows) {
  if (!rows.length) return '<div class="muted small">Report not found in results/.</div>';
  const [, ...body] = rows;
  return `<table class="rep"><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>
    ${body.map((r) => {
      const isAcc = r[0] === "accuracy";
      const sum = isAcc || r[0].includes("avg");
      if (isAcc) return `<tr class="sum"><td>accuracy</td><td></td><td></td><td>${(+r[3]).toFixed(3)}</td><td></td></tr>`;
      return `<tr class="${sum ? "sum" : ""}"><td>${esc(nice(r[0]))}</td>${[1, 2, 3].map((k) => `<td class="cell-bar" style="--v:${+r[k]}">${(+r[k]).toFixed(3)}</td>`).join("")}<td>${Math.round(+r[4])}</td></tr>`;
    }).join("")}</tbody></table>`;
}

function comparisonChart(rows, title) {
  if (!rows.length) return "";
  const [, ...body] = rows;
  const cols = [["Baseline", 1, "#94a3b8"], ["Week 3", 2, "#22d3ee"], ["Week 4", 3, "#818cf8"]];
  const data = body.filter((r) => r[0] !== "weighted avg");
  return `<div><h3 style="font-size:.95rem">${title}</h3>
    <div class="cmp-legend">${cols.map(([n, , c]) => `<span style="--c:${c}">${n}</span>`).join("")}</div>
    <div class="cmp-chart">${data.map((r) => `
      <div class="cmp-row"><div class="nm"><span>${esc(nice(r[0]))}</span><span>${cols.map(([, k]) => (+r[k]).toFixed(2)).join(" · ")}</span></div>
        <div class="trio">${cols.map(([, k, c]) => `<i style="background:${c}" data-w="${+r[k] * 100}"></i>`).join("")}</div></div>`).join("")}
    </div></div>`;
}

const macro = (rows, col) => { const r = rows.find((x) => x[0] === "macro avg"); return r ? (+r[col]).toFixed(3) : "-"; };

async function loadPipeline() {
  renderPipeline();
  try {
    const [res, ds] = await Promise.all([api("/api/results"), api("/api/dataset")]);

    const tl = [
      { wk: "Week 2", t: "TF-IDF + Logistic Regression", d: "Bag-of-words baseline. Fast and explainable, but only matches exact words.", c: "#94a3b8", cat: macro(res.category, 1), urg: macro(res.urgency, 1), note: "35-row test" },
      { wk: "Week 3", t: "MiniLM embeddings + LogReg", d: "384-d sentence embeddings capture meaning, not just words. Used by the hosted Streamlit demo.", c: "#22d3ee", cat: macro(res.category, 2), urg: macro(res.urgency, 2), note: "35-row test" },
      { wk: "Week 4", t: "MPNet embeddings + selected classifier", d: "768-d embeddings, classifier picked on validation, retrained in Week 7 with review-style examples. Used by this app.", c: "#818cf8", cat: macro(res.week4_category_report, 3), urg: macro(res.week4_urgency_report, 3), note: "41-row test, current", current: true },
    ];
    $("#timeline").innerHTML = tl.map((x) => `
      <div class="tl-item ${x.current ? "current" : ""}" style="--c:${x.c}">
        <span class="wk">${x.wk}</span>
        <h3>${x.t}</h3>
        <p class="muted small">${x.d}</p>
        <div class="kv"><span>Category macro F1</span><b>${x.cat}</b></div>
        <div class="kv"><span>Urgency macro F1</span><b>${x.urg}</b></div>
        <div class="kv"><span class="muted">Evaluated on</span><span class="muted">${x.note}</span></div>
      </div>`).join("");

    const labels = { train: "Training", val: "Validation", test: "Test" };
    $("#datasetCards").innerHTML = Object.entries(ds).map(([k, v], i) => {
      const max = Math.max(...Object.values(v.categories));
      return `<div class="card ds-card reveal" style="animation-delay:${i * 80}ms">
        <div class="label">${labels[k]} split</div>
        <div class="big" data-v="${v.rows}">0</div>
        <div class="muted small">messages</div>
        <div class="mini-bars">${CATEGORIES.map((c) => `<div><span>${nice(c)}</span><i style="--c:${CAT_COLOURS[c]}" data-w="${((v.categories[c] || 0) / max) * 100}"></i><b>${v.categories[c] || 0}</b></div>`).join("")}</div>
      </div>`;
    }).join("");
    $$("#datasetCards .big").forEach((n) => countUp(n, +n.dataset.v));

    $("#repCat").innerHTML = reportTable(res.week4_category_report);
    $("#repUrg").innerHTML = reportTable(res.week4_urgency_report);
    $("#comparison").innerHTML = comparisonChart(res.category, "Category") + comparisonChart(res.urgency, "Urgency");

    setTimeout(() => $$("#tab-pipeline [data-w]").forEach((s) => (s.style.width = s.dataset.w + "%")), 120);
  } catch (err) {
    toast("Could not load results: " + esc(err.message), "var(--bad)");
  }
}

/* ================================================================ STACK */
const STACK = [
  { cat: "Language & runtime", c: "#818cf8", items: [
    ["Python", "3.10+", "Everything from data generation to the server is written in Python."],
    ["Windows batch files", ".bat", "start_app.bat and stop_app.bat start and stop this app with a double-click."],
  ] },
  { cat: "NLP models", c: "#22d3ee", items: [
    ["sentence-transformers", "all-mpnet-base-v2", "Primary encoder: turns a message into a 768-d meaning vector."],
    ["sentence-transformers", "all-MiniLM-L6-v2", "Lighter 384-d encoder from Week 3, used by the hosted demo to fit in 1 GB RAM."],
    ["PyTorch (CPU)", "torch", "Runs the transformer encoders. CPU-only build keeps the install small."],
  ] },
  { cat: "Machine learning", c: "#c084fc", items: [
    ["scikit-learn", "TfidfVectorizer", "Week 2 baseline features (word and word-pair weights)."],
    ["scikit-learn", "LogisticRegression · SVC", "Classifiers for category and urgency, picked on validation macro F1."],
    ["scikit-learn", "metrics", "classification_report, confusion_matrix and f1_score for evaluation."],
    ["joblib", ".joblib", "Saves trained classifiers to src/models/saved/ so they load instantly."],
  ] },
  { cat: "Data handling", c: "#34d399", items: [
    ["pandas", "DataFrame", "Reads and writes the CSV splits and result tables."],
    ["NumPy", ".npy", "Stores cached embedding matrices."],
    ["CSV & JSON", "files", "Dataset splits, results and the Group 5 handoff format {items:[{id,text}]}."],
  ] },
  { cat: "Serving & API", c: "#fbbf24", items: [
    ["FastAPI", "src/api/app.py", "REST API so other groups can call the engine over HTTP."],
    ["Uvicorn", "ASGI server", "Runs the FastAPI apps, including this local web app on 127.0.0.1:8765."],
    ["Pydantic", "schemas", "Validates request bodies such as {text} and {items:[...]}."],
  ] },
  { cat: "Interfaces", c: "#f87171", items: [
    ["HTML · CSS · JavaScript", "this app", "Hand-written, no frameworks or CDNs, so it works offline. Charts are plain SVG/CSS."],
    ["Streamlit + Altair", "hosted demo", "The public demo on Streamlit Community Cloud."],
    ["Git & GitHub", "version control", "Weekly history of the project and the public repository."],
  ] },
];

const ARCH = [
  ["Browser UI", "webapp/static", "#f87171"],
  ["FastAPI server", "webapp/server.py", "#fbbf24"],
  ["analyze_message()", "pipeline_v2.py", "#c084fc"],
  ["MPNet encoder", "768-d vector", "#22d3ee"],
  ["Week 4 classifiers", "category + urgency", "#818cf8"],
  ["JSON result", "+ action lookup", "#34d399"],
];

function loadStack() {
  $("#arch").innerHTML = `<div class="label" style="margin-bottom:12px">Request flow in this app</div>
    <div class="arch-row">${ARCH.map(([b, s, c], i) => `${i ? '<div class="arch-arrow">→</div>' : ""}<div class="arch-box" style="--c:${c};animation-delay:${i * 90}ms"><b>${b}</b><small>${s}</small></div>`).join("")}</div>`;
  $("#stackGrid").innerHTML = STACK.map((g, i) => `
    <div class="card stack-card" style="--c:${g.c};animation-delay:${i * 80}ms">
      <div class="cat">${g.cat}</div>
      ${g.items.map(([n, tag, d]) => `<div class="stack-item"><b>${n} <em>${tag}</em></b><p>${d}</p></div>`).join("")}
    </div>`).join("");
}

/* ================================================================= CODE */
const KW = new Set("False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(" "));
const BI = new Set("print len range open str int float dict list set tuple enumerate zip sorted min max sum isinstance super Path self round next".split(" "));
const TOKEN = /(#[^\n]*)|("""[\s\S]*?"""|'''[\s\S]*?'''|[rbfuRBFU]{0,2}"(?:\\.|[^"\\\n])*"|[rbfuRBFU]{0,2}'(?:\\.|[^'\\\n])*')|(^[ \t]*@[\w.]+)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/gm;

function highlightPython(src) {
  const tokens = [];
  let last = 0, m;
  while ((m = TOKEN.exec(src))) {
    if (m.index > last) tokens.push(["", src.slice(last, m.index)]);
    let cls = "";
    if (m[1]) cls = "tok-com";
    else if (m[2]) cls = "tok-str";
    else if (m[3]) cls = "tok-dec";
    else if (m[4]) cls = "tok-num";
    else if (m[5]) {
      const w = m[5];
      if (KW.has(w)) cls = "tok-kw";
      else if (BI.has(w)) cls = "tok-bi";
      else if (/^\s*\(/.test(src.slice(TOKEN.lastIndex, TOKEN.lastIndex + 3))) cls = "tok-fn";
    }
    tokens.push([cls, m[0]]);
    last = TOKEN.lastIndex;
  }
  tokens.push(["", src.slice(last)]);
  // Split into lines, closing and reopening spans that cross a line break.
  const lines = [""];
  for (const [cls, text] of tokens) {
    text.split("\n").forEach((piece, i) => {
      if (i > 0) lines.push("");
      if (piece) lines[lines.length - 1] += cls ? `<span class="${cls}">${esc(piece)}</span>` : esc(piece);
    });
  }
  return lines;
}

let codeFiles = [];
let currentNotes = [];

async function loadCode() {
  try {
    codeFiles = await api("/api/code");
    const groups = {};
    codeFiles.forEach((f) => (groups[f.group] ||= []).push(f));
    $("#fileTree").innerHTML = Object.entries(groups).map(([g, files]) => `
      <div class="ft-group">${esc(g)}</div>
      ${files.map((f) => `<button class="ft-file" data-path="${esc(f.path)}">${esc(f.title)}<small>${esc(f.path)}</small></button>`).join("")}`).join("");
    $$(".ft-file").forEach((b) => b.addEventListener("click", () => openCode(b.dataset.path)));
    if (!$(".ft-file.active")) openCode(pendingCode || "src/models/pipeline_v2.py");
  } catch (err) {
    toast("Could not load code list: " + esc(err.message), "var(--bad)");
  }
}

let pendingCode = null;
async function openCode(path) {
  if (!loaded.code) { pendingCode = path; await showTab("code"); return; }
  if ($(".panel.active")?.id !== "tab-code") await showTab("code");
  $$(".ft-file").forEach((b) => b.classList.toggle("active", b.dataset.path === path));
  try {
    const f = await api("/api/code/file?path=" + encodeURIComponent(path));
    currentNotes = f.annotations;
    $("#codeHead").innerHTML = `<div class="path">${esc(f.path)}</div><h2>${esc(f.title)}</h2><p>${esc(f.summary)}</p>`;
    const view = $("#codeView");
    view.classList.remove("swap"); void view.offsetWidth; view.classList.add("swap");
    view.innerHTML = `<pre>${highlightPython(f.source).map((l, i) => `<span class="ln" data-ln="${i + 1}">${l || " "}</span>`).join("")}</pre>`;
    view.scrollTop = 0;
    $("#codeNotes").innerHTML = f.annotations.map((a, i) => `
      <div class="note" data-i="${i}" style="animation-delay:${i * 60}ms">
        <div class="lines">lines ${a.start}–${a.end}</div><b>${esc(a.title)}</b><p>${esc(a.text)}</p>
      </div>`).join("") || '<div class="muted small">No notes for this file.</div>';
    $$(".note").forEach((n) => n.addEventListener("click", () => focusNote(+n.dataset.i, true)));
    $$(".ln", view).forEach((ln) => ln.addEventListener("click", () => {
      const line = +ln.dataset.ln;
      const i = currentNotes.findIndex((a) => line >= a.start && line <= a.end);
      if (i >= 0) focusNote(i, false);
    }));
  } catch (err) {
    toast(esc(err.message), "var(--bad)");
  }
}

function focusNote(i, scrollCode) {
  const a = currentNotes[i];
  $$(".note").forEach((n) => n.classList.toggle("active", +n.dataset.i === i));
  $$("#codeView .ln").forEach((ln) => {
    const l = +ln.dataset.ln;
    ln.classList.toggle("hl", l >= a.start && l <= a.end);
  });
  const view = $("#codeView");
  if (scrollCode) {
    const first = $(`#codeView .ln[data-ln="${a.start}"]`);
    view.scrollTo({ top: first.offsetTop - 40, behavior: "smooth" });
  } else {
    $(`.note[data-i="${i}"]`).scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

/* ============================================================= SHUTDOWN */
const modal = $("#modal");
$("#shutdownBtn").addEventListener("click", () => modal.classList.add("open"));
$("#cancelShutdown").addEventListener("click", () => modal.classList.remove("open"));
modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("open"); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") modal.classList.remove("open"); });

$("#confirmShutdown").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  setLoading(btn, true);
  try { await api("/api/shutdown", {}); } catch (_) { /* server may close before replying */ }
  modal.classList.remove("open");
  const r = $("#shutdownBtn").getBoundingClientRect();
  const g = $("#goodbye");
  g.style.setProperty("--x", `${r.left + r.width / 2}px`);
  g.style.setProperty("--y", `${r.top + r.height / 2}px`);
  g.classList.add("on");
  $("#statusPill").className = "status-pill offline";
  $("#statusText").textContent = "Server stopped";
});

/* ================================================================= boot */
const LOADERS = { pipeline: loadPipeline, stack: loadStack, code: loadCode };
updateCount();
pollStatus();
const startTab = location.hash.slice(1);
showTab($(`.tab[data-tab="${startTab}"]`) ? startTab : "analyse");
requestAnimationFrame(moveInk);
