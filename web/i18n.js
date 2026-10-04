/* VLF Noise Scout — i18n motoru
   - 17 dil kataloğu (web/locales/<kod>.json — .po/.mo kaynaklarından üretilir)
   - Açılır menü dili, tarayıcı dili algılama, localStorage kalıcılığı
   - Farsça (fa) için RTL desteği
   - Katalog yüklenene kadar minimal İngilizce yedek sözlük
*/
(function () {
  "use strict";

  var LANGS = {
    tr:  { name: "Türkçe",      rtl: false },
    en:  { name: "English",     rtl: false },
    es:  { name: "Español",     rtl: false },
    zh:  { name: "中文",         rtl: false },
    ja:  { name: "日本語",       rtl: false },
    vi:  { name: "Tiếng Việt",  rtl: false },
    de:  { name: "Deutsch",     rtl: false },
    fr:  { name: "Français",    rtl: false },
    ru:  { name: "Русский",     rtl: false },
    az:  { name: "Azərbaycanca", rtl: false },
    kk:  { name: "Қазақша",     rtl: false },
    mn:  { name: "Монгол",      rtl: false },
    ta:  { name: "தமிழ்",        rtl: false },
    ku:  { name: "Kurmancî",    rtl: false },
    zza: { name: "Zazakî",      rtl: false },
    yua: { name: "Maya t'aan",  rtl: false },
    fa:  { name: "فارسی",        rtl: true }
  };

  /* Katalog gelmeden önce kritik arayüz metinleri (EN yedeği) */
  var FALLBACK = {
    tagline: "Live natural radio from Ankara, Türkiye",
    chanClean: "Clean", chanRaw: "Raw", volume: "Volume",
    hintClean: "Adaptive cancellation on — shared interference removed",
    hintRaw: "Raw antenna signal — no processing applied",
    stOnline: "On air", stOffline: "No connection", stMock: "SIMULATION",
    listeners: "listeners", clipping: "CLIPPING",
    wfStart: "Press ▶ to start the waterfall",
    freeze: "Freeze", unfreeze: "Resume", jmode: "J hunt", jmodeOn: "J hunt ✓",
    perMin: "events/min", recNote: "While the stream plays, the last 60 seconds are continuously buffered — press the button after you hear something interesting.",
    recWait: "Buffer still filling… try again in a few seconds.",
    recDone: "Saved.", scanAt: "Last scan: {d}",
    seen: "DETECTED", trace: "faint trace", none: "not seen", unknown: "—",
    thState: "Status", thFreq: "Frequency", thStation: "Station"
  };

  var current = "tr";
  var dict = null;
  var ready = false;
  var cache = {};
  var listeners = [];

  function detect() {
    try {
      var saved = localStorage.getItem("vlf-lang");
      if (saved && LANGS[saved]) return saved;
    } catch (e) { /* gizli mod */ }
    var candidates = (navigator.languages && navigator.languages.length)
      ? navigator.languages
      : [navigator.language || "tr"];
    for (var i = 0; i < candidates.length; i += 1) {
      var low = String(candidates[i] || "").toLowerCase();
      if (LANGS[low]) return low;
      var base = low.split("-")[0];
      if (LANGS[base]) return base;
    }
    return "tr";
  }

  function fetchCatalog(code) {
    if (cache[code]) return cache[code];
    cache[code] = fetch("locales/" + code + ".json")
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .catch(function () { return null; });
    return cache[code];
  }

  function applyStatic() {
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var val = api.t(el.getAttribute("data-i18n"));
      if (typeof val === "string") el.innerHTML = val;
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
        var parts = pair.split(":");
        var attr = (parts[0] || "").trim();
        var key = (parts[1] || "").trim();
        if (attr && key) el.setAttribute(attr, api.t(key));
      });
    });
    var sel = document.querySelector("#lang-select");
    if (sel) sel.value = current;
  }

  var api = {
    get lang() { return current; },
    get ready() { return ready; },
    langs: LANGS,

    t: function (key) {
      if (dict && Object.prototype.hasOwnProperty.call(dict, key) && dict[key]) return dict[key];
      if (Object.prototype.hasOwnProperty.call(FALLBACK, key)) return FALLBACK[key];
      return key;
    },

    fmt: function (key, vars) {
      var s = api.t(key);
      Object.keys(vars || {}).forEach(function (k) {
        s = s.split("{" + k + "}").join(vars[k]);
      });
      return s;
    },

    isRTL: function (code) {
      var cfg = LANGS[code || current];
      return !!(cfg && cfg.rtl);
    },

    init: function () {
      return api.set(detect(), false);
    },

    set: function (code, persist) {
      if (!LANGS[code]) code = "tr";
      current = code;
      return fetchCatalog(code)
        .then(function (d) {
          if (!d && code !== "en") return fetchCatalog("en");
          return d;
        })
        .then(function (d) {
          dict = d || FALLBACK;
          if (persist !== false) {
            try { localStorage.setItem("vlf-lang", code); } catch (e) { /* yok say */ }
          }
          var html = document.documentElement;
          html.lang = code;
          html.dir = api.isRTL() ? "rtl" : "ltr";
          applyStatic();
          ready = true;
          listeners.forEach(function (fn) {
            try { fn(code); } catch (err) { /* dinleyici hatası uygulamayı düşürmesin */ }
          });
        });
    },

    onChange: function (fn) { listeners.push(fn); }
  };

  window.VLF_I18N = api;
})();
