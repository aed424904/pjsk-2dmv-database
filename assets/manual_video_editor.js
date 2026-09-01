/* ========== ManualVideoEditor Namespace ========== */
const ManualVideoEditor = (function() {
  const DEFAULT_CHANNEL_TITLE = 'プロジェクトセカイ カラフルステージ! feat. 初音ミク';
  const DEFAULT_CHANNEL_ID = 'UCdMGYXL38w6htx6Yf9YJa-w';
  const VERSION_BASE_OPTIONS = new Set(['original', 'sekai', 'virtual_singer', 'another_vocal', 'unknown']);

  let songCatalog = [];
  let draftVideos = [];
  let overrideDrafts = [];
  let performerReviewItems = [];
  let selectedSongTitle = '';
  let editingDraftId = null;
  let editingOverrideId = null;
  let currentOverrideContext = {};
  let songSearchQuery = '';
  let entrySearchQuery = '';
  let overrideSearchQuery = '';
  let reviewSearchQuery = '';

  function createClientId(prefix) {
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  }
  function createDraftId() { return createClientId('draft'); }
  function createOverrideDraftId() { return createClientId('override'); }
  function createReviewId() { return createClientId('review'); }

  function extractVideoId(value) {
    const input = String(value || '').trim();
    if (!input) return '';
    if (/^[A-Za-z0-9_-]{11}$/.test(input)) return input;
    const patterns = [
      /[?&]v=([A-Za-z0-9_-]{11})/,
      /youtu\.be\/([A-Za-z0-9_-]{11})/,
      /youtube\.com\/embed\/([A-Za-z0-9_-]{11})/,
      /youtube\.com\/shorts\/([A-Za-z0-9_-]{11})/,
    ];
    for (const p of patterns) {
      const m = input.match(p);
      if (m) return m[1];
    }
    return '';
  }

  function buildVideoUrl(videoId) {
    return videoId ? `https://www.youtube.com/watch?v=${videoId}` : '';
  }

  function buildThumbnailMap(videoId) {
    if (!videoId) return {};
    return {
      default: `https://i.ytimg.com/vi/${videoId}/default.jpg`,
      medium: `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`,
      high: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
      standard: `https://i.ytimg.com/vi/${videoId}/sddefault.jpg`,
      maxres: `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`,
    };
  }

  function normalizeVersionBase(value) {
    const vb = String(value || '').trim();
    return VERSION_BASE_OPTIONS.has(vb) ? vb : '';
  }

  function normalizeVersionSpecial(value) {
    if (Array.isArray(value)) return value.filter(item => item === 'april_fool');
    return value === 'april_fool' ? ['april_fool'] : [];
  }

  function normalizePerformers(value) {
    if (Array.isArray(value)) {
      return [...new Set(value.map(item => String(item || '').trim()).filter(Boolean))];
    }
    return [...new Set(
      String(value || '').split(/[\r\n,，、]+/).map(item => item.trim()).filter(Boolean)
    )];
  }

  function extractOverrideRows(payload) {
    if (Array.isArray(payload)) return payload;
    const raw = payload && typeof payload === 'object' && Object.prototype.hasOwnProperty.call(payload, 'videos')
      ? payload.videos : payload;
    if (Array.isArray(raw)) return raw;
    if (raw && typeof raw === 'object') {
      return Object.entries(raw)
        .filter(([key]) => key !== 'metadata')
        .map(([videoId, override]) => ({ videoId, ...(override || {}) }));
    }
    return [];
  }

  function normalizeDraftVideo(video) {
    const videoId = extractVideoId(video.videoId || video.url);
    const versionBase = normalizeVersionBase(video.versionBase || video.version?.base);
    const versionSpecial = normalizeVersionSpecial(video.versionSpecial || video.version?.special);
    return {
      draftId: video.draftId || createDraftId(),
      songTitle: String(video.songTitle || '').trim(),
      title: String(video.title || '').trim(),
      url: String(video.url || buildVideoUrl(videoId)).trim(),
      videoId,
      publishedAt: String(video.publishedAt || '').trim(),
      channelTitle: String(video.channelTitle || DEFAULT_CHANNEL_TITLE).trim(),
      channelId: String(video.channelId || DEFAULT_CHANNEL_ID).trim(),
      position: video.position === 0 || video.position ? String(video.position).trim() : '',
      versionBase,
      versionSpecial,
      description: String(video.description || '').trim(),
      notes: String(video.notes || '').trim(),
    };
  }

  function normalizeOverrideDraft(override) {
    const videoId = extractVideoId(override.videoId || override.url);
    const versionBase = normalizeVersionBase(override.versionBase || override.version?.base);
    const versionSpecial = normalizeVersionSpecial(override.versionSpecial || override.version?.special);
    return {
      draftId: override.draftId || createOverrideDraftId(),
      videoId,
      url: String(override.url || buildVideoUrl(videoId)).trim(),
      songTitle: String(override.songTitle || '').trim(),
      videoTitle: String(override.videoTitle || override.title || '').trim(),
      performers: normalizePerformers(override.performers || override.performersText || ''),
      versionBase,
      versionSpecial,
      notes: String(override.notes || '').trim(),
      sourceKey: String(override.sourceKey || '').trim(),
      sourceName: String(override.sourceName || '').trim(),
      confidence: String(override.confidence || '').trim(),
      matchedText: String(override.matchedText || '').trim(),
      descriptionPreview: String(override.descriptionPreview || '').trim(),
    };
  }

  function normalizeReviewItem(item) {
    const videoId = extractVideoId(item.videoId || item.url);
    return {
      reviewId: item.reviewId || createReviewId(),
      videoId,
      url: String(item.url || buildVideoUrl(videoId)).trim(),
      songTitle: String(item.songTitle || '').trim(),
      videoTitle: String(item.videoTitle || item.title || '').trim(),
      performers: normalizePerformers(item.performers || []),
      sourceKey: String(item.sourceKey || '').trim(),
      sourceName: String(item.sourceName || '').trim(),
      confidence: String(item.confidence || '').trim(),
      matchedText: String(item.matchedText || '').trim(),
      descriptionPreview: String(item.descriptionPreview || '').trim(),
    };
  }

  function serializeDraftVideos() {
    const videos = draftVideos.map(video => {
      const n = normalizeDraftVideo(video);
      const payload = {
        songTitle: n.songTitle,
        title: n.title,
        videoId: n.videoId,
        url: n.url || buildVideoUrl(n.videoId),
        description: n.description,
        channelTitle: n.channelTitle || DEFAULT_CHANNEL_TITLE,
        channelId: n.channelId || DEFAULT_CHANNEL_ID,
        publishedAt: n.publishedAt,
        thumbnails: buildThumbnailMap(n.videoId),
      };
      if (n.position !== '') payload.position = Number(n.position);
      if (n.versionBase || n.versionSpecial.length) {
        payload.version = { base: n.versionBase || 'unknown', special: n.versionSpecial };
      }
      if (n.notes) payload.notes = n.notes;
      return payload;
    });
    return {
      metadata: { updatedAt: new Date().toISOString(), totalVideos: videos.length, generatedBy: 'editor.html' },
      videos,
    };
  }

  function serializeOriginalVideoOverrides() {
    const videos = {};
    [...overrideDrafts]
      .map(normalizeOverrideDraft)
      .sort((a, b) => String(a.videoId || '').localeCompare(String(b.videoId || '')))
      .forEach(override => {
        if (!override.videoId) return;
        const payload = {};
        if (override.performers.length) payload.performers = override.performers;
        if (override.versionBase || override.versionSpecial.length) {
          payload.version = { base: override.versionBase || 'unknown', special: override.versionSpecial };
        }
        if (override.notes) payload.notes = override.notes;
        if (Object.keys(payload).length) videos[override.videoId] = payload;
      });
    return {
      metadata: { updatedAt: new Date().toISOString(), totalVideos: Object.keys(videos).length, generatedBy: 'editor.html' },
      videos,
    };
  }

  // Data loading
  async function loadSongCatalog() {
    const paths = ['output/combined_music_data.json', 'sekai viewer_json/musics.json'];
    for (const path of paths) {
      try {
        const response = await fetch(path);
        if (!response.ok) continue;
        const data = await response.json();
        songCatalog = (Array.isArray(data) ? data : data.songs || []).map(song => ({
          id: song.id,
          title: song.title,
          creator: song.creators?.creatorArtistName || song.pronunciation || '',
        }));
        document.getElementById('stat-catalog').textContent = songCatalog.length;
        return;
      } catch (e) { /* try next */ }
    }
    songCatalog = [];
    document.getElementById('stat-catalog').textContent = '0';
  }

  async function loadExistingDrafts() {
    try {
      const resp = await fetch('manual_data/manual_videos.json');
      if (!resp.ok) { draftVideos = []; return; }
      const payload = await resp.json();
      const rawVideos = Array.isArray(payload) ? payload : (payload?.videos || []);
      draftVideos = rawVideos.map(normalizeDraftVideo);
    } catch (e) { draftVideos = []; }
  }

  async function loadExistingOverrides() {
    try {
      const resp = await fetch('manual_data/original_video_overrides.json');
      if (!resp.ok) { overrideDrafts = []; return; }
      const payload = await resp.json();
      overrideDrafts = extractOverrideRows(payload).map(normalizeOverrideDraft);
    } catch (e) { overrideDrafts = []; }
  }

  async function loadPerformerReviewItems() {
    try {
      const resp = await fetch('output/original_mv_review.json');
      if (!resp.ok) { performerReviewItems = []; return; }
      const payload = await resp.json();
      performerReviewItems = (Array.isArray(payload) ? payload : []).map(normalizeReviewItem);
    } catch (e) { performerReviewItems = []; }
  }

  // Stats
  function updateStats() {
    document.getElementById('stat-videos').textContent = draftVideos.length;
    const songCount = new Set(draftVideos.map(v => v.songTitle).filter(Boolean)).size;
    document.getElementById('stat-songs').textContent = songCount;
    document.getElementById('stat-overrides').textContent = overrideDrafts.length;
    const overrideIds = new Set(overrideDrafts.map(item => item.videoId).filter(Boolean));
    const pending = performerReviewItems.filter(item => item.videoId && !overrideIds.has(item.videoId)).length;
    document.getElementById('stat-review').textContent = pending;
  }

  // Render helpers
  function renderSongHelperList() {
    const container = document.getElementById('song-helper-list');
    if (!container) return;
    const query = songSearchQuery.trim().toLowerCase();
    let filtered = songCatalog;
    if (query) {
      filtered = songCatalog.filter(s => {
        return [s.title, s.creator, String(s.id || '')].some(v => String(v || '').toLowerCase().includes(query));
      });
    }
    filtered = filtered.slice(0, 120);
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">没有匹配到曲目。<br>你也可以直接在右侧手填歌曲名。</div>';
      return;
    }
    container.innerHTML = filtered.map(song => `
      <div class="helper-item${selectedSongTitle === song.title ? ' active' : ''}" data-song-title="${esc(song.title)}">
        <div class="helper-title">${esc(song.title)}</div>
        <div class="helper-meta">
          <span class="helper-id">#${esc(song.id)}</span>
          ${song.creator ? ` · ${esc(song.creator)}` : ''}
        </div>
      </div>
    `).join('');
    container.querySelectorAll('.helper-item').forEach(item => {
      item.addEventListener('click', () => {
        selectedSongTitle = item.dataset.songTitle;
        document.getElementById('song-title').value = selectedSongTitle;
        renderSongHelperList();
        showToast(`已填入歌曲名：${selectedSongTitle}`);
      });
    });
  }

  function renderDraftList() {
    const container = document.getElementById('entry-list');
    if (!container) return;
    const query = entrySearchQuery.trim().toLowerCase();
    let filtered = draftVideos;
    if (query) {
      filtered = draftVideos.filter(v => {
        return [v.songTitle, v.title, v.videoId, v.publishedAt].some(x => String(x || '').toLowerCase().includes(query));
      });
    }
    filtered = [...filtered].sort((a, b) => String(b.publishedAt || '').localeCompare(String(a.publishedAt || '')));
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">当前没有符合条件的草稿视频。</div>';
      return;
    }
    container.innerHTML = filtered.map(video => `
      <div class="entry-card${editingDraftId === video.draftId ? ' active' : ''}" data-draft-id="${esc(video.draftId)}">
        <div class="entry-card-top">
          <div style="min-width:0">
            <div class="entry-title">${esc(video.songTitle || '未命名歌曲')}</div>
            <div class="entry-meta">${esc(video.title || '未填写视频标题')}</div>
          </div>
          <div class="entry-actions">
            <button class="action-link" type="button" data-action="edit">编辑</button>
            <button class="action-link delete" type="button" data-action="delete">删除</button>
          </div>
        </div>
        <div class="entry-badges">
          <span class="badge">${esc(video.videoId || '无 videoId')}</span>
          <span class="badge">${esc(video.publishedAt || '无发布时间')}</span>
          ${video.versionBase ? `<span class="badge">${esc(video.versionBase)}</span>` : ''}
          ${(video.versionSpecial || []).includes('april_fool') ? '<span class="badge">april_fool</span>' : ''}
          ${video.position !== '' ? `<span class="badge">position ${esc(video.position)}</span>` : ''}
        </div>
      </div>
    `).join('');
    container.querySelectorAll('.entry-card').forEach(card => {
      card.addEventListener('click', event => {
        const draftId = card.dataset.draftId;
        const action = event.target?.dataset?.action;
        if (action === 'delete') { event.stopPropagation(); deleteDraft(draftId); return; }
        editDraft(draftId);
      });
    });
  }

  function findOverrideDraftByVideoId(videoId) {
    return overrideDrafts.find(item => item.videoId === videoId);
  }

  function getReviewItemByVideoId(videoId) {
    return performerReviewItems.find(item => item.videoId === videoId);
  }

  function hydrateOverrideDraft(override) {
    const reviewItem = getReviewItemByVideoId(override.videoId || '');
    return normalizeOverrideDraft({
      ...(reviewItem || {}),
      ...(override || {}),
      performers: (override?.performers && override.performers.length) ? override.performers : (reviewItem?.performers || []),
    });
  }

  function buildOverrideContextHtml(override) {
    const lines = [];
    if (override.songTitle) lines.push(`<strong>参考歌曲：</strong>${esc(override.songTitle)}`);
    if (override.videoTitle) lines.push(`<strong>参考标题：</strong>${esc(override.videoTitle)}`);
    const metaParts = [];
    if (override.sourceName) metaParts.push(esc(override.sourceName));
    if (override.confidence) metaParts.push(`置信度 ${esc(override.confidence)}`);
    if (metaParts.length) lines.push(`<strong>来源：</strong>${metaParts.join(' · ')}`);
    if (override.matchedText) lines.push(`<strong>命中文本：</strong>${esc(override.matchedText)}`);
    if (override.descriptionPreview) lines.push(`<strong>描述预览：</strong>${esc(override.descriptionPreview)}`);
    if (!lines.length) return '可以从左侧"待复核原曲视频"点一条带入。当前表单只输出 `performers`、`version`、`notes` 到 `original_video_overrides.json`。';
    return lines.join('<br>');
  }

  function updateOverrideContext(override) {
    currentOverrideContext = {
      videoId: override.videoId || '',
      songTitle: override.songTitle || '',
      videoTitle: override.videoTitle || '',
      sourceKey: override.sourceKey || '',
      sourceName: override.sourceName || '',
      confidence: override.confidence || '',
      matchedText: override.matchedText || '',
      descriptionPreview: override.descriptionPreview || '',
    };
    const noteEl = document.getElementById('override-context-note');
    if (noteEl) noteEl.innerHTML = buildOverrideContextHtml({ ...currentOverrideContext });
  }

  function renderReviewList() {
    const container = document.getElementById('review-list');
    if (!container) return;
    const query = reviewSearchQuery.trim().toLowerCase();
    let filtered = performerReviewItems;
    if (query) {
      filtered = performerReviewItems.filter(item => {
        return [item.songTitle, item.videoTitle, item.videoId, item.descriptionPreview, item.matchedText]
          .some(v => String(v || '').toLowerCase().includes(query));
      });
    }
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">当前没有待复核 performer 条目。<br>后续刷新数据后，低置信度记录会出现在这里。</div>';
      return;
    }
    container.innerHTML = filtered.map(item => {
      const existing = findOverrideDraftByVideoId(item.videoId);
      const actionLabel = existing ? '编辑覆写' : '带入覆写';
      return `
        <div class="entry-card${existing && editingOverrideId === existing.draftId ? ' active' : ''}" data-review-id="${esc(item.reviewId)}">
          <div class="entry-card-top">
            <div style="min-width:0">
              <div class="entry-title">${esc(item.songTitle || item.videoTitle || item.videoId || '未命名条目')}</div>
              <div class="entry-meta">${esc(item.videoTitle || '未提供视频标题')}</div>
              ${item.descriptionPreview ? `<div class="entry-meta">${esc(item.descriptionPreview)}</div>` : ''}
            </div>
            <div class="entry-actions">
              <button class="action-link" type="button" data-action="apply">${actionLabel}</button>
            </div>
          </div>
          <div class="entry-badges">
            <span class="badge">${esc(item.videoId || '无 videoId')}</span>
            ${item.sourceName ? `<span class="badge">${esc(item.sourceName)}</span>` : ''}
            ${item.confidence ? `<span class="badge">${esc(item.confidence)}</span>` : ''}
            ${existing ? '<span class="badge">已覆写</span>' : ''}
          </div>
        </div>
      `;
    }).join('');
    container.querySelectorAll('.entry-card').forEach(card => {
      card.addEventListener('click', () => { startOverrideFromReview(card.dataset.reviewId); });
    });
  }

  function renderOverrideList() {
    const container = document.getElementById('override-entry-list');
    if (!container) return;
    const query = overrideSearchQuery.trim().toLowerCase();
    let filtered = overrideDrafts;
    if (query) {
      filtered = overrideDrafts.filter(item => {
        return [item.videoId, item.songTitle, item.videoTitle, item.performers.join(' '), item.notes]
          .some(v => String(v || '').toLowerCase().includes(query));
      });
    }
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">还没有覆写条目。左侧待复核列表或手动输入都可以建立一条。</div>';
      return;
    }
    container.innerHTML = filtered.map(item => `
      <div class="entry-card${editingOverrideId === item.draftId ? ' active' : ''}" data-override-id="${esc(item.draftId)}">
        <div class="entry-card-top">
          <div style="min-width:0">
            <div class="entry-title">${esc(item.songTitle || item.videoTitle || item.videoId || '未命名覆写')}</div>
            <div class="entry-meta">${esc(item.performers.length ? item.performers.join(' / ') : '未填写歌手')}</div>
            ${item.notes ? `<div class="entry-meta">${esc(item.notes)}</div>` : ''}
          </div>
          <div class="entry-actions">
            <button class="action-link" type="button" data-action="edit">编辑</button>
            <button class="action-link delete" type="button" data-action="delete">删除</button>
          </div>
        </div>
        <div class="entry-badges">
          <span class="badge">${esc(item.videoId || '无 videoId')}</span>
          ${item.versionBase ? `<span class="badge">${esc(item.versionBase)}</span>` : ''}
          ${item.versionSpecial.includes('april_fool') ? '<span class="badge">april_fool</span>' : ''}
          ${item.performers.length ? `<span class="badge">${esc(`${item.performers.length} 人`)}</span>` : ''}
        </div>
      </div>
    `).join('');
    container.querySelectorAll('.entry-card').forEach(card => {
      card.addEventListener('click', event => {
        const draftId = card.dataset.overrideId;
        const action = event.target?.dataset?.action;
        if (action === 'delete') { event.stopPropagation(); deleteOverride(draftId); return; }
        editOverride(draftId);
      });
    });
  }

  // Form mode labels
  function setFormModeLabel() {
    const el = document.getElementById('form-mode-label');
    const delBtn = document.getElementById('delete-current-btn');
    if (!el) return;
    if (editingDraftId) {
      el.textContent = '当前模式：编辑已有条目';
      if (delBtn) delBtn.disabled = false;
    } else {
      el.textContent = '当前模式：新增条目';
      if (delBtn) delBtn.disabled = true;
    }
  }

  function setOverrideFormModeLabel() {
    const el = document.getElementById('override-form-mode-label');
    const delBtn = document.getElementById('delete-current-override-btn');
    if (!el) return;
    if (editingOverrideId) {
      el.textContent = '当前模式：编辑已有覆写';
      if (delBtn) delBtn.disabled = false;
    } else {
      el.textContent = '当前模式：新增覆写';
      if (delBtn) delBtn.disabled = true;
    }
  }

  // Form write/read
  function writeForm(video) {
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
    setVal('song-title', video.songTitle || '');
    setVal('video-title', video.title || '');
    setVal('video-url', video.url || '');
    setVal('video-id', video.videoId || '');
    setVal('published-at', video.publishedAt || '');
    setVal('position', video.position || '');
    setVal('version-base', video.versionBase || '');
    const aprilEl = document.getElementById('version-special-april-fool');
    if (aprilEl) aprilEl.checked = (video.versionSpecial || []).includes('april_fool');
    setVal('channel-title', video.channelTitle || DEFAULT_CHANNEL_TITLE);
    setVal('channel-id', video.channelId || DEFAULT_CHANNEL_ID);
    setVal('description', video.description || '');
    setVal('notes', video.notes || '');
    selectedSongTitle = video.songTitle || '';
    renderSongHelperList();
    setFormModeLabel();
  }

  function readForm() {
    const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : ''; };
    const videoId = extractVideoId(getVal('video-id') || getVal('video-url'));
    const aprilEl = document.getElementById('version-special-april-fool');
    return normalizeDraftVideo({
      draftId: editingDraftId || createDraftId(),
      songTitle: getVal('song-title'),
      title: getVal('video-title'),
      url: getVal('video-url') || buildVideoUrl(videoId),
      videoId,
      publishedAt: getVal('published-at'),
      position: getVal('position'),
      versionBase: getVal('version-base'),
      versionSpecial: aprilEl && aprilEl.checked ? ['april_fool'] : [],
      channelTitle: getVal('channel-title'),
      channelId: getVal('channel-id'),
      description: getVal('description'),
      notes: getVal('notes'),
    });
  }

  function resetForm() {
    editingDraftId = null;
    writeForm({
      songTitle: selectedSongTitle || '',
      title: '', url: '', videoId: '', publishedAt: '', position: '',
      versionBase: '', versionSpecial: [],
      channelTitle: DEFAULT_CHANNEL_TITLE, channelId: DEFAULT_CHANNEL_ID,
      description: '', notes: '',
    });
    renderDraftList();
  }

  function writeOverrideForm(override) {
    const n = hydrateOverrideDraft(override || {});
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
    setVal('override-video-id', n.videoId || '');
    setVal('override-video-url', n.url || '');
    setVal('override-version-base', n.versionBase || '');
    const aprilEl = document.getElementById('override-version-special-april-fool');
    if (aprilEl) aprilEl.checked = n.versionSpecial.includes('april_fool');
    setVal('override-performers', n.performers.join('\n'));
    setVal('override-notes', n.notes || '');
    updateOverrideContext(n);
    setOverrideFormModeLabel();
  }

  function readOverrideForm() {
    const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : ''; };
    const videoId = extractVideoId(getVal('override-video-id') || getVal('override-video-url'));
    const aprilEl = document.getElementById('override-version-special-april-fool');
    return normalizeOverrideDraft({
      draftId: editingOverrideId || createOverrideDraftId(),
      videoId,
      url: getVal('override-video-url') || buildVideoUrl(videoId),
      performers: getVal('override-performers'),
      versionBase: getVal('override-version-base'),
      versionSpecial: aprilEl && aprilEl.checked ? ['april_fool'] : [],
      notes: getVal('override-notes'),
      ...(currentOverrideContext.videoId === videoId ? currentOverrideContext : {}),
    });
  }

  function resetOverrideForm() {
    editingOverrideId = null;
    currentOverrideContext = {};
    writeOverrideForm({ videoId: '', url: '', performers: [], versionBase: '', versionSpecial: [], notes: '' });
    renderOverrideList();
    renderReviewList();
  }

  // Validation
  function validateDraft(video) {
    const errors = [];
    if (!video.songTitle) errors.push('歌曲名不能为空');
    if (!video.title) errors.push('视频标题不能为空');
    if (!video.videoId) errors.push('请提供有效的 YouTube 链接或 videoId');
    if (!video.publishedAt) errors.push('发布时间不能为空');
    return errors;
  }

  function validateOverrideDraft(override) {
    const errors = [];
    if (!override.videoId) errors.push('请提供有效的 YouTube 链接或 videoId');
    if (!override.performers.length && !override.versionBase && !override.versionSpecial.length && !override.notes) {
      errors.push('至少填写歌手、版本或备注中的一项');
    }
    return errors;
  }

  // CRUD
  function saveCurrentForm() {
    const video = readForm();
    const errors = validateDraft(video);
    if (errors.length) { showToast(`请先补全信息：${errors[0]}`); return; }
    const duplicate = draftVideos.find(item => item.videoId === video.videoId && item.draftId !== video.draftId);
    if (duplicate) { showToast(`videoId 已存在：${video.videoId}`); return; }
    const existingIndex = draftVideos.findIndex(item => item.draftId === video.draftId);
    if (existingIndex >= 0) {
      draftVideos.splice(existingIndex, 1, video);
      editingDraftId = video.draftId;
      showToast('已更新当前草稿视频');
    } else {
      draftVideos.unshift(video);
      editingDraftId = video.draftId;
      showToast('已新增手动补录视频');
    }
    updateStats();
    setFormModeLabel();
    renderDraftList();
  }

  function editDraft(draftId) {
    const video = draftVideos.find(item => item.draftId === draftId);
    if (!video) return;
    editingDraftId = draftId;
    writeForm(video);
    renderDraftList();
  }

  function deleteDraft(draftId) {
    const index = draftVideos.findIndex(item => item.draftId === draftId);
    if (index < 0) return;
    const [removed] = draftVideos.splice(index, 1);
    if (editingDraftId === draftId) { editingDraftId = null; resetForm(); }
    updateStats();
    renderDraftList();
    showToast(`已删除：${removed.songTitle || removed.videoId}`);
  }

  function deleteCurrentEditing() {
    if (!editingDraftId) return;
    deleteDraft(editingDraftId);
  }

  function saveCurrentOverride() {
    const override = readOverrideForm();
    const errors = validateOverrideDraft(override);
    if (errors.length) { showToast(`请先补全信息：${errors[0]}`); return; }
    const duplicate = overrideDrafts.find(item => item.videoId === override.videoId && item.draftId !== override.draftId);
    if (duplicate) { showToast(`videoId 已存在于覆写列表：${override.videoId}`); return; }
    const existingIndex = overrideDrafts.findIndex(item => item.draftId === override.draftId);
    if (existingIndex >= 0) {
      overrideDrafts.splice(existingIndex, 1, override);
      editingOverrideId = override.draftId;
      showToast('已更新当前覆写条目');
    } else {
      overrideDrafts.unshift(override);
      editingOverrideId = override.draftId;
      showToast('已新增字段覆写条目');
    }
    updateStats();
    setOverrideFormModeLabel();
    renderOverrideList();
    renderReviewList();
  }

  function editOverride(draftId) {
    const override = overrideDrafts.find(item => item.draftId === draftId);
    if (!override) return;
    editingOverrideId = draftId;
    writeOverrideForm(override);
    renderOverrideList();
    renderReviewList();
  }

  function deleteOverride(draftId) {
    const index = overrideDrafts.findIndex(item => item.draftId === draftId);
    if (index < 0) return;
    const [removed] = overrideDrafts.splice(index, 1);
    if (editingOverrideId === draftId) { editingOverrideId = null; resetOverrideForm(); }
    updateStats();
    renderOverrideList();
    renderReviewList();
    showToast(`已删除覆写：${removed.videoId}`);
  }

  function deleteCurrentEditingOverride() {
    if (!editingOverrideId) return;
    deleteOverride(editingOverrideId);
  }

  function startOverrideFromReview(reviewId) {
    const reviewItem = performerReviewItems.find(item => item.reviewId === reviewId);
    if (!reviewItem) return;
    const existing = findOverrideDraftByVideoId(reviewItem.videoId);
    if (existing) {
      editingOverrideId = existing.draftId;
      writeOverrideForm({
        ...reviewItem, ...existing,
        performers: existing.performers, notes: existing.notes,
        versionBase: existing.versionBase, versionSpecial: existing.versionSpecial,
      });
      showToast(`已打开现有覆写：${reviewItem.videoId}`);
    } else {
      editingOverrideId = null;
      writeOverrideForm(reviewItem);
      showToast(`已带入待复核条目：${reviewItem.videoId}`);
    }
    renderOverrideList();
    renderReviewList();
    const panel = document.getElementById('override-form-panel');
    if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Export functions
  function exportManualVideos() {
    const payload = JSON.stringify(serializeDraftVideos(), null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'manual_videos.json'; link.click();
    URL.revokeObjectURL(url);
    showToast('已导出 manual_videos.json');
  }

  async function copyJsonToClipboard() {
    const payload = JSON.stringify(serializeDraftVideos(), null, 2);
    try {
      await navigator.clipboard.writeText(payload);
      showToast('JSON 已复制到剪贴板');
    } catch (e) { showToast('复制失败，请使用"导出 JSON"'); }
  }

  function exportOriginalVideoOverrides() {
    const payload = JSON.stringify(serializeOriginalVideoOverrides(), null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'original_video_overrides.json'; link.click();
    URL.revokeObjectURL(url);
    showToast('已导出 original_video_overrides.json');
  }

  async function copyOverrideJsonToClipboard() {
    const payload = JSON.stringify(serializeOriginalVideoOverrides(), null, 2);
    try {
      await navigator.clipboard.writeText(payload);
      showToast('覆写 JSON 已复制到剪贴板');
    } catch (e) { showToast('复制失败，请使用"导出覆写 JSON"'); }
  }

  // Import modals
  function showImportModal() {
    document.getElementById('import-modal').classList.add('show');
    document.getElementById('import-textarea').value = '';
    document.getElementById('import-textarea').focus();
  }

  function closeImportModal() {
    document.getElementById('import-modal').classList.remove('show');
  }

  function importDrafts(replaceAll) {
    const text = document.getElementById('import-textarea').value.trim();
    if (!text) return;
    try {
      const payload = JSON.parse(text);
      const rawVideos = Array.isArray(payload) ? payload : (payload?.videos || []);
      const importedVideos = rawVideos.map(normalizeDraftVideo);
      if (replaceAll) {
        draftVideos = importedVideos;
      } else {
        const existingIds = new Map(draftVideos.map(v => [v.videoId, v]));
        importedVideos.forEach(v => {
          if (!v.videoId || existingIds.has(v.videoId)) return;
          draftVideos.push(v);
          existingIds.set(v.videoId, v);
        });
      }
      closeImportModal();
      updateStats();
      renderDraftList();
      showToast(replaceAll ? '已替换当前草稿列表' : '已合并导入草稿列表');
    } catch (e) { showToast(`导入失败：${e.message}`); }
  }

  function showOverrideImportModal() {
    document.getElementById('override-import-modal').classList.add('show');
    document.getElementById('override-import-textarea').value = '';
    document.getElementById('override-import-textarea').focus();
  }

  function closeOverrideImportModal() {
    document.getElementById('override-import-modal').classList.remove('show');
  }

  function importOverrideDrafts(replaceAll) {
    const text = document.getElementById('override-import-textarea').value.trim();
    if (!text) return;
    try {
      const payload = JSON.parse(text);
      const importedOverrides = extractOverrideRows(payload).map(normalizeOverrideDraft);
      if (replaceAll) {
        overrideDrafts = importedOverrides;
      } else {
        const existingIds = new Map(overrideDrafts.map(item => [item.videoId, item]));
        importedOverrides.forEach(item => {
          if (!item.videoId) return;
          if (existingIds.has(item.videoId)) {
            const existing = existingIds.get(item.videoId);
            const idx = overrideDrafts.findIndex(o => o.draftId === existing.draftId);
            if (idx >= 0) overrideDrafts.splice(idx, 1, { ...existing, ...item, draftId: existing.draftId });
          } else {
            overrideDrafts.push(item);
            existingIds.set(item.videoId, item);
          }
        });
      }
      closeOverrideImportModal();
      updateStats();
      renderOverrideList();
      renderReviewList();
      showToast(replaceAll ? '已替换当前覆写列表' : '已合并导入覆写列表');
    } catch (e) { showToast(`覆写导入失败：${e.message}`); }
  }

  // Input sync helpers
  function syncVideoIdFromUrlInput(urlId, vidId) {
    const urlInput = document.getElementById(urlId);
    const videoIdInput = document.getElementById(vidId);
    if (!urlInput || !videoIdInput) return;
    const videoId = extractVideoId(urlInput.value);
    if (videoId) videoIdInput.value = videoId;
  }

  function syncUrlFromVideoIdInput(vidId, urlId) {
    const videoIdInput = document.getElementById(vidId);
    const urlInput = document.getElementById(urlId);
    if (!videoIdInput || !urlInput) return;
    const videoId = extractVideoId(videoIdInput.value);
    if (!videoId) return;
    videoIdInput.value = videoId;
    if (!urlInput.value.trim()) urlInput.value = buildVideoUrl(videoId);
  }

  function syncOverrideContextWithVideoId() {
    const vidEl = document.getElementById('override-video-id');
    const urlEl = document.getElementById('override-video-url');
    if (!vidEl) return;
    const currentVideoId = extractVideoId(vidEl.value || (urlEl ? urlEl.value : ''));
    if (currentOverrideContext.videoId && currentOverrideContext.videoId !== currentVideoId) {
      updateOverrideContext({});
    }
  }

  function bindInputs() {
    const byId = (id) => document.getElementById(id);

    const songSearch = byId('song-search');
    if (songSearch) songSearch.addEventListener('input', e => { songSearchQuery = e.target.value; renderSongHelperList(); });

    const entrySearch = byId('entry-search');
    if (entrySearch) entrySearch.addEventListener('input', e => { entrySearchQuery = e.target.value; renderDraftList(); });

    const overrideSearch = byId('override-search');
    if (overrideSearch) overrideSearch.addEventListener('input', e => { overrideSearchQuery = e.target.value; renderOverrideList(); });

    const reviewSearch = byId('review-search');
    if (reviewSearch) reviewSearch.addEventListener('input', e => { reviewSearchQuery = e.target.value; renderReviewList(); });

    const videoUrl = byId('video-url');
    const videoId = byId('video-id');
    if (videoUrl) videoUrl.addEventListener('blur', () => syncVideoIdFromUrlInput('video-url', 'video-id'));
    if (videoId) videoId.addEventListener('blur', () => syncUrlFromVideoIdInput('video-id', 'video-url'));

    const ovUrl = byId('override-video-url');
    const ovId = byId('override-video-id');
    if (ovUrl) ovUrl.addEventListener('blur', () => { syncVideoIdFromUrlInput('override-video-url', 'override-video-id'); syncOverrideContextWithVideoId(); });
    if (ovId) ovId.addEventListener('blur', () => { syncUrlFromVideoIdInput('override-video-id', 'override-video-url'); syncOverrideContextWithVideoId(); });

    const songTitle = byId('song-title');
    if (songTitle) songTitle.addEventListener('input', e => { selectedSongTitle = e.target.value.trim(); renderSongHelperList(); });
  }

  function render() {
    return `
      <aside class="sidebar">
        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">歌曲助手</div>
              <div class="panel-subtitle">点一下即可把曲名填进右侧表单</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="helper-note">
              适合给已经知道视频链接，但不想手打曲名的场景。<br>
              如果这首歌还不在曲库里，也可以直接在右侧自由填写。
            </div>
            <div class="search-box">
              <span class="search-icon">🔎</span>
              <input type="text" id="song-search" placeholder="搜索歌名、ID、作曲者..." autocomplete="off">
            </div>
            <div class="helper-list" id="song-helper-list">
              <div class="empty-state">加载曲库中...</div>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">待复核原曲视频</div>
              <div class="panel-subtitle">来自 \`output/original_mv_review.json\`，点一下即可带入右侧覆写表单</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="helper-note">
              这里主要处理歌手低置信度条目。<br>
              保存后导出为 \`original_video_overrides.json\`，下次构建会直接覆盖对应视频字段。
            </div>
            <div class="search-box">
              <span class="search-icon">🔎</span>
              <input type="text" id="review-search" placeholder="搜索曲名、标题、videoId..." autocomplete="off">
            </div>
            <div class="entry-list" id="review-list">
              <div class="empty-state">待复核列表加载中...</div>
            </div>
          </div>
        </section>
      </aside>

      <main class="main">
        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">补录表单</div>
              <div class="panel-subtitle">填写一个视频条目，新增或更新到草稿列表</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="toolbar">
              <div class="field-tip">支持粘贴完整 YouTube 链接，会自动提取 \`videoId\` 并补全标准链接。</div>
              <div class="toolbar-actions">
                <button class="btn" type="button" onclick="ManualVideoEditor.showImportModal()">导入 JSON</button>
                <button class="btn" type="button" onclick="ManualVideoEditor.copyJsonToClipboard()">复制 JSON</button>
                <button class="btn btn-success" type="button" onclick="ManualVideoEditor.exportManualVideos()">导出 JSON</button>
              </div>
            </div>

            <div class="form-banner">
              <div>
                <strong id="form-mode-label">当前模式：新增条目</strong><br>
                <span>导出的文件请放到 \`manual_data/manual_videos.json\`，然后运行 \`python scripts\\build_database.py\`。</span>
              </div>
              <button class="btn" type="button" onclick="ManualVideoEditor.resetForm()">清空表单</button>
            </div>

            <div class="section-grid">
              <div class="field-block">
                <label class="field-label" for="song-title">歌曲名</label>
                <input class="field" id="song-title" placeholder="例如：CRASH THE PARTY" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="video-title">视频标题</label>
                <input class="field" id="video-title" placeholder="例如：CRASH THE PARTY / Vivid BAD SQUAD × 巡音ルカ" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="video-url">YouTube 链接</label>
                <input class="field" id="video-url" placeholder="https://www.youtube.com/watch?v=xxxxxxxxxxx" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="video-id">videoId</label>
                <input class="field mono" id="video-id" placeholder="11 位 YouTube videoId" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="published-at">发布时间</label>
                <input class="field mono" id="published-at" placeholder="例如：2026-04-21T12:34:56Z" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="position">播放列表位置（可选）</label>
                <input class="field mono" id="position" placeholder="留空即可自动排到手动区段" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="version-base">版本主类</label>
                <select class="field" id="version-base">
                  <option value="">自动判断</option>
                  <option value="original">本家</option>
                  <option value="sekai">SEKAI ver</option>
                  <option value="virtual_singer">Virtual Singer ver</option>
                  <option value="another_vocal">Another Vocal</option>
                  <option value="unknown">未分类</option>
                </select>
              </div>
              <div class="field-block">
                <label class="field-label">特殊版本</label>
                <label class="checkbox-inline">
                  <input type="checkbox" id="version-special-april-fool">
                  <span>愚人节版 / April Fool</span>
                </label>
              </div>
              <div class="field-block">
                <label class="field-label" for="channel-title">频道名</label>
                <input class="field" id="channel-title" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="channel-id">频道 ID</label>
                <input class="field mono" id="channel-id" autocomplete="off">
              </div>
              <div class="field-block full">
                <label class="field-label" for="description">视频描述</label>
                <textarea class="textarea" id="description" placeholder="把 YouTube 描述完整贴进来，后续 staff 提取也会直接用这里的数据。"></textarea>
              </div>
              <div class="field-block full">
                <label class="field-label" for="notes">备注（可选）</label>
                <textarea class="textarea" id="notes" placeholder="例如：没有进官方播放列表，手动补录。此字段只保留在 manual_videos.json 中，方便以后回看。"></textarea>
              </div>
            </div>

            <div class="button-row">
              <button class="btn btn-primary" type="button" onclick="ManualVideoEditor.saveCurrentForm()">保存到草稿列表</button>
              <button class="btn btn-danger" type="button" id="delete-current-btn" onclick="ManualVideoEditor.deleteCurrentEditing()" disabled>删除当前编辑条目</button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">已补录视频</div>
              <div class="panel-subtitle">点卡片进入编辑，导出时会自动生成 \`thumbnails\` 字段</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="search-box">
              <span class="search-icon">🔎</span>
              <input type="text" id="entry-search" placeholder="搜索草稿里的歌曲名、标题、videoId..." autocomplete="off">
            </div>
            <div class="entry-list" id="entry-list">
              <div class="empty-state">还没有手动补录视频。先在上面填一条看看。</div>
            </div>
          </div>
        </section>

        <section class="panel" id="override-form-panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">字段覆写表单</div>
              <div class="panel-subtitle">为已存在于 playlist 的视频生成 \`original_video_overrides.json\`</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="toolbar">
              <div class="field-tip">适合修正歌手、版本和备注。不会替换整条视频，只会覆盖你明确填写的字段。</div>
              <div class="toolbar-actions">
                <button class="btn" type="button" onclick="ManualVideoEditor.showOverrideImportModal()">导入覆写 JSON</button>
                <button class="btn" type="button" onclick="ManualVideoEditor.copyOverrideJsonToClipboard()">复制覆写 JSON</button>
                <button class="btn btn-success" type="button" onclick="ManualVideoEditor.exportOriginalVideoOverrides()">导出覆写 JSON</button>
              </div>
            </div>

            <div class="form-banner">
              <div>
                <strong id="override-form-mode-label">当前模式：新增覆写</strong><br>
                <span>导出的文件请放到 \`manual_data/original_video_overrides.json\`，然后运行 \`python scripts\\build_database.py\`。</span>
              </div>
              <button class="btn" type="button" onclick="ManualVideoEditor.resetOverrideForm()">清空覆写表单</button>
            </div>

            <div class="helper-note" id="override-context-note">
              可以从左侧"待复核原曲视频"点一条带入。当前表单只输出 \`performers\`、\`version\`、\`notes\` 到 \`original_video_overrides.json\`。
            </div>

            <div class="section-grid">
              <div class="field-block">
                <label class="field-label" for="override-video-id">videoId</label>
                <input class="field mono" id="override-video-id" placeholder="11 位 YouTube videoId" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="override-video-url">YouTube 链接（可选）</label>
                <input class="field" id="override-video-url" placeholder="https://www.youtube.com/watch?v=xxxxxxxxxxx" autocomplete="off">
              </div>
              <div class="field-block">
                <label class="field-label" for="override-version-base">版本主类</label>
                <select class="field" id="override-version-base">
                  <option value="">不覆写</option>
                  <option value="original">本家</option>
                  <option value="sekai">SEKAI ver</option>
                  <option value="virtual_singer">Virtual Singer ver</option>
                  <option value="another_vocal">Another Vocal</option>
                  <option value="unknown">未分类</option>
                </select>
              </div>
              <div class="field-block">
                <label class="field-label">特殊版本</label>
                <label class="checkbox-inline">
                  <input type="checkbox" id="override-version-special-april-fool">
                  <span>愚人节版 / April Fool</span>
                </label>
              </div>
              <div class="field-block full">
                <label class="field-label" for="override-performers">歌手 / Performers</label>
                <textarea class="textarea" id="override-performers" placeholder="每行一个，也支持逗号分隔。例如：&#10;初音ミク&#10;可不"></textarea>
                <div class="field-tip">主要用于补齐 \`original_mv_review.json\` 里的低置信度歌手结果。</div>
              </div>
              <div class="field-block full">
                <label class="field-label" for="override-notes">备注（可选）</label>
                <textarea class="textarea" id="override-notes" placeholder="例如：标题没写具体歌手，按曲目 vocal 资料手动补录。"></textarea>
              </div>
            </div>

            <div class="button-row">
              <button class="btn btn-primary" type="button" onclick="ManualVideoEditor.saveCurrentOverride()">保存到覆写列表</button>
              <button class="btn btn-danger" type="button" id="delete-current-override-btn" onclick="ManualVideoEditor.deleteCurrentEditingOverride()" disabled>删除当前覆写</button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">已保存覆写</div>
              <div class="panel-subtitle">导出时会按 \`videoId\` 生成 \`original_video_overrides.json\` 的 \`videos\` 对象</div>
            </div>
          </div>
          <div class="panel-body">
            <div class="search-box">
              <span class="search-icon">🔎</span>
              <input type="text" id="override-search" placeholder="搜索覆写里的 videoId、歌手、备注..." autocomplete="off">
            </div>
            <div class="entry-list" id="override-entry-list">
              <div class="empty-state">还没有覆写条目。左侧待复核列表或手动输入都可以建立一条。</div>
            </div>
          </div>
        </section>
      </main>`;
  }

  function init() {
    bindInputs();
    resetForm();
    resetOverrideForm();
    return Promise.all([
      loadSongCatalog(),
      loadExistingDrafts(),
      loadExistingOverrides(),
      loadPerformerReviewItems(),
    ]).then(() => {
      updateStats();
      renderSongHelperList();
      renderDraftList();
      renderReviewList();
      renderOverrideList();
      setFormModeLabel();
      setOverrideFormModeLabel();
    });
  }

  // Public API
  return {
    init, render,
    showImportModal, closeImportModal, importDrafts,
    copyJsonToClipboard, exportManualVideos,
    saveCurrentForm, deleteCurrentEditing, resetForm,
    showOverrideImportModal, closeOverrideImportModal, importOverrideDrafts,
    copyOverrideJsonToClipboard, exportOriginalVideoOverrides,
    saveCurrentOverride, deleteCurrentEditingOverride, resetOverrideForm,
  };
})();
