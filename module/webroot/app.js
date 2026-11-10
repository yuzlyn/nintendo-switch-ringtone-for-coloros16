// Nintendo Switch 音效 - WebUI 逻辑
// 设计与交互沿用 Font Settings 那一版模板：卡片 + 分组列表 + 开关 + 底部弹层。
const MODULE_ID = "ns-ringtone";
const MODDIR = `/data/adb/modules/${MODULE_ID}`;
const CTL = `sh ${MODDIR}/tools/soundctl.sh`;

const GROUPS = [
  { id: "product_ui", label: "按键与系统 UI" },
  { id: "mystock_ui", label: "触摸与提示音" },
  { id: "notifications", label: "通知音" },
];

const els = {
  main: document.querySelector("[data-main]"),
  sub: document.querySelector("[data-sub]"),
  reset: document.querySelector("[data-reset]"),
  toast: document.querySelector("[data-toast]"),
};

const state = {
  slots: new Map(),      // "group/file" -> id | "-"
  remembered: new Map(), // slot -> 最后一次启用的 id
  library: [],           // { id, label, ms }
  missing: new Set(),    // 当前系统上不存在的目标文件
  status: {},
  query: "",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function toast(message) {
  els.toast.textContent = message;
  els.toast.dataset.show = "true";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { els.toast.dataset.show = "false"; }, 2200);
}

const EXEC_TIMEOUT = 15000;

// KernelSU accepts exec(cmd), exec(cmd, fn) and exec(cmd, callbackName); older
// builds silently ignore the name form and never call back, which used to leave
// the page stuck on "读取中". A function callback is tried first, every call has
// a timeout, and the local httpd CGI endpoint is the last resort.
// KernelSU's signature is exec(command, optionsJson, callbackName): the callback
// is a global function *name*, and a function passed as the second argument is
// silently ignored - which is exactly how this page used to hang on "读取中".
function ksuExec(command, timeout) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (code, out) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code: Number.isFinite(Number(code)) ? Number(code) : -1, out: String(out ?? "") });
    };
    const timer = setTimeout(() => finish(-1, "timeout"), timeout);
    const name = `__ns_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;

    window[name] = (code, stdout, stderr) => {
      delete window[name];
      const errno = Number(code) || 0;
      finish(errno === 0 ? 0 : errno, errno === 0 ? stdout : (stderr || stdout));
    };

    try {
      const sync = window.ksu.exec(command, "{}", name);
      if (sync != null && typeof sync !== "function") {
        delete window[name];
        finish(0, sync);
      }
    } catch (first) {
      delete window[name];
      try {
        finish(0, window.ksu.exec(command) ?? "");
      } catch (second) {
        finish(-1, String(second));
      }
    }
  });
}

async function exec(command, timeout = EXEC_TIMEOUT) {
  if (window.ksu && typeof window.ksu.exec === "function") {
    return ksuExec(command, timeout);
  }
  // Outside KernelSU the page talks to the bundled busybox httpd. Its CGI
  // handler does not reliably forward POST bodies, so the command travels in
  // the query string as base64. The relative URL covers both the 127.0.0.1
  // server and a WebView that serves the files itself; the absolute one is the
  // fallback when the page origin is not the server.
  const encoded = encodeURIComponent(btoa(unescape(encodeURIComponent(command))));
  const absolute = "http://127.0.0.1:7127/cgi-bin/exec";
  // KernelSU serves the WebUI from an https virtual origin where a relative
  // path returns the raw CGI source, so https origins must use the absolute URL.
  const bases = location.protocol === "https:" ? [absolute, "cgi-bin/exec"] : ["cgi-bin/exec", absolute];
  for (const base of bases) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);
      const response = await fetch(`${base}?b64=${encoded}`, { signal: controller.signal });
      clearTimeout(timer);
      const text = await response.text();
      const cut = text.indexOf("\n");
      return { code: Number(text.slice(0, cut)), out: text.slice(cut + 1) };
    } catch (error) {
      /* try the next base */
    }
  }
  return { code: -1, out: "bridge_unavailable" };
}

function parseKeyValues(text) {
  const result = {};
  for (const line of text.split("\n")) {
    const at = line.indexOf("=");
    if (at > 0) result[line.slice(0, at)] = line.slice(at + 1);
  }
  return result;
}

function soundLabel(id) {
  if (!id || id === "-") return "保持原声";
  const hit = state.library.find((entry) => entry.id === id);
  return hit ? hit.label : id;
}

function targetLabel(slot) {
  const file = slot.split("/")[1] || slot;
  return file.replace(/\.[^.]+$/, "");
}

function rememberSlot(slot, id) {
  if (id && id !== "-") state.remembered.set(slot, id);
}

// Everything arrives in a single shell call: each CGI/exec round trip costs a
// fork on the device, and four of them in sequence is what made the page sit on
// "正在读取" for seconds. fetch() is avoided entirely - inside the KernelSU
// WebView a relative fetch may never settle.
async function loadAll() {
  const { out } = await exec(`${CTL} snapshot`, 8000);
  const sections = { status: [], slots: [], missing: [], library: [] };
  let current = null;
  for (const line of out.split("\n")) {
    if (line.startsWith("#")) {
      current = line.slice(1).trim();
      if (!sections[current]) sections[current] = [];
      continue;
    }
    if (current) sections[current].push(line);
  }

  state.status = parseKeyValues(sections.status.join("\n"));
  state.missing = new Set(sections.missing.map((line) => line.trim()).filter(Boolean));

  state.slots.clear();
  for (const line of sections.slots) {
    const at = line.indexOf("=");
    if (at <= 0) continue;
    const slot = line.slice(0, at);
    const id = line.slice(at + 1).trim();
    state.slots.set(slot, id);
    rememberSlot(slot, id);
  }

  state.library = sections.library.filter(Boolean).map((line) => {
    const [id, label, ms] = line.split("\t");
    return { id, label: label || id, ms: Number(ms) || 0 };
  }).sort((a, b) => a.label.localeCompare(b.label, "zh-Hans-CN"));
}

async function setSlot(slot, id) {
  const result = await exec(`${CTL} set '${slot}' '${id}'`);
  if (!/ok=set/.test(result.out)) {
    toast(`保存失败：${result.out.trim() || "未知错误"}`);
    return false;
  }
  state.slots.set(slot, id);
  rememberSlot(slot, id);
  state.status.pending_reboot = "1";
  return true;
}

function renderSummary() {
  const card = el("section", "card");
  const head = el("div", "card-head");
  const copy = el("div", "card-copy");
  copy.append(el("div", "card-title", "当前替换状态"));
  copy.append(el("div", "list-supporting", `音效库 ${state.library.length} 个可选音效`));
  head.append(copy);
  card.append(head);

  const stats = el("div", "ns-stats");
  const enabled = Number(state.status.enabled || 0);
  const total = Number(state.status.total || 0);
  for (const [value, key] of [[String(enabled), "已替换"], [String(Math.max(total - enabled, 0)), "保持原声"]]) {
    const box = el("div", "ns-stat");
    box.append(el("div", "n", value));
    box.append(el("div", "k", key));
    stats.append(box);
  }
  card.append(stats);

  if (state.status.pending_reboot === "1") {
    const note = el("div", "list-supporting", "改动已保存，重启后生效");
    note.style.paddingTop = "var(--sp-2)";
    note.style.color = "var(--md-sys-color-primary)";
    card.append(note);
  }
  const absent = state.missing.size;
  if (absent) {
    const note = el("div", "list-supporting",
      `${absent} 项在当前系统上没有对应文件，已自动跳过`);
    note.style.paddingTop = "var(--sp-1)";
    note.style.color = "var(--md-sys-color-on-surface-variant)";
    card.append(note);
  }
  return card;
}

function renderItem(slot, id) {
  const off = !id || id === "-";
  const absent = state.missing.has(slot);
  const item = el("div", "list-item ns-item");
  item.dataset.off = off || absent ? "true" : "false";

  const body = el("div", "list-body");
  body.append(el("div", "list-headline", targetLabel(slot)));
  body.append(el("div", "list-supporting",
    absent ? "此機型沒有這個音效檔案，不會被替換" : soundLabel(id)));

  const trailing = el("div", "list-trailing");
  const toggle = el("button", "switch");
  toggle.type = "button";
  toggle.dataset.selected = off || absent ? "false" : "true";
  toggle.setAttribute("role", "switch");
  toggle.setAttribute("aria-checked", off || absent ? "false" : "true");
  toggle.append(el("span", "switch-thumb"));

  toggle.addEventListener("click", async (event) => {
    event.stopPropagation();
    if (absent) return;
    if (!off) {
      if (await setSlot(slot, "-")) render();
      return;
    }
    const previous = state.remembered.get(slot);
    if (!previous) {
      openPicker(slot);
      return;
    }
    if (await setSlot(slot, previous)) render();
  });

  trailing.append(toggle);
  item.append(body, trailing);
  if (!absent) item.addEventListener("click", () => openPicker(slot));
  return item;
}

function renderGroup(group) {
  const rows = [...state.slots.entries()].filter(([slot]) => slot.startsWith(`${group.id}/`));
  if (!rows.length) return null;

  const wrap = el("section");
  wrap.append(el("div", "ns-group-title", `${group.label} · ${rows.length} 项`));

  const list = el("div", "list-group");
  rows.forEach(([slot, id], index) => {
    const item = renderItem(slot, id);
    if (rows.length === 1) item.dataset.shape = "only";
    else if (index === 0) item.dataset.shape = "first";
    else if (index === rows.length - 1) item.dataset.shape = "last";
    list.append(item);
  });
  wrap.append(list);
  return wrap;
}

function render() {
  els.main.replaceChildren();
  if (!state.slots.size) {
    const empty = el("div", "ns-empty", "没有读到槽位配置，请确认模块已启用并重启一次。");
    els.main.append(empty);
    els.sub.textContent = "模块状态未知";
    els.reset.disabled = true;
    return;
  }
  els.main.append(renderSummary());
  for (const group of GROUPS) {
    const section = renderGroup(group);
    if (section) els.main.append(section);
  }
  els.sub.textContent = `已替换 ${state.status.enabled || 0} / 共 ${state.status.total || state.slots.size} 项`;
  els.reset.disabled = false;
}

function closeSheet() {
  const scrim = document.querySelector("[data-ns-scrim]");
  if (!scrim) return;
  scrim.dataset.open = "false";
  setTimeout(() => scrim.remove(), 240);
}

// 试听与选择是两个动作：点行只试听，保存必须点「使用」。
// 音频优先按相对路径直接取静态文件并缓存成 blob URL，避免每次点都走一次
// base64 的 shell 往返——那一下的主线程阻塞就是「卡一下」的来源。
const audioCache = new Map();
let currentAudio = null;

async function soundUrl(id) {
  if (audioCache.has(id)) return audioCache.get(id);
  let url = "";
  try {
    const response = await fetch(`sounds/${id}.ogg`);
    if (response.ok) {
      const blob = await response.blob();
      if (blob.size > 0 && !/text\/html/.test(blob.type)) url = URL.createObjectURL(blob);
    }
  } catch (error) {
    /* 取不到就退回 shell */
  }
  if (!url) {
    const { out } = await exec(`base64 '${MODDIR}/webroot/sounds/${id}.ogg'`, 20000);
    const clean = out.replace(/\s+/g, "");
    if (clean) {
      const binary = atob(clean);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      url = URL.createObjectURL(new Blob([bytes], { type: "audio/ogg" }));
    }
  }
  if (url) audioCache.set(id, url);
  return url;
}

async function previewSound(id) {
  try {
    const url = await soundUrl(id);
    if (!url) {
      toast("无法试听该音效");
      return;
    }
    if (!currentAudio) currentAudio = new Audio();
    currentAudio.pause();
    currentAudio.src = url;
    await currentAudio.play();
  } catch (error) {
    toast("无法试听该音效");
  }
}

function openPicker(slot) {
  closeSheet();

  const scrim = el("div", "scrim");
  scrim.dataset.nsScrim = "true";
  scrim.dataset.open = "false";
  const sheet = el("div", "sheet");
  const handle = el("div", "sheet-handle");
  const title = el("div", "sheet-title typescale-title-medium-emphasized", `选择音效 · ${targetLabel(slot)}`);
  const body = el("div", "sheet-body");

  const search = el("input", "ns-sheet-search");
  search.type = "search";
  search.placeholder = "搜索音效名称";
  search.value = state.query;

  const list = el("div", "ns-sheet-list");

  const options = [{ id: "-", label: "保持原声（系统默认）", ms: 0 }, ...state.library];
  const current = state.slots.get(slot) || "-";

  function paint() {
    list.replaceChildren();
    const query = state.query.trim().toLowerCase();
    const shown = options.filter((option) => !query || option.label.toLowerCase().includes(query));
    if (!shown.length) {
      list.append(el("div", "ns-empty", "没有匹配的音效"));
      return;
    }
    for (const option of shown) {
      const isStock = option.id === "-";
      const isCurrent = option.id === current;
      const row = el("div", "ns-sound");
      row.dataset.current = isCurrent ? "true" : "false";

      const play = el("button", "ns-play");
      play.type = "button";
      play.title = "试听";
      play.setAttribute("aria-label", "试听");
      play.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
      if (isStock) {
        play.disabled = true;
        play.style.visibility = "hidden";
      } else {
        play.addEventListener("click", (event) => {
          event.stopPropagation();
          previewSound(option.id);
        });
      }

      row.append(play);
      row.append(el("span", "label", option.label));
      if (option.ms) row.append(el("span", "ms", `${(option.ms / 1000).toFixed(2)}s`));

      const use = el("button", "ns-use", isCurrent ? "当前" : isStock ? "用原声" : "使用");
      use.type = "button";
      if (isCurrent) {
        use.disabled = true;
      } else {
        use.addEventListener("click", async (event) => {
          event.stopPropagation();
          use.disabled = true;
          if (await setSlot(slot, option.id)) {
            closeSheet();
            render();
            toast("已保存，重启后生效");
          } else {
            use.disabled = false;
          }
        });
      }
      row.append(use);

      // 点行只试听，不保存：误触不会改掉已选的音效。
      if (!isStock) row.addEventListener("click", () => previewSound(option.id));
      list.append(row);
    }
  }

  search.addEventListener("input", () => {
    state.query = search.value;
    paint();
  });

  body.append(search, list);
  sheet.append(handle, title, body);
  scrim.append(sheet);
  scrim.addEventListener("click", (event) => {
    if (event.target === scrim) closeSheet();
  });
  document.body.append(scrim);
  paint();
  requestAnimationFrame(() => { scrim.dataset.open = "true"; });
}

els.reset.addEventListener("click", async () => {
  if (!confirm("恢复全部默认映射？当前的自定义选择会被覆盖。")) return;
  const result = await exec(`${CTL} reset`);
  if (!/ok=reset/.test(result.out)) {
    toast("恢复失败，请重试");
    return;
  }
  await loadState();
  render();
  toast("已恢复默认，重启后生效");
});

(async function boot() {
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.documentElement.dataset.theme = "dark";
  }
  try {
    await loadAll();
  } catch (error) {
    els.sub.textContent = "读取模块状态失败";
  }
  render();
})();
