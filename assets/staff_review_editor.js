/* ========== StaffReviewEditor Namespace ========== */
const StaffReviewEditor = (function() {
  const ISSUE_RENDER_LIMIT = 200;
  const ROLE_OPTIONS = [
    ['illustrator', '插画 / Illustrator'],
    ['pvCreator', '映像 / PV・Movie'],
    ['illustrationAnimation', '插画动画'],
    ['lyricDesign', '歌词设计'],
    ['animation', '动画'],
    ['design', '视觉设计'],
    ['cg3d', '3D / CG'],
    ['ignore', '忽略（非视觉 Staff）'],
  ];
  const ROLE_LABELS = Object.fromEntries(ROLE_OPTIONS);

  let reviewRows = [];
  let issues = [];
  let roleAliases = {};
  let nameAliases = {};
  let ignoredLines = new Set();
  let initialRoleAliases = {};
  let initialNameAliases = {};
  let initialIgnoredLines = new Set();
  let selectedIssueId = null;
  let searchQuery = '';
  let kindFilter = 'all';
  let statusFilter = 'open';
  let loaded = false;
  let loadError = '';
  let loadPromise = null;

  function cleanToken(value) {
    return String(value || '').replace(/\u3000/g, ' ').replace(/\s+/g, ' ').trim().replace(/^[-:：\s]+|[-:：\s]+$/g, '');
  }

  function findRoleDelimiter(line) {
    const value = String(line || '');
    const urlMatch = value.match(/https?:\/\//i);
    const urlStart = urlMatch ? urlMatch.index : value.length + 1;
    const indexes = ['：', ':']
      .map(delimiter => ({ delimiter, index: value.indexOf(delimiter) }))
      .filter(item => item.index >= 0 && item.index < urlStart)
      .sort((a, b) => a.index - b.index);
    return indexes[0] || null;
  }

  function extractCandidateRole(line) {
    const value = String(line || '').trim();
    const delimiter = findRoleDelimiter(value);
    if (delimiter) return cleanToken(value.slice(0, delimiter.index));
    const byMatch = value.match(/^(.+?)\s+by\s+.+$/i);
    return byMatch ? cleanToken(byMatch[1]) : '';
  }

  function extractCandidateName(line) {
    const value = String(line || '').trim();
    const delimiter = findRoleDelimiter(value);
    let candidate = '';
    if (delimiter) candidate = value.slice(delimiter.index + delimiter.delimiter.length);
    else {
      const byMatch = value.match(/^.+?\s+by\s+(.+)$/i);
      if (byMatch) candidate = byMatch[1];
    }
    return cleanToken(candidate
      .replace(/[（(]\s*https?:\/\/[^\s)）]+[)）]?/gi, '')
      .replace(/https?:\/\/\S+/gi, ''));
  }

  function buildIssues(rows) {
    const result = [];
    rows.forEach((row, rowIndex) => {
      [
        ['unknown', row.unknownRoleLines || []],
        ['unparsed', row.unparsedLines || []],
      ].forEach(([kind, lines]) => {
        lines.forEach((line, lineIndex) => {
          result.push({
            id: `${row.videoId || rowIndex}:${kind}:${lineIndex}`,
            kind,
            line: String(line || '').trim(),
            candidateRole: extractCandidateRole(line),
            candidateName: extractCandidateName(line),
            songId: row.songId || '',
            songTitle: row.songTitle || '',
            videoId: row.videoId || '',
            videoTitle: row.videoTitle || '',
          });
        });
      });
    });
    return result;
  }

  function getIssueStatus(issue) {
    if (ignoredLines.has(issue.line)) return 'ignored';
    if (issue.candidateRole && Object.prototype.hasOwnProperty.call(roleAliases, issue.candidateRole)) return 'mapped';
    return 'open';
  }

  function statusLabel(status) {
    return { open: '待处理', mapped: '已映射', ignored: '已忽略' }[status] || status;
  }

  function kindLabel(kind) {
    return kind === 'unknown' ? '未知角色' : '未解析行';
  }

  function getFilteredIssues() {
    const query = searchQuery.toLowerCase().trim();
    return issues.filter(issue => {
      if (kindFilter !== 'all' && issue.kind !== kindFilter) return false;
      if (statusFilter !== 'all' && getIssueStatus(issue) !== statusFilter) return false;
      if (!query) return true;
      return [issue.songTitle, issue.videoTitle, issue.videoId, issue.line, issue.candidateRole]
        .some(value => String(value || '').toLowerCase().includes(query));
    });
  }

  function countChangedEntries() {
    const roleKeys = new Set([...Object.keys(initialRoleAliases), ...Object.keys(roleAliases)]);
    const nameKeys = new Set([...Object.keys(initialNameAliases), ...Object.keys(nameAliases)]);
    let count = 0;
    roleKeys.forEach(key => { if (initialRoleAliases[key] !== roleAliases[key]) count += 1; });
    nameKeys.forEach(key => { if (initialNameAliases[key] !== nameAliases[key]) count += 1; });
    const ignoredUnion = new Set([...initialIgnoredLines, ...ignoredLines]);
    ignoredUnion.forEach(line => {
      if (initialIgnoredLines.has(line) !== ignoredLines.has(line)) count += 1;
    });
    return count;
  }

  function updateStats() {
    const unknownCount = issues.filter(issue => issue.kind === 'unknown').length;
    const unparsedCount = issues.filter(issue => issue.kind === 'unparsed').length;
    const values = {
      'stat-staff-records': reviewRows.length,
      'stat-staff-unknown': unknownCount,
      'stat-staff-unparsed': unparsedCount,
      'stat-staff-fixes': countChangedEntries(),
    };
    Object.entries(values).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    });
  }

  function renderQueue() {
    const container = document.getElementById('staff-issue-list');
    const countElement = document.getElementById('staff-filtered-count');
    if (!container) return;
    const filtered = getFilteredIssues();
    if (countElement) countElement.textContent = `${filtered.length} 条`;

    if (!filtered.some(issue => issue.id === selectedIssueId)) {
      selectedIssueId = filtered[0]?.id || null;
    }
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">当前条件下没有待复核记录</div>';
      renderSelectedIssue();
      return;
    }

    const visibleIssues = filtered.slice(0, ISSUE_RENDER_LIMIT);
    container.innerHTML = visibleIssues.map(issue => {
      const status = getIssueStatus(issue);
      const selected = issue.id === selectedIssueId;
      return `<button class="staff-issue-card status-${status}${selected ? ' active' : ''}" type="button"
          data-issue-id="${esc(issue.id)}" aria-pressed="${selected}">
        <span class="staff-issue-topline">
          <span class="staff-kind-badge kind-${issue.kind}">${kindLabel(issue.kind)}</span>
          <span class="staff-status-badge status-${status}">${statusLabel(status)}</span>
        </span>
        <span class="staff-issue-song">${esc(issue.songTitle || '未关联歌曲')}</span>
        <span class="staff-issue-line">${esc(issue.line)}</span>
        ${issue.candidateRole ? `<span class="staff-candidate">候选标签 · ${esc(issue.candidateRole)}</span>` : ''}
      </button>`;
    }).join('') + (filtered.length > ISSUE_RENDER_LIMIT
      ? `<div class="staff-list-limit">仅显示前 ${ISSUE_RENDER_LIMIT} 条，请继续搜索以缩小范围。</div>`
      : '');

    container.querySelectorAll('.staff-issue-card').forEach(button => {
      button.addEventListener('click', () => {
        selectedIssueId = button.dataset.issueId;
        renderQueue();
        if (window.matchMedia('(max-width: 1100px)').matches) {
          window.requestAnimationFrame(() => {
            document.getElementById('staff-review-detail')?.closest('.panel')
              ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          });
        }
      });
    });
    renderSelectedIssue();
  }

  function renderSelectedIssue() {
    const container = document.getElementById('staff-review-detail');
    if (!container) return;
    const issue = issues.find(item => item.id === selectedIssueId);
    if (!issue) {
      container.innerHTML = loadError
        ? `<div class="editor-empty">加载失败<br><small>${esc(loadError)}</small></div>`
        : '<div class="editor-empty">← 从左侧选择一条记录<br>即可开始复核</div>';
      return;
    }

    const status = getIssueStatus(issue);
    const currentRole = issue.candidateRole ? roleAliases[issue.candidateRole] || '' : '';
    const roleOptions = ROLE_OPTIONS.map(([value, label]) =>
      `<option value="${value}"${currentRole === value ? ' selected' : ''}>${esc(label)}</option>`).join('');
    const videoLink = issue.videoId ? `https://www.youtube.com/watch?v=${encodeURIComponent(issue.videoId)}` : '';

    container.innerHTML = `
      <div class="staff-detail-head">
        <div>
          <div class="staff-detail-kicker">${kindLabel(issue.kind)} · ${statusLabel(status)}</div>
          <h2>${esc(issue.songTitle || '未关联歌曲')}</h2>
          <div class="staff-detail-video">${esc(issue.videoTitle || '-')}</div>
        </div>
        ${videoLink ? `<a class="btn" href="${videoLink}" target="_blank" rel="noopener noreferrer">打开视频 ↗</a>` : ''}
      </div>
      <div class="staff-source-block">
        <div class="field-label">原始描述行</div>
        <code>${esc(issue.line)}</code>
      </div>
      <div class="staff-context-grid">
        <div><span>videoId</span><strong>${esc(issue.videoId || '-')}</strong></div>
        <div><span>候选角色</span><strong>${esc(issue.candidateRole || '未可靠提取')}</strong></div>
      </div>
      <div class="staff-action-grid">
        <section class="staff-action-card">
          <div class="staff-action-number">01</div>
          <div class="staff-action-title">角色映射</div>
          <div class="field-group">
            <label class="field-label" for="staff-role-raw">原始角色标签</label>
            <input class="input" id="staff-role-raw" value="${esc(issue.candidateRole)}" placeholder="例如：Movie assistant">
          </div>
          <div class="field-group">
            <label class="field-label" for="staff-role-value">映射为</label>
            <select class="select" id="staff-role-value">
              <option value="">请选择标准角色</option>
              ${roleOptions}
            </select>
          </div>
          <div class="staff-inline-actions">
            <button class="btn btn-primary" id="staff-save-role-btn" type="button">保存角色映射</button>
            <button class="btn" id="staff-remove-role-btn" type="button"${currentRole ? '' : ' disabled'}>移除映射</button>
          </div>
        </section>
        <section class="staff-action-card">
          <div class="staff-action-number">02</div>
          <div class="staff-action-title">人名归一化</div>
          <div class="field-group">
            <label class="field-label" for="staff-name-raw">描述中的写法</label>
            <input class="input" id="staff-name-raw" value="${esc(issue.candidateName)}" placeholder="例如：omu (THINGS.)">
          </div>
          <div class="field-group">
            <label class="field-label" for="staff-name-value">统一写作</label>
            <input class="input" id="staff-name-value" value="${esc(issue.candidateName ? nameAliases[issue.candidateName] || '' : '')}" placeholder="例如：omu">
          </div>
          <button class="btn btn-primary" id="staff-save-name-btn" type="button">保存人名映射</button>
        </section>
      </div>
      <div class="staff-ignore-strip status-${ignoredLines.has(issue.line) ? 'ignored' : 'open'}">
        <div>
          <strong>03 · 原文忽略</strong>
          <span>用于链接、宣传信息或明确与视觉 Staff 无关的整行内容。</span>
        </div>
        <button class="btn${ignoredLines.has(issue.line) ? ' btn-danger' : ''}" id="staff-toggle-ignore-btn" type="button">
          ${ignoredLines.has(issue.line) ? '恢复此行' : '忽略此行'}
        </button>
      </div>`;

    document.getElementById('staff-save-role-btn').addEventListener('click', saveRoleMapping);
    document.getElementById('staff-remove-role-btn').addEventListener('click', removeSelectedRoleMapping);
    document.getElementById('staff-save-name-btn').addEventListener('click', saveNameAlias);
    document.getElementById('staff-toggle-ignore-btn').addEventListener('click', toggleIgnoredLine);
  }

  function sortedObject(value) {
    return Object.keys(value)
      .sort((a, b) => a.localeCompare(b, 'ja'))
      .reduce((result, key) => {
        result[key] = value[key];
        return result;
      }, {});
  }

  function renderCorrections() {
    const container = document.getElementById('staff-correction-list');
    if (!container) return;
    const roleEntries = Object.entries(sortedObject(roleAliases));
    const nameEntries = Object.entries(sortedObject(nameAliases));
    const ignoredEntries = [...ignoredLines].sort((a, b) => a.localeCompare(b, 'ja'));

    const renderMapping = (entries, kind) => entries.length
      ? entries.map(([from, to]) => `<div class="staff-correction-row">
          <span class="staff-correction-from">${esc(from)}</span>
          <span class="staff-correction-arrow">→</span>
          <span class="staff-correction-to">${esc(kind === 'role' ? ROLE_LABELS[to] || to : to)}</span>
          <button class="staff-correction-remove" type="button" data-remove-kind="${kind}" data-remove-key="${esc(from)}" aria-label="移除 ${esc(from)}">×</button>
        </div>`).join('')
      : '<div class="staff-correction-empty">暂无记录</div>';

    container.innerHTML = `
      <div class="staff-correction-column">
        <div class="staff-correction-title">角色别名 <span>${roleEntries.length}</span></div>
        <div class="staff-correction-scroll">${renderMapping(roleEntries, 'role')}</div>
      </div>
      <div class="staff-correction-column">
        <div class="staff-correction-title">人名别名 <span>${nameEntries.length}</span></div>
        <div class="staff-correction-scroll">${renderMapping(nameEntries, 'name')}</div>
      </div>
      <div class="staff-correction-column">
        <div class="staff-correction-title">忽略原文 <span>${ignoredEntries.length}</span></div>
        <div class="staff-correction-scroll">${ignoredEntries.length
          ? ignoredEntries.map(line => `<div class="staff-correction-row staff-correction-line">
              <span class="staff-correction-from">${esc(line)}</span>
              <button class="staff-correction-remove" type="button" data-remove-kind="ignore" data-remove-key="${esc(line)}" aria-label="恢复此行">×</button>
            </div>`).join('')
          : '<div class="staff-correction-empty">暂无记录</div>'}
        </div>
      </div>`;

    container.querySelectorAll('.staff-correction-remove').forEach(button => {
      button.addEventListener('click', () => removeCorrection(button.dataset.removeKind, button.dataset.removeKey));
    });
  }

  function renderAll() {
    updateStats();
    renderQueue();
    renderCorrections();
  }

  function saveRoleMapping() {
    const rawInput = document.getElementById('staff-role-raw');
    const valueInput = document.getElementById('staff-role-value');
    const rawRole = cleanToken(rawInput?.value);
    const canonicalRole = valueInput?.value || '';
    if (!rawRole || !ROLE_LABELS[canonicalRole]) {
      showToast('请填写原始角色标签并选择标准角色');
      return;
    }
    roleAliases[rawRole] = canonicalRole;
    showToast(`已映射「${rawRole}」`);
    renderAll();
  }

  function removeSelectedRoleMapping() {
    const rawRole = cleanToken(document.getElementById('staff-role-raw')?.value);
    if (!rawRole || !Object.prototype.hasOwnProperty.call(roleAliases, rawRole)) return;
    delete roleAliases[rawRole];
    showToast(`已移除「${rawRole}」的角色映射`);
    renderAll();
  }

  function saveNameAlias() {
    const rawName = cleanToken(document.getElementById('staff-name-raw')?.value);
    const canonicalName = cleanToken(document.getElementById('staff-name-value')?.value);
    if (!rawName || !canonicalName) {
      showToast('请填写原始写法和统一写法');
      return;
    }
    if (rawName === canonicalName) {
      showToast('两种写法相同，无需添加映射');
      return;
    }
    nameAliases[rawName] = canonicalName;
    showToast(`已统一「${rawName}」`);
    renderAll();
  }

  function toggleIgnoredLine() {
    const issue = issues.find(item => item.id === selectedIssueId);
    if (!issue) return;
    if (ignoredLines.has(issue.line)) {
      ignoredLines.delete(issue.line);
      showToast('已恢复此原始行');
    } else {
      ignoredLines.add(issue.line);
      showToast('已加入忽略原文');
    }
    renderAll();
  }

  function removeCorrection(kind, key) {
    if (kind === 'role') delete roleAliases[key];
    if (kind === 'name') delete nameAliases[key];
    if (kind === 'ignore') ignoredLines.delete(key);
    renderAll();
  }

  function downloadJson(filename, value) {
    const blob = new Blob([JSON.stringify(value, null, 2) + '\n'], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`已导出 ${filename}`);
  }

  function exportRoleAliases() {
    downloadJson('staff_role_aliases.json', sortedObject(roleAliases));
  }

  function exportNameAliases() {
    downloadJson('staff_name_aliases.json', sortedObject(nameAliases));
  }

  function exportIgnoredLines() {
    downloadJson('staff_line_ignores.json', [...ignoredLines].sort((a, b) => a.localeCompare(b, 'ja')));
  }

  async function fetchJson(path, fallback, required = false) {
    try {
      const response = await fetch(path, { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      if (required) throw new Error(`${path}: ${error.message}`);
      return fallback;
    }
  }

  async function loadData() {
    if (loadPromise) return loadPromise;
    loadPromise = (async () => {
      try {
        const [reviewData, roleData, nameData, ignoredData] = await Promise.all([
          fetchJson('output/staff_review.json', [], true),
          fetchJson('manual_data/staff_role_aliases.json', {}),
          fetchJson('manual_data/staff_name_aliases.json', {}),
          fetchJson('manual_data/staff_line_ignores.json', []),
        ]);
        reviewRows = Array.isArray(reviewData) ? reviewData : [];
        roleAliases = roleData && typeof roleData === 'object' && !Array.isArray(roleData) ? { ...roleData } : {};
        nameAliases = nameData && typeof nameData === 'object' && !Array.isArray(nameData) ? { ...nameData } : {};
        const ignoredPayload = Array.isArray(ignoredData) ? ignoredData : ignoredData?.lines || [];
        ignoredLines = new Set(ignoredPayload.map(line => String(line).trim()).filter(Boolean));
        initialRoleAliases = { ...roleAliases };
        initialNameAliases = { ...nameAliases };
        initialIgnoredLines = new Set(ignoredLines);
        issues = buildIssues(reviewRows);
        loaded = true;
        loadError = '';
        renderAll();
      } catch (error) {
        loadError = error.message;
        renderSelectedIssue();
      } finally {
        loadPromise = null;
      }
    })();
    return loadPromise;
  }

  function bindStaticControls() {
    document.getElementById('staff-review-search')?.addEventListener('input', event => {
      searchQuery = event.target.value;
      renderQueue();
    });
    document.getElementById('staff-kind-filter')?.addEventListener('change', event => {
      kindFilter = event.target.value;
      renderQueue();
    });
    document.getElementById('staff-status-filter')?.addEventListener('change', event => {
      statusFilter = event.target.value;
      renderQueue();
    });
  }

  function render() {
    return `
      <aside class="sidebar staff-review-sidebar">
        <section class="panel staff-queue-panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">问题队列</div>
              <div class="panel-subtitle">逐行处理，不必直接修改审计 JSON</div>
            </div>
            <span class="staff-queue-count" id="staff-filtered-count">-</span>
          </div>
          <div class="panel-body">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input type="text" id="staff-review-search" value="${esc(searchQuery)}" placeholder="搜索歌曲、视频、角色或原文..." autocomplete="off">
            </div>
            <div class="staff-filter-row">
              <label>
                <span>问题类型</span>
                <select class="select" id="staff-kind-filter">
                  <option value="all"${kindFilter === 'all' ? ' selected' : ''}>全部类型</option>
                  <option value="unknown"${kindFilter === 'unknown' ? ' selected' : ''}>未知角色</option>
                  <option value="unparsed"${kindFilter === 'unparsed' ? ' selected' : ''}>未解析行</option>
                </select>
              </label>
              <label>
                <span>处理状态</span>
                <select class="select" id="staff-status-filter">
                  <option value="open"${statusFilter === 'open' ? ' selected' : ''}>待处理</option>
                  <option value="mapped"${statusFilter === 'mapped' ? ' selected' : ''}>已映射</option>
                  <option value="ignored"${statusFilter === 'ignored' ? ' selected' : ''}>已忽略</option>
                  <option value="all"${statusFilter === 'all' ? ' selected' : ''}>全部状态</option>
                </select>
              </label>
            </div>
            <div class="staff-issue-list" id="staff-issue-list">
              <div class="empty-state">加载 Staff 审计记录中...</div>
            </div>
          </div>
        </section>
      </aside>
      <main class="main staff-review-main">
        <div class="staff-review-toolbar">
          <div>
            <div class="header-kicker">Credit Triage Desk</div>
            <div class="staff-toolbar-note">导出后替换 manual_data 中的同名文件，再重新构建数据库。</div>
          </div>
          <div class="staff-export-actions">
            <button class="btn" type="button" onclick="StaffReviewEditor.exportRoleAliases()">导出角色别名</button>
            <button class="btn" type="button" onclick="StaffReviewEditor.exportNameAliases()">导出人名别名</button>
            <button class="btn btn-success" type="button" onclick="StaffReviewEditor.exportIgnoredLines()">导出忽略行</button>
          </div>
        </div>
        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">复核与修正</div>
              <div class="panel-subtitle">优先处理重复出现的角色标签；无关内容可按原文忽略</div>
            </div>
          </div>
          <div class="panel-body staff-review-detail" id="staff-review-detail">
            <div class="editor-empty">加载中...</div>
          </div>
        </section>
        <section class="panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">当前维护规则</div>
              <div class="panel-subtitle">包含已存在规则与本次修改；导出时生成完整文件</div>
            </div>
          </div>
          <div class="panel-body staff-correction-list" id="staff-correction-list"></div>
        </section>
      </main>`;
  }

  function init() {
    bindStaticControls();
    if (loaded) renderAll();
    else return loadData();
  }

  return {
    init,
    render,
    saveRoleMapping,
    saveNameAlias,
    toggleIgnoredLine,
    exportRoleAliases,
    exportNameAliases,
    exportIgnoredLines,
  };
})();
