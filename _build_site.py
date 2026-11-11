#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GitHub Pages 站点（输出到 docs/）。

用法：
    python3 _build_site.py

结构：
    docs/index.html
    docs/viewer.html
    docs/texts/richu.txt
    docs/texts/taiyang.txt
    docs/data/pages.json
    docs/*.html                 由 md 渲染
    docs/downloads/              docx / pdf
"""
import json
import os
import re
import shutil
from urllib.parse import quote

import markdown

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "docs")
SITE_BASE = "https://derekham.github.io/Chinese-Paper-2-Revision"

PAGES = [
    # (源文件, 站点文件名, 标题, 导航分组)
    ("INDEX.md", "index-nav.html", "总导航", "home"),
    ("README.md", "readme.html", "工作说明", "home"),
    ("文本索引/00_使用说明与标签表.md", "00-guide.html", "使用说明与标签表", "index"),
    ("文本索引/01_日出_分段索引.md", "01-richu-index.html", "《日出》分段索引", "index"),
    ("文本索引/02_太阳照常升起_分段索引.md", "02-taiyang-index.html", "《太阳照常升起》分段索引", "index"),
    ("文本索引/03_标签反查表.md", "03-tags.html", "标签反查表", "index"),
    ("文本索引/04_全文速查地图.md", "04-map.html", "全文速查地图", "index"),
    ("文本索引/05_Paper2_例证路线.md", "05-evidence.html", "Paper 2 例证路线", "paper2"),
    ("Paper2_一页速览.md", "paper2-overview.html", "Paper 2 一页速览", "paper2"),
    ("Paper2_研究资料_日出_太阳照常升起.md", "paper2-research.html", "Paper 2 研究资料", "paper2"),
    ("意象整理_日出_太阳照常升起.md", "imagery.html", "意象整理", "topics"),
    ("意象_镜子与影子_日出_太阳照常升起.md", "mirrors-shadows.html", "意象：镜子与影子", "topics"),
    ("次要人物与生存困境_小东西_黑人.md", "minor-characters.html", "次要人物与生存困境", "topics"),
    ("literary_analysis_guidelines.md", "guidelines.html", "文学分析规范", "about"),
    ("两份文本比较阅读索引工作流_分享版.md", "workflow.html", "索引工作流（分享版）", "about"),
]

SLUG_BY_BASENAME = {os.path.basename(src): slug for src, slug, _, _ in PAGES}
SLUG_BY_SRC = {src: slug for src, slug, _, _ in PAGES}

NAV = [
    ("index.html", "首页", "home"),
    ("viewer.html", "原文跳转", "viewer"),
    ("01-richu-index.html", "分段索引", "index"),
    ("05-evidence.html", "例证路线", "paper2"),
    ("imagery.html", "专题整理", "topics"),
    ("paper2-overview.html", "Paper 2", "paper2"),
    ("readme.html", "工作说明", "about"),
]


def read(path):
    with open(os.path.join(BASE, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    full = os.path.join(DOCS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def nav_html(active):
    items = []
    for href, label, key in NAV:
        cls = ' class="active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return "\n".join(items)


def page_template(title, content, active, description=""):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}｜Chinese Paper 2 Revision</title>
<meta name="description" content="{esc(description or title)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="index.html">Chinese Paper 2 Revision</a>
  <nav>{nav_html(active)}</nav>
</header>
<main class="page">
{content}
</main>
<footer class="site-footer">
  <p>《日出》×《太阳照常升起》比较阅读资料库 · <a href="viewer.html">原文跳转</a> · <a href="index.html">首页</a></p>
</footer>
</body>
</html>
"""


def viewer_query(work, kind, num):
    key = "l" if kind == "L" else "p"
    return f"viewer.html?w={work}&{key}={num}"


def rewrite_links(html):
    # 绝对站点链接 -> 相对
    html = html.replace(SITE_BASE + "/viewer.html", "viewer.html")
    # 旧短跳转页
    def old_redirect(m):
        return viewer_query(m.group(1).lower(), m.group(2), m.group(3))
    html = re.sub(r"(?:\.\./)*原文跳转/([RS])-([LP])(\d+)\.html", old_redirect, html)
    html = re.sub(r"(?:\.\./)*原文跳转\.html#([RS])-([LP])(\d+)", old_redirect, html)

    # md 链接 -> 站点 html
    def md_link(m):
        href = m.group(1)
        frag = m.group(2) or ""
        base = os.path.basename(href.split("#")[0])
        slug = SLUG_BY_BASENAME.get(base)
        if not slug:
            return m.group(0)
        return f'href="{slug}{frag}"'

    html = re.sub(r'href="([^"]+\.md)(#[^"]*)?"', md_link, html)

    # txt 链接
    html = html.replace('href="日出.txt"', 'href="texts/richu.txt"')
    html = html.replace('href="太阳照常升起.txt"', 'href="texts/taiyang.txt"')
    html = html.replace('href="../日出.txt"', 'href="texts/richu.txt"')
    html = html.replace('href="../太阳照常升起.txt"', 'href="texts/taiyang.txt"')

    # docx / pdf 下载
    def file_link(m):
        href = m.group(1)
        base = os.path.basename(href)
        if href.endswith(".docx"):
            return f'href="downloads/{quote(base)}"'
        if href.endswith(".pdf"):
            if href.startswith("参考文献/"):
                return f'href="downloads/references/{quote(base)}"'
            return f'href="downloads/{quote(base)}"'
        return m.group(0)

    html = re.sub(r'href="([^"]+\.(?:docx|pdf))"', file_link, html)
    return html


def render_pages():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc"])
    for src, slug, title, section in PAGES:
        md.reset()
        body = md.convert(read(src))
        body = rewrite_links(body)
        html = page_template(title, body, section, f"{title}｜《日出》与《太阳照常升起》比较阅读")
        write(slug, html)


def build_pages_json():
    pages = {"r": [], "s": []}
    # 日出：page -> start line
    with open(os.path.join(BASE, "文本索引", "页码映射_日出.tsv"), encoding="utf-8") as f:
        next(f, None)
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                pages["r"].append({"page": int(parts[0]), "line": int(parts[1])})
    # 太阳：txt 里的页码标记
    lines = read("太阳照常升起.txt").splitlines()
    pages["s"].append({"page": 1, "line": 1})
    for i, line in enumerate(lines, 1):
        m = re.fullmatch(r"【第\s*(\d+)\s*页】", line.strip())
        if m and int(m.group(1)) != 1:
            pages["s"].append({"page": int(m.group(1)), "line": i})
    write("data/pages.json", json.dumps(pages, ensure_ascii=False, indent=1))


VIEWER = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>原文跳转｜Chinese Paper 2 Revision</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/viewer.css">
</head>
<body class="viewer-page">
<header class="viewer-header">
  <a class="brand" href="index.html">← 首页</a>
  <strong>原文跳转</strong>
  <div class="work-tabs">
    <button type="button" data-work="r" class="active">《日出》</button>
    <button type="button" data-work="s">《太阳照常升起》</button>
  </div>
  <form id="jumpForm">
    <input id="jumpInput" placeholder="R5046 / S208 / R-P51 / S-P208" autocomplete="off">
    <button type="submit">跳转</button>
  </form>
</header>
<main id="reader" class="reader">
  <p class="loading">正在读取原文……</p>
</main>
<script src="assets/viewer.js"></script>
</body>
</html>
"""

VIEWER_CSS = """
.viewer-page { background:#faf8f3; }
.viewer-header { position:sticky; top:0; z-index:20; display:flex; gap:.8rem 1rem; align-items:center;
  flex-wrap:wrap; padding:.55rem 1rem; background:#fffdf8; border-bottom:1px solid #d8cfbf;
  font-family:-apple-system,"PingFang SC",sans-serif; font-size:.9rem; }
.viewer-header .brand { color:#6b4f1d; text-decoration:none; border-bottom:1px dotted #b9a06a; }
.work-tabs { display:flex; gap:.3rem; }
.work-tabs button { border:1px solid #d8cfbf; background:#f4ecd8; padding:.3rem .65rem; border-radius:4px; cursor:pointer; }
.work-tabs button.active { background:#6b4f1d; color:#fff; border-color:#6b4f1d; }
.viewer-header form { display:flex; gap:.3rem; margin-left:auto; }
.viewer-header input { width:16rem; padding:.3rem .5rem; border:1px solid #d8cfbf; border-radius:4px; background:#fff; font-size:.85rem; }
.viewer-header button[type=submit] { padding:.3rem .7rem; border:1px solid #d8cfbf; border-radius:4px; background:#f4ecd8; cursor:pointer; }
.reader { max-width:64rem; margin:0 auto; padding:.5rem 1.2rem 5rem; }
.reader h1 { font-size:1.45rem; margin:1rem 0 .5rem; border-bottom:2px solid #d8cfbf; padding-bottom:.35rem; }
.reader .meta { color:#8a8175; font-size:.82rem; margin-bottom:.8rem; }
.pagebreak { margin:1.5rem 0 .5rem; padding-top:.35rem; border-top:1px dashed #c9b98a; color:#8a6d3b;
  font-size:.82rem; scroll-margin-top:4.5rem; font-family:-apple-system,"PingFang SC",sans-serif; }
.line { display:flex; gap:.9rem; padding:.02rem 0; scroll-margin-top:4.5rem; border-radius:3px; }
.line .ln { flex:0 0 3.5rem; width:3.5rem; text-align:right; color:#b0a695; text-decoration:none;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.76rem; padding-top:.35rem; }
.line .ln:hover { color:#6b4f1d; text-decoration:underline; }
.line .txt { flex:1; white-space:pre-wrap; word-break:break-word; }
.line:target,.line.found,.pagebreak:target { background:#fff1a8; box-shadow:0 0 0 2px #fff1a8; }
.loading,.error { padding:2rem 1rem; color:#8a8175; }
.error { color:#9b2c2c; }
@media (max-width:640px) {
  .viewer-header form { width:100%; margin-left:0; }
  .viewer-header input { flex:1; width:auto; }
  .reader { padding:0 .7rem 4rem; }
  .line .ln { flex-basis:2.6rem; width:2.6rem; }
}
"""

VIEWER_JS = r"""
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
"""


def build_home():
    cards = [
        ("原文跳转", "按行号、页码直接跳到《日出》或《太阳照常升起》原文。",
         "viewer.html?w=r", "打开阅读器", "primary"),
        ("分段索引", "118 段《日出》＋137 段《太阳》，逐段页码、摘要、引文、标签。",
         "01-richu-index.html", "从《日出》开始", ""),
        ("Paper 2 例证路线", "按三个论点和五个比较点整理的最短例证链。",
         "05-evidence.html", "看例证路线", ""),
        ("专题整理", "意象、镜子与影子、次要人物与生存困境。",
         "imagery.html", "看专题", ""),
        ("Paper 2 资料", "一页速览、研究资料、文献与段落模板。",
         "paper2-overview.html", "看速览", ""),
        ("工作说明", "索引怎么用、引文怎么写、文件怎么维护。",
         "readme.html", "读工作说明", ""),
    ]
    card_html = []
    for title, desc, href, cta, cls in cards:
        card_html.append(f"""<section class="card {cls}">
  <h2>{esc(title)}</h2>
  <p>{esc(desc)}</p>
  <a href="{href}">{esc(cta)} →</a>
</section>""")
    content = f"""<section class="hero">
  <p class="eyebrow">Chinese Paper 2 Revision</p>
  <h1>《日出》×《太阳照常升起》</h1>
  <p class="lede">比较阅读资料库：原文跳转、分段索引、例证路线、意象与人物整理、Paper 2 写作资料。</p>
  <p><a class="button" href="viewer.html?w=r">打开原文阅读器</a> <a class="button ghost" href="05-evidence.html">直接看例证路线</a></p>
</section>
<section class="cards">
{''.join(card_html)}
</section>
<section class="note">
  <h2>怎么用</h2>
  <p>先在 <a href="05-evidence.html">例证路线</a> 找论点，再按段号回到 <a href="01-richu-index.html">《日出》索引</a> 或 <a href="02-taiyang-index.html">《太阳》索引</a>；索引里的 <code>L...</code>、<code>第...页</code> 会打开 <a href="viewer.html">原文跳转</a> 的对应位置。</p>
</section>"""
    write("index.html", page_template("首页", content, "home",
                                      "《日出》与《太阳照常升起》比较阅读资料库"))


def copy_assets():
    write("assets/viewer.css", VIEWER_CSS)
    write("assets/viewer.js", VIEWER_JS)
    write("viewer.html", VIEWER)
    write(".nojekyll", "")

    os.makedirs(os.path.join(DOCS, "texts"), exist_ok=True)
    shutil.copyfile(os.path.join(BASE, "日出.txt"), os.path.join(DOCS, "texts", "richu.txt"))
    shutil.copyfile(os.path.join(BASE, "太阳照常升起.txt"), os.path.join(DOCS, "texts", "taiyang.txt"))

    # docx 下载
    dl = os.path.join(DOCS, "downloads")
    os.makedirs(dl, exist_ok=True)
    for name in os.listdir(BASE):
        if name.endswith(".docx") and not name.startswith("~$"):
            shutil.copyfile(os.path.join(BASE, name), os.path.join(dl, name))

    # PDF 下载
    for name in os.listdir(BASE):
        if name.endswith(".pdf"):
            shutil.copyfile(os.path.join(BASE, name), os.path.join(dl, name))
    refs = os.path.join(BASE, "参考文献")
    if os.path.isdir(refs):
        dest = os.path.join(dl, "references")
        os.makedirs(dest, exist_ok=True)
        for name in os.listdir(refs):
            if name.endswith(".pdf"):
                shutil.copyfile(os.path.join(refs, name), os.path.join(dest, name))


def site_css():
    return """
:root { --bg:#faf8f3; --paper:#fffdf8; --ink:#222; --muted:#7b7265; --line:#d8cfbf; --accent:#6b4f1d; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",serif; line-height:1.85; }
a { color:#6b4f1d; }
.site-header { position:sticky; top:0; z-index:20; display:flex; gap:1rem 1.4rem; align-items:center;
  flex-wrap:wrap; padding:.7rem 1.2rem; background:rgba(255,253,248,.98);
  border-bottom:1px solid var(--line); font-family:-apple-system,"PingFang SC",sans-serif; font-size:.9rem; }
.brand { font-weight:700; text-decoration:none; color:var(--ink); }
.site-header nav { display:flex; gap:.9rem; flex-wrap:wrap; }
.site-header nav a { text-decoration:none; color:var(--muted); padding-bottom:2px; border-bottom:2px solid transparent; }
.site-header nav a:hover,.site-header nav a.active { color:var(--accent); border-bottom-color:var(--accent); }
.page { max-width:62rem; margin:0 auto; padding:1.2rem 1.2rem 4rem; }
.page h1 { font-size:1.9rem; line-height:1.35; margin:1.2rem 0 .8rem; border-bottom:2px solid var(--line); padding-bottom:.45rem; }
.page h2 { font-size:1.3rem; margin:1.6rem 0 .5rem; color:var(--accent); }
.page h3 { font-size:1.08rem; margin:1.2rem 0 .4rem; }
.page p,.page li { font-size:1rem; }
.page blockquote { margin:1rem 0; padding:.6rem 1rem; border-left:4px solid #c9b98a; background:#f7f0df; color:#4f4638; }
.page code { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.9em; background:#f1eadb; padding:.1em .25em; border-radius:3px; }
.page pre { background:#2f2a22; color:#f6f0e3; padding:1rem; overflow:auto; border-radius:6px; line-height:1.6; }
.page pre code { background:none; padding:0; color:inherit; }
.page table { width:100%; border-collapse:collapse; margin:1rem 0; font-size:.92rem; }
.page th,.page td { border:1px solid var(--line); padding:.4rem .55rem; vertical-align:top; }
.page th { background:#f1eadb; text-align:left; }
.page tr:nth-child(even) td { background:#fdfaf2; }
.page hr { border:0; border-top:1px solid var(--line); margin:1.6rem 0; }
.page img { max-width:100%; height:auto; }
.site-footer { border-top:1px solid var(--line); padding:1rem 1.2rem 2rem; color:var(--muted);
  font-family:-apple-system,"PingFang SC",sans-serif; font-size:.82rem; text-align:center; }
.hero { padding:2.2rem 0 1.2rem; }
.eyebrow { color:var(--accent); letter-spacing:.08em; text-transform:uppercase; font-family:-apple-system,"PingFang SC",sans-serif; font-size:.78rem; }
.hero h1 { font-size:clamp(2rem,5vw,3.1rem); border:0; margin:.2rem 0 .6rem; }
.lede { font-size:1.1rem; color:#4f4638; max-width:44rem; }
.button { display:inline-block; background:var(--accent); color:#fff; text-decoration:none; padding:.55rem .9rem; border-radius:5px; margin:.3rem .4rem .3rem 0; }
.button.ghost { background:transparent; color:var(--accent); border:1px solid var(--accent); }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(16rem,1fr)); gap:1rem; margin:1.4rem 0; }
.card { background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:1rem 1.1rem; }
.card h2 { margin:.1rem 0 .4rem; font-size:1.15rem; }
.card p { margin:.2rem 0 .7rem; color:#5c5346; font-size:.94rem; }
.card a { text-decoration:none; font-weight:600; }
.card.primary { border-color:#b9a06a; background:#fff8e6; }
.note { margin-top:1.6rem; padding:1rem 1.2rem; background:var(--paper); border:1px solid var(--line); border-radius:8px; }
@media (max-width:640px) {
  .site-header { padding:.55rem .8rem; }
  .page { padding:1rem .8rem 3rem; }
}
"""


def main():
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(DOCS)
    copy_assets()
    write("assets/style.css", site_css())
    build_pages_json()
    render_pages()
    build_home()
    print("site written to", DOCS)


if __name__ == "__main__":
    main()
