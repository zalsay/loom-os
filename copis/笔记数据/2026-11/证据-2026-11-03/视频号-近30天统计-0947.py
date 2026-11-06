#!/usr/bin/env python3
import csv, json
from collections import Counter
from pathlib import Path
p = Path(__file__).resolve().parent
with (p / '视频号-近30天官方导出-0947.csv').open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    records = list(reader)
    headers = reader.fieldnames
ids = [r['视频ID'] for r in records]
fields = ['播放量', '推荐', '喜欢', '评论量', '分享量', '关注量', '转发聊天和朋友圈', '设为铃声', '设为状态', '设为朋友圈封面', '企微链接点击次数', '企微链接点击人数', '添加到通讯录次数', '添加到通讯录人数']
totals = {}
for key in fields:
    values = [r[key].strip() for r in records]
    present = [int(v.replace(',', '')) for v in values if v not in ('', '-', '--')]
    totals[key] = {'sum': sum(present) if present else None, 'missing': len(values)-len(present)}
result = {'rows': len(records), 'duplicates': [key for key, n in Counter(ids).items() if n > 1], 'missing_ids': sum(not i for i in ids), 'headers': headers, 'totals': totals,
          'videos': [{'发布时间': r['发布时间'], '视频描述': r['视频描述'].splitlines()[0], '播放量': r['播放量'], '分享量': r['分享量'], '评论量': r['评论量'], '完播率': r['完播率'], '平均播放时长': r['平均播放时长']} for r in records]}
assert len(records) == 17 and not result['duplicates'] and not result['missing_ids'], '导出行数或视频ID异常'
with (p / '视频号-近30天统计-0947.json').open('w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))
