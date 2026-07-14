#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动更新数据工具
从 GitHub 仓库 sekai-master-db-diff 拉取最新数据，
备份旧数据，重新生成前端使用的全部数据产物。
"""

import os
import sys
import json
import shutil
import subprocess
import importlib.util
from datetime import datetime

try:
    from .video_source_registry import get_preferred_snapshot_for_source
    from .video_source_registry import load_video_sources
except ImportError:
    from video_source_registry import get_preferred_snapshot_for_source
    from video_source_registry import load_video_sources

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.join(BASE_DIR, 'sekai-master-db-diff-main')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
BACKUP_DIR = os.path.join(BASE_DIR, 'backup')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
MANUAL_DATA_DIR = os.path.join(BASE_DIR, 'manual_data')
YOUTUBE_DIR = os.path.join(BASE_DIR, 'fetch_youtube_playlist')
VIDEO_SOURCES_CONFIG_PATH = os.path.join(MANUAL_DATA_DIR, 'video_sources.json')
ORIGINAL_VIDEO_OVERRIDES_PATH = os.path.join(MANUAL_DATA_DIR, 'original_video_overrides.json')

# 我们关心的音乐相关文件
MUSIC_FILES = [
    'musics.json',
    'musicArtists.json',
    'musicTags.json',
    'musicVocals.json',
    'musicOriginals.json',
    'musicDifficulties.json',
    'musicDanceMembers.json',
    'musicVideoCharacters.json',
    'musicCollaborations.json',
    'musicAssetVariants.json',
]


def configure_console_output():
    """尽量让 Windows 控制台按 UTF-8 输出，避免 emoji / 日文导致编码报错。"""
    for stream_name in ('stdout', 'stderr'):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, 'reconfigure', None)
        if not reconfigure:
            continue
        try:
            reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            continue


def run_git(args, cwd=None):
    """运行 git 命令并返回输出"""
    repo_dir = cwd or REPO_DIR
    cmd = ['git', '-c', f'safe.directory={repo_dir}'] + args
    try:
        result = subprocess.run(
            cmd, cwd=repo_dir,
            capture_output=True, text=True, encoding='utf-8'
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        print("❌ 错误: 未找到 git 命令，请确保已安装 Git 并添加到 PATH")
        sys.exit(1)


def check_repo():
    """检查仓库目录，返回是否具备 git 元数据。"""
    if not os.path.isdir(REPO_DIR):
        print(f"❌ 数据仓库目录不存在: {REPO_DIR}")
        print("   请先运行: git clone https://github.com/Sekai-World/sekai-master-db-diff.git sekai-master-db-diff-main")
        sys.exit(1)

    git_dir = os.path.join(REPO_DIR, '.git')
    if not os.path.isdir(git_dir):
        print(f"⚠️  {REPO_DIR} 不是一个 git 仓库")
        print("   将跳过主库 fetch/pull，只刷新外部视频来源并按本地文件状态决定是否重建")
        return False

    return True


def get_local_head():
    """获取本地 HEAD commit hash"""
    code, out, _ = run_git(['rev-parse', 'HEAD'])
    return out if code == 0 else None


def get_remote_head():
    """获取远程 HEAD commit hash"""
    code, out, err = run_git(['rev-parse', 'origin/main'])
    if code != 0:
        # 尝试 master 分支
        code, out, err = run_git(['rev-parse', 'origin/master'])
    return out if code == 0 else None


def fetch_remote():
    """Fetch 远程更新"""
    print("🔍 检查远程更新...")
    code, out, err = run_git(['fetch', '--all'])
    if code != 0:
        print(f"❌ git fetch 失败: {err}")
        return False
    return True


def get_changed_files(old_hash, new_hash):
    """获取两个 commit 之间变更的文件列表"""
    code, out, _ = run_git(['diff', '--name-only', old_hash, new_hash])
    if code == 0 and out:
        return out.split('\n')
    return []


def get_commit_log(old_hash, new_hash):
    """获取 commit 日志摘要"""
    code, out, _ = run_git([
        'log', '--oneline', f'{old_hash}..{new_hash}'
    ])
    if code == 0 and out:
        return out.split('\n')
    return []


def backup_data():
    """备份当前数据"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backed_up = []
    for filename in ['combined_music_data.json', 'musics_base.json', 'database_v2.json', 'aliases.json']:
        src = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(src):
            dst = os.path.join(BACKUP_DIR, f'{os.path.splitext(filename)[0]}_{timestamp}.json')
            shutil.copy2(src, dst)
            backed_up.append(dst)

    return backed_up


def pull_updates():
    """拉取最新更新"""
    print("⬇️  拉取最新数据...")
    code, out, err = run_git(['pull', '--ff-only'])
    if code != 0:
        print(f"❌ git pull 失败: {err}")
        print("   尝试: git pull --rebase 或手动解决冲突")
        return False
    return True


def run_python_script(script_name, description):
    """运行 Python 构建脚本"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"❌ 未找到脚本: {script_path}")
        return False

    print(f"   → {description}")
    child_env = os.environ.copy()
    child_env.setdefault('PYTHONIOENCODING', 'utf-8')
    child_env.setdefault('PYTHONUTF8', '1')
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=SCRIPTS_DIR,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        env=child_env,
    )

    if result.returncode != 0:
        print(f"❌ 执行失败 ({script_name}): {(result.stderr or '').strip()}")
        return False

    stdout = (result.stdout or '').strip()
    if stdout:
        for line in stdout.splitlines():
            print(f"     {line}")
    return True


def regenerate_data():
    """重新生成前端和构建脚本依赖的数据产物"""
    print("\n🔄 重新生成数据...")
    steps = [
        ('combine_music_data.py', '生成 combined_music_data.json'),
        ('build_musics_base.py', '生成 musics_base.json'),
        ('build_database.py', '生成 database_v2.json 并同步 aliases.json'),
        ('validate_data.py', '校验 database_v2.json'),
    ]

    for script_name, description in steps:
        if not run_python_script(script_name, description):
            return False

    return True


def compare_data(old_file, new_file):
    """对比新旧数据，找出新增/删除的歌曲"""
    changes = {'added': [], 'removed': []}

    if not old_file or not os.path.exists(old_file):
        return changes

    try:
        with open(old_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        with open(new_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        old_ids = {s['id']: s['title'] for s in old_data}
        new_ids = {s['id']: s['title'] for s in new_data}

        for sid, title in new_ids.items():
            if sid not in old_ids:
                changes['added'].append((sid, title))

        for sid, title in old_ids.items():
            if sid not in new_ids:
                changes['removed'].append((sid, title))

        changes['old_count'] = len(old_data)
        changes['new_count'] = len(new_data)
    except Exception:
        pass

    return changes


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_preferred_playlist_file(source_key='official_2dmv'):
    path = get_preferred_snapshot_for_source(BASE_DIR, source_key)
    return str(path) if path else None


def normalize_playlist_videos(videos):
    normalized = []
    for video in videos or []:
        normalized.append(
            {
                'videoId': video.get('videoId'),
                'title': video.get('title'),
                'description': video.get('description'),
                'channelTitle': video.get('channelTitle'),
                'channelId': video.get('channelId'),
                'publishedAt': video.get('publishedAt'),
                'thumbnails': video.get('thumbnails'),
                'position': video.get('position'),
                'duration': video.get('duration'),
                'viewCount': video.get('viewCount'),
                'likeCount': video.get('likeCount'),
            }
        )
    return normalized


def load_playlist_fetcher_module():
    module_path = os.path.join(YOUTUBE_DIR, 'fetch_youtube_playlist.py')
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"未找到抓取脚本: {module_path}")

    spec = importlib.util.spec_from_file_location('project_sekai_playlist_fetcher', module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载抓取脚本: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_source_snapshot_payload(source, fetcher, videos):
    enriched_videos = []
    for video in videos:
        enriched_video = dict(video)
        enriched_video.setdefault('sourceKey', source['key'])
        enriched_video.setdefault('sourceName', source['name'])
        enriched_video.setdefault('sourceKind', source['kind'])
        if source.get('videoType') and not enriched_video.get('videoType'):
            enriched_video['videoType'] = source['videoType']
        if source.get('versionBase') and not enriched_video.get('versionBase') and not enriched_video.get('version'):
            enriched_video['versionBase'] = source['versionBase']
        if source.get('versionSpecial') and not enriched_video.get('versionSpecial') and not enriched_video.get('version'):
            enriched_video['versionSpecial'] = source['versionSpecial']
        if source.get('extractors') and not enriched_video.get('extractors'):
            enriched_video['extractors'] = source['extractors']
        enriched_videos.append(enriched_video)

    return {
        'metadata': {
            'fetchedAt': datetime.now().isoformat(),
            'status': 'complete',
            'totalVideos': len(enriched_videos),
            'fetchMethod': 'API' if getattr(fetcher, 'api_key', None) else 'yt-dlp',
            'sourceKey': source['key'],
            'sourceName': source['name'],
            'sourceKind': source['kind'],
            'sourceUrl': source.get('url'),
            'videoType': source.get('videoType'),
            'versionBase': source.get('versionBase'),
            'versionSpecial': source.get('versionSpecial', []),
            'extractors': source.get('extractors', []),
        },
        'videos': enriched_videos,
    }


def save_source_snapshot(source, fetcher, videos):
    os.makedirs(YOUTUBE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(YOUTUBE_DIR, f"playlist_{source['key']}_{timestamp}.json")
    payload = build_source_snapshot_payload(source, fetcher, videos)
    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return output_path


def refresh_playlist_source(source, fetch_module):
    source_name = source['name']
    print(f"\n📺 刷新视频来源: {source_name}...")

    current_best_path = get_preferred_playlist_file(source['key'])
    current_videos = []
    if current_best_path:
        try:
            current_videos = load_json(current_best_path).get('videos', [])
        except Exception:
            current_videos = []

    try:
        fetcher = fetch_module.YouTubePlaylistFetcher(
            api_key=getattr(fetch_module, 'DEFAULT_API_KEY', None) or None
        )
        videos = fetcher.fetch_playlist(source['url'], use_api_first=True)
    except Exception as exc:
        print(f"⚠️  {source_name} 抓取失败，将继续使用现有文件: {exc}")
        return False

    if not videos:
        print(f"⚠️  {source_name} 未返回数据，将继续使用现有文件")
        return False

    if normalize_playlist_videos(current_videos) == normalize_playlist_videos(videos):
        current_name = os.path.basename(current_best_path) if current_best_path else '（无现有文件）'
        print(f"   → {source_name} 无变化，沿用 {current_name}")
        return True

    try:
        output_path = save_source_snapshot(source, fetcher, videos)
    except Exception as exc:
        print(f"⚠️  {source_name} 抓取成功，但保存失败，将继续使用现有文件: {exc}")
        return False

    print(f"   → 已更新 {source_name}: {os.path.basename(output_path)} ({len(videos)} 条)")
    return True


def refresh_configured_playlists():
    sources = load_video_sources(BASE_DIR)
    if not sources:
        print("\nℹ️  未配置视频来源，跳过 Playlist 刷新")
        return []

    fetch_module = load_playlist_fetcher_module()
    results = []
    for source in sources:
        if not source.get('enabled', True):
            print(f"\n⏭️  跳过已禁用来源: {source['name']}")
            continue
        if source.get('kind') != 'playlist':
            print(f"\n⏭️  暂不支持的来源类型 {source.get('kind')}: {source['name']}")
            continue
        result = refresh_playlist_source(source, fetch_module)
        results.append((source['key'], result))
    return results


def is_newer(source_path, target_path):
    if not os.path.exists(source_path):
        return False
    if not os.path.exists(target_path):
        return True
    return os.path.getmtime(source_path) > os.path.getmtime(target_path)


def get_regeneration_reasons(music_changed):
    reasons = []

    required_outputs = {
        'combined_music_data.json': os.path.join(OUTPUT_DIR, 'combined_music_data.json'),
        'musics_base.json': os.path.join(OUTPUT_DIR, 'musics_base.json'),
        'database_v2.json': os.path.join(OUTPUT_DIR, 'database_v2.json'),
        'aliases.json': os.path.join(OUTPUT_DIR, 'aliases.json'),
    }

    missing_outputs = [name for name, path in required_outputs.items() if not os.path.exists(path)]
    if missing_outputs:
        reasons.append(f"缺少输出文件: {', '.join(missing_outputs)}")

    if music_changed:
        reasons.append(f"检测到 {len(music_changed)} 个音乐相关文件变更")

    manual_aliases = os.path.join(MANUAL_DATA_DIR, 'aliases.json')
    manual_corrections = os.path.join(MANUAL_DATA_DIR, 'corrections.json')
    output_aliases = required_outputs['aliases.json']
    database_output = required_outputs['database_v2.json']

    if is_newer(manual_aliases, output_aliases):
        reasons.append('manual_data/aliases.json 比 output/aliases.json 更新')

    if is_newer(manual_aliases, database_output):
        reasons.append('manual_data/aliases.json 比 database_v2.json 更新')

    if is_newer(manual_corrections, database_output):
        reasons.append('manual_data/corrections.json 比 database_v2.json 更新')

    if is_newer(VIDEO_SOURCES_CONFIG_PATH, database_output):
        reasons.append('manual_data/video_sources.json 比 database_v2.json 更新')

    if is_newer(ORIGINAL_VIDEO_OVERRIDES_PATH, database_output):
        reasons.append('manual_data/original_video_overrides.json 比 database_v2.json 更新')

    for source in load_video_sources(BASE_DIR):
        preferred_playlist = get_preferred_playlist_file(source['key'])
        if preferred_playlist and is_newer(preferred_playlist, database_output):
            reasons.append(f"{os.path.basename(preferred_playlist)} 比 database_v2.json 更新")

    return reasons


def main():
    configure_console_output()
    print(f"\n╔{'═' * 50}╗")
    print(f"║{'自动更新数据工具':^42}║")
    print(f"╚{'═' * 50}╝\n")

    # 1. 检查仓库
    has_git_repo = check_repo()

    # 2. 记录当前 HEAD
    local_head = None
    remote_head = None
    fetch_succeeded = False
    changed = []
    music_changed = []
    commits = []

    if has_git_repo:
        local_head = get_local_head()
        if not local_head:
            print("❌ 无法获取本地 HEAD")
            sys.exit(1)
        print(f"📌 本地版本: {local_head[:8]}")

        # 3. Fetch 远程
        fetch_succeeded = fetch_remote()

        # 4. 对比
        remote_head = local_head
        if fetch_succeeded:
            remote_head = get_remote_head()
            if not remote_head:
                print("❌ 无法获取远程 HEAD")
                sys.exit(1)
            print(f"📡 远程版本: {remote_head[:8]}")
        else:
            print("⚠️  无法检查远程版本，将仅根据本地状态决定是否重建输出")

        if local_head != remote_head:
            # 5. 查看变更
            changed = get_changed_files(local_head, remote_head)
            music_changed = [f for f in changed if os.path.basename(f) in MUSIC_FILES]
            commits = get_commit_log(local_head, remote_head)

            print(f"\n📊 发现 {len(commits)} 个新提交，{len(changed)} 个文件变更")
            if music_changed:
                print(f"🎵 音乐相关变更 ({len(music_changed)}):")
                for f in music_changed:
                    print(f"   • {f}")
            else:
                print("ℹ️  无音乐相关文件变更（但仍会更新仓库）")
    else:
        print("ℹ️  当前仅执行本地模式刷新：不会检查 sekai-master-db-diff 的远程更新")

    # 6. 刷新所有配置的视频来源
    refresh_configured_playlists()

    regeneration_reasons = get_regeneration_reasons(music_changed)
    if has_git_repo and local_head == remote_head and not regeneration_reasons:
        print("\n✅ 数据已是最新，无需更新！")
        return
    if has_git_repo and local_head == remote_head:
        print("\nℹ️  远程数据已是最新，但本地输出需要重建：")
        for reason in regeneration_reasons:
            print(f"   • {reason}")
    elif not has_git_repo and not regeneration_reasons:
        print("\n✅ 本地来源和输出都没有变化，无需重建")
        return
    elif not has_git_repo:
        print("\nℹ️  当前为本地模式，按本地来源与输出状态继续重建")

    # 7. 备份
    print("\n💾 备份当前数据...")
    backup_files = backup_data()
    if backup_files:
        for bf in backup_files:
            print(f"   → {os.path.basename(bf)}")
    else:
        print("   (无需备份的文件)")

    # 找当用来对比的备份文件
    old_combined = None
    for bf in backup_files:
        if 'combined_music_data' in bf:
            old_combined = bf
            break

    # 8. 拉取
    new_head = local_head
    if has_git_repo and local_head != remote_head:
        if not pull_updates():
            sys.exit(1)

        new_head = get_local_head()
        print(f"✅ 已更新到 {new_head[:8]}")
    elif has_git_repo:
        print("✅ Git 数据已是最新，跳过 pull")
    else:
        print("✅ 本地模式下跳过 Git pull")

    # 9. 重新生成数据（音乐相关变更、输出缺失、本地手动数据变更或 playlist 更新时）
    regeneration_reasons = get_regeneration_reasons(music_changed)
    if regeneration_reasons:
        print("\n🧩 触发重建原因:")
        for reason in regeneration_reasons:
            print(f"   • {reason}")
        if regenerate_data():
            # 10. 对比新旧
            new_combined = os.path.join(OUTPUT_DIR, 'combined_music_data.json')
            changes = compare_data(old_combined, new_combined)

            if changes.get('added') or changes.get('removed'):
                print(f"\n📋 数据变更:")
                print(f"   歌曲总数: {changes.get('old_count', '?')} → {changes.get('new_count', '?')}")
                if changes['added']:
                    print(f"   ✨ 新增 {len(changes['added'])} 首:")
                    for sid, title in sorted(changes['added']):
                        print(f"      + #{sid} {title}")
                if changes['removed']:
                    print(f"   🗑️  删除 {len(changes['removed'])} 首:")
                    for sid, title in sorted(changes['removed']):
                        print(f"      - #{sid} {title}")
            else:
                print("\n📋 歌曲列表无变化（可能是其他字段更新）")
        else:
            print("\n❌ 数据重建失败，自动刷新未完成")
            sys.exit(1)
    else:
        print("\nℹ️  音乐相关文件和本地输出都无需重建，跳过数据重新生成")

    # 完成
    print(f"\n{'═' * 52}")
    print(f"🎉 更新完成！")
    print(f"{'═' * 52}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
