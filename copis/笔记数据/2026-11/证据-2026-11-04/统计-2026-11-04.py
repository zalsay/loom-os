#!/usr/bin/env python3
"""2026-11-04 双平台导出统计（可复现）。
视频号：账号日表 CSV、单篇 30 天 CSV；小红书：官方 XLSX（zipfile 解析，避免改扩展名）。
输出：视频号-单篇30天统计-0913.json、小红书-列表统计-0906.json
口径：留存用「人均播放时长」与「总播放时长=播放×人均」，完播率仅记录（WF-2 第3条）。
"""
import csv, json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def wx():
    rows = list(csv.DictReader((HERE/'视频号-单篇30天官方导出-0913.csv').open(encoding='utf-8-sig')))
    out, tot, totsec = [], 0, 0.0
    for r in rows:
        p = int(r['播放量'])
        m = None if r['平均播放时长'] in ('-', '') else float(r['平均播放时长'].replace('秒', ''))
        sec = p * m if m else 0.0
        tot += p; totsec += sec
        out.append({'日期': r['发布时间'], '播放': p, '人均': m, '总时长': sec,
                    '完播率_仅记录': r['完播率'], '评论': r['评论量'], '分享': r['分享量']})
    json.dump({'rows': out, 'totals': {'播放': tot, '总秒': round(totsec)}},
              (HERE/'视频号-单篇30天统计-0913.json').open('w'), ensure_ascii=False, indent=1)
    print('视频号', len(rows), '条  播放', tot, ' 总秒', round(totsec))

def xhs():
    with zipfile.ZipFile(HERE/'小红书-官方列表导出-0906.xlsx') as z:
        ss = []
        r = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in r.findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter(
                '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))
        sh = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        data = []
        for row in sh.find('m:sheetData', NS):
            cells = {}
            for c in row.findall('m:c', NS):
                v = c.find('m:v', NS)
                val = v.text if v is not None else ''
                if c.get('t') == 's' and val != '':
                    val = ss[int(val)]
                elif c.get('t') == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter(
                        '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
                cells[''.join(ch for ch in c.get('r') if ch.isalpha())] = val
            data.append(cells)
    hdr = next(i for i, c in enumerate(data) if c.get('A') == '笔记标题')
    rows = data[hdr+1:]
    sums = {k: sum(float(r.get(col) or 0) for r in rows) for k, col in
            [('曝光','D'),('观看量','E'),('点赞','G'),('评论','H'),('收藏','I'),('涨粉','J'),('分享','K')]}
    json.dump({'rows': rows, 'totals': sums},
              (HERE/'小红书-列表统计-0906.json').open('w'), ensure_ascii=False, indent=1)
    print('小红书', len(rows), '条 ', sums)

if __name__ == '__main__':
    wx(); xhs()
