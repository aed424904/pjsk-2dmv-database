import { spawnSync } from 'node:child_process';
import { createReadStream, existsSync, mkdirSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';


const PROJECT_ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const DIST_ROOT = resolve(PROJECT_ROOT, 'dist');
const SCREENSHOT_ROOT = resolve(PROJECT_ROOT, 'output', 'playwright');
const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};


function assert(condition, message) {
  if (!condition) throw new Error(message);
}


function buildSite() {
  const python = process.env.PROJECT_SEKAI_PYTHON || 'python';
  const result = spawnSync(python, ['scripts/build_site.py'], {
    cwd: PROJECT_ROOT,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.status !== 0) {
    throw new Error(`站点构建失败：${result.stderr || result.stdout || `exit ${result.status}`}`);
  }
}


function createStaticServer() {
  return createServer((request, response) => {
    try {
      if (!['GET', 'HEAD'].includes(request.method || 'GET')) {
        response.writeHead(405).end('Method Not Allowed');
        return;
      }

      const url = new URL(request.url || '/', 'http://127.0.0.1');
      const relativePath = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname)
        .replace(/^[/\\]+/, '');
      const filePath = resolve(DIST_ROOT, relativePath);
      if (filePath !== DIST_ROOT && !filePath.startsWith(`${DIST_ROOT}${sep}`)) {
        response.writeHead(403).end('Forbidden');
        return;
      }
      if (!existsSync(filePath)) {
        response.writeHead(404).end('Not Found');
        return;
      }

      response.writeHead(200, {
        'Cache-Control': 'no-store',
        'Content-Type': MIME_TYPES[extname(filePath).toLowerCase()] || 'application/octet-stream',
      });
      if (request.method === 'HEAD') response.end();
      else createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(500).end(error.message);
    }
  });
}


function listen(server) {
  return new Promise((resolveListen, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      server.removeListener('error', reject);
      const address = server.address();
      resolveListen(`http://127.0.0.1:${address.port}`);
    });
  });
}


function closeServer(server) {
  return new Promise(resolveClose => {
    if (!server.listening) resolveClose();
    else server.close(() => resolveClose());
  });
}


async function launchBrowser() {
  try {
    return await chromium.launch({ channel: 'chrome', headless: true });
  } catch (chromeError) {
    try {
      return await chromium.launch({ headless: true });
    } catch (chromiumError) {
      throw new Error(
        `无法启动 Chrome/Chromium。请运行 npx playwright install chromium。\n${chromeError.message}\n${chromiumError.message}`,
      );
    }
  }
}


function collectErrors(page, baseUrl) {
  const errors = [];
  const firstPartyHost = new URL(baseUrl).host;
  page.on('console', message => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('pageerror', error => errors.push(`page: ${error.message}`));
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.host === firstPartyHost && response.status() >= 400) {
      errors.push(`http ${response.status()}: ${url.pathname}`);
    }
  });
  return errors;
}


async function waitForNumericText(page, selector, minimum = 1, label = selector) {
  try {
    await page.waitForFunction(
      ({ target, min }) => Number(document.querySelector(target)?.textContent) >= min,
      { target: selector, min: minimum },
    );
  } catch (error) {
    throw new Error(`${label} 未在限时内就绪（${selector} >= ${minimum}）：${error.message}`);
  }
  return Number(await page.locator(selector).textContent());
}


async function checkSongViewer(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = collectErrors(page, baseUrl);
  try {
    await page.goto(`${baseUrl}/index.html`, { waitUntil: 'domcontentloaded' });
    const total = await waitForNumericText(page, '#stat-total', 700, '歌曲页');
    await page.locator('#search-input').fill('洛基');
    await page.waitForFunction(() => Number(document.querySelector('#stat-filtered')?.textContent) === 1);
    assert(new URL(page.url()).searchParams.get('q') === '洛基', '歌曲搜索词未写入 URL');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => Number(document.querySelector('#stat-filtered')?.textContent) === 1);
    assert(await page.locator('#search-input').inputValue() === '洛基', '歌曲搜索词刷新后未恢复');

    await page.locator('.sort-button[data-sort="title"]').click();
    const sortedUrl = new URL(page.url());
    assert(sortedUrl.searchParams.get('sort') === 'title', '歌曲排序字段未写入 URL');
    assert(sortedUrl.searchParams.get('dir') === 'asc', '歌曲排序方向未写入 URL');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => Number(document.querySelector('#stat-filtered')?.textContent) === 1);
    assert(await page.locator('#sort-title').textContent() === '▲', '歌曲排序刷新后未恢复');
    const matchedTitle = (await page.locator('.song-title').first().textContent() || '').trim();
    assert(matchedTitle === 'ロキ', `别称搜索结果错误：${matchedTitle}`);

    const row = page.locator('.song-row').first();
    await row.click();
    assert(await row.locator('.expand-arrow').getAttribute('aria-expanded') === 'true', '歌曲详情未展开');
    assert(await page.locator('.song-detail').count() === 1, '歌曲详情节点数异常');

    await page.goto(`${baseUrl}/index.html`, { waitUntil: 'domcontentloaded' });
    await waitForNumericText(page, '#stat-total', 700, '歌曲页筛选检查');
    const expected = await page.evaluate(async () => {
      const songs = await (await fetch('output/combined_music_data.json', { cache: 'no-store' })).json();
      const teamTags = new Set(['light_music_club', 'idol', 'street', 'theme_park', 'school_refusal', 'vocaloid']);
      return {
        virtualSingerOnly: songs.filter(song => {
          const units = (song.tags || []).filter(tag => teamTags.has(tag));
          return units.length === 1 && units[0] === 'vocaloid';
        }).length,
        original: songs.filter(song => song.songType === 'original').length,
        cover: songs.filter(song => song.songType === 'cover').length,
        miku: songs.filter(song => (song.vocals || []).some(vocal => (
          (vocal.characters || []).some(character => (
            character.characterType === 'game_character' && Number(character.characterId) === 21
          ))
        ))).length,
      };
    });

    await page.locator('.sort-button[data-sort="releasedAt"]').click();
    assert(new URL(page.url()).searchParams.get('sort') === 'releasedAt', '投稿时间排序字段未写入 URL');
    assert(await page.locator('#sort-releasedAt').textContent() === '▲', '投稿时间升序指示未更新');
    const publicationDates = await page.locator('.song-release-date').evaluateAll(items => items.slice(0, 10).map(item => item.textContent.trim()));
    assert(publicationDates.every((date, index) => index === 0 || publicationDates[index - 1] <= date), `投稿时间未按升序排列：${publicationDates.join(',')}`);

    const vsFilter = page.locator('#tag-filters [data-filter="tag"][data-value="vocaloid"]');
    await vsFilter.click();
    await page.waitForFunction(count => Number(document.querySelector('#stat-filtered')?.textContent) === count, expected.virtualSingerOnly);
    assert(await page.evaluate(() => typeof hasOnlyVirtualSingerTeam === 'function'), 'V.S. 精确筛选逻辑未加载');
    const visibleTeamLabels = await page.locator('.song-row .song-tags').evaluateAll(items => items.map(item => (
      [...item.querySelectorAll('.tag')].map(tag => tag.textContent.trim())
    )));
    assert(visibleTeamLabels.every(labels => labels.length === 1 && labels[0] === 'V.S.'), 'V.S. 筛选包含了其他团队歌曲');
    await vsFilter.click();

    const songTypeFilter = page.locator('#song-type-filters [data-filter="songType"][data-value="original"]');
    await songTypeFilter.click();
    await page.waitForFunction(count => Number(document.querySelector('#stat-filtered')?.textContent) === count, expected.original);
    assert(new URL(page.url()).searchParams.get('songType') === 'original', '歌曲类型筛选未写入 URL');
    await songTypeFilter.click();
    const coverFilter = page.locator('#song-type-filters [data-filter="songType"][data-value="cover"]');
    await coverFilter.click();
    await page.waitForFunction(count => Number(document.querySelector('#stat-filtered')?.textContent) === count, expected.cover);
    await coverFilter.click();

    const characterFilter = page.locator('#character-filters [data-filter="character"][data-value="game_character:21"]');
    await characterFilter.click();
    await page.waitForFunction(count => Number(document.querySelector('#stat-filtered')?.textContent) === count, expected.miku);
    assert(new URL(page.url()).searchParams.get('character') === 'game_character:21', '单角色筛选未写入 URL');
    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      mkdirSync(SCREENSHOT_ROOT, { recursive: true });
      await page.screenshot({ path: resolve(SCREENSHOT_ROOT, 'song-type-character-filters.png'), fullPage: false });
    }
    assert(errors.length === 0, errors.join('\n'));
    return { total, matchedTitle, expected, publicationDates };
  } finally {
    await page.close();
  }
}


async function checkVideoViewer(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = collectErrors(page, baseUrl);
  try {
    await page.goto(`${baseUrl}/video_viewer.html`, { waitUntil: 'domcontentloaded' });
    const total = await waitForNumericText(page, '#stat-total', 400, '视频页');
    await page.locator('#search-input').fill('CRASH THE PARTY');
    await page.waitForFunction(() => Number(document.querySelector('#stat-filtered')?.textContent) === 2);
    assert(new URL(page.url()).searchParams.get('q') === 'CRASH THE PARTY', '视频搜索词未写入 URL');

    const row = page.locator('.video-row').first();
    await row.focus();
    await page.keyboard.press('Enter');
    assert(await row.getAttribute('aria-expanded') === 'true', '视频详情未展开');
    assert(await page.locator('.video-detail').count() === 1, '视频详情节点数异常');
    const staffGroupLabels = await page.locator('.video-detail .staff-role-group-label').allTextContents();
    assert(staffGroupLabels.includes('音乐'), `视频详情缺少音乐 Staff 分组：${staffGroupLabels.join('/')}`);
    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      mkdirSync(SCREENSHOT_ROOT, { recursive: true });
      await page.locator('.video-detail').screenshot({ path: resolve(SCREENSHOT_ROOT, 'video-staff-groups.png') });
    }
    assert(errors.length === 0, errors.join('\n'));
    return { total, filtered: 2, staffGroupLabels };
  } finally {
    await page.close();
  }
}


async function checkEditorAndLegacyRoute(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = collectErrors(page, baseUrl);
  try {
    await page.goto(`${baseUrl}/editor.html?tab=video`, { waitUntil: 'domcontentloaded' });
    await waitForNumericText(page, '#stat-catalog', 700, '编辑器曲库');
    await page.locator('#tab-alias').click();
    assert(new URL(page.url()).searchParams.get('tab') === 'alias', '编辑器 URL 标签未更新');
    assert(await page.locator('.tab-btn[aria-selected="true"]').getAttribute('data-tab') === 'alias', '别称标签未激活');

    await page.goto(`${baseUrl}/alias_editor.html?source=smoke#keep`, { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/editor.html?source=smoke&tab=alias#keep');
    assert(await page.locator('.tab-btn[aria-selected="true"]').getAttribute('data-tab') === 'alias', '旧别称入口未到达正确标签');
    assert(errors.length === 0, errors.join('\n'));
    return { legacyRoute: new URL(page.url()).pathname + new URL(page.url()).search + new URL(page.url()).hash };
  } finally {
    await page.close();
  }
}


async function checkStaffReviewEditor(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1050 } });
  const errors = collectErrors(page, baseUrl);
  try {
    await page.goto(`${baseUrl}/editor.html?tab=staff`, { waitUntil: 'domcontentloaded' });
    const expectedReviewStats = await page.evaluate(async () => {
      const response = await fetch('output/staff_review.json', { cache: 'no-store' });
      const rows = await response.json();
      return {
        records: rows.length,
        unknownLines: rows.reduce((total, row) => total + (row.unknownRoleLines || []).length, 0),
        unparsedLines: rows.reduce((total, row) => total + (row.unparsedLines || []).length, 0),
      };
    });
    assert(expectedReviewStats.records > 0, 'Staff 复核样本为空，无法执行编辑器交互烟测');
    await page.waitForFunction(expected => (
      Number(document.querySelector('#stat-staff-records')?.textContent) === expected.records
      && Number(document.querySelector('#stat-staff-unknown')?.textContent) === expected.unknownLines
      && Number(document.querySelector('#stat-staff-unparsed')?.textContent) === expected.unparsedLines
    ), expectedReviewStats);
    const reviewRecords = Number(await page.locator('#stat-staff-records').textContent());
    const unknownLines = Number(await page.locator('#stat-staff-unknown').textContent());
    const unparsedLines = Number(await page.locator('#stat-staff-unparsed').textContent());
    assert(
      reviewRecords === expectedReviewStats.records
        && unknownLines === expectedReviewStats.unknownLines
        && unparsedLines === expectedReviewStats.unparsedLines,
      `Staff 审计统计与 JSON 不一致：${reviewRecords}/${unknownLines}/${unparsedLines}`,
    );
    assert(new URL(page.url()).searchParams.get('tab') === 'staff', 'Staff 标签未由 URL 激活');

    const desktopReadingState = await page.evaluate(() => {
      const app = document.querySelector('#app-container');
      const queue = document.querySelector('.staff-review-sidebar');
      const issue = document.querySelector('.staff-issue-card');
      const source = document.querySelector('.staff-source-block code');
      const input = document.querySelector('.staff-action-card .input');
      return {
        fontFamily: getComputedStyle(document.body).fontFamily,
        appWidth: app.getBoundingClientRect().width,
        queueWidth: queue.getBoundingClientRect().width,
        issueCardHeight: issue.getBoundingClientRect().height,
        issueFontSize: parseFloat(getComputedStyle(document.querySelector('.staff-issue-song')).fontSize),
        sourceFontSize: parseFloat(getComputedStyle(source).fontSize),
        inputHeight: input.getBoundingClientRect().height,
      };
    });
    assert(desktopReadingState.fontFamily.includes('Noto Sans SC'), `Staff 多语种字体未生效：${desktopReadingState.fontFamily}`);
    assert(desktopReadingState.appWidth >= 1500, `Staff 工作区未充分拉宽：${desktopReadingState.appWidth}`);
    assert(desktopReadingState.queueWidth >= 315, `Staff 问题队列过窄：${desktopReadingState.queueWidth}`);
    assert(desktopReadingState.issueCardHeight >= 132, `Staff 问题卡片过矮：${desktopReadingState.issueCardHeight}`);
    assert(desktopReadingState.issueFontSize >= 15 && desktopReadingState.sourceFontSize >= 14, 'Staff 核心文字未放大');
    assert(desktopReadingState.inputHeight >= 48, `Staff 输入控件过矮：${desktopReadingState.inputHeight}`);

    const roleIssue = page.locator('.staff-issue-card').filter({ has: page.locator('.staff-candidate') }).first();
    await roleIssue.click();
    const candidateRole = await page.locator('#staff-role-raw').inputValue();
    assert(candidateRole.length > 0, 'Staff 未能从未知职位中提取候选角色');
    await page.locator('#staff-role-value').selectOption('illustrator');
    await page.locator('#staff-save-role-btn').click();
    await page.waitForFunction(() => Number(document.querySelector('#stat-staff-fixes')?.textContent) === 1);
    assert(await page.locator('#staff-correction-list').getByText(candidateRole, { exact: true }).count() >= 1, '角色映射未进入维护规则');

    await page.locator('#staff-kind-filter').selectOption('unparsed');
    const unparsedIssue = page.locator('.staff-issue-card').first();
    await unparsedIssue.click();
    const ignoredLine = await page.locator('.staff-source-block code').textContent();
    await page.locator('#staff-toggle-ignore-btn').click();
    await page.waitForFunction(() => Number(document.querySelector('#stat-staff-fixes')?.textContent) === 2);
    assert(await page.locator('#staff-correction-list').getByText(ignoredLine, { exact: true }).count() >= 1, '忽略原文未进入维护规则');

    await page.locator('#tab-alias').click();
    await page.locator('#tab-staff').click();
    assert(Number(await page.locator('#stat-staff-fixes').textContent()) === 2, '标签切换后 Staff 修正草稿丢失');
    assert(await page.locator('#staff-correction-list').getByText(candidateRole, { exact: true }).count() >= 1, '标签切换后角色映射丢失');

    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      mkdirSync(SCREENSHOT_ROOT, { recursive: true });
      await page.waitForFunction(() => !document.querySelector('#toast')?.classList.contains('show'));
      await page.waitForTimeout(350);
      await page.screenshot({ path: resolve(SCREENSHOT_ROOT, 'staff-review-workbench.png'), fullPage: false });
    }

    await page.locator('#staff-review-search').fill('');
    await page.locator('#staff-kind-filter').selectOption('all');
    await page.setViewportSize({ width: 468, height: 878 });
    const mobileQueueState = await page.evaluate(() => {
      const songTitles = [...document.querySelectorAll('.staff-issue-song')];
      return {
        songTitleCount: songTitles.length,
        songTitlesOverflowing: songTitles.filter(title => (
          title.scrollWidth > title.clientWidth + 1 || title.scrollHeight > title.clientHeight + 1
        )).length,
        compressedSongTitles: songTitles.filter(title => (
          title.getBoundingClientRect().height + 0.5 < parseFloat(getComputedStyle(title).lineHeight)
        )).length,
      };
    });
    assert(mobileQueueState.songTitleCount > 0, '窄屏 Staff 问题队列没有可检查的歌名');
    assert(mobileQueueState.songTitlesOverflowing === 0, `窄屏 Staff 歌名仍被截断：${mobileQueueState.songTitlesOverflowing}`);
    assert(mobileQueueState.compressedSongTitles === 0, `窄屏 Staff 歌名仍被压扁：${mobileQueueState.compressedSongTitles}`);
    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      await page.locator('.staff-issue-list').screenshot({ path: resolve(SCREENSHOT_ROOT, 'staff-review-mobile-queue.png') });
    }

    await page.setViewportSize({ width: 390, height: 844 });
    const mobileState = await page.evaluate(() => ({
      viewportWidth: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      appColumns: getComputedStyle(document.querySelector('#app-container')).gridTemplateColumns,
      appWidth: document.querySelector('#app-container').getBoundingClientRect().width,
      overflowingElements: [...document.querySelectorAll('body *')]
        .filter(element => element.getBoundingClientRect().right > innerWidth + 1)
        .slice(0, 8)
        .map(element => ({
          tag: element.tagName,
          className: element.className,
          right: Math.round(element.getBoundingClientRect().right),
          width: Math.round(element.getBoundingClientRect().width),
        })),
    }));
    assert(mobileState.scrollWidth <= mobileState.viewportWidth, `手机 Staff 工作台横向溢出：${mobileState.scrollWidth}/${mobileState.viewportWidth} ${JSON.stringify(mobileState.overflowingElements)}`);
    assert(!mobileState.appColumns.includes('300px'), `手机 Staff 工作台未切换单列：${mobileState.appColumns}`);
    assert(mobileState.appWidth >= 360, `手机 Staff 工作区未利用可用宽度：${mobileState.appWidth}`);
    await page.locator('.staff-issue-card').first().click();
    await page.waitForFunction(() => document.querySelector('#staff-review-detail')?.getBoundingClientRect().top < 260);
    mobileState.detailTop = await page.locator('#staff-review-detail').evaluate(element => element.getBoundingClientRect().top);
    assert(mobileState.detailTop < 260, `手机选择问题后未滚动到修正区：${mobileState.detailTop}`);
    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      await page.screenshot({ path: resolve(SCREENSHOT_ROOT, 'staff-review-mobile.png'), fullPage: false });
    }
    assert(errors.length === 0, errors.join('\n'));
    return { reviewRecords, unknownLines, unparsedLines, fixes: 2, desktopReadingState, mobileQueueState, mobileState };
  } finally {
    await page.close();
  }
}


async function checkMobileVideoCards(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = collectErrors(page, baseUrl);
  try {
    await page.goto(`${baseUrl}/video_viewer.html`, { waitUntil: 'domcontentloaded' });
    const total = await waitForNumericText(page, '#stat-total', 400, '手机视频页');
    const drawerTrigger = page.locator('#filter-drawer-trigger');
    await drawerTrigger.click();
    const drawer = page.locator('#sidebar');
    assert(await drawerTrigger.getAttribute('aria-expanded') === 'true', '手机筛选按钮未标记展开');
    assert(await drawer.getAttribute('aria-hidden') === 'false', '手机筛选抽屉仍对辅助技术隐藏');
    assert(await drawer.evaluate(element => element.inert) === false, '手机筛选抽屉打开后仍不可交互');

    await drawer.locator('[data-filter="types"][data-value="official_2dmv"]').click();
    await page.waitForFunction(() => new URL(location.href).searchParams.get('type') === 'official_2dmv');
    await page.waitForFunction(expected => {
      const value = Number(document.querySelector('#stat-filtered')?.textContent);
      return value > 0 && value < expected;
    }, total);
    assert(await page.locator('#active-filter-count').textContent() === '1', '手机已选筛选数未更新');
    const filtered = Number(await page.locator('#stat-filtered').textContent());
    assert(await page.locator('#filter-drawer-result-count').textContent() === String(filtered), '抽屉结果数未更新');
    if (process.env.PROJECT_SEKAI_SCREENSHOTS === '1') {
      mkdirSync(SCREENSHOT_ROOT, { recursive: true });
      await page.screenshot({ path: resolve(SCREENSHOT_ROOT, 'mobile-filter-drawer.png'), fullPage: false });
    }
    await page.locator('#filter-drawer-done').click();
    assert(await drawerTrigger.getAttribute('aria-expanded') === 'false', '完成后筛选抽屉未关闭');
    assert(await drawer.getAttribute('aria-hidden') === 'true', '关闭后筛选抽屉仍暴露给辅助技术');

    await page.goBack();
    await page.waitForFunction(() => !new URL(location.href).searchParams.has('type'));
    await page.waitForFunction(expected => Number(document.querySelector('#stat-filtered')?.textContent) === expected, total);
    assert(await page.locator('#active-filter-count').isHidden(), '返回历史后筛选计数未清除');

    const row = page.locator('.video-row').first();
    const state = await row.evaluate(rowElement => {
      const meta = rowElement.querySelector('.video-meta');
      const metadata = [...meta.querySelectorAll(':scope > span')];
      return {
        gridTemplateAreas: getComputedStyle(rowElement).gridTemplateAreas,
        metaDisplay: getComputedStyle(meta).display,
        metadataCount: metadata.length,
        metadataVisible: metadata.every(item => item.getBoundingClientRect().width > 0 && item.getBoundingClientRect().height > 0),
        titleWhiteSpace: getComputedStyle(rowElement.querySelector('.video-title')).whiteSpace,
        viewportWidth: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
      };
    });
    assert(state.gridTemplateAreas.includes('type title arrow'), `手机卡片网格异常：${state.gridTemplateAreas}`);
    assert(state.gridTemplateAreas.includes('meta meta meta'), `手机元数据网格异常：${state.gridTemplateAreas}`);
    assert(state.metaDisplay === 'flex', `手机元数据布局异常：${state.metaDisplay}`);
    assert(state.metadataCount === 4 && state.metadataVisible, '手机卡片未完整显示四个元数据字段');
    assert(state.titleWhiteSpace === 'normal', `手机标题未允许换行：${state.titleWhiteSpace}`);
    assert(state.scrollWidth <= state.viewportWidth, `手机页面横向溢出：${state.scrollWidth}/${state.viewportWidth}`);
    await row.click();
    state.expanded = await row.getAttribute('aria-expanded');
    state.detailVisible = await page.locator('.video-detail').first().isVisible();
    state.drawerFiltered = filtered;
    assert(state.expanded === 'true' && state.detailVisible, '手机卡片详情未正常展开');
    assert(errors.length === 0, errors.join('\n'));
    return state;
  } finally {
    await page.close();
  }
}


async function main() {
  let server;
  let browser;
  try {
    buildSite();
    server = createStaticServer();
    const baseUrl = await listen(server);
    browser = await launchBrowser();
    const results = {
      songs: await checkSongViewer(browser, baseUrl),
      videos: await checkVideoViewer(browser, baseUrl),
      editor: await checkEditorAndLegacyRoute(browser, baseUrl),
      staffReview: await checkStaffReviewEditor(browser, baseUrl),
      mobile: await checkMobileVideoCards(browser, baseUrl),
    };
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    if (browser) await browser.close();
    if (server) await closeServer(server);
  }
}


main().catch(error => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exitCode = 1;
});
