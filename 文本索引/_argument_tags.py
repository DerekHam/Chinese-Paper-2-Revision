#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为两份总索引补充跨作品共用的论文论点标签。

分段原稿中的「论点A—E」标签由各分册独立标注，标准不完全一致；
这里按比较点统一补齐两份作品的对应段落，避免检索时漏掉另一部作品。
"""
import re

A = "论点A：日出未得救"
B = "论点B：钱说与藏"
C = "论点C：女人被看"
D = "论点D：热闹之后"
E = "论点E：看得见与省略"

# 段号 -> 需补充的标签
SUPPLEMENT = {
    # ---- 《日出》 ----
    "R1-01": [E],
    "R1-02": [C],
    "R1-07": [D],
    "R1-10": [C],
    "R1-11": [C],
    "R1-13": [C],
    "R1-15": [A, C],
    "R1-18": [B],
    "R1-28": [A],
    "R2-01": [E],
    "R2-02": [A],
    "R2-27": [B],
    "R2-28": [D],
    "R3-02": [C, E],
    "R4-02": [C],
    "R4-09": [E],
    "R4-12": [A],
    "R4-14": [B],
    "R4-16": [B],
    "R4-24": [D],
    "R4-27": [D],
    "R4-28": [A, B, C],
    "R4-29": [A],
    "R4-30": [A, E],
    # ---- 《太阳照常升起》 ----
    "S0-06": [A],
    "S1-03-05": [C],
    "S1-04-04": [B, E],
    "S1-04-05": [A, B, C, E],
    "S1-07-03": [C],
    "S1-07-07": [D],
    "S2-13-07": [B],
    "S2-13-08": [C],
    "S2-14-01": [B, D],
    "S2-15-01": [D],
    "S2-15-06": [C],
    "S2-16-08": [C, E],
    "S2-17-01": [B],
    "S2-18-10": [D, E],
    "S3-19-01": [B, D],
    "S3-19-05": [A],
    "S3-19-11": [C, D],
    "S3-19-13": [A, C, E],
}

# 分册原稿中与“太阳/得救”论点关系较远的段落，去掉误加的 A 标签
REMOVE = {
    "R1-20": [A],
    "R2-21": [A],
}

SEG_RE = re.compile(r"^###\s+([^\s｜]+)｜")
TAG_RE = re.compile(r"^\*\*标签\*\*[：:]\s*(.+)$")


def apply(text):
    lines = text.splitlines()
    cur = None
    added = 0
    for i, line in enumerate(lines):
        m = SEG_RE.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur and TAG_RE.match(line):
            existing = re.findall(r"`([^`]+)`", line)
            for t in REMOVE.get(cur, []):
                if t in existing:
                    existing.remove(t)
            for t in SUPPLEMENT.get(cur, []):
                if t not in existing:
                    existing.append(t)
                    added += 1
            lines[i] = "**标签**：" + " ".join(f"`{t}`" for t in existing)
            cur = None
    print(f"  补充论点标签 {added} 个")
    return "\n".join(lines)
