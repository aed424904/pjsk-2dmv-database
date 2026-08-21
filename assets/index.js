let allSongs = [];
let filteredSongs = [];
let activeFilters = {
  tags: new Set(),
  categories: new Set(),
  vocalTypes: new Set(),
  videoVersions: new Set(),
  staffRoles: new Set(),
};
let sortField = 'id';
let sortAsc = true;
let expandedId = null;
const PAGE_SIZE = 50;
let visibleCount = PAGE_SIZE;
let aliasMap = {};
let characterNameMap = { game_character: new Map(), outside_character: new Map() };
let viewerDrawer = null;
let viewerUrlState = null;

const TAG_CONFIG = {
  light_music_club: { label: 'Leo/need', color: '#4dabf7' },
  idol: { label: 'MORE MORE JUMP!', color: '#69db7c' },
  street: { label: 'Vivid BAD SQUAD', color: '#f06595' },
  theme_park: { label: 'WxS', color: '#ffd43b' },
  school_refusal: { label: 'N25', color: '#9b6dff' },
  vocaloid: { label: 'V.S.', color: '#38d9e8' },
  other: { label: 'Other', color: '#868e96' },
};
const CAT_LABELS = { mv: '3D MV', mv_2d: '2D MV', image: 'Image', original: 'Original' };
const VOCAL_LABELS = {
  original_song: '原唱', sekai: 'セカイ', another_vocal: 'アナザー',
  virtual_singer: 'V家合唱', instrumental: 'Inst.',
  april_fool_2022: 'エイプリル', streaming_live: 'Connect Live',
};
const VIDEO_VERSION_CONFIG = {
  'base:original': { label: '本家' },
  'base:sekai': { label: 'SEKAI ver' },
  'base:virtual_singer': { label: 'Virtual Singer ver' },
  'base:another_vocal': { label: 'Another Vocal' },
  'base:unknown': { label: '未分类' },
  'special:april_fool': { label: '愚人节版' },
};
const VIDEO_VERSION_ORDER = Object.keys(VIDEO_VERSION_CONFIG);
const STAFF_ROLE_CONFIG = {
  illustrator: { label: '插画师' },
  pvCreator: { label: 'PV / 视频' },
  illustrationAnimation: { label: '插图动画' },
  lyricDesign: { label: '歌词设计' },
  animation: { label: '动画' },
  design: { label: '设计 / Logo' },
  cg3d: { label: '3DCG' },
  unknown: { label: '待整理' },
};
const STAFF_ROLE_ORDER = Object.keys(STAFF_ROLE_CONFIG);

function formatDate(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
function formatNumber(num) {
  if (num == null || isNaN(num)) return '-';
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
  if (num >= 10000) return (num / 10000).toFixed(1) + '万';
  return num.toLocaleString('zh-CN');
}
function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '-';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
function getDisplayTags(tags) { return (tags || []).filter(t => t !== 'all'); }
function esc(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
function createEmptyStaffSummary() {
  return {
    illustrators: [],
    pvCreators: [],
    otherRoles: {
      illustrationAnimation: [],
      lyricDesign: [],
      animation: [],
      design: [],
      cg3d: [],
      unknown: [],
    },
    allContributors: [],
  };
}
function createEmptyVideoVersionSummary() {
  return {
    bases: [],
    special: [],
    labels: [],
  };
}
function buildGameCharacterName(character) {
  return [character?.firstName, character?.givenName].filter(Boolean).join('') ||
    character?.givenName ||
    character?.firstName ||
    character?.name ||
    '';
}
function buildCharacterNameLookup(gameCharacters = [], outsideCharacters = []) {
  const lookup = {
    game_character: new Map(),
    outside_character: new Map(),
  };

  gameCharacters.forEach(character => {
    const name = buildGameCharacterName(character);
    if (name) lookup.game_character.set(Number(character.id), name);
  });

  outsideCharacters.forEach(character => {
    const name = character?.name || '';
    if (name) lookup.outside_character.set(Number(character.id), name);
  });

  return lookup;
}
function getCharacterDisplayName(character) {
  const type = character?.characterType === 'outside_character' ? 'outside_character' : 'game_character';
  const id = Number(character?.characterId);
  const name = characterNameMap[type]?.get(id);
  if (name) return type === 'outside_character' ? `⭐ ${name}` : name;
  return type === 'outside_character'
    ? `⭐ #${character?.characterId ?? '?'}`
    : `#${character?.characterId ?? '?'}`;
}
function formatVocalCharacterNames(vocal) {
  const names = (vocal?.characters || []).map(getCharacterDisplayName).filter(Boolean);
  return names.length ? names.join(' / ') : '(无角色)';
}
function getStaffSummary(song) {
  return song.staffSummary || createEmptyStaffSummary();
}
function getSongVersionSummary(song) {
  const summary = song.videoVersionSummary || createEmptyVideoVersionSummary();
  return {
    bases: Array.isArray(summary.bases) ? summary.bases : [],
    special: Array.isArray(summary.special) ? summary.special : [],
    labels: Array.isArray(summary.labels) ? summary.labels : [],
  };
}
function getVersionLabel(versionKey, fallbackValue = '') {
  if (VIDEO_VERSION_CONFIG[versionKey]?.label) return VIDEO_VERSION_CONFIG[versionKey].label;
  if (fallbackValue === 'unknown') return '未分类';
  return fallbackValue || versionKey;
}
function getSongVersionFilterKeys(song) {
  const summary = getSongVersionSummary(song);
  const keys = [];
  summary.bases.forEach(base => {
    const key = `base:${base}`;
    if (VIDEO_VERSION_CONFIG[key]) keys.push(key);
  });
  summary.special.forEach(special => {
    const key = `special:${special}`;
    if (VIDEO_VERSION_CONFIG[key]) keys.push(key);
  });
  return Array.from(new Set(keys));
}
function getSongVersionLabels(song) {
  const summary = getSongVersionSummary(song);
  const labels = new Set(summary.labels || []);
  summary.bases.forEach(base => labels.add(getVersionLabel(`base:${base}`, base)));
  summary.special.forEach(special => labels.add(getVersionLabel(`special:${special}`, special)));
  return Array.from(labels);
}
function getVideoUrlMap(song) {
  const videos = song.dbVideos || [];
  const map = {};
  videos.forEach(v => {
    const base = v.version?.base;
    if (base) { const key = `base:${base}`; if (!map[key]) map[key] = v.url; }
    (v.version?.special || []).forEach(s => {
      const key = `special:${s}`; if (!map[key]) map[key] = v.url;
    });
    if (v.version?.label) { if (!map[v.version.label]) map[v.version.label] = v.url; }
  });
  return map;
}
function buildVersionBadgeItems(song) {
  const summary = getSongVersionSummary(song);
  const urlMap = getVideoUrlMap(song);
  const badges = [];
  const seen = new Set();

  if (summary.labels.length) {
    summary.labels.forEach(label => {
      if (!label || seen.has(label)) return;
      seen.add(label);
      const url = urlMap[label];
      const inner = `<span class="version-preview-badge label-custom">${esc(label)}</span>`;
      badges.push(url ? `<a class="version-badge-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${esc(label)}">${inner}</a>` : inner);
    });
    return badges;
  }

  summary.bases.forEach(base => {
    const key = `base:${base}`;
    if (seen.has(key)) return;
    seen.add(key);
    const url = urlMap[key];
    const inner = `<span class="version-preview-badge base-${base}">${esc(getVersionLabel(key, base))}</span>`;
    badges.push(url ? `<a class="version-badge-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${esc(getVersionLabel(key, base))}">${inner}</a>` : inner);
  });

  summary.special.forEach(special => {
    const key = `special:${special}`;
    if (seen.has(key)) return;
    seen.add(key);
    const url = urlMap[key];
    const inner = `<span class="version-preview-badge special-${special}">${esc(getVersionLabel(key, special))}</span>`;
    badges.push(url ? `<a class="version-badge-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${esc(getVersionLabel(key, special))}">${inner}</a>` : inner);
  });

  return badges;
}
function buildVersionPreviewHtml(song) {
  const badges = buildVersionBadgeItems(song);
  return badges.length ? `<div class="song-version-preview">${badges.join('')}</div>` : '';
}
function buildVersionDetailSection(song) {
  const badges = buildVersionBadgeItems(song);
  if (!badges.length) return '';
  return `<div class="detail-section">
        <div class="detail-label">视频版本</div>
        <div class="detail-badge-list">${badges.join('')}</div>
      </div>`;
}
function getStaffValues(song, roleKey) {
  const summary = getStaffSummary(song);
  if (roleKey === 'illustrator') return summary.illustrators || [];
  if (roleKey === 'pvCreator') return summary.pvCreators || [];
  return summary.otherRoles?.[roleKey] || [];
}
function getAllStaffNames(song) {
  const summary = getStaffSummary(song);
  const names = new Set();
  (summary.allContributors || []).forEach(item => {
    if (item?.name) names.add(item.name);
    if (item?.roleRaw) names.add(item.roleRaw);
  });
  STAFF_ROLE_ORDER.forEach(roleKey => {
    getStaffValues(song, roleKey).forEach(name => names.add(name));
    if (getStaffValues(song, roleKey).length) names.add(STAFF_ROLE_CONFIG[roleKey].label);
  });
  return Array.from(names);
}
function getFilterSet(type) {
  if (type === 'tag') return activeFilters.tags;
  if (type === 'cat') return activeFilters.categories;
  if (type === 'vocal') return activeFilters.vocalTypes;
  if (type === 'version') return activeFilters.videoVersions;
  if (type === 'staff') return activeFilters.staffRoles;
  return null;
}
function renderLoadingNotice(html) {
  document.getElementById('song-list').innerHTML = `<div class="loading">${html}</div>`;
}
function getLocalServerViewerUrl() {
  const fileName = location.pathname.split('/').pop() || 'index.html';
  return `http://localhost:8000/${fileName}${location.search}${location.hash}`;
}
function handleFileProtocolAccess() {
  if (location.protocol !== 'file:') return false;
  const targetUrl = getLocalServerViewerUrl();
  renderLoadingNotice(
    `检测到你是直接打开本地 HTML 文件。<br>` +
    `浏览器会拦截对 JSON 的读取。<br><br>` +
    `请通过本地服务器访问：<a class="detail-link" href="${targetUrl}">${targetUrl}</a><br>` +
    `如果服务器已启动，页面将自动跳转；否则请先运行 <strong>start_server.bat</strong> 或 <strong>启动本地服务器.bat</strong>。`
  );
  setTimeout(() => {
    window.location.href = targetUrl;
  }, 1200);
  return true;
}
function buildStaffDetailSection(staff, label) {
  if (!staff) return '';
  const staffItems = [];
  const addRole = (roleKey, values) => {
    if (values && values.length) {
      staffItems.push(`<div class="detail-item"><span class="label">${STAFF_ROLE_CONFIG[roleKey].label}</span> <span class="value">${esc(values.join(' / '))}</span></div>`);
    }
  };
  addRole('illustrator', staff.illustrators);
  addRole('pvCreator', staff.pvCreators);
  if (staff.otherRoles) {
    STAFF_ROLE_ORDER.filter(k => k !== 'illustrator' && k !== 'pvCreator').forEach(roleKey => {
      addRole(roleKey, staff.otherRoles[roleKey]);
    });
  }
  if (!staffItems.length) return '';
  return `<div class="detail-section">
        <div class="detail-label">Staff${label ? ' · ' + esc(label) : ''}</div>
        <div class="detail-grid">${staffItems.join('')}</div>
      </div>`;
}

function buildPerVersionStaffSections(song) {
  const videos = song.dbVideos || [];
  const sections = [];
  const seenStaff = new Set();

  videos.forEach(v => {
    const staff = v.staff || {};
    const vTypeLabel = v.type === 'original_mv' ? '本家MV' : '官方2DMV';
    const vVerLabel = v.version?.label || getVersionLabel(`base:${v.version?.base}`) || '';
    const headerLabel = [vTypeLabel, vVerLabel].filter(Boolean).join(' · ');

    const hasStaff = !!(staff.illustrators?.length || staff.pvCreators?.length ||
      Object.values(staff.otherRoles || {}).some(arr => arr?.length));

    if (!hasStaff) return;

    const fingerprint = JSON.stringify({ i: staff.illustrators, p: staff.pvCreators, o: staff.otherRoles });
    if (seenStaff.has(fingerprint)) return;
    seenStaff.add(fingerprint);

    const html = buildStaffDetailSection(staff, headerLabel);
    if (html) sections.push(html);
  });

  if (!sections.length) {
    // Fallback to aggregated staffSummary
    const summary = getStaffSummary(song);
    const fakeStaff = { illustrators: summary.illustrators, pvCreators: summary.pvCreators, otherRoles: summary.otherRoles };
    const html = buildStaffDetailSection(fakeStaff, '');
    if (html) sections.push(html);
  }

  return sections.join('');
}
function formatStaffPreviewValue(values) {
  if (!values.length) return '';
  const visibleValues = values.slice(0, 2);
  const remainingCount = values.length - visibleValues.length;
  const suffix = remainingCount > 0 ? ` +${remainingCount}` : '';
  return `${visibleValues.join(' / ')}${suffix}`;
}
function buildStaffPreviewHtml(song) {
  const selectedRoleKeys = STAFF_ROLE_ORDER.filter(roleKey => activeFilters.staffRoles.has(roleKey) && getStaffValues(song, roleKey).length);
  if (!selectedRoleKeys.length) return '';

  const previewItems = selectedRoleKeys.map(roleKey => {
    const values = getStaffValues(song, roleKey);
    return `<span class="staff-preview-item">
        <span class="staff-preview-label">${esc(STAFF_ROLE_CONFIG[roleKey].label)}</span>
        <span class="staff-preview-value">${esc(formatStaffPreviewValue(values))}</span>
      </span>`;
  }).join('');

  return `<div class="song-staff-preview">${previewItems}</div>`;
}
function getVisibleStaffRoleKeys(songs) {
  const selectedRoleKeys = STAFF_ROLE_ORDER.filter(roleKey => activeFilters.staffRoles.has(roleKey));
  if (selectedRoleKeys.length) return selectedRoleKeys;
  return STAFF_ROLE_ORDER.filter(roleKey => songs.some(song => getStaffValues(song, roleKey).length));
}
function buildStaffStats(songs) {
  const roleKeys = getVisibleStaffRoleKeys(songs);
  return roleKeys.map(roleKey => {
    const counts = new Map();
    songs.forEach(song => {
      getStaffValues(song, roleKey).forEach(name => {
        counts.set(name, (counts.get(name) || 0) + 1);
      });
    });
    const topEntries = Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'ja'))
      .slice(0, 8);
    return {
      roleKey,
      roleLabel: STAFF_ROLE_CONFIG[roleKey].label,
      uniqueCount: counts.size,
      topEntries,
    };
  });
}
function renderStaffStats(songs) {
  const subtitle = document.getElementById('staff-stats-subtitle');
  const grid = document.getElementById('staff-stats-grid');
  const stats = buildStaffStats(songs);
  subtitle.textContent = `基于当前结果统计 · ${songs.length} 首歌曲`;

  if (!stats.length) {
    grid.innerHTML = '<div class="staff-stat-card"><div class="staff-stat-empty">当前结果里没有可统计的 Staff 字段。</div></div>';
    return;
  }

  grid.innerHTML = stats.map(stat => {
    const rows = stat.topEntries.length
      ? stat.topEntries.map(([name, count], index) => `
          <div class="staff-stat-row">
            <div class="staff-stat-rank">${index + 1}</div>
            <div class="staff-stat-name" title="${esc(name)}">${esc(name)}</div>
            <div class="staff-stat-count">${count}</div>
          </div>
        `).join('')
      : '<div class="staff-stat-empty">当前结果里没有这个字段。</div>';

    return `
      <div class="staff-stat-card${activeFilters.staffRoles.has(stat.roleKey) ? ' active-role' : ''}">
        <div class="staff-stat-card-header">
          <div class="staff-stat-role">${esc(stat.roleLabel)}</div>
          <div class="staff-stat-meta">${stat.uniqueCount} 人</div>
        </div>
        <div class="staff-stat-list">${rows}</div>
      </div>
    `;
  }).join('');
}
function mergeSupplementalSongData(baseSongs, databaseV2) {
  const supplementalMap = new Map();
  (databaseV2?.songs || []).forEach(song => {
    supplementalMap.set(song.title, {
      staffSummary: song.staffSummary || createEmptyStaffSummary(),
      videoVersionSummary: song.videoVersionSummary || createEmptyVideoVersionSummary(),
      classification: song.classification || null,
      dates: song.dates || null,
      gameData: song.gameData || null,
      performerSummary: song.performerSummary || null,
      videos: song.videos || [],
      creators: song.creators || null,
      sekaiMusicId: song.sekaiMusicId || null,
    });
  });
  return baseSongs.map(song => {
    const extra = supplementalMap.get(song.title) || {};
    return {
      ...song,
      staffSummary: extra.staffSummary || createEmptyStaffSummary(),
      videoVersionSummary: extra.videoVersionSummary || createEmptyVideoVersionSummary(),
      classification: extra.classification || null,
      dates: extra.dates || null,
      gameData: extra.gameData || null,
      performerSummary: extra.performerSummary || null,
      dbVideos: extra.videos || [],
      dbCreators: extra.creators || null,
      sekaiMusicId: extra.sekaiMusicId || null,
    };
  });
}

function renderFilters() {
  const tagCounts = {}, catCounts = {}, vocalCounts = {}, versionCounts = {}, staffCounts = {};
  allSongs.forEach(s => {
    getDisplayTags(s.tags).forEach(t => tagCounts[t] = (tagCounts[t] || 0) + 1);
    (s.categories || []).forEach(c => catCounts[c] = (catCounts[c] || 0) + 1);
    (s.vocals || []).forEach(v => vocalCounts[v.musicVocalType] = (vocalCounts[v.musicVocalType] || 0) + 1);
    getSongVersionFilterKeys(s).forEach(key => versionCounts[key] = (versionCounts[key] || 0) + 1);
    STAFF_ROLE_ORDER.forEach(roleKey => {
      if (getStaffValues(s, roleKey).length) {
        staffCounts[roleKey] = (staffCounts[roleKey] || 0) + 1;
      }
    });
  });

  const mkFilter = (container, items, counts, labels, type, colorMap) => {
    document.getElementById(container).innerHTML = items.filter(k => counts[k]).map(k => {
      const label = labels[k]?.label || labels[k] || k;
      const color = colorMap?.[k];
      const dot = color ? `<span class="filter-dot" style="background:${color}"></span>` : '';
      const activeSet = getFilterSet(type);
      const checked = activeSet?.has(k);
      return `<label class="filter-item${checked ? ' active' : ''}" data-filter="${type}" data-value="${k}">
        <input type="checkbox"${checked ? ' checked' : ''}>${dot}${label}<span class="filter-count">${counts[k]}</span></label>`;
    }).join('');
  };

  mkFilter('tag-filters',
    ['light_music_club', 'idol', 'street', 'theme_park', 'school_refusal', 'vocaloid', 'other'],
    tagCounts, TAG_CONFIG, 'tag', Object.fromEntries(Object.entries(TAG_CONFIG).map(([k, v]) => [k, v.color])));
  mkFilter('cat-filters', ['mv', 'mv_2d', 'image', 'original'], catCounts, CAT_LABELS, 'cat', null);
  mkFilter('vocal-filters',
    ['original_song', 'sekai', 'another_vocal', 'virtual_singer', 'instrumental', 'april_fool_2022', 'streaming_live'],
    vocalCounts, VOCAL_LABELS, 'vocal', null);
  mkFilter('version-filters', VIDEO_VERSION_ORDER, versionCounts, VIDEO_VERSION_CONFIG, 'version', null);
  mkFilter('staff-filters', STAFF_ROLE_ORDER, staffCounts, STAFF_ROLE_CONFIG, 'staff', null);

  document.querySelectorAll('[data-filter]').forEach(el => {
    el.addEventListener('change', () => {
      const { filter: type, value } = el.dataset;
      const checked = el.querySelector('input').checked;
      const set = getFilterSet(type);
      if (!set) return;
      checked ? set.add(value) : set.delete(value);
      el.classList.toggle('active', checked);
      applyFilters();
    });
  });
}

// Build a lookup map for quick access by id
let songMap = {};

function buildDetailHtml(s) {
  const c = s.dbCreators || s.creators || {};
  const cls = s.classification || {};
  const game = s.gameData || {};
  const dates = s.dates || {};
  const performers = s.performerSummary?.performers || [];
  const videos = s.dbVideos || [];

  // --- 创作者信息 ---
  const creatorRows = [];
  if (c.lyricist) creatorRows.push(`<div class="detail-item"><span class="label">作词</span> <span class="value">${esc(c.lyricist)}</span></div>`);
  if (c.composer) creatorRows.push(`<div class="detail-item"><span class="label">作曲</span> <span class="value">${esc(c.composer)}</span></div>`);
  if (c.arranger) creatorRows.push(`<div class="detail-item"><span class="label">编曲</span> <span class="value">${esc(c.arranger)}</span></div>`);
  if (c.creatorArtistName) creatorRows.push(`<div class="detail-item"><span class="label">艺术家</span> <span class="value">${esc(c.creatorArtistName)}</span></div>`);

  // --- 时间 ---
  const timeRows = [];
  timeRows.push(`<div class="detail-item"><span class="label">实装时间</span> <span class="value">${formatDate(s.publishedAt)}</span></div>`);
  if (dates.sekaiReleaseDate) timeRows.push(`<div class="detail-item"><span class="label">SEKAI 发布</span> <span class="value">${esc(dates.sekaiReleaseDate)}</span></div>`);
  if (dates.youtubeUploadDate) timeRows.push(`<div class="detail-item"><span class="label">YouTube 上传</span> <span class="value">${esc(dates.youtubeUploadDate)}</span></div>`);
  if (s.releasedAt) timeRows.push(`<div class="detail-item"><span class="label">原曲发布</span> <span class="value">${formatDate(s.releasedAt)}</span></div>`);

  // --- 游戏信息 ---
  const gameRows = [];
  if (game.bpm) gameRows.push(`<div class="detail-item"><span class="label">BPM</span> <span class="value">${esc(String(game.bpm))}</span></div>`);
  if (game.duration) gameRows.push(`<div class="detail-item"><span class="label">时长</span> <span class="value">${formatDuration(game.duration)}</span></div>`);
  if (s.sekaiMusicId) gameRows.push(`<div class="detail-item"><span class="label">游戏ID</span> <span class="value">#${esc(String(s.sekaiMusicId))}</span></div>`);
  if (game.publishedAt) gameRows.push(`<div class="detail-item"><span class="label">游戏收录</span> <span class="value">${esc(String(game.publishedAt))}</span></div>`);

  // 难度
  const diff = game.difficulty || {};
  const diffLabels = { easy: 'EASY', normal: 'NORMAL', hard: 'HARD', expert: 'EXPERT', master: 'MASTER' };
  const diffBadges = Object.entries(diffLabels).filter(([k]) => diff[k] != null).map(([k, label]) =>
    `<span class="diff-badge diff-${k}">${label} ${diff[k]}</span>`
  ).join('');

  // --- 分类 ---
  const clsRows = [];
  if (cls.units && cls.units.length) clsRows.push(`<div class="detail-item"><span class="label">组合</span> <span class="value">${esc(cls.units.join(' / '))}</span></div>`);
  if (cls.virtualSingers && cls.virtualSingers.length) clsRows.push(`<div class="detail-item"><span class="label">虚拟歌手</span> <span class="value">${esc(cls.virtualSingers.join(' / '))}</span></div>`);
  if (cls.mvType) clsRows.push(`<div class="detail-item"><span class="label">MV 类型</span> <span class="value">${esc(cls.mvType)}</span></div>`);
  if (cls.category) clsRows.push(`<div class="detail-item"><span class="label">分类</span> <span class="value">${esc(cls.category)}</span></div>`);

  // --- 视频列表 ---
  function buildVideoItems(vids) {
    if (!vids.length) return '';
    return `<div class="detail-section">
      <div class="detail-label">收录视频 (${vids.length})</div>
      <div style="display:flex;flex-direction:column;gap:8px">${vids.map(v => {
        const vTypeLabel = v.type === 'original_mv' ? '本家MV' : '官方2DMV';
        const vTypeClass = v.type === 'original_mv' ? 'vt-original' : 'vt-official';
        const vVerLabel = v.version?.label || '';
        const vStaff = v.staff || {};
        const vContributors = vStaff.allContributors || [];
        const vStaffSummary = vContributors.slice(0, 4).map(c =>
          `<span class="staff-tag">${esc(c.roleRaw || c.role)}: ${esc(c.name)}</span>`
        ).join('');
        return `<div class="db-video-item">
          <div class="db-video-header">
            <span class="db-video-type-badge ${vTypeClass}">${vTypeLabel}</span>
            ${vVerLabel ? `<span class="db-video-version">${esc(vVerLabel)}</span>` : ''}
            <a class="db-video-link" href="${esc(v.url)}" target="_blank" rel="noopener noreferrer">
              <span class="db-video-title">${esc(v.title)}</span>
            </a>
          </div>
          <div class="db-video-meta">
            <span>📺 ${esc(v.channelTitle || '-')}</span>
            <span>👁 ${formatNumber(v.viewCount)}</span>
            <span>👍 ${formatNumber(v.likeCount)}</span>
            <span>📅 ${esc((v.uploadDate || '').slice(0, 10))}</span>
          </div>
          ${vStaffSummary ? `<div class="db-video-staff">${vStaffSummary}</div>` : ''}
        </div>`;
      }).join('')}</div>
    </div>`;
  }

  // --- 组装 ---
  const sections = [];

  if (creatorRows.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">创作者信息</div><div class="detail-grid">${creatorRows.join('')}</div></div>`);
  }

  if (gameRows.length || diffBadges) {
    sections.push(`<div class="detail-section"><div class="detail-label">游戏信息</div><div class="detail-grid">${gameRows.join('')}</div>${diffBadges ? `<div class="difficulty-badges" style="margin-top:8px">${diffBadges}</div>` : ''}</div>`);
  }

  if (clsRows.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">分类信息</div><div class="detail-grid">${clsRows.join('')}</div></div>`);
  }

  if (performers.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">演出者</div><div class="detail-item"><span class="value">${esc(performers.join(' / '))}</span></div></div>`);
  }

  sections.push(`<div class="detail-section"><div class="detail-label">时间</div><div class="detail-grid">${timeRows.join('')}</div></div>`);

  // --- 视频链接 ---
  const allVideoLinks = [];
  const linkedUrls = new Set();
  if (s.originalVideoLink) {
    allVideoLinks.push({ type: 'original', label: '原曲链接', title: s.title, url: s.originalVideoLink });
    linkedUrls.add(s.originalVideoLink);
  }
  videos.forEach(v => {
    const vTypeLabel = v.type === 'original_mv' ? '本家MV' : '官方2DMV';
    const vVerLabel = v.version?.label || getVersionLabel(`base:${v.version?.base}`) || '';
    const label = [vTypeLabel, vVerLabel].filter(Boolean).join(' · ');
    if (!linkedUrls.has(v.url)) {
      allVideoLinks.push({ type: v.type, label, title: v.title, url: v.url });
      linkedUrls.add(v.url);
    }
  });
  if (allVideoLinks.length) {
    sections.push(`<div class="detail-section">
      <div class="detail-label">视频链接 (${allVideoLinks.length})</div>
      <div style="display:flex;flex-direction:column;gap:6px">${allVideoLinks.map(vl => {
        const typeClass = vl.type === 'original_mv' ? 'vt-original' : vl.type === 'original' ? 'vt-original' : 'vt-official';
        return `<div class="db-video-item" style="padding:8px 14px">
          <div class="db-video-header">
            <span class="db-video-type-badge ${typeClass}">${esc(vl.label)}</span>
            <a class="detail-link" href="${esc(vl.url)}" target="_blank" rel="noopener noreferrer">${esc(vl.title)}</a>
          </div>
        </div>`;
      }).join('')}</div>
    </div>`);
  }

  if (aliasMap[s.id] && aliasMap[s.id].length > 0) {
    sections.push(`<div class="detail-section"><div class="detail-label">别称</div><div style="display:flex;flex-wrap:wrap;gap:4px">${aliasMap[s.id].map(a => `<span style="padding:2px 8px;border-radius:10px;font-size:11px;background:rgba(155,109,255,0.15);color:#9b6dff">${esc(a)}</span>`).join('')}</div></div>`);
  }

  sections.push(buildVersionDetailSection(s));
  sections.push(buildPerVersionStaffSections(s));

  sections.push(`<div class="detail-section"><div class="detail-label">歌声版本 (${(s.vocals || []).length})</div><div class="vocal-list">${(s.vocals || []).map(v => {
    const chars = formatVocalCharacterNames(v);
    return `<div class="vocal-item"><span class="vocal-type-badge vt-${v.musicVocalType}">${VOCAL_LABELS[v.musicVocalType] || v.musicVocalType}</span><span class="vocal-caption">${esc(v.caption)}</span><span class="vocal-chars">${chars || '(无角色)'}</span><span class="vocal-num">#${v.id}</span></div>`;
  }).join('')}</div></div>`);

  sections.push(buildVideoItems(videos));

  return `<div class="song-detail show" id="detail-${s.id}">${sections.filter(Boolean).join('')}</div>`;
}

function buildRowHtml(s) {
  const tags = getDisplayTags(s.tags);
  const tagsHtml = tags.map(t => `<span class="tag tag-${TAG_CONFIG[t] ? t : 'other'}">${TAG_CONFIG[t]?.label || t}</span>`).join('');
  const catsHtml = (s.categories || []).map(c => `<span class="cat-badge cat-${c}">${CAT_LABELS[c] || c}</span>`).join('');
  const versionPreviewHtml = buildVersionPreviewHtml(s);
  const staffPreviewHtml = buildStaffPreviewHtml(s);
  return `<div class="song-row" data-id="${s.id}">
    <span class="song-id">#${s.id}</span>
    <div class="song-title-col">
      <div class="song-title">${esc(s.title)}</div>
      <div class="song-creator">${esc(s.creators?.creatorArtistName || s.creators?.composer || '-')}</div>
      ${versionPreviewHtml}
      ${staffPreviewHtml}
    </div>
    <div class="song-tags">${tagsHtml}</div>
    <div class="song-categories">${catsHtml}</div>
    <div class="song-date">${formatDate(s.publishedAt)}</div>
    <button class="expand-arrow" type="button" aria-expanded="false" aria-label="展开歌曲 ${esc(s.title)} 的详情">▶</button>
  </div>`;
}

function renderSongList() {
  const container = document.getElementById('song-list');
  if (!filteredSongs.length) { container.innerHTML = '<div class="loading">没有找到匹配的歌曲</div>'; updateLoadMore(); return; }

  // Only render first page of rows
  const pageItems = filteredSongs.slice(0, visibleCount);
  container.innerHTML = pageItems.map(buildRowHtml).join('');
  updateLoadMore();
  bindListClick(container);
}

function loadMore() {
  const container = document.getElementById('song-list');
  const from = visibleCount;
  visibleCount = Math.min(visibleCount + PAGE_SIZE, filteredSongs.length);
  const newItems = filteredSongs.slice(from, visibleCount);
  container.insertAdjacentHTML('beforeend', newItems.map(buildRowHtml).join(''));
  updateLoadMore();
}

function updateLoadMore() {
  const bar = document.getElementById('load-more-bar');
  const btn = document.getElementById('load-more-btn');
  if (visibleCount < filteredSongs.length) {
    bar.style.display = '';
    btn.textContent = `加载更多 (${visibleCount}/${filteredSongs.length})`;
  } else {
    bar.style.display = 'none';
  }
}

function toggleSongRow(row, container) {
    const id = parseInt(row.dataset.id);

    if (expandedId === id) {
      expandedId = null;
      row.classList.remove('expanded');
      row.querySelector('.expand-arrow')?.setAttribute('aria-expanded', 'false');
      const detail = document.getElementById(`detail-${id}`);
      if (detail) detail.remove();
    } else {
      if (expandedId !== null) {
        const prevRow = container.querySelector(`.song-row[data-id="${expandedId}"]`);
        if (prevRow) {
          prevRow.classList.remove('expanded');
          prevRow.querySelector('.expand-arrow')?.setAttribute('aria-expanded', 'false');
        }
        const prevDetail = document.getElementById(`detail-${expandedId}`);
        if (prevDetail) prevDetail.remove();
      }
      expandedId = id;
      row.classList.add('expanded');
      row.querySelector('.expand-arrow')?.setAttribute('aria-expanded', 'true');
      const s = songMap[id];
      if (s) row.insertAdjacentHTML('afterend', buildDetailHtml(s));
    }
}

function bindListClick(container) {
  container.onclick = (e) => {
    if (e.target.closest('a')) return;
    const row = e.target.closest('.song-row');
    if (row) toggleSongRow(row, container);
  };
  container.onkeydown = (e) => {
    if ((e.key !== 'Enter' && e.key !== ' ') || !e.target.closest('.expand-arrow')) return;
    const row = e.target.closest('.song-row');
    if (!row) return;
    e.preventDefault();
    toggleSongRow(row, container);
  };
}

function clearAllFilters() {
  Object.values(activeFilters).forEach(set => set.clear());
  renderFilters();
  applyFilters();
}

function updateSortUi() {
  document.querySelectorAll('.sort-indicator').forEach(indicator => indicator.textContent = '');
  document.querySelectorAll('.list-header [role="columnheader"]').forEach(header => header.removeAttribute('aria-sort'));
  const activeButton = document.querySelector(`.sort-button[data-sort="${sortField}"]`);
  const indicator = document.getElementById(`sort-${sortField}`);
  if (indicator) indicator.textContent = sortAsc ? '▲' : '▼';
  activeButton?.closest('[role="columnheader"]')?.setAttribute('aria-sort', sortAsc ? 'ascending' : 'descending');
}

function updateFilterSummary(q) {
  const summary = document.getElementById('filter-summary');
  const labels = [];
  if (q) labels.push(`搜索：${q}`);
  Object.values(activeFilters).forEach(values => {
    values.forEach(value => {
      const label = TAG_CONFIG[value]?.label || CAT_LABELS[value] || VOCAL_LABELS[value]
        || VIDEO_VERSION_CONFIG[value]?.label || STAFF_ROLE_CONFIG[value]?.label || value;
      labels.push(label);
    });
  });
  summary.innerHTML = labels.length
    ? `<strong>当前条件</strong>${labels.map(label => `<span class="filter-chip">${esc(label)}</span>`).join('')}`
    : '';
  summary.classList.toggle('visible', labels.length > 0);
  document.getElementById('clear-search-btn').disabled = !q;
}

function updateBackToTopButton() {
  const btn = document.getElementById('back-to-top-btn');
  if (!btn) return;
  btn.classList.toggle('visible', window.scrollY > 320);
}

function bindBackToTopButton() {
  const btn = document.getElementById('back-to-top-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  window.addEventListener('scroll', updateBackToTopButton, { passive: true });
  updateBackToTopButton();
}

function applyFilters({ syncUrl = true } = {}) {
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  updateFilterSummary(q);
  filteredSongs = allSongs.filter(s => {
    if (q) {
      const fields = [
        s.title,
        s.creators?.creatorArtistName,
        s.creators?.lyricist,
        s.creators?.composer,
        ...getAllStaffNames(s),
        ...getSongVersionLabels(s),
        ...getSongVersionSummary(s).bases,
        ...getSongVersionSummary(s).special,
      ].map(f => (f || '').toLowerCase());
      const songAliases = aliasMap[s.id] || [];
      if (!fields.some(f => f.includes(q)) && !songAliases.some(a => a.toLowerCase().includes(q))) return false;
    }
    if (activeFilters.tags.size && !getDisplayTags(s.tags).some(t => activeFilters.tags.has(t))) return false;
    if (activeFilters.categories.size && !(s.categories || []).some(c => activeFilters.categories.has(c))) return false;
    if (activeFilters.vocalTypes.size && !(s.vocals || []).some(v => activeFilters.vocalTypes.has(v.musicVocalType))) return false;
    if (activeFilters.videoVersions.size) {
      const versionKeys = new Set(getSongVersionFilterKeys(s));
      if (![...activeFilters.videoVersions].every(key => versionKeys.has(key))) return false;
    }
    if (activeFilters.staffRoles.size && !STAFF_ROLE_ORDER.some(roleKey => activeFilters.staffRoles.has(roleKey) && getStaffValues(s, roleKey).length)) return false;
    return true;
  });
  filteredSongs.sort((a, b) => {
    let va = a[sortField], vb = b[sortField];
    if (sortField === 'title') { va = (va || '').toLowerCase(); vb = (vb || '').toLowerCase(); }
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });
  document.getElementById('stat-filtered').textContent = filteredSongs.length;
  document.getElementById('results-info').textContent = `显示 ${filteredSongs.length} / ${allSongs.length} 首歌曲`;
  expandedId = null;
  visibleCount = PAGE_SIZE;
  renderStaffStats(filteredSongs);
  renderSongList();
  viewerDrawer?.update();
  if (syncUrl) viewerUrlState?.sync();
}

async function init() {
  if (handleFileProtocolAccess()) return;
  try {
    const [resp, databaseResp, gameCharactersResp, outsideCharactersResp] = await Promise.all([
      fetch('output/combined_music_data.json', { cache: 'no-store' }),
      fetch('output/database_v2.json', { cache: 'no-store' }).catch(() => null),
      fetch('sekai-master-db-diff-main/gameCharacters.json', { cache: 'no-store' }).catch(() => null),
      fetch('sekai-master-db-diff-main/outsideCharacters.json', { cache: 'no-store' }).catch(() => null),
    ]);
    const baseSongs = await resp.json();
    let databaseV2 = null;
    let gameCharacters = [];
    let outsideCharacters = [];
    if (databaseResp && databaseResp.ok) {
      databaseV2 = await databaseResp.json();
    }
    if (gameCharactersResp && gameCharactersResp.ok) {
      gameCharacters = await gameCharactersResp.json();
    }
    if (outsideCharactersResp && outsideCharactersResp.ok) {
      outsideCharacters = await outsideCharactersResp.json();
    }
    characterNameMap = buildCharacterNameLookup(gameCharacters, outsideCharacters);
    allSongs = mergeSupplementalSongData(baseSongs, databaseV2);
    // Update notice date from response header or fallback to today
    const lastMod = databaseResp?.headers?.get('Last-Modified') || resp.headers.get('Last-Modified');
    const updateDate = lastMod ? new Date(lastMod) : new Date();
    document.getElementById('notice-date').textContent =
      `最后更新：${updateDate.getFullYear()}-${String(updateDate.getMonth() + 1).padStart(2, '0')}-${String(updateDate.getDate()).padStart(2, '0')}`;
  } catch (e) {
    renderLoadingNotice(`加载失败：${e.message}<br>请确保 output 目录中的 JSON 文件存在，并通过 HTTP 服务器访问当前页面。`);
    return;
  }
  // Load alias data
  try {
    const aliasResp = await fetch('output/aliases.json', { cache: 'no-store' });
    const aliasData = await aliasResp.json();
    Object.entries(aliasData).forEach(([id, aliasList]) => {
      aliasMap[parseInt(id)] = Array.isArray(aliasList) ? aliasList : [];
    });
  } catch(e) { /* aliases.json not found, skip */ }
  document.getElementById('stat-total').textContent = allSongs.length;
  allSongs.forEach(s => songMap[s.id] = s);
  renderFilters();
  viewerDrawer = ViewerControls.createFilterDrawer();
  viewerUrlState = ViewerControls.createUrlState({
    groups: [
      { param: 'tag', filterType: 'tag', set: activeFilters.tags },
      { param: 'cat', filterType: 'cat', set: activeFilters.categories },
      { param: 'vocal', filterType: 'vocal', set: activeFilters.vocalTypes },
      { param: 'version', filterType: 'version', set: activeFilters.videoVersions },
      { param: 'staff', filterType: 'staff', set: activeFilters.staffRoles },
    ],
    defaultSortField: 'id',
    defaultSortAsc: true,
    allowedSortFields: ['id', 'title', 'publishedAt'],
    getSort: () => ({ field: sortField, asc: sortAsc }),
    setSort: sort => {
      sortField = sort.field;
      sortAsc = sort.asc;
    },
    onRestore: () => {
      renderFilters();
      updateSortUi();
      applyFilters({ syncUrl: false });
    },
  });
  viewerUrlState.restore();

  document.getElementById('load-more-btn').addEventListener('click', loadMore);

  let timer;
  document.getElementById('search-input').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(applyFilters, 200); });
  document.getElementById('clear-search-btn').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    applyFilters();
    document.getElementById('search-input').focus();
  });
  document.getElementById('clear-filters-btn').addEventListener('click', clearAllFilters);

  document.querySelectorAll('.sort-button[data-sort]').forEach(el => {
    el.addEventListener('click', () => {
      const f = el.dataset.sort;
      if (sortField === f) sortAsc = !sortAsc; else { sortField = f; sortAsc = true; }
      updateSortUi();
      applyFilters();
    });
  });

  bindBackToTopButton();
}
init();
