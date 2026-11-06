#!/usr/bin/env python3
"""Reproduce 2026-11-03 list export checks; original files remain unmodified."""
import csv
import json
import re
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parent
xlsx = root / '小红书-官方列表导出-0925.xlsx'
video = root / '视频号-官方列表导出-0927.csv'
raw = subprocess.check_output(['officecli', 'get', str(xlsx), '/Sheet1', '--depth', '2', '--json'], text=True)
rows = json.loads(raw)['data']['results'][0]['children']
def cells(row):
    return {re.search(r'/([A-Z]+)\d+$', c['path']).group(1): c.get('text', '') for c in row['children']}
header = cells(rows[1])
notes = [{name: cells(row).get(col, '') for col, name in header.items()} for row in rows[2:]]
assert len(notes) == 22 and len(header) == 13
with video.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    videos = list(reader)
    video_header = reader.fieldnames
assert len(videos) == 6 and len({x['视频ID'] for x in videos}) == 6

def totals(items, fields):
    result = {}
    for field in fields:
        vals = [r.get(field, '').strip() for r in items]
        missing = sum(v in ('', '-', '--') for v in vals)
        nums = [Decimal(v.replace(',', '')) for v in vals if v not in ('', '-', '--')]
        result[field] = {'sum': str(sum(nums)) if nums else None, 'missing': missing, 'sum_scope': '已提供值' if missing else '全部行'}
    return result

note_keys = [(r['笔记标题'], r['首次发布时间']) for r in notes]
summary = {
    '小红书': {'rows': len(notes), 'headers': list(header.values()),
             'duplicate_title_time': len(note_keys) - len(set(note_keys)),
             'blank_titles': sum(not r['笔记标题'] for r in notes),
             'totals': totals(notes, ['曝光','观看量','点赞','评论','收藏','涨粉','分享','弹幕'])},
    '视频号': {'rows': len(videos), 'headers': video_header,
              'duplicate_video_id': len(videos) - len({r['视频ID'] for r in videos}),
              'totals': totals(videos, ['播放量','推荐','喜欢','评论量','分享量','关注量','转发聊天和朋友圈','设为铃声','设为状态','设为朋友圈封面','企微链接点击次数','企微链接点击人数','添加到通讯录次数','添加到通讯录人数'])}}
with (root / '小红书-官方列表导出-0925-转换.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(header.values()))
    writer.writeheader()
    writer.writerows(notes)
with (root / '双平台列表统计-0927.json').open('w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
