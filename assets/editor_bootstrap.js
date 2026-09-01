/* ========== Bootstrap: Tab Switching + Init ========== */
(function() {
  if (handleFileProtocolAccess()) return;

  const VALID_TABS = new Set(['video', 'alias', 'staff']);
  let activeTab = null;
  const appContainer = document.getElementById('app-container');
  const tabButtons = Array.from(document.querySelectorAll('.tab-btn[role="tab"]'));

  function requestedTab() {
    const tab = new URLSearchParams(location.search).get('tab');
    return VALID_TABS.has(tab) ? tab : 'video';
  }

  function updateTabUrl(tab) {
    const params = new URLSearchParams(location.search);
    params.set('tab', tab);
    const query = params.toString();
    const nextUrl = `${location.pathname}${query ? `?${query}` : ''}${location.hash}`;
    history.replaceState({ tab }, '', nextUrl);
  }

  function activateTab(tab, options = {}) {
    const nextTab = VALID_TABS.has(tab) ? tab : 'video';
    const selectedButton = tabButtons.find(button => button.dataset.tab === nextTab);
    document.body.dataset.editorTab = nextTab;

    tabButtons.forEach(button => {
      const selected = button === selectedButton;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });

    document.getElementById('stats-video').style.display = nextTab === 'video' ? 'flex' : 'none';
    document.getElementById('stats-alias').style.display = nextTab === 'alias' ? 'flex' : 'none';
    document.getElementById('stats-staff').style.display = nextTab === 'staff' ? 'flex' : 'none';
    appContainer.setAttribute('aria-labelledby', `tab-${nextTab}`);

    if (nextTab !== activeTab || !appContainer.children.length) {
      if (nextTab === 'video') {
        appContainer.innerHTML = ManualVideoEditor.render();
        ManualVideoEditor.init();
      } else if (nextTab === 'alias') {
        appContainer.innerHTML = AliasEditor.render();
        AliasEditor.init();
      } else {
        appContainer.innerHTML = StaffReviewEditor.render();
        StaffReviewEditor.init();
      }
      activeTab = nextTab;
    }

    if (options.updateUrl) updateTabUrl(nextTab);
    if (options.focus) selectedButton?.focus();
  }

  function activateRequestedTab() {
    const rawTab = new URLSearchParams(location.search).get('tab');
    activateTab(requestedTab(), {
      updateUrl: rawTab !== null && !VALID_TABS.has(rawTab),
    });
  }

  // Modal overlay click-to-close (modals are static, bind once)
  document.getElementById('import-modal').addEventListener('click', event => {
    if (event.target.id === 'import-modal') ManualVideoEditor.closeImportModal();
  });
  document.getElementById('override-import-modal').addEventListener('click', event => {
    if (event.target.id === 'override-import-modal') ManualVideoEditor.closeOverrideImportModal();
  });
  document.getElementById('alias-import-modal').addEventListener('click', event => {
    if (event.target.id === 'alias-import-modal') AliasEditor.closeImportModal();
  });

  tabButtons.forEach((button, index) => {
    button.addEventListener('click', () => activateTab(button.dataset.tab, { updateUrl: true }));
    button.addEventListener('keydown', event => {
      const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
      if (!keys.includes(event.key)) return;
      event.preventDefault();
      let targetIndex = index;
      if (event.key === 'ArrowLeft') targetIndex = (index - 1 + tabButtons.length) % tabButtons.length;
      if (event.key === 'ArrowRight') targetIndex = (index + 1) % tabButtons.length;
      if (event.key === 'Home') targetIndex = 0;
      if (event.key === 'End') targetIndex = tabButtons.length - 1;
      activateTab(tabButtons[targetIndex].dataset.tab, { updateUrl: true, focus: true });
    });
  });

  window.addEventListener('popstate', activateRequestedTab);
  activateRequestedTab();
})();
