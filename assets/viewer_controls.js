(function attachViewerControls(global) {
  'use strict';

  const MOBILE_QUERY = '(max-width: 900px)';
  const FOCUSABLE_SELECTOR = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(',');

  function createFilterDrawer(options = {}) {
    const sidebar = document.querySelector(options.sidebar || '#sidebar');
    const trigger = document.querySelector(options.trigger || '#filter-drawer-trigger');
    const backdrop = document.querySelector(options.backdrop || '#filter-drawer-backdrop');
    const closeButton = document.querySelector(options.closeButton || '#filter-drawer-close');
    const doneButton = document.querySelector(options.doneButton || '#filter-drawer-done');
    const countBadge = document.querySelector(options.countBadge || '#active-filter-count');
    const resultCount = document.querySelector(options.resultCount || '#filter-drawer-result-count');
    const filteredStat = document.querySelector(options.filteredStat || '#stat-filtered');
    const mobileMedia = global.matchMedia(MOBILE_QUERY);
    let isOpen = false;
    let lastFocusedElement = null;

    if (!sidebar || !trigger || !backdrop || !closeButton || !doneButton) {
      return { close() {}, open() {}, update() {} };
    }

    function getFocusableElements() {
      return [...sidebar.querySelectorAll(FOCUSABLE_SELECTOR)].filter(element => {
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    }

    function setOpen(nextOpen, { restoreFocus = true } = {}) {
      if (!mobileMedia.matches && nextOpen) return;
      isOpen = Boolean(nextOpen && mobileMedia.matches);
      sidebar.classList.toggle('is-open', isOpen);
      backdrop.classList.toggle('is-open', isOpen);
      document.body.classList.toggle('filter-drawer-open', isOpen);
      trigger.setAttribute('aria-expanded', String(isOpen));
      backdrop.setAttribute('aria-hidden', String(!isOpen));
      sidebar.inert = mobileMedia.matches && !isOpen;
      if (mobileMedia.matches) sidebar.setAttribute('aria-hidden', String(!isOpen));
      else sidebar.removeAttribute('aria-hidden');

      if (isOpen) {
        lastFocusedElement = document.activeElement;
        global.requestAnimationFrame(() => closeButton.focus());
      } else if (restoreFocus && lastFocusedElement?.focus) {
        lastFocusedElement.focus();
      }
    }

    function syncViewport() {
      if (mobileMedia.matches) {
        sidebar.inert = !isOpen;
        sidebar.setAttribute('aria-hidden', String(!isOpen));
      } else {
        isOpen = false;
        sidebar.inert = false;
        sidebar.removeAttribute('aria-hidden');
        sidebar.classList.remove('is-open');
        backdrop.classList.remove('is-open');
        backdrop.setAttribute('aria-hidden', 'true');
        trigger.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('filter-drawer-open');
      }
    }

    function handleKeydown(event) {
      if (!isOpen) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        setOpen(false);
        return;
      }
      if (event.key === 'Tab') {
        const focusable = getFocusableElements();
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }

    function update() {
      const activeCount = sidebar.querySelectorAll('[data-filter] input:checked').length;
      if (countBadge) {
        countBadge.textContent = String(activeCount);
        countBadge.hidden = activeCount === 0;
      }
      if (resultCount && filteredStat) {
        resultCount.textContent = filteredStat.textContent.trim();
      }
    }

    trigger.addEventListener('click', () => setOpen(true));
    backdrop.addEventListener('click', () => setOpen(false));
    closeButton.addEventListener('click', () => setOpen(false));
    doneButton.addEventListener('click', () => setOpen(false));
    document.addEventListener('keydown', handleKeydown);
    mobileMedia.addEventListener?.('change', syncViewport);
    syncViewport();

    return {
      close: () => setOpen(false),
      open: () => setOpen(true),
      update,
    };
  }

  function createUrlState(config) {
    const searchInput = document.querySelector(config.searchInput || '#search-input');
    const groups = config.groups || [];
    const knownParams = ['q', 'sort', 'dir', ...groups.map(group => group.param)];
    const defaultSortField = config.defaultSortField;
    const defaultSortAsc = Boolean(config.defaultSortAsc);
    const allowedSortFields = new Set(config.allowedSortFields || [defaultSortField]);

    function restore() {
      const params = new URLSearchParams(global.location.search);
      if (searchInput) searchInput.value = params.get('q') || '';

      groups.forEach(group => {
        group.set.clear();
        const availableValues = new Set(
          [...document.querySelectorAll(`[data-filter="${group.filterType}"]`)]
            .map(element => element.dataset.value),
        );
        params.getAll(group.param).forEach(value => {
          if (availableValues.has(value)) group.set.add(value);
        });
      });

      const requestedSortField = params.get('sort');
      const sortField = allowedSortFields.has(requestedSortField) ? requestedSortField : defaultSortField;
      const requestedDirection = params.get('dir');
      const sortAsc = requestedSortField && allowedSortFields.has(requestedSortField)
        && (requestedDirection === 'asc' || requestedDirection === 'desc')
        ? requestedDirection === 'asc'
        : defaultSortAsc;
      config.setSort({ field: sortField, asc: sortAsc });
      config.onRestore?.();
    }

    function sync() {
      const url = new URL(global.location.href);
      const params = new URLSearchParams(url.search);
      knownParams.forEach(param => params.delete(param));

      const query = searchInput?.value.trim() || '';
      if (query) params.set('q', query);
      groups.forEach(group => {
        [...group.set].sort((a, b) => a.localeCompare(b)).forEach(value => {
          params.append(group.param, value);
        });
      });

      const sort = config.getSort();
      if (sort.field !== defaultSortField || sort.asc !== defaultSortAsc) {
        params.set('sort', sort.field);
        params.set('dir', sort.asc ? 'asc' : 'desc');
      }

      url.search = params.toString();
      const nextUrl = `${url.pathname}${url.search}${url.hash}`;
      const currentUrl = `${global.location.pathname}${global.location.search}${global.location.hash}`;
      if (nextUrl !== currentUrl) history.pushState(null, '', nextUrl);
    }

    global.addEventListener('popstate', restore);
    return { restore, sync };
  }

  global.ViewerControls = {
    createFilterDrawer,
    createUrlState,
  };
})(window);
