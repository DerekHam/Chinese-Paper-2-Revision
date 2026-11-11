#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验分段索引的覆盖与标签，并生成标签反查表、全文速查地图。"""
import re
import os
from collections import defaultdict, OrderedDict


BASE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    ("01_日出_分段索引.md", "日出", 1, 5072),
    ("02_太阳照常升起_分段索引.md", "太阳", 1, 7448),
]

SEG_RE = re.compile(r"^###\s+([^\s｜]+)｜(?:\[)?L(\d+)[–\-]L?(\d+)(?:\]\([^)]*\))?｜(.+?)\s*$")
TAG_RE = re.compile(r"^\*\*标签\*\*[：:]\s*(.+)$")
PAGE_RE = re.compile(r"^\*\*页码\*\*[：:]\s*(.+)$")
SITE_VIEWER = "https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html"


def src_link(work, kind, num, text):
    w = "r" if work == "日出" else "s"
    key = "l" if kind == "L" else "p"
    return f"[{text}]({SITE_VIEWER}?w={w}&{key}={num})"


def page_num(page):
    m = re.search(r"\d+", page or "")
    return int(m.group(0)) if m else 0

# 从使用说明中读取标签表
with open(os.path.join(BASE, "00_使用说明与标签表.md"), encoding="utf-8") as f:
    readme = f.read()
tag_section = readme.split("## 三、标签体系", 1)[1].split("## 四、", 1)[0]
ALLOWED = set(re.findall(r"`([^`]+)`", tag_section))

segments = []
errors = []
warnings = []

for fname, work, exp_start, exp_end in FILES:
    path = os.path.join(BASE, fname)
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    local = []
    cur = None
    for i, line in enumerate(lines, 1):
        m = SEG_RE.match(line.rstrip("\n"))
        if m:
            if cur:
                local.append(cur)
            sid, a, b, title = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
            cur = {"id": sid, "start": a, "end": b, "title": title,
                   "file": fname, "work": work, "tags": [], "page": "", "line": i}
        elif cur is not None and TAG_RE.match(line.strip()):
            raw = TAG_RE.match(line.strip()).group(1)
            cur["tags"] = re.findall(r"`([^`]+)`", raw)
        elif cur is not None and PAGE_RE.match(line.strip()):
            raw = PAGE_RE.match(line.strip()).group(1).strip()
            m = re.fullmatch(r"\[([^\]]+)\]\([^)]*\)", raw)
            if m:
                raw = m.group(1)
            cur["page"] = raw.strip("【】")
    if cur:
        local.append(cur)

    # 检查
    if not local:
        errors.append(f"{fname}: 未解析到任何段")
        continue
    local.sort(key=lambda s: (s["start"], s["end"]))
    if local[0]["start"] != exp_start:
        errors.append(f"{fname}: 首段起于 L{local[0]['start']}，应为 L{exp_start}")
    if local[-1]["end"] != exp_end:
        errors.append(f"{fname}: 末段止于 L{local[-1]['end']}，应为 L{exp_end}")
    prev = None
    for s in local:
        if s["end"] < s["start"]:
            errors.append(f"{s['id']}: 起止行颠倒 L{s['start']}-L{s['end']}")
        if prev:
            if s["start"] == prev["end"] + 1:
                pass
            elif s["start"] <= prev["end"]:
                errors.append(f"{s['id']}: 与 {prev['id']} 重叠（{prev['end']}→{s['start']}）")
            else:
                errors.append(f"{s['id']}: 与 {prev['id']} 之间有缺口（L{prev['end']+1}–L{s['start']-1}）")
        if not s["tags"]:
            errors.append(f"{s['id']}: 无标签")
        bad = [t for t in s["tags"] if t not in ALLOWED]
        if bad:
            errors.append(f"{s['id']}: 未登记标签 {bad}")
        if len(s["tags"]) > 8:
            warnings.append(f"{s['id']}: 标签 {len(s['tags'])} 个（偏多）")
        prev = s
    segments.extend(local)

ids = [s["id"] for s in segments]
dups = {x for x in ids if ids.count(x) > 1}
if dups:
    errors.append(f"重复段号：{sorted(dups)}")

# 生成标签反查表
by_tag = defaultdict(list)
for s in segments:
    for t in s["tags"]:
        by_tag[t].append(s)

GROUPS = OrderedDict([
    ("主题 / 母题", [
        "太阳/天亮","光与暗","金钱/账单","阶级/贫富","劳动/工作","女性/被看","男性凝视",
        "爱情/欲望","婚姻/贞操","性/身体","身体残缺/创伤","战争/战后","酒/醉酒","狂欢/节日",
        "跳舞/娱乐","赌博/投机","死亡/自杀","疾病/衰老","宗教/引文","道德/罪与罚","迷惘/虚无",
        "逃避/麻木","孤独/无家","回忆/过去","自然/风景","钓鱼/野外","斗牛/暴力","城市/旅馆",
        "旅行/流亡","希望/幻灭","命运/偶然","亲情/家庭","友谊","权力/控制","欺骗/谎言",
        "同情/残忍","时间/日常"]),
    ("人物：《日出》", ["陈白露","方达生","潘月亭","李石清","黄省三","王福升","顾八奶奶","胡四",
        "张乔治","小东西","翠喜","黑三","金八","李太太","仆役/茶房","打夯工人","乞丐/流浪者"]),
    ("人物：《太阳照常升起》", ["杰克","勃莱特","科恩","迈克","比尔","罗梅罗","伯爵","佐伊","阿施利",
        "哈维","蒙托亚","酒店侍者","妓女/舞女","神父"]),
    ("写法 / 形式", ["舞台说明","灯光","音响/鸡鸣","空间/屋内窗外","拉帐子","道具","服装/化妆",
        "动作/表演","对白","独白/自言自语","沉默/停顿","旁白/评论","第一人称叙述","对话体",
        "省略/留白","重复/回环","反讽","象征","引用/题词","结构对照","结尾/收束","开头/起笔",
        "景物描写","细节/数字","节奏/长短句","不可靠叙述","视角/聚焦","互文"]),
    ("用途", ["核心例证","次要例证","人物介绍","背景/过渡","对比点：日出","对比点：太阳",
        "论点A：日出未得救","论点B：钱说与藏","论点C：女人被看","论点D：热闹之后",
        "论点E：看得见与省略","备考引用"]),
])

out = ["# 标签反查表（自动生成）",
       "",
       "> 用法：按 `Ctrl+F` 搜标签，得到段号后到对应索引或原文行号查看。",
       "> 本表由 `_build_tag_index.py` 从两份分段索引自动生成；修改索引后请重跑脚本。",
       ""]
for gname, tags in GROUPS.items():
    out.append(f"## {gname}")
    out.append("")
    for t in tags:
        items = by_tag.get(t, [])
        if items:
            out.append(f"### `{t}`（{len(items)} 段）")
            for s in items:
                line_link = src_link(s["work"], "L", s["start"], f"L{s['start']}–L{s['end']}")
                page_link = src_link(s["work"], "P", page_num(s.get("page")), s["page"]) if s.get("page") else ""
                page_part = f"，{page_link}" if page_link else ""
                out.append(f"- **{s['id']}** {s['title']}（{s['work']}，{line_link}{page_part}）")
            out.append("")
    out.append("")

with open(os.path.join(BASE, "03_标签反查表.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))

# 生成全文速查地图
out = ["# 全文速查地图（自动生成）",
       "",
       "> 按幕/章列出段号、行号、一句话内容和标签。适合先定位，再跳转。",
       ""]
cur_work = None
for s in segments:
    if s["work"] != cur_work:
        out.append(f"# 《{s['work']}》")
        out.append("")
        cur_work = s["work"]
    line_link = src_link(s["work"], "L", s["start"], f"L{s['start']}–L{s['end']}")
    page_link = src_link(s["work"], "P", page_num(s.get("page")), s["page"]) if s.get("page") else ""
    page_part = f"，{page_link}" if page_link else ""
    out.append(f"- **{s['id']}**（{line_link}{page_part}）{s['title']}  \n  {' '.join('`'+t+'`' for t in s['tags'])}")
out.append("")

with open(os.path.join(BASE, "04_全文速查地图.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"段总数：{len(segments)}")
print(f"标签总数：{len(by_tag)}")
print(f"错误：{len(errors)}")
for e in errors:
    print("  ✗", e)
print(f"提醒：{len(warnings)}")
for w in warnings[:20]:
    print("  !", w)
