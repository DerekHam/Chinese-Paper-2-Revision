
const WORKS = {
  r: { title: "《日出》", file: "texts/richu.txt", prefix: "R" },
  s: { title: "《太阳照常升起》", file: "texts/taiyang.txt", prefix: "S" },
};
const state = { work: "r", lines: [], pages: [], query: "" };
const reader = document.getElementById("reader");
const jumpForm = document.getElementById("jumpForm");
const jumpInput = document.getElementById("jumpInput");
const tabs = [...document.querySelectorAll(".work-tabs button")];
const header = document.querySelector(".viewer-header");

function headerOffset() { return header.offsetHeight + 12; }

function jumpTo(id, mark) {
  const el = document.getElementById(id);
  if (!el) return false;
  const y = el.getBoundingClientRect().top + window.scrollY - headerOffset();
  window.scrollTo(0, Math.max(0, y));
  if (mark) {
    document.querySelectorAll(".found").forEach(x => x.classList.remove("found"));
    el.classList.add("found");
  }
  return true;
}

function jumpAfterRender(id) {
  const doJump = () => jumpTo(id, true);
  doJump();
  requestAnimationFrame(doJump);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(doJump);
  [60, 200, 500].forEach(t => setTimeout(doJump, t));
}

function setUrl(work, l, p) {
  const u = new URL(location.href);
  u.search = "";
  u.searchParams.set("w", work);
  if (l) u.searchParams.set("l", l);
  else if (p !== undefined && p !== null && p !== "") u.searchParams.set("p", p);
  history.replaceState(null, "", u);
}

async function loadWork(work, line, page, mark) {
  state.work = WORKS[work] ? work : "r";
  const cfg = WORKS[state.work];
  tabs.forEach(b => b.classList.toggle("active", b.dataset.work === state.work));
  document.title = `${cfg.title}原文｜Chinese Paper 2 Revision`;
  reader.innerHTML = '<p class="loading">正在读取原文……</p>';
  try {
    const [text, data] = await Promise.all([
      fetch(cfg.file).then(r => { if (!r.ok) throw new Error(r.status); return r.text(); }),
      fetch("data/pages.json").then(r => r.json()),
    ]);
    state.lines = text.split(/\r?\n/);
    state.pages = data[state.work] || [];
    render();
    let targetId = null;
    if (line) targetId = `${cfg.prefix}-L${line}`;
    else if (page !== undefined && page !== null && page !== "") targetId = `${cfg.prefix}-P${page}`;
    state.targetId = targetId;
    if (targetId) jumpAfterRender(targetId);
    else window.scrollTo(0, 0);
  } catch (err) {
    reader.innerHTML = `<p class="error">读取 ${cfg.file} 失败。GitHub Pages 上应正常工作；本地请用 <code>python3 -m http.server</code> 打开，不要直接双击 file://。错误：${err.message}</p>`;
  }
}

function render() {
  const cfg = WORKS[state.work];
  const pageAt = new Map(state.pages.map(p => [p.line, p.page]));
  const frag = document.createDocumentFragment();
  const h = document.createElement("h1");
  h.textContent = cfg.title + "原文";
  frag.appendChild(h);
  const meta = document.createElement("p");
  meta.className = "meta";
  meta.textContent = state.work === "r"
    ? "行号指 日出.txt；页码为原网页页序（第 1–51 页，序页为 P0）。"
    : "行号指 太阳照常升起.txt；页码为上海译文出版社 2011 年版 PDF 页序（第 1–210 页）。";
  frag.appendChild(meta);

  state.lines.forEach((line, idx) => {
    const n = idx + 1;
    const page = pageAt.get(n);
    if (page !== undefined) {
      const pb = document.createElement("div");
      pb.className = "pagebreak";
      pb.id = `${cfg.prefix}-P${page}`;
      pb.textContent = page === 0 ? "卷首 / 序页" : `第 ${page} 页`;
      frag.appendChild(pb);
    }
    if (state.work === "s" && /^【第\s*\d+\s*页】$/.test(line.trim())) return;
    const row = document.createElement("div");
    row.className = "line";
    row.id = `${cfg.prefix}-L${n}`;
    const a = document.createElement("a");
    a.className = "ln";
    a.href = `viewer.html?w=${state.work}&l=${n}`;
    a.textContent = n;
    a.addEventListener("click", ev => {
      ev.preventDefault();
      setUrl(state.work, n);
      jumpTo(`${cfg.prefix}-L${n}`, true);
    });
    const span = document.createElement("span");
    span.className = "txt";
    span.textContent = line || "\u00a0";
    row.appendChild(a);
    row.appendChild(span);
    frag.appendChild(row);
  });
  reader.innerHTML = "";
  reader.appendChild(frag);
}

function parseJump(raw) {
  let v = (raw || "").trim().replace(/\s+/g, "").toUpperCase();
  if (!v) return null;
  let work = state.work;
  let m = v.match(/^([RS])-?L(\d+)$/);
  if (m) return { work: m[1].toLowerCase(), l: m[2] };
  m = v.match(/^([RS])-?P(\d+)$/);
  if (m) return { work: m[1].toLowerCase(), p: m[2] };
  m = v.match(/^([RS])(\d+)$/);
  if (m) return { work: m[1].toLowerCase(), l: m[2] };
  m = v.match(/^L(\d+)$/);
  if (m) return { work, l: m[1] };
  m = v.match(/^P(\d+)$/);
  if (m) return { work, p: m[1] };
  m = v.match(/^(\d+)$/);
  if (m) return { work, l: m[1] };
  return null;
}

jumpForm.addEventListener("submit", ev => {
  ev.preventDefault();
  const t = parseJump(jumpInput.value);
  if (!t) return;
  setUrl(t.work, t.l, t.p);
  loadWork(t.work, t.l, t.p, true);
});

tabs.forEach(btn => btn.addEventListener("click", () => {
  setUrl(btn.dataset.work);
  loadWork(btn.dataset.work);
}));

window.addEventListener("load", () => { if (state.targetId) jumpTo(state.targetId, true); });
const params = new URLSearchParams(location.search);
loadWork(params.get("w") || "r", params.get("l"), params.get("p"), true);
window.addEventListener("popstate", () => {
  const p = new URLSearchParams(location.search);
  loadWork(p.get("w") || "r", p.get("l"), p.get("p"), true);
});
