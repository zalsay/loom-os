import hashlib
import json
from pathlib import Path
import re

TYPES = {'idea', 'build', 'test', 'compare', 'ai', 'garden', 'growth', 'record', 'end'}
PLACEHOLDER = re.compile(r'待填写|待补充|TODO|PLACEHOLDER|<[^>]+>')

def load(project, allow_draft=False):
    project = Path(project).resolve()
    config = json.loads((project / 'episode.json').read_text())
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', config['episode_id']), 'Invalid episode_id'
    assert isinstance(config['revision'], int) and config['revision'] > 0, 'revision must be a positive integer'
    assert config['scenes'], 'No scenes'
    time, scenes = 0.0, []
    for index, scene in enumerate(config['scenes'], 1):
        assert scene['type'] in TYPES, f'Unknown scene type: {scene["type"]}'
        length = float(scene['duration'])
        assert 2 <= length <= 30, f'Scene {index}: duration must be 2–30 seconds'
        body_limit, body_count = {'idea': (7,2), 'ai': (10,3), 'garden': (9,4), 'growth': (14,2), 'test': (14,4), 'end': (14,2)}.get(scene['type'], (14,5))
        for field, limit, count in [('title', 13, 2), ('caption', 17, 2), ('body', body_limit, body_count), ('before', 8, 3), ('after', 8, 3)]:
            lines = scene.get(field, [])
            assert isinstance(lines, list) and len(lines) <= count, f'Scene {index}: invalid {field}'
            assert all(isinstance(v, str) and len(v) <= limit for v in lines), f'Scene {index}: shorten {field}'
        assert scene.get('illustration', 'generic') in {'car', 'garden', 'generic'}, f'Scene {index}: invalid illustration'
        narration = scene.get('narration', '')
        assert isinstance(narration, str), f'Scene {index}: narration must be text'
        evidence = scene.get('evidence', [])
        assert isinstance(evidence, list), f'Scene {index}: evidence must be a list'
        if not allow_draft:
            assert not PLACEHOLDER.search(json.dumps(scene, ensure_ascii=False)), f'Scene {index}: unresolved placeholders'
        item = dict(scene, id=index, a=time, b=time+length)
        item['start'] = time + (0.45 if index == len(config['scenes']) else 0.6)
        item['end'] = time + length - (0.15 if index == len(config['scenes']) else 0.45)
        assert item['end'] > item['start']
        scenes.append(item)
        time += length
    if not allow_draft:
        assert not PLACEHOLDER.search(config.get('topic','')), 'Fill the episode topic'
    assert isinstance(config.get('header'), str) and len(config['header']) <= 14, 'Shorten header'
    assert 2 <= time <= 180, 'Episode must be 2–180 seconds'
    assert abs(time * 24 - round(time * 24)) < 0.0001, 'Total duration must be a whole frame at 24fps'
    config['duration'] = time
    config['timeline'] = scenes
    return project, config

def stem(config):
    return f'Zhi-Jie-{config["episode_id"]}-v{config["revision"]:03d}'

def request(config, scene):
    voice = config['voice']
    return {'model': voice['model'], 'messages': [
        {'role': 'user', 'content': voice['direction'] + f'本段在约 {scene["end"]-scene["start"]:.1f} 秒内自然读完，避免拖长句尾。'},
        {'role': 'assistant', 'content': scene['narration']}],
        'audio': {'format': 'wav', 'voice': voice['voice']}, 'stream': False}

def fingerprint(config, scene):
    data = {'endpoint': 'https://api.xiaomimimo.com/v1/chat/completions', 'request': request(config, scene),
            'window': [scene['start'], scene['end']]}
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def cache_matches(project, config, scene):
    raw = project / 'narration' / 'raw'
    wav, meta = raw / f'{scene["id"]:02d}.wav', raw / f'{scene["id"]:02d}.json'
    if not wav.is_file() or not meta.is_file():
        return False
    receipt = json.loads(meta.read_text())
    return receipt.get('fingerprint') == fingerprint(config, scene) and receipt.get('audio_sha256') == hashlib.sha256(wav.read_bytes()).hexdigest()

def timestamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'
