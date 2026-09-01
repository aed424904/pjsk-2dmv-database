let allVideos = [];
let filteredVideos = [];
let activeFilters = {
  tags: new Set(),
  types: new Set(),
  versions: new Set(),
  channels: new Set(),
};
let sortField = 'uploadDate';
let sortAsc = false;
let expandedId = null;
const PAGE_SIZE = 50;
let visibleCount = PAGE_SIZE;
let songMap = {};
let unmatchedVideoCount = 0;
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

const VIDEO_TYPE_CONFIG = {
  official_2dmv: { label: '官方 2DMV', color: 'var(--accent-blue)' },
  original_mv: { label: '本家 MV', color: 'var(--accent-orange)' },
};

const VIDEO_VERSION_CONFIG = {
  'base:original': { label: '本家' },
  'base:sekai': { label: 'SEKAI ver' },
  'base:virtual_singer': { label: 'Virtual Singer ver' },
  'base:another_vocal': { label: 'Another Vocal' },
  'base:unknown': { label: '未分类' },
  'special:april_fool': { label: '愚人节版' },
};

const STAFF_ROLE_CONFIG = {
  illustrator: { label: '插画师' },
  pvCreator: { label: 'PV / 视频' },
  illustrationAnimation: { label: '插图动画' },
  lyricDesign: { label: '歌词设计' },
  animation: { label: '动画' },
  design: { label: '设计 / Logo' },
  cg3d: { label: '3DCG' },
  direction: { label: '监督 / 演出' },
  storyboard: { label: '分镜' },
  compositing: { label: '摄影 / 合成' },
  editing: { label: '剪辑' },
  production: { label: '制片 / 制作' },
  productionSupport: { label: '制作协力' },
  lyricist: { label: '作词' },
  composer: { label: '作曲' },
  arranger: { label: '编曲' },
  vocalist: { label: '演唱' },
  musician: { label: '乐器演奏' },
  mixing: { label: '混音' },
  mastering: { label: '母带' },
  vocalEdit: { label: 'Vocal Edit' },
  musicProduction: { label: '音乐制作' },
  unknown: { label: '待整理' },
};
const STAFF_ROLE_GROUPS = [
  { label: '视觉', roles: ['illustrator', 'pvCreator', 'illustrationAnimation', 'lyricDesign', 'design', 'cg3d'] },
  { label: '动画与后期', roles: ['direction', 'storyboard', 'animation', 'compositing', 'editing'] },
  { label: '制作', roles: ['production', 'productionSupport'] },
  { label: '音乐', roles: ['lyricist', 'composer', 'arranger', 'vocalist', 'musician', 'mixing', 'mastering', 'vocalEdit', 'musicProduction'] },
  { label: '待整理', roles: ['unknown'] },
];

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

function esc(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

function getDisplayTags(tags) { return (tags || []).filter(t => t !== 'all'); }

function getVersionLabel(version) {
  if (!version) return '';
  if (version.label) return version.label;
  const baseKey = `base:${version.base}`;
  if (VIDEO_VERSION_CONFIG[baseKey]) return VIDEO_VERSION_CONFIG[baseKey].label;
  const specialKey = `special:${(version.special || [])[0]}`;
  if (VIDEO_VERSION_CONFIG[specialKey]) return VIDEO_VERSION_CONFIG[specialKey].label;
  return version.base || '';
}

function getVersionKeys(version) {
  if (!version) return [];
  const keys = [];
  if (version.base) keys.push(`base:${version.base}`);
  if (version.special && version.special.length) {
    version.special.forEach(s => keys.push(`special:${s}`));
  }
  return keys;
}

function buildVideoDetailHtml(v) {
  const sections = [];

  // Basic info
  const infoRows = [];
  infoRows.push(`<div class="detail-item"><span class="label">所属歌曲</span> <span class="value">${esc(v.songTitle || '-')}</span></div>`);
  infoRows.push(`<div class="detail-item"><span class="label">视频类型</span> <span class="value">${esc(VIDEO_TYPE_CONFIG[v.type]?.label || v.type)}</span></div>`);
  const verLabel = getVersionLabel(v.version);
  if (verLabel) infoRows.push(`<div class="detail-item"><span class="label">版本</span> <span class="value">${esc(verLabel)}</span></div>`);
  infoRows.push(`<div class="detail-item"><span class="label">频道</span> <span class="value">${esc(v.channelTitle || '-')}</span></div>`);
  infoRows.push(`<div class="detail-item"><span class="label">上传时间</span> <span class="value">${esc((v.uploadDate || '').slice(0, 10))}</span></div>`);
  if (infoRows.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">基本信息</div><div class="detail-grid">${infoRows.join('')}</div></div>`);
  }

  // Stats
  const statRows = [];
  statRows.push(`<div class="detail-item"><span class="label">播放量</span> <span class="value">${formatNumber(v.viewCount)}</span></div>`);
  statRows.push(`<div class="detail-item"><span class="label">点赞</span> <span class="value">${formatNumber(v.likeCount)}</span></div>`);
  if (v.playlistPosition != null) statRows.push(`<div class="detail-item"><span class="label">播放列表位置</span> <span class="value">#${v.playlistPosition + 1}</span></div>`);
  if (statRows.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">数据</div><div class="detail-grid">${statRows.join('')}</div></div>`);
  }

  // Link
  sections.push(`<div class="detail-section"><div class="detail-label">链接</div><div class="detail-item"><a class="detail-link" href="${esc(v.url)}" target="_blank" rel="noopener noreferrer">${esc(v.url)}</a></div></div>`);

  // Staff
  const staff = v.staff || {};
  const allContributors = staff.allContributors || staff.contributors || [];
  const getStaffValues = roleKey => {
    if (roleKey === 'illustrator') return staff.illustrators || [];
    if (roleKey === 'pvCreator') return staff.pvCreators || [];
    return staff.otherRoles?.[roleKey] || [];
  };
  const staffGroups = STAFF_ROLE_GROUPS.map(group => {
    const roleItems = group.roles.map(roleKey => {
      const names = getStaffValues(roleKey);
      if (!names.length) return '';
      return `<div class="detail-item"><span class="label">${esc(STAFF_ROLE_CONFIG[roleKey].label)}</span> <span class="value">${esc(names.join(' / '))}</span></div>`;
    }).filter(Boolean);
    if (!roleItems.length) return '';
    return `<div class="staff-role-group"><div class="staff-role-group-label">${esc(group.label)}</div><div class="detail-grid">${roleItems.join('')}</div></div>`;
  }).filter(Boolean);
  if (staffGroups.length) {
    sections.push(`<div class="detail-section"><div class="detail-label">Staff</div><div class="staff-role-groups">${staffGroups.join('')}</div></div>`);
  }

  // All contributors detail
  if (allContributors.length) {
    const contributorTags = allContributors.map(c =>
      `<span class="staff-tag">${esc(c.roleRaw || c.role || '')}: ${esc(c.name || '')}</span>`
    ).join('');
    sections.push(`<div class="detail-section"><div class="detail-label">全部贡献者 (${allContributors.length})</div><div class="db-video-staff">${contributorTags}</div></div>`);
  }

  // Song context
  const song = songMap[v.songTitle];
  if (song) {
    const ctxRows = [];
    const tags = getDisplayTags(song.tags);
    if (tags.length) {
      ctxRows.push(`<div class="detail-item"><span class="label">标签</span> <span class="value"><div class="song-tags">${tags.map(t => `<span class="tag tag-${TAG_CONFIG[t] ? t : 'other'}">${TAG_CONFIG[t]?.label || t}</span>`).join('')}</div></span></div>`);
    }
    if (song.categories && song.categories.length) {
      ctxRows.push(`<div class="detail-item"><span class="label">MV 类型</span> <span class="value">${esc(song.categories.join(' / '))}</span></div>`);
    }
    if (song.creators) {
      const c = song.creators;
      if (c.creatorArtistName) ctxRows.push(`<div class="detail-item"><span class="label">艺术家</span> <span class="value">${esc(c.creatorArtistName)}</span></div>`);
      if (c.composer) ctxRows.push(`<div class="detail-item"><span class="label">作曲</span> <span class="value">${esc(c.composer)}</span></div>`);
    }
    if (ctxRows.length) {
      sections.push(`<div class="detail-section"><div class="detail-label">歌曲信息</div><div class="detail-grid">${ctxRows.join('')}</div></div>`);
    }
  }

  return `<div class="video-detail show" id="detail-${v._uid}">${sections.filter(Boolean).join('')}</div>`;
}

function buildVideoRowHtml(v) {
  const typeConfig = VIDEO_TYPE_CONFIG[v.type] || {};
  const typeLabel = typeConfig.label || v.type || '?';
  const typeClass = v.type === 'original_mv' ? 'vt-original' : 'vt-official';
  const verLabel = getVersionLabel(v.version);

  return `<div class="video-row" data-uid="${v._uid}" role="button" tabindex="0" aria-expanded="false" aria-label="展开视频 ${esc(v.title)} 的详情">
    <span class="video-type-col"><span class="video-type-badge ${typeClass}">${typeLabel}</span></span>
    <div class="video-title-col">
      <div class="video-title">${esc(v.title)}</div>
      <div class="video-song-name">${esc(v.songTitle || '-')}${v.isUnmatched ? ' · <span class="filter-chip">待关联</span>' : ''}</div>
    </div>
    <div class="video-meta">
      <span class="video-version-col" data-label="版本">${esc(verLabel || '-')}</span>
      <span class="video-channel-col" data-label="频道" title="${esc(v.channelTitle || '')}">${esc(v.channelTitle || '-')}</span>
      <span class="video-views-col" data-label="播放">${formatNumber(v.viewCount)}</span>
      <span class="video-date-col" data-label="日期">${formatDate(v.uploadDate)}</span>
    </div>
    <span class="expand-arrow">▶</span>
  </div>`;
}

function renderVideoList() {
  const container = document.getElementById('video-list');
  if (!filteredVideos.length) {
    container.innerHTML = '<div class="loading">没有找到匹配的视频</div>';
    updateLoadMore();
    return;
  }

  const pageItems = filteredVideos.slice(0, visibleCount);
  container.innerHTML = pageItems.map(buildVideoRowHtml).join('');
  updateLoadMore();
  bindListClick(container);
}

function loadMore() {
  const container = document.getElementById('video-list');
  const from = visibleCount;
  visibleCount = Math.min(visibleCount + PAGE_SIZE, filteredVideos.length);
  const newItems = filteredVideos.slice(from, visibleCount);
  container.insertAdjacentHTML('beforeend', newItems.map(buildVideoRowHtml).join(''));
  updateLoadMore();
}

function updateLoadMore() {
  const bar = document.getElementById('load-more-bar');
  const btn = document.getElementById('load-more-btn');
  if (visibleCount < filteredVideos.length) {
    bar.style.display = '';
    btn.textContent = `加载更多 (${visibleCount}/${filteredVideos.length})`;
  } else {
    bar.style.display = 'none';
  }
}

function toggleVideoRow(row, container) {
    const uid = row.dataset.uid;

    if (expandedId === uid) {
      expandedId = null;
      row.classList.remove('expanded');
      row.setAttribute('aria-expanded', 'false');
      const detail = document.getElementById(`detail-${uid}`);
      if (detail) detail.remove();
    } else {
      if (expandedId !== null) {
        const prevRow = container.querySelector(`.video-row[data-uid="${expandedId}"]`);
        if (prevRow) {
          prevRow.classList.remove('expanded');
          prevRow.setAttribute('aria-expanded', 'false');
        }
        const prevDetail = document.getElementById(`detail-${expandedId}`);
        if (prevDetail) prevDetail.remove();
      }
      expandedId = uid;
      row.classList.add('expanded');
      row.setAttribute('aria-expanded', 'true');
      const v = allVideos.find(x => x._uid === uid);
      if (v) row.insertAdjacentHTML('afterend', buildVideoDetailHtml(v));
    }
}

function bindListClick(container) {
  container.onclick = (e) => {
    const row = e.target.closest('.video-row');
    if (row) toggleVideoRow(row, container);
  };
  container.onkeydown = (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const row = e.target.closest('.video-row');
    if (!row) return;
    e.preventDefault();
    toggleVideoRow(row, container);
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
  Object.entries(activeFilters).forEach(([group, values]) => {
    values.forEach(value => {
      const label = TAG_CONFIG[value]?.label || VIDEO_TYPE_CONFIG[value]?.label || VIDEO_VERSION_CONFIG[value]?.label || value;
      labels.push(label);
    });
  });
  summary.innerHTML = labels.length
    ? `<strong>当前条件</strong>${labels.map(label => `<span class="filter-chip">${esc(label)}</span>`).join('')}`
    : '';
  summary.classList.toggle('visible', labels.length > 0);
  document.getElementById('clear-search-btn').disabled = !q;
}

function renderFilters() {
  const tagCounts = {}, typeCounts = {}, versionCounts = {}, channelCounts = {};
  allVideos.forEach(v => {
    getDisplayTags(v.songTags).forEach(t => tagCounts[t] = (tagCounts[t] || 0) + 1);
    typeCounts[v.type] = (typeCounts[v.type] || 0) + 1;
    getVersionKeys(v.version).forEach(key => {
      if (VIDEO_VERSION_CONFIG[key]) versionCounts[key] = (versionCounts[key] || 0) + 1;
    });
    if (v.channelTitle) channelCounts[v.channelTitle] = (channelCounts[v.channelTitle] || 0) + 1;
  });

  const mkFilter = (container, items, counts, labels, type, colorMap) => {
    document.getElementById(container).innerHTML = items.filter(k => counts[k]).map(k => {
      const label = labels[k]?.label || labels[k] || k;
      const color = colorMap?.[k];
      const dot = color ? `<span class="filter-dot" style="background:${color}"></span>` : '';
      const set = activeFilters[type];
      const checked = set?.has(k);
      return `<label class="filter-item${checked ? ' active' : ''}" data-filter="${type}" data-value="${k}">
        <input type="checkbox"${checked ? ' checked' : ''}>${dot}${label}<span class="filter-count">${counts[k]}</span></label>`;
    }).join('');
  };

  mkFilter('tag-filters',
    ['light_music_club', 'idol', 'street', 'theme_park', 'school_refusal', 'vocaloid', 'other'],
    tagCounts, TAG_CONFIG, 'tags', Object.fromEntries(Object.entries(TAG_CONFIG).map(([k, v]) => [k, v.color])));

  mkFilter('type-filters', ['official_2dmv', 'original_mv'], typeCounts, VIDEO_TYPE_CONFIG, 'types', null);

  mkFilter('version-filters',
    ['base:original', 'base:sekai', 'base:virtual_singer', 'base:another_vocal', 'base:unknown', 'special:april_fool'],
    versionCounts, VIDEO_VERSION_CONFIG, 'versions', null);

  // Channels - only show top 20
  const topChannels = Object.entries(channelCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([name]) => name);
  mkFilter('channel-filters', topChannels, channelCounts,
    Object.fromEntries(topChannels.map(n => [n, { label: n }])), 'channels', null);

  document.querySelectorAll('[data-filter]').forEach(el => {
    el.addEventListener('change', () => {
      const { filter: type, value } = el.dataset;
      const set = activeFilters[type];
      if (!set) return;
      const checked = el.querySelector('input').checked;
      checked ? set.add(value) : set.delete(value);
      el.classList.toggle('active', checked);
      applyFilters();
    });
  });
}

function applyFilters({ syncUrl = true } = {}) {
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  updateFilterSummary(q);
  filteredVideos = allVideos.filter(v => {
    if (q) {
      const staff = v.staff || {};
      const allContributors = staff.allContributors || staff.contributors || [];
      const staffNames = [
        ...(staff.illustrators || []),
        ...(staff.pvCreators || []),
        ...allContributors.map(c => c.name || ''),
        ...allContributors.map(c => c.roleRaw || ''),
      ];
      const fields = [
        v.title,
        v.songTitle,
        v.channelTitle,
        v.description || '',
        getVersionLabel(v.version),
        ...staffNames,
      ].map(f => (f || '').toLowerCase());
      if (!fields.some(f => f.includes(q))) return false;
    }
    if (activeFilters.tags.size && !getDisplayTags(v.songTags).some(t => activeFilters.tags.has(t))) return false;
    if (activeFilters.types.size && !activeFilters.types.has(v.type)) return false;
    if (activeFilters.versions.size) {
      const vKeys = new Set(getVersionKeys(v.version));
      if (![...activeFilters.versions].every(key => vKeys.has(key))) return false;
    }
    if (activeFilters.channels.size && !activeFilters.channels.has(v.channelTitle)) return false;
    return true;
  });

  filteredVideos.sort((a, b) => {
    let va = a[sortField], vb = b[sortField];
    if (sortField === 'title') { va = (va || '').toLowerCase(); vb = (vb || '').toLowerCase(); }
    if (sortField === 'version') { va = getVersionLabel(a.version); vb = getVersionLabel(b.version); }
    if (sortField === 'type') { va = a.type || ''; vb = b.type || ''; }
    if (va == null) va = '';
    if (vb == null) vb = '';
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });

  document.getElementById('stat-filtered').textContent = filteredVideos.length;
  document.getElementById('results-info').textContent =
    `显示 ${filteredVideos.length} / ${allVideos.length} 个视频 · 待关联 ${unmatchedVideoCount}`;
  expandedId = null;
  visibleCount = PAGE_SIZE;
  renderVideoList();
  viewerDrawer?.update();
  if (syncUrl) viewerUrlState?.sync();
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

function handleFileProtocolAccess() {
  if (location.protocol !== 'file:') return false;
  const targetUrl = 'http://localhost:8000/video_viewer.html';
  document.getElementById('video-list').innerHTML =
    `<div class="loading">
      检测到你是直接打开本地 HTML 文件。<br>
      浏览器会拦截对 JSON 的读取。<br><br>
      请通过本地服务器访问：<a class="detail-link" href="${targetUrl}">${targetUrl}</a><br>
      如果服务器已启动，页面将自动跳转；否则请先运行 <strong>start_server.bat</strong>。
    </div>`;
  setTimeout(() => { window.location.href = targetUrl; }, 1200);
  return true;
}

function normalizeSongTitle(value) {
  return String(value || '')
    .normalize('NFKC')
    .toLocaleLowerCase('ja')
    .replace(/[\s・･·:：!！?？'"“”‘’()（）\[\]【】「」『』\-‐‑‒–—―_/／\\]/g, '');
}

function buildFallbackSongContext(dbSong) {
  const unitTags = {
    'Leo/need': 'light_music_club',
    'MORE MORE JUMP!': 'idol',
    'Vivid BAD SQUAD': 'street',
    'ワンダショ': 'theme_park',
    'Wonderlands×Showtime': 'theme_park',
    '25時、ナイトコードで。': 'school_refusal',
    'Virtual Singer': 'vocaloid',
  };
  const tags = (dbSong.classification?.units || []).map(unit => unitTags[unit]).filter(Boolean);
  return {
    id: dbSong.sekaiMusicId || dbSong.id,
    title: dbSong.title,
    tags: tags.length ? tags : ['other'],
    categories: dbSong.classification?.mvType ? [dbSong.classification.mvType] : [],
    creators: dbSong.creators || null,
  };
}

async function init() {
  if (handleFileProtocolAccess()) return;

  try {
    const [baseResp, dbResp] = await Promise.all([
      fetch('output/combined_music_data.json', { cache: 'no-store' }),
      fetch('output/database_v2.json', { cache: 'no-store' }).catch(() => null),
    ]);
    const baseSongs = await baseResp.json();
    let databaseV2 = null;
    if (dbResp && dbResp.ok) databaseV2 = await dbResp.json();
    if (!databaseV2) throw new Error('database_v2.json 不可用，无法保证视频列表完整性');

    const baseById = new Map(baseSongs.map(song => [Number(song.id), song]));
    const baseByTitle = new Map();
    baseSongs.forEach(song => {
      const key = normalizeSongTitle(song.title);
      if (key && !baseByTitle.has(key)) baseByTitle.set(key, song);
      songMap[song.title] = song;
    });

    // database_v2 is the video source of truth. Base data only enriches rows.
    let uidCounter = 0;
    allVideos = [];
    unmatchedVideoCount = 0;

    (databaseV2?.songs || []).forEach(dbSong => {
      const matchedSong = baseById.get(Number(dbSong.sekaiMusicId)) || baseByTitle.get(normalizeSongTitle(dbSong.title));
      const song = matchedSong || buildFallbackSongContext(dbSong);
      songMap[dbSong.title] = song;
      (dbSong.videos || []).forEach(video => {
        if (!matchedSong) unmatchedVideoCount += 1;
        allVideos.push({
          ...video,
          _uid: String(uidCounter++),
          songId: song.id,
          songTitle: dbSong.title,
          songTags: song.tags || [],
          songCategories: song.categories || [],
          songCreators: song.creators || null,
          isUnmatched: !matchedSong,
        });
      });
    });

    document.getElementById('stat-total').textContent = allVideos.length;
    document.getElementById('stat-unmatched').textContent = unmatchedVideoCount;
    filteredVideos = [...allVideos];
    renderFilters();
    viewerDrawer = ViewerControls.createFilterDrawer();
    viewerUrlState = ViewerControls.createUrlState({
      groups: [
        { param: 'tag', filterType: 'tags', set: activeFilters.tags },
        { param: 'type', filterType: 'types', set: activeFilters.types },
        { param: 'version', filterType: 'versions', set: activeFilters.versions },
        { param: 'channel', filterType: 'channels', set: activeFilters.channels },
      ],
      defaultSortField: 'uploadDate',
      defaultSortAsc: false,
      allowedSortFields: ['type', 'title', 'version', 'channelTitle', 'viewCount', 'uploadDate'],
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
  } catch (e) {
    document.getElementById('video-list').innerHTML =
      `<div class="loading">加载失败：${e.message}<br>请确保 output 目录中的 JSON 文件存在，并通过 HTTP 服务器访问当前页面。</div>`;
    return;
  }

  document.getElementById('load-more-btn').addEventListener('click', loadMore);

  let timer;
  document.getElementById('search-input').addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(applyFilters, 200);
  });
  document.getElementById('clear-search-btn').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    applyFilters();
    document.getElementById('search-input').focus();
  });
  document.getElementById('clear-filters-btn').addEventListener('click', clearAllFilters);

  document.querySelectorAll('.sort-button[data-sort]').forEach(el => {
    el.addEventListener('click', () => {
      const f = el.dataset.sort;
      if (sortField === f) sortAsc = !sortAsc;
      else { sortField = f; sortAsc = (f === 'viewCount'); }
      updateSortUi();
      applyFilters();
    });
  });

  bindBackToTopButton();
}

init();
