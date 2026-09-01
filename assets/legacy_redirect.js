(function () {
  'use strict';

  const ROUTES = {
    music: { path: 'index.html', label: '歌曲列表' },
    video: { path: 'editor.html', tab: 'video', label: '视频补录' },
    alias: { path: 'editor.html', tab: 'alias', label: '别称编辑' },
  };

  function buildTarget(routeKey, locationObject) {
    const route = ROUTES[routeKey];
    if (!route) return 'index.html';

    const params = new URLSearchParams(locationObject.search);
    if (route.tab) params.set('tab', route.tab);
    const query = params.toString();
    return `${route.path}${query ? `?${query}` : ''}${locationObject.hash || ''}`;
  }

  function startRedirect(locationObject) {
    const routeKey = document.body.dataset.legacyRoute;
    const route = ROUTES[routeKey] || ROUTES.music;
    const target = buildTarget(routeKey, locationObject);
    const link = document.getElementById('continue-link');
    const destination = document.getElementById('destination-label');
    if (link) link.href = target;
    if (destination) destination.textContent = route.label;

    window.setTimeout(() => {
      locationObject.replace(target);
    }, 180);
  }

  window.LegacyRedirect = { ROUTES, buildTarget, startRedirect };
  startRedirect(window.location);
})();
