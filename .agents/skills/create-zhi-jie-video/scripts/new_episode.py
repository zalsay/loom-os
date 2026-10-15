#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('episode_id')
    parser.add_argument('--output', required=True)
    parser.add_argument('--kind', choices=['promo', 'course-update', 'process', 'showcase', 'recap'], default='course-update')
    parser.add_argument('--duration', type=float, default=60)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.episode_id), 'Use lowercase letters, digits and hyphens'
    assert 12 <= args.duration <= 180 and abs(args.duration * 24 - round(args.duration * 24)) < .0001
    root = Path(__file__).resolve().parents[1]
    destination = Path(args.output).expanduser().resolve() / args.episode_id
    if destination.exists():
        raise SystemExit('Episode directory already exists; edit it and increment revision instead of overwriting.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / 'assets' / 'engine', destination)
    tools = destination / 'tools'
    tools.mkdir()
    for name in ['workflow.py', 'mimo_tts.py', 'video_pipeline.py']:
        shutil.copy2(root / 'scripts' / name, tools / name)
    shutil.copy2(root / 'assets/templates/lesson-input.md', destination / 'lesson-input.md')
    types = {'promo': ['idea','build','test','ai','garden','end'],
             'course-update': ['idea','build','test','record','ai','end'],
             'process': ['idea','compare','build','test','record','end'],
             'showcase': ['idea','build','test','record','end'],
             'recap': ['idea','compare','record','garden','end']}[args.kind]
    frames = round(args.duration * 24)
    allocation = [frames // len(types)] * len(types)
    for index in range(frames % len(types)):
        allocation[index] += 1
    voice = {'model':'mimo-v2.5-tts', 'voice':'茉莉', 'direction':'温暖明亮的普通话女声，像引导孩子探索的年轻导师。语速适中略轻快，短句停顿自然，带着好奇与鼓励，保持统一音色，不用夸张广告播音腔。AI读作字母A I，织界读作zhī jiè。只朗读指定逐字稿。'}
    scenes = [{'type':t,'duration':n/24,'title':['待填写本期标题'], 'caption':['待填写本期说明'],
               'body':['待填写具体观察'], 'illustration':'generic','narration':'待填写本期逐字稿',
               'evidence':[]} for t,n in zip(types,allocation)]
    for scene in scenes:
        if scene['type']=='compare':
            scene.update(before=['待填写方案A'],after=['待填写方案B'])
    config={'episode_id':args.episode_id,'revision':1,'kind':args.kind,'topic':'待填写课程主题',
            'header':'创造日记','source_notes':[],'voice':voice,'scenes':scenes}
    (destination/'episode.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    print(str(destination))

if __name__=='__main__':
    main()
