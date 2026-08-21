/* ========== AliasEditor Namespace ========== */
const AliasEditor = (function() {
  let songs = [];
  let aliases = {};
  let selectedId = null;
  let searchQuery = '';

  async function loadData() {
    try {
      const resp = await fetch('output/combined_music_data.json');
      songs = await resp.json();
    } catch (e) {
      const container = document.getElementById('alias-song-list-container');
      if (container) container.innerHTML = `<div class="empty-state">无法加载歌曲数据<br><small>${e.message}</small></div>`;
      return;
    }
    try {
      const aliasResp = await fetch('output/aliases.json');
      aliases = await aliasResp.json();
    } catch (e) { aliases = {}; }
    updateStats();
    renderSongList();
  }

  function updateStats() {
    const totalEl = document.getElementById('stat-total');
    const aliasedEl = document.getElementById('stat-aliased');
    const aliasesEl = document.getElementById('stat-aliases');
    if (totalEl) totalEl.textContent = songs.length;
    if (aliasedEl) aliasedEl.textContent = Object.keys(aliases).length;
    if (aliasesEl) aliasesEl.textContent = Object.values(aliases).reduce((sum, arr) => sum + arr.length, 0);
  }

  function renderSongList() {
    const container = document.getElementById('alias-song-list-container');
    if (!container) return;
    const q = searchQuery.toLowerCase().trim();
    let filtered = songs;
    if (q) {
      filtered = songs.filter(s => {
        if (String(s.id) === q) return true;
        if ((s.title || '').toLowerCase().includes(q)) return true;
        if ((s.creators?.creatorArtistName || '').toLowerCase().includes(q)) return true;
        const songAliases = aliases[String(s.id)] || [];
        if (songAliases.some(a => a.toLowerCase().includes(q))) return true;
        return false;
      });
    }
    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">没有匹配的歌曲</div>';
      return;
    }
    container.innerHTML = filtered.map(s => {
      const count = (aliases[String(s.id)] || []).length;
      const isSelected = s.id === selectedId;
      return `<div class="helper-item${isSelected ? ' active' : ''}" data-id="${s.id}">
        <span class="helper-id">#${s.id}</span>
        <span class="helper-title">${esc(s.title)}</span>
        ${count > 0
          ? `<span class="alias-count-badge">${count}</span>`
          : `<span class="alias-count-badge empty">0</span>`
        }
      </div>`;
    }).join('');
    container.querySelectorAll('.helper-item').forEach(el => {
      el.addEventListener('click', () => {
        selectedId = parseInt(el.dataset.id);
        renderSongList();
        renderEditor();
      });
    });
  }

  function renderEditor() {
    const container = document.getElementById('alias-editor-container');
    if (!container) return;
    if (selectedId === null) {
      container.innerHTML = '<div class="editor-empty">← 从左侧选择一首歌曲<br>即可编辑其别称</div>';
      return;
    }
    const song = songs.find(s => s.id === selectedId);
    if (!song) return;
    const currentAliases = aliases[String(selectedId)] || [];
    container.innerHTML = `
      <div class="editor-content">
        <div class="selected-song-info">
          <div class="song-name">${esc(song.title)}</div>
          <div class="song-meta">ID: ${song.id} · ${esc(song.creators?.creatorArtistName || '-')}</div>
        </div>
        <div class="alias-section">
          <div class="alias-label">当前别称 (${currentAliases.length})</div>
          <div class="alias-tags" id="alias-tags">
            ${currentAliases.length === 0
              ? '<span class="no-aliases">暂无别称，在下方输入添加</span>'
              : currentAliases.map((a, i) => `
                <span class="alias-tag">
                  ${esc(a)}
                  <button class="remove-btn" data-index="${i}" title="删除">✕</button>
                </span>
              `).join('')
            }
          </div>
        </div>
        <div class="alias-section">
          <div class="alias-label">添加别称</div>
          <div class="add-alias-row">
            <input type="text" id="alias-input" placeholder="输入别称后按 Enter 添加..." autocomplete="off">
            <button class="btn btn-primary" type="button" onclick="AliasEditor.addAliasFromInput()">添加</button>
          </div>
        </div>
        <div style="margin-top:16px;display:flex;gap:8px">
          <button class="btn btn-danger" type="button" onclick="AliasEditor.clearAliases()" ${currentAliases.length === 0 ? 'disabled style="opacity:0.4;cursor:default"' : ''}>
            清空此歌别称
          </button>
        </div>
      </div>
    `;
    container.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeAlias(parseInt(btn.dataset.index));
      });
    });
    const input = document.getElementById('alias-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); addAliasFromInput(); }
      });
      input.focus();
    }
  }

  function addAliasFromInput() {
    const input = document.getElementById('alias-input');
    if (!input) return;
    const val = input.value.trim();
    if (!val || selectedId === null) return;
    const key = String(selectedId);
    if (!aliases[key]) aliases[key] = [];
    if (aliases[key].some(a => a.toLowerCase() === val.toLowerCase())) {
      showToast('该别称已存在');
      return;
    }
    aliases[key].push(val);
    input.value = '';
    renderEditor();
    renderSongList();
    updateStats();
    showToast(`已添加别称「${val}」`);
  }

  function removeAlias(index) {
    const key = String(selectedId);
    if (!aliases[key]) return;
    const removed = aliases[key].splice(index, 1)[0];
    if (aliases[key].length === 0) delete aliases[key];
    renderEditor();
    renderSongList();
    updateStats();
    showToast(`已删除别称「${removed}」`);
  }

  function clearAliases() {
    const key = String(selectedId);
    delete aliases[key];
    renderEditor();
    renderSongList();
    updateStats();
    showToast('已清空该歌曲的所有别称');
  }

  function exportAliases() {
    const sorted = {};
    Object.keys(aliases)
      .sort((a, b) => parseInt(a) - parseInt(b))
      .forEach(k => { sorted[k] = aliases[k]; });
    const json = JSON.stringify(sorted, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'aliases.json'; a.click();
    URL.revokeObjectURL(url);
    showToast('已导出 aliases.json');
  }

  function showImportModal() {
    document.getElementById('alias-import-modal').classList.add('show');
    document.getElementById('alias-import-textarea').value = '';
    document.getElementById('alias-import-textarea').focus();
  }

  function closeImportModal() {
    document.getElementById('alias-import-modal').classList.remove('show');
  }

  function doImport() {
    const text = document.getElementById('alias-import-textarea').value.trim();
    if (!text) return;
    try {
      const data = JSON.parse(text);
      let addedCount = 0;
      Object.entries(data).forEach(([id, aliasList]) => {
        if (!Array.isArray(aliasList)) return;
        if (!aliases[id]) aliases[id] = [];
        aliasList.forEach(a => {
          if (typeof a === 'string' && !aliases[id].some(ex => ex.toLowerCase() === a.toLowerCase())) {
            aliases[id].push(a);
            addedCount++;
          }
        });
      });
      closeImportModal();
      renderSongList();
      renderEditor();
      updateStats();
      showToast(`合并完成，新增 ${addedCount} 个别称`);
    } catch (e) { showToast('JSON 格式错误: ' + e.message); }
  }

  function doImportReplace() {
    const text = document.getElementById('alias-import-textarea').value.trim();
    if (!text) return;
    try {
      const data = JSON.parse(text);
      aliases = {};
      Object.entries(data).forEach(([id, aliasList]) => {
        if (Array.isArray(aliasList)) aliases[id] = aliasList.filter(a => typeof a === 'string');
      });
      closeImportModal();
      renderSongList();
      renderEditor();
      updateStats();
      showToast('已替换全部别称数据');
    } catch (e) { showToast('JSON 格式错误: ' + e.message); }
  }

  function render() {
    return `
      <aside class="sidebar">
        <section class="panel">
          <div class="panel-header">
            <div class="panel-title">歌曲列表</div>
          </div>
          <div class="panel-body">
            <div class="search-box">
              <span class="search-icon">🔎</span>
              <input type="text" id="alias-song-search" placeholder="搜索歌名、ID..." autocomplete="off">
            </div>
            <div class="helper-list" id="alias-song-list-container">
              <div class="empty-state">加载中...</div>
            </div>
          </div>
        </section>
      </aside>
      <main class="main">
        <section class="panel">
          <div class="panel-header">
            <div class="panel-title">别称编辑</div>
          </div>
          <div class="panel-body" id="alias-editor-container">
            <div class="editor-empty">← 从左侧选择一首歌曲<br>即可编辑其别称</div>
          </div>
        </section>
        <div class="toolbar" style="justify-content:flex-end">
          <button class="btn" type="button" onclick="AliasEditor.showImportModal()">导入</button>
          <button class="btn btn-success" type="button" onclick="AliasEditor.exportAliases()">导出 JSON</button>
        </div>
      </main>`;
  }

  function init() {
    document.getElementById('alias-song-search').addEventListener('input', (e) => {
      searchQuery = e.target.value;
      renderSongList();
    });
    return loadData();
  }

  // Public API
  return {
    init, render,
    addAliasFromInput, clearAliases,
    showImportModal, closeImportModal, doImport, doImportReplace, exportAliases,
  };
})();
