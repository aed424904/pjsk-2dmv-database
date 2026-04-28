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

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'sekai-master-db-diff-main')

def load_json(filename):
    path = os.path.join(DB_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def main():
    # 1. 加载所有需要的数据源
    musics = load_json('musics.json')
    music_artists = load_json('musicArtists.json')
    music_tags = load_json('musicTags.json')
    music_vocals = load_json('musicVocals.json')
    music_originals = load_json('musicOriginals.json')

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
            'releasedAt': m.get('releasedAt'),
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
