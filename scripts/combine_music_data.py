"""
合并 sekai-master-db-diff-main 中的多个 JSON 文件，
生成 combined_music_data.json，包含每首歌曲的以下信息：
  - id: 唯一ID
  - title: 歌名
  - creators: 创作者信息 (creatorArtistId, creatorArtistName, lyricist, composer, arranger)
  - tags: 所属团队/标签
  - categories: MV类型
  - publishedAt: 实装时间（游戏内发布时间戳）
  - releasedAt: 原曲发布时间戳
  - originalVideoLink: 原曲投稿链接（YouTube / Niconico）
  - vocals: 歌声版本列表，每个版本包含类型、描述、参与角色
"""

import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'sekai-master-db-diff-main')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

def load_json(filename):
    path = os.path.join(DB_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_output_json(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def parse_youtube_date(date_str):
    """Parse ISO 8601 date like '2026-04-17T12:01:13Z' to millisecond timestamp."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return None

def build_original_mv_date_map(database_v2):
    """Build a map from sekaiMusicId -> earliest original MV upload timestamp (ms)."""
    date_map = {}
    songs = database_v2.get('songs', []) if isinstance(database_v2, dict) else database_v2
    for song in songs:
        sid = song.get('sekaiMusicId')
        if not sid:
            continue
        videos = song.get('videos', [])
        for v in videos:
            if v.get('type') == 'original_mv':
                ts = parse_youtube_date(v.get('uploadDate'))
                if ts:
                    existing = date_map.get(sid)
                    if existing is None or ts < existing:
                        date_map[sid] = ts
    return date_map

JST_OFFSET_MS = 9 * 3600 * 1000  # 9 hours in milliseconds

def resolve_released_at(music_id, game_ts, mv_date_map):
    """Determine releasedAt: prefer original MV upload date, otherwise JST-corrected game timestamp."""
    mv_ts = mv_date_map.get(music_id)
    if mv_ts:
        return mv_ts
    if game_ts:
        return game_ts + JST_OFFSET_MS
    return None

def main():
    # 1. 加载所有需要的数据源
    musics = load_json('musics.json')
    music_artists = load_json('musicArtists.json')
    music_tags = load_json('musicTags.json')
    music_vocals = load_json('musicVocals.json')
    music_originals = load_json('musicOriginals.json')

    # 加载 database_v2 获取本家 MV 上传日期
    try:
        database_v2 = load_output_json('database_v2.json')
        original_mv_dates = build_original_mv_date_map(database_v2)
        print(f'Loaded {len(original_mv_dates)} original MV dates from database_v2.json')
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Warning: could not load database_v2.json: {e}')
        original_mv_dates = {}

    # 2. 构建查找索引
    # musicArtists: id -> artist object
    artist_map = {a['id']: a for a in music_artists}

    # musicTags: musicId -> [tag, ...]
    tags_map = {}
    for tag in music_tags:
        mid = tag['musicId']
        tags_map.setdefault(mid, []).append(tag['musicTag'])

    # musicVocals: musicId -> [vocal, ...]
    vocals_map = {}
    for vocal in music_vocals:
        mid = vocal['musicId']
        vocals_map.setdefault(mid, []).append(vocal)

    # musicOriginals: musicId -> videoLink
    original_links_map = {}
    for row in music_originals:
        mid = row.get('musicId')
        if mid is None:
            continue
        video_link = row.get('videoLink')
        if video_link:
            original_links_map[mid] = video_link

    # 3. 合并生成结果
    result = []
    for m in musics:
        mid = m['id']

        # 创作者信息
        artist_id = m.get('creatorArtistId')
        artist_name = artist_map.get(artist_id, {}).get('name') if artist_id else None

        # 歌声版本
        vocals_raw = vocals_map.get(mid, [])
        vocals_list = []
        for v in vocals_raw:
            characters = []
            for c in v.get('characters', []):
                characters.append({
                    'characterType': c['characterType'],
                    'characterId': c['characterId'],
                })
            vocals_list.append({
                'id': v['id'],
                'musicVocalType': v['musicVocalType'],
                'caption': v['caption'],
                'characters': characters,
                'assetbundleName': v['assetbundleName'],
            })

        song = {
            'id': mid,
            'title': m['title'],
            'creators': {
                'creatorArtistId': artist_id,
                'creatorArtistName': artist_name,
                'lyricist': m.get('lyricist'),
                'composer': m.get('composer'),
                'arranger': m.get('arranger'),
            },
            'tags': tags_map.get(mid, []),
            'categories': m.get('categories', []),
            'publishedAt': m.get('publishedAt'),
            'releasedAt': resolve_released_at(mid, m.get('releasedAt'), original_mv_dates),
            'originalVideoLink': original_links_map.get(mid),
            'vocals': vocals_list,
        }
        result.append(song)

    # 4. 输出
    out_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'combined_music_data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f'Done! Generated {len(result)} songs -> {out_path}')

if __name__ == '__main__':
    main()
