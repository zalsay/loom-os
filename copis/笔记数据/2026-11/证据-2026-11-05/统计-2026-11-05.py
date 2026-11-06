#!/usr/bin/env python3
"""2026-11-05 双平台导出统计（可复现）。口径：触达=播放量；留存=人均播放时长与总播放时长。"""
import csv, json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).parent
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
rows=list(csv.DictReader((HERE/'视频号-单篇30天官方导出-0933.csv').open(encoding='utf-8-sig')))
out=[];tot=0;totsec=0
for r in rows:
    p=int(r['播放量']); m=None if r['平均播放时长'] in ('-','') else float(r['平均播放时长'].replace('秒',''))
    sec=p*m if m else 0; tot+=p; totsec+=sec
    out.append({'日期':r['发布时间'],'播放':p,'人均':m,'总时长':sec,'完播率_仅记录':r['完播率']})
json.dump({'rows':out,'totals':{'播放':tot,'总秒':round(totsec)}},(HERE/'视频号-单篇30天统计-0933.json').open('w'),ensure_ascii=False,indent=1)
print('视频号',len(rows),'播放',tot,'总秒',round(totsec))
for v in out[:6]: print(v['日期'],v['播放'],v['人均'],round(v['总时长']))

with zipfile.ZipFile(HERE/'小红书-官方列表导出-0935.xlsx') as z:
    ss=[]; r=ET.fromstring(z.read('xl/sharedStrings.xml'))
    for si in r.findall('m:si',NS): ss.append(''.join(t.text or '' for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))
    sh=ET.fromstring(z.read('xl/worksheets/sheet1.xml')); data=[]
    for row in sh.find('m:sheetData',NS):
        cells={}
        for c in row.findall('m:c',NS):
            v=c.find('m:v',NS); val=v.text if v is not None else ''
            if c.get('t')=='s' and val!='': val=ss[int(val)]
            elif c.get('t')=='inlineStr': val=''.join(x.text or '' for x in c.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
            cells[''.join(ch for ch in c.get('r') if ch.isalpha())]=val
        data.append(cells)
hdr=next(i for i,c in enumerate(data) if c.get('A')=='笔记标题'); rs=data[hdr+1:]
sums={k:sum(float(r.get(c) or 0) for r in rs) for k,c in [('曝光','D'),('观看量','E'),('点赞','G'),('评论','H'),('收藏','I'),('涨粉','J'),('分享','K')]}
json.dump({'rows':rs,'totals':sums},(HERE/'小红书-列表统计-0935.json').open('w'),ensure_ascii=False,indent=1)
print('小红书',len(rs),sums)
