/* VLF Noise Scout — istasyon arayüzü
   - 17 dil desteği (web/locales/<kod>.json — .po/.mo kaynaklarından derlenir)
   - Açık / karanlık tema (localStorage + sistem tercihi)
   - Ham/Temiz geçişi kesintisiz (iki akış paralel çalışır, biri sessize alınır)
   - Olay modlu waterfall (bin başına öğrenen taban çıkarma)
   - Son 60 saniyenin ses + görüntü kaydı
   - Bilinen VLF vericileri tablosu (/api/transmitters)
*/

"use strict";

const BACKEND = (window.VLF_CONFIG && window.VLF_CONFIG.backendUrl) || "";
const api = (path) => `${BACKEND}${path}`;

/* ============================ DİL ============================ */
/* Dil motoru i18n.js'te: VLF_I18N.t(key) -> aktif katalog | EN yedeği | anahtar */
const t = (key) => window.VLF_I18N.t(key);
const fmtMsg = (key, vars) => window.VLF_I18N.fmt(key, vars);
const i18nReady = () => window.VLF_I18N.ready;

/* ============================ TEMA ============================ */
const THEME_META = { light: "#f2f6f3", dark: "#060d0b" };

function applyTheme(theme, persist) {
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector("#meta-theme");
  if (meta) meta.setAttribute("content", THEME_META[theme] || THEME_META.dark);
  const btn = document.querySelector("#theme-toggle");
  if (btn) btn.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  if (persist) {
    try { localStorage.setItem("vlf-theme", theme); } catch (e) { /* yok say */ }
  }
}

(function initTheme() {
  applyTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark", false);
  const btn = document.querySelector("#theme-toggle");
  if (btn) {
    btn.addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
      applyTheme(next, true);
    });
  }
  /* Kullanıcı elle seçim yapmadıysa sistem temasını canlı izle */
  if (window.matchMedia) {
    try {
      const mq = matchMedia("(prefers-color-scheme: light)");
      const onSystem = (ev) => {
        let saved = null;
        try { saved = localStorage.getItem("vlf-theme"); } catch (e) { /* yok say */ }
        if (saved !== "light" && saved !== "dark") applyTheme(ev.matches ? "light" : "dark", false);
      };
      if (mq.addEventListener) mq.addEventListener("change", onSystem);
      else if (mq.addListener) mq.addListener(onSystem);
    } catch (e) { /* yok say */ }
  }
})();

/* ========================== ELEMANLAR ========================== */
const playBtn = document.querySelector("#play");
const chanBox = document.querySelector("#chan-box");
const hintEl = document.querySelector("#player-hint");
const volume = document.querySelector("#volume");
const statusLine = document.querySelector("#status-line");
const liveDot = document.querySelector("#live-dot");
const freezeBtn = document.querySelector("#wf-freeze");

/* ===================== SES: iki akış, tek çıkış ===================== */
/* Kesintisiz geçiş için iki MP3 akışı aynı anda çalışır; kanal değişince
   sadece kazanç düğümleri swap edilir - yeniden bağlantı/gecikme yok. */
let audioCtx = null;
const players = {};   // { clean: {el, src, gain}, raw: {...} }
let channel = "clean";
let playing = false;
let analyser = null, wfAnalyser = null, recDest = null, recorder = null;
let recChunks = [];

function buildAudio() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048; analyser.smoothingTimeConstant = 0.7;
  wfAnalyser = audioCtx.createAnalyser();
  wfAnalyser.fftSize = 2048; wfAnalyser.smoothingTimeConstant = 0;
  wfAnalyser.minDecibels = -105; wfAnalyser.maxDecibels = -20;

  const master = audioCtx.createGain();
  master.gain.value = volume.value / 100;
  master.connect(analyser);
  master.connect(wfAnalyser);
  master.connect(audioCtx.destination);
  players.master = master;

  // Kayıt için ayrı hedef (MediaRecorder bunu dinler)
  try {
    recDest = audioCtx.createMediaStreamDestination();
    master.connect(recDest);
  } catch (e) { recDest = null; }

  ["clean", "raw"].forEach((kind) => {
    const el = new Audio();
    el.crossOrigin = "anonymous";
    el.preload = "none";
    el.src = api(`/stream/${kind}.mp3?t=${Date.now()}`);
    const src = audioCtx.createMediaElementSource(el);
    const gain = audioCtx.createGain();
    gain.gain.value = kind === channel ? 1 : 0;
    src.connect(gain); gain.connect(master);
    players[kind] = { el, gain };
  });

  volume.addEventListener("input", () => { master.gain.value = volume.value / 100; });
}

async function start() {
  buildAudio();
  await audioCtx.resume();
  try {
    await Promise.all(["clean", "raw"].map((k) => players[k].el.play()));
    playing = true;
    playBtn.textContent = "⏸";
    playBtn.classList.add("playing");
    startRecorder();
  } catch (err) {
    statusLine.textContent = `${t("stOffline")} — ${err.message}`;
    statusLine.classList.add("err");
  }
}

function stop() {
  ["clean", "raw"].forEach((k) => players[k] && players[k].el.pause());
  playing = false;
  playBtn.textContent = "▶";
  playBtn.classList.remove("playing");
  stopRecorder();
}

playBtn.addEventListener("click", () => (playing ? stop() : start()));

chanBox.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-chan]");
  if (!btn) return;
  channel = btn.dataset.chan;
  chanBox.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
  hintEl.innerHTML = channel === "clean" ? t("hintClean") : t("hintRaw");
  wf.baseline = null;                       // yeni kanalın tabanı yeniden öğrenilsin
  if (players.clean) {
    const now = audioCtx.currentTime;
    ["clean", "raw"].forEach((k) => {
      const g = players[k].gain.gain;
      g.cancelScheduledValues(now);
      g.setTargetAtTime(k === channel ? 1 : 0, now, 0.05);   // 50 ms yumuşak geçiş
    });
  }
});

/* ================= GERİYE DÖNÜK KAYIT (son 60 sn) ================= */
function startRecorder() {
  if (!recDest || recorder || typeof MediaRecorder === "undefined") return;
  try {
    recorder = new MediaRecorder(recDest.stream);
    recChunks = [];
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size) recChunks.push({ t: Date.now(), blob: e.data });
      const cutoff = Date.now() - 65000;
      while (recChunks.length > 1 && recChunks[0].t < cutoff) recChunks.shift();
    };
    recorder.start(1000);                 // saniyelik parçalar
  } catch (e) { recorder = null; }
}
function stopRecorder() {
  if (recorder && recorder.state !== "inactive") recorder.stop();
  recorder = null;
}
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}
function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}
document.querySelector("#grab-audio").addEventListener("click", () => {
  const note = document.querySelector("#rec-note");
  if (!recChunks.length) { note.textContent = t("recWait"); return; }
  const blobs = recChunks.map((c) => c.blob);
  download(new Blob(blobs, { type: blobs[0].type || "audio/webm" }), `vlf_${channel}_${stamp()}.webm`);
  note.textContent = t("recDone");
  setTimeout(() => (note.innerHTML = t("recNote")), 4000);
});
document.querySelector("#grab-image").addEventListener("click", () => {
  wf.canvas.toBlob((blob) => blob && download(blob, `waterfall_${stamp()}.png`));
});

/* ========================= DURUM / METRİK ========================= */
const fmt = (v, unit = "") => (v === null || v === undefined || Number.isNaN(v) ? "—" : `${v}${unit}`);
async function pollStatus() {
  try {
    const r = await fetch(api("/api/status"), { cache: "no-store" });
    const s = await r.json();
    liveDot.classList.toggle("on", !!s.online);
    document.querySelector("#m-cancel").textContent = fmt((s.cancellation_db ?? 0).toFixed(1), " dB");
    document.querySelector("#m-band").textContent = fmt((s.band_reject_db ?? 0).toFixed(1), " dB");
    document.querySelector("#m-coh").textContent = fmt(Math.round((s.coherence ?? 0) * 100), " %");
    const up = s.uptime_seconds ?? 0;
    const hh = String(Math.floor(up / 3600)).padStart(2, "0");
    const mm = String(Math.floor((up % 3600) / 60)).padStart(2, "0");
    document.querySelector("#m-up").textContent = `${hh}:${mm}`;
    const bits = [];
    bits.push(s.online ? t("stOnline") : t("stOffline"));
    if (s.mode === "mock") bits.push(t("stMock"));
    if (s.sample_rate) bits.push(`${(s.sample_rate / 1000).toFixed(0)} kHz`);
    if (s.band_hz) bits.push(`${s.band_hz[0]}–${s.band_hz[1]} Hz`);
    if (typeof s.listeners === "number") bits.push(`${s.listeners} ${t("listeners")}`);
    if (s.clipping) bits.push(t("clipping"));
    if (s.error) bits.push(String(s.error));
    statusLine.textContent = bits.join("  ·  ");
    statusLine.classList.toggle("err", !s.online || !!s.error);
  } catch (e) {
    liveDot.classList.remove("on");
    statusLine.textContent = t("stOffline");
    statusLine.classList.add("err");
  }
}

/* ============================ REHBER ============================ */
function renderGuide() {
  const box = document.querySelector("#guide-cards");
  if (!box || !i18nReady()) return;
  const cards = [0, 1, 2, 3, 4, 5].map((i) => ({
    t: t(`guide${i}_t`),
    s: t(`guide${i}_s`),
    d: t(`guide${i}_d`),
  }));
  box.innerHTML = cards.map((g) => `
    <article class="card">
      <h3>${g.t}</h3>
      <p class="sound">${g.s}</p>
      <p>${g.d}</p>
    </article>`).join("");
}

/* ========================= VERİCİ TABLOSU ========================= */
function stationNote(s) {
  const key = "station" + String(s.call || "").replace(/[^A-Za-z0-9]/g, "");
  const localized = t(key);
  if (localized !== key) return localized;      // katalogda çevirisi var
  return s.note_tr || s.note_en || "";          // yedek: JSON'daki notlar
}

let txData = null;
async function loadTx() {
  const valid = (d) => d && Array.isArray(d.stations) && d.stations.length;
  // 1) Canlı sunucu API'si
  try {
    const r = await fetch(api("/api/transmitters"), { cache: "no-store" });
    if (r.ok) {
      const d = await r.json();
      if (valid(d)) { txData = d; renderTx(); return; }
    }
  } catch (e) { /* aşağıda yedek denenecek */ }
  // 2) Statik yedek (API yoksa veya GitHub Pages'ta)
  try {
    const r2 = await fetch("transmitters.json", { cache: "no-store" });
    const d2 = await r2.json();
    if (valid(d2)) txData = d2;
  } catch (e) { txData = null; }
  renderTx();
}

function renderTx() {
  const box = document.querySelector("#tx-table");
  const meta = document.querySelector("#scan-meta");
  if (!box || !i18nReady()) return;
  if (!txData || !Array.isArray(txData.stations) || !txData.stations.length) {
    box.innerHTML = ""; if (meta) meta.textContent = "";
    const sb = document.querySelector("#tx-summary"); if (sb) sb.innerHTML = "";
    return;
  }
  meta.textContent = txData.meta && txData.meta.scanned_at
    ? fmtMsg("scanAt", { d: txData.meta.scanned_at.replace("T", " ") })
    : t("scanNever");
  // Özet şeridi
  const hit = txData.stations.filter((s) => s.verdict === "seen" || s.verdict === "trace");
  const countries = new Set(hit.map((s) => s.country));
  const DIST = { RU: 2100, GB: 3200, IT: 1600, FR: 2700, DE: 2200, US: 8600, TR: 450, IS: 4600 };
  let far = null;
  hit.forEach((s) => { if (DIST[s.country] && (!far || DIST[s.country] > DIST[far.country])) far = s; });
  const sumBox = document.querySelector("#tx-summary");
  if (sumBox) {
    sumBox.innerHTML = hit.length ? `
      <div class="tx-sum"><b>${hit.length}/${txData.stations.length}</b><span>${t("sumDetected").toUpperCase()}</span></div>
      <div class="tx-sum"><b>${countries.size}</b><span>${t("sumCountries").toUpperCase()}</span></div>
      <div class="tx-sum"><b>${far ? "~" + DIST[far.country].toLocaleString() + " km" : "—"}</b><span>${t("sumFar").toUpperCase()}${far ? " · " + far.call : ""}</span></div>` : "";
  }

  const rows = txData.stations.map((s) => {
    const label = t(s.verdict) || s.verdict;
    const snr = s.snr_db === null || s.snr_db === undefined ? "" : ` ${s.snr_db.toFixed(1)} dB`;
    return `<div class="tx-row">
      <span class="tx-call">${s.call}</span>
      <span class="tx-note">${flag(s.country)} ${stationNote(s)}</span>
      <span class="tx-freq">${(s.freq_hz / 1000).toFixed(2)} kHz</span>
      <span class="tx-state ${s.verdict}">${label}${snr}</span>
    </div>`;
  }).join("");
  box.innerHTML = `<div class="tx-row head">
      <span>${t("thStation")}</span><span></span><span>${t("thFreq")}</span><span>${t("thState")}</span>
    </div>` + rows;
}

function flag(cc) {
  if (!cc || cc.length !== 2) return "";
  return String.fromCodePoint(...[...cc.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0)));
}
loadTx(); setInterval(loadTx, 300000);

/* ========================== SPEKTRUM ========================== */
const spec = document.querySelector("#spectrum");
const specCtx = spec.getContext("2d");
function drawSpectrum() {
  const ratio = window.devicePixelRatio || 1;
  const w = spec.clientWidth, h = spec.clientHeight;
  if (spec.width !== w * ratio || spec.height !== h * ratio) {
    spec.width = w * ratio; spec.height = h * ratio;
  }
  specCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
  specCtx.clearRect(0, 0, w, h);
  specCtx.fillStyle = "#040a08"; specCtx.fillRect(0, 0, w, h);
  specCtx.strokeStyle = "rgba(109,255,196,.08)";
  for (let i = 1; i < 6; i += 1) {
    const x = (w * i) / 6;
    specCtx.beginPath(); specCtx.moveTo(x, 0); specCtx.lineTo(x, h); specCtx.stroke();
  }
  if (analyser && playing && audioCtx) {
    const bins = analyser.frequencyBinCount;
    const data = new Uint8Array(bins);
    analyser.getByteFrequencyData(data);
    const binHz = audioCtx.sampleRate / analyser.fftSize;
    const maxBin = Math.min(bins - 1, Math.floor(12000 / binHz));
    specCtx.beginPath();
    for (let x = 0; x < w; x += 1) {
      const bin = Math.round((x / w) * maxBin);
      const y = h - (data[bin] / 255) * h;
      x === 0 ? specCtx.moveTo(x, y) : specCtx.lineTo(x, y);
    }
    specCtx.strokeStyle = "#45efac"; specCtx.lineWidth = 1.4; specCtx.stroke();
  }
  requestAnimationFrame(drawSpectrum);
}
drawSpectrum();

/* ========================== WATERFALL ========================== */
const wf = {
  canvas: document.querySelector("#waterfall"),
  labels: document.querySelector("#wf-labels"),
  zoomBox: document.querySelector("#wf-zoom"),
  speedBox: document.querySelector("#wf-speed"),
  modeBox: document.querySelector("#wf-mode"),
  badge: document.querySelector("#wf-badge"),
  countEl: document.querySelector("#wf-count"),
  maxFreq: 3000, speed: 2, mode: "olay", sens: 2.5,
  frozen: false, acc: 0, baseline: null, events: [],
};
const wfCtx = wf.canvas.getContext("2d");
const wfPalette = (() => {
  const off = document.createElement("canvas"); off.width = 256; off.height = 1;
  const g = off.getContext("2d");
  const grad = g.createLinearGradient(0, 0, 256, 0);
  grad.addColorStop(0.00, "#040a08");
  grad.addColorStop(0.18, "#0a2419");
  grad.addColorStop(0.45, "#1c7a54");
  grad.addColorStop(0.70, "#38e7a0");
  grad.addColorStop(0.88, "#c8ffe9");
  grad.addColorStop(1.00, "#ffffff");
  g.fillStyle = grad; g.fillRect(0, 0, 256, 1);
  return g.getImageData(0, 0, 256, 1).data;
})();

function wfResize() {
  const w = wf.canvas.clientWidth, h = wf.canvas.clientHeight;
  if (wf.canvas.width !== w || wf.canvas.height !== h) {
    wf.canvas.width = w; wf.canvas.height = h;
    wfCtx.fillStyle = "#040a08"; wfCtx.fillRect(0, 0, w, h);
  }
}
function wfRelabel() {
  const step = wf.maxFreq >= 12000 ? 2000 : wf.maxFreq >= 6000 ? 1000 : 500;
  const parts = [];
  for (let f = wf.maxFreq; f >= 0; f -= step) {
    parts.push(`<span>${f >= 1000 ? (f / 1000).toFixed(f % 1000 ? 1 : 0) + "k" : f}</span>`);
  }
  wf.labels.innerHTML = parts.join("");
}
if (wf.zoomBox) wf.zoomBox.addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-max]"); if (!b) return;
  wf.maxFreq = Number(b.dataset.max); wf.baseline = null;
  wf.zoomBox.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x === b));
  wfRelabel();
});
if (wf.speedBox) wf.speedBox.addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-speed]"); if (!b) return;
  wf.speed = Number(b.dataset.speed);
  wf.speedBox.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x === b));
});
if (wf.modeBox) wf.modeBox.addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-mode]"); if (!b) return;
  wf.mode = b.dataset.mode; wf.baseline = null;
  wf.modeBox.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x === b));
});
const jBtn = document.querySelector("#wf-jmode");
if (jBtn) jBtn.addEventListener("click", () => {
  wf.jhunt = !wf.jhunt;
  jBtn.classList.toggle("active", wf.jhunt);
  jBtn.textContent = wf.jhunt ? t("jmodeOn") : t("jmode");
  if (wf.jhunt) {
    // Tweek 50-100 ms sürer: pencereyi kısalt (zaman çözünürlüğü),
    // bandı daralt ve akışı hızlandır ki kanca yatayda yayılsın.
    if (wfAnalyser) wfAnalyser.fftSize = 512;            // ~10.7 ms pencere
    wf.maxFreq = 3000; wf.speed = 8; wf.sens = 1.5;
  } else {
    if (wfAnalyser) wfAnalyser.fftSize = 1024;
    wf.maxFreq = 3000; wf.speed = 2; wf.sens = 2.5;
  }
  wf.baseline = null; wf.dev = null;
  document.querySelectorAll("#wf-zoom button").forEach((x) => x.classList.toggle("active", Number(x.dataset.max) === wf.maxFreq));
  document.querySelectorAll("#wf-speed button").forEach((x) => x.classList.toggle("active", Number(x.dataset.speed) === wf.speed));
  wfRelabel();
});
if (freezeBtn) freezeBtn.addEventListener("click", () => {
  wf.frozen = !wf.frozen;
  freezeBtn.textContent = wf.frozen ? t("unfreeze") : t("freeze");
  freezeBtn.classList.toggle("active", wf.frozen);
});

let wfColumn = null;
function wfDraw() {
  wfResize();
  const w = wf.canvas.width, h = wf.canvas.height;
  if (wfAnalyser && playing && !wf.frozen && audioCtx) {
    const bins = wfAnalyser.frequencyBinCount;
    if (!wfColumn || wfColumn.length !== bins) wfColumn = new Uint8Array(bins);
    wfAnalyser.getByteFrequencyData(wfColumn);
    const binHz = audioCtx.sampleRate / wfAnalyser.fftSize;
    const maxBin = Math.min(bins - 1, Math.floor(wf.maxFreq / binHz));
    wf.acc += wf.speed;
    const s = Math.floor(wf.acc);
    if (s < 1) { requestAnimationFrame(wfDraw); return; }
    wf.acc -= s;
    wfCtx.drawImage(wf.canvas, -s, 0);

    let col = wfColumn;
    if (wf.mode === "olay") {
      if (!wf.baseline || wf.baseline.length !== bins) wf.baseline = Float32Array.from(wfColumn);
      const base = wf.baseline;
      const dev = wf.dev || (wf.dev = new Float32Array(bins).fill(4));
      const out = new Uint8Array(bins);
      let hits = 0, sum = 0;

      for (let i = 0; i <= maxBin; i += 1) {
        const v = wfColumn[i];
        const diff = v - base[i];
        // Taban: yukarı yavaş, aşağı hızlı. Sapma da öğrenilir (kendi gürültü ölçeği)
        base[i] += (diff > 0 ? 0.02 : 0.20) * diff;
        dev[i] += 0.02 * (Math.abs(diff) - dev[i]);
        const thr = wf.sens * Math.max(2.5, dev[i]);     // her bin kendi gürültüsüne göre
        const excess = diff - thr;
        if (excess > 0) { hits += 1; sum += excess; }
        out[i] = excess > 0 ? Math.min(255, 45 + excess * 7) : 0;
      }

      // Sferic = aynı anda GENİŞ bir bant boyunca yükselme (dikey çizgi).
      // Tek tük bin parlaması gürültüdür; onu ele.
      const span = maxBin + 1;
      const nowT = performance.now();
      const fresh = nowT - (wf.lineUntil || 0) > 0;
      const minFrac = 0.25;
      const isLine = fresh && hits >= span * minFrac && sum / Math.max(hits, 1) > 1.5;
      if (isLine) wf.lineUntil = nowT + (wf.jhunt ? 25 : 60);   // çizim: J avında kuyruk devam edebilsin
      if (!isLine) {
        out.fill(0);                                     // serpintiyi bastır
      }
      // isLine ise dokunma: gerçek genlikler kalsın ki tweek kuyruğu (J) görünsün
      col = out;

      const now = performance.now();
      if (isLine && now - (wf.lastEvent || 0) > 400) {   // sayım: aynı darbeyi 400 ms içinde tekrar sayma
        wf.lastEvent = now;
        wf.events.push(now);
      }
      while (wf.events.length && now - wf.events[0] > 60000) wf.events.shift();
      if (wf.countEl) {
        if (!wf.t0) wf.t0 = now;
        const spanMin = Math.min(60000, now - wf.t0) / 60000;
        const rate = spanMin > 0.08 ? wf.events.length / spanMin : wf.events.length;
        wf.countEl.textContent = String(Math.round(rate));
      }
      if (wf.badge) wf.badge.classList.toggle("hot", isLine);
    }

    const img = wfCtx.createImageData(s, h);
    const d = img.data;
    for (let y = 0; y < h; y += 1) {
      const bin = Math.min(maxBin, Math.round((1 - y / (h - 1)) * maxBin));
      const p = col[bin] * 4;
      const r = wfPalette[p], gg = wfPalette[p + 1], b = wfPalette[p + 2];
      for (let x = 0; x < s; x += 1) {
        const o = (y * s + x) * 4;
        d[o] = r; d[o + 1] = gg; d[o + 2] = b; d[o + 3] = 255;
      }
    }
    wfCtx.putImageData(img, w - s, 0);
  } else if (!playing) {
    wfCtx.fillStyle = "#040a08"; wfCtx.fillRect(0, 0, w, h);
    wfCtx.fillStyle = "rgba(213,255,237,.4)";
    wfCtx.font = "500 13px 'Open Sans', system-ui, sans-serif";
    wfCtx.fillText(t("wfStart"), 18, h / 2);
  }
  requestAnimationFrame(wfDraw);
}
wfRelabel(); wfDraw();

/* ==================== DİL SEÇİMİ + BAŞLATMA ==================== */
const langSelect = document.querySelector("#lang-select");
if (langSelect) {
  langSelect.addEventListener("change", (ev) => window.VLF_I18N.set(ev.target.value));
}

/* Dil değişince statik data-i18n düğümlerini i18n.js halleder;
   burada dinamik render'ları tazeliyoruz. */
function refreshDynamicTexts() {
  hintEl.innerHTML = channel === "clean" ? t("hintClean") : t("hintRaw");
  if (freezeBtn) {
    freezeBtn.textContent = wf.frozen ? t("unfreeze") : t("freeze");
    freezeBtn.classList.toggle("active", !!wf.frozen);
  }
  if (jBtn) {
    jBtn.textContent = wf.jhunt ? t("jmodeOn") : t("jmode");
    jBtn.classList.toggle("active", !!wf.jhunt);
  }
}
window.VLF_I18N.onChange(() => {
  refreshDynamicTexts();
  renderGuide();
  renderTx();
  if (i18nReady()) pollStatus();   // durum satırı da anında yeni dile dönsün
});

window.VLF_I18N.init().then(() => {
  refreshDynamicTexts();
  renderGuide();
  renderTx();
  pollStatus();
  setInterval(pollStatus, 2000);
});

/* ====================== YILDIRIM HARİTASI ====================== */
const LX_VIEWS = {
  tr: "https://map.blitzortung.org/#6/39.2/35.2",     // Türkiye ve çevresi
  eu: "https://map.blitzortung.org/#4/48.0/15.0",     // Avrupa
};
const lxFrame = document.querySelector("#lx-frame");
const lxWrap = document.querySelector("#lx-wrap");
const lxLink = document.querySelector("#lx-link");
let lxLoaded = false;

function lxShow(view) {
  if (!lxFrame) return;
  const url = LX_VIEWS[view] || LX_VIEWS.tr;
  if (lxLink) lxLink.href = url;
  lxLoaded = false;
  lxFrame.src = url;
  // Gömme engellenirse (X-Frame-Options) yedek karta düş
  setTimeout(() => { if (!lxLoaded && lxWrap) lxWrap.classList.add("failed"); }, 6000);
}
if (lxFrame) {
  lxFrame.addEventListener("load", () => {
    lxLoaded = true;
    if (lxWrap) lxWrap.classList.remove("failed");
  });
  const box = document.querySelector("#lx-zoom");
  if (box) box.addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-z]"); if (!b) return;
    box.querySelectorAll("button").forEach((x) => x.classList.toggle("active", x === b));
    lxShow(b.dataset.z);
  });
  // Sayfa açılır açılmaz değil, görünür olunca yükle (performans)
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { lxShow("tr"); io.disconnect(); } });
  }, { rootMargin: "200px" });
  io.observe(lxWrap);
}
