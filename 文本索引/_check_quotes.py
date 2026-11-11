#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对索引中的引文是否能在原文对应行找到（忽略引号样式与省略号）。"""
import re, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = {"日出": os.path.join(BASE, "..", "日出.txt"),
       "太阳": os.path.join(BASE, "..", "太阳照常升起.txt")}
texts = {}
for k, p in SRC.items():
    with open(p, encoding="utf-8") as f:
        texts[k] = f.read().splitlines()

QUOTE_RE = re.compile(r"^-\s*(?:\[)?L(\d+)(?:\]\([^)]*\))?[：:]\s*[“\"](.+)[”\"]\s*$")
SEG_RE = re.compile(r"^###\s+([^\s｜]+)｜(?:\[)?L(\d+)[–\-]L?(\d+)(?:\]\([^)]*\))?｜")

QUOTES = "“”‘’「」『』\"'《》〈〉"
def norm(s):
    s = re.sub(r"…+", "", s)
    s = re.sub(r"[\s" + QUOTES + "]", "", s)
    return s

bad, total = [], 0
for path in sorted(glob.glob(os.path.join(BASE, "0[12]*.md"))):
    work = "日出" if "日出" in os.path.basename(path) else "太阳"
    lines = texts[work]
    cur = None
    for ln in open(path, encoding="utf-8").read().splitlines():
        m = SEG_RE.match(ln)
        if m:
            cur = m.group(1)
            continue
        q = QUOTE_RE.match(ln)
        if not q or not cur:
            continue
        total += 1
        lineno = int(q.group(1))
        quote = q.group(2)
        parts = [p for p in re.split(r"…+", quote) if norm(p)]
        window = norm("".join(lines[max(0, lineno-1):lineno+1]))
        missing = [p for p in parts if norm(p) not in window]
        if missing:
            window2 = norm("".join(lines[max(0, lineno-10):lineno+9]))
            missing2 = [p for p in parts if norm(p) not in window2]
            if missing2:
                bad.append((cur, lineno, quote[:60], missing2[0][:40]))
            else:
                bad.append((cur, lineno, quote[:60], "（标错行，但在前后10行内）"))

print(f"引文总数：{total}，疑似问题：{len(bad)}")
for b in bad:
    print("  ✗", b)
