#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把分幕/分部原稿合并为两份总索引（去掉各分册标题与覆盖表）。"""
import os
import re
import importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location("argument_tags", os.path.join(BASE, "_argument_tags.py"))
_argument_tags = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_argument_tags)

def body(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines)
                 if (l.startswith("## ") or l.startswith("### "))
                 and "覆盖核对" not in l)
    end = next((i for i, l in enumerate(lines) if l.strip() == "## 覆盖核对"), len(lines))
    return "\n".join(lines[start:end]).strip()

groups = [
    ("01_日出_分段索引.md",
     "# 《日出》分段索引（全剧）\n"
     "> 覆盖：[L1–L5072](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=r&l=1)（序 + 四幕）｜段号：R-序-01…、R1-01…R4-30｜页：[序页](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=r&p=0)–[第 51 页](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=r&p=51)\n"
     "> 标签说明见 `00_使用说明与标签表.md`；标签反查见 `03_标签反查表.md`。\n"
     "> 行号指 `日出.txt`；引用前请核对原文。\n"
     "> 页码说明：页码按太玄书阁原网页页序标注（`00.htm` 的“序”未编号，记作“序页”；`01.htm`–`51.htm` 依次为第 1–51 页），页码行采用《太阳照常升起.txt》的 `【第 N 页】` 格式。网页页序不等于纸本页码，正式引用纸本时请以纸本为准。\n\n",
     ["01a_日出_序_第一幕.md", "01b_日出_第二幕.md", "01c_日出_第三幕.md", "01d_日出_第四幕.md"]),
    ("02_太阳照常升起_分段索引.md",
     "# 《太阳照常升起》分段索引（全书）\n"
     "> 覆盖：[L1–L7448](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=s&l=1)（卷首 + 三部·十九章）｜段号：S0-01…、S1-01-01…S3-19-14｜页：[第 1–210 页](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=s&p=1)\n"
     "> 标签说明见 `00_使用说明与标签表.md`；标签反查见 `03_标签反查表.md`。\n"
     "> 行号指 `太阳照常升起.txt`；译本引文以赵静男译文为准。\n"
     "> 页码说明：页码按 `太阳照常升起.txt` 中的 `【第 N 页】` 标记标注（上海译文出版社 2011 年版 PDF 页序；[第 1 页](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=s&p=1)为封面，[第 15 页](https://derekham.github.io/Chinese-Paper-2-Revision/viewer.html?w=s&p=15)为正文“第一部·第一章”起始页）；页码行采用同一 `【第 N 页】` 格式。\n\n",
     ["02a_太阳_卷首_第一部.md", "02b_太阳_第二部上.md", "02c_太阳_第二部下.md", "02d_太阳_第三部.md"]),
]

for outname, header, parts in groups:
    chunks = [header]
    for p in parts:
        chunks.append(body(os.path.join(BASE, "_分段原稿", p)))
        chunks.append("\n\n---\n\n")
    text = "".join(chunks).rstrip() + "\n"
    text = _argument_tags.apply(text)
    # 分册原稿在 _分段原稿/，链接指向 ../../；合并到上级目录后改为 ../
    # 清理引文行外层重复的引号（正文对白本身带引号时会形成 ““…””）
    text = text.replace("：““", "：“")
    text = re.sub(r"””\s*$", "”", text, flags=re.M)
    text += "\n"
    with open(os.path.join(BASE, outname), "w", encoding="utf-8") as f:
        f.write(text)
    print(outname, "ok", len(text), "chars")
