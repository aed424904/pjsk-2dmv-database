import fs from 'node:fs/promises';
import path from 'node:path';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';


const PROJECT_ROOT = path.resolve(import.meta.dirname, '..');
const OUTPUT_DIR = path.resolve(process.argv[2] || path.join(PROJECT_ROOT, 'outputs', 'song-data-export'));
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'Project_Sekai_歌曲全量数据.xlsx');
const PREVIEW_DIR = path.join(OUTPUT_DIR, 'previews');

const SONG_TYPE_LABELS = { original: '原创曲', cover: '翻唱曲' };
const VOCAL_TYPE_LABELS = {
  original_song: '原唱',
  sekai: 'SEKAI ver.',
  another_vocal: 'Another Vocal',
  virtual_singer: 'Virtual Singer',
  instrumental: 'Instrumental',
  april_fool_2022: '愚人节版',
  streaming_live: 'Connect Live',
};
const UNIT_LABELS = {
  light_music_club: 'Leo/need',
  idol: 'MORE MORE JUMP!',
  street: 'Vivid BAD SQUAD',
  theme_park: 'Wonderlands×Showtime',
  school_refusal: '25时、Nightcord见。',
  vocaloid: 'Virtual Singer',
};


async function loadJson(relativePath) {
  return JSON.parse(await fs.readFile(path.join(PROJECT_ROOT, relativePath), 'utf8'));
}

function toDate(value) {
  if (value == null || value === '') return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function buildCharacterLookup(gameCharacters, outsideCharacters) {
  const lookup = new Map();
  gameCharacters.forEach(character => {
    const name = [character.firstName, character.givenName].filter(Boolean).join('')
      || character.name
      || `#${character.id}`;
    lookup.set(`game_character:${character.id}`, name);
  });
  outsideCharacters.forEach(character => {
    lookup.set(`outside_character:${character.id}`, `⭐ ${character.name || `#${character.id}`}`);
  });
  return lookup;
}

function getCharacterName(character, lookup) {
  const type = character?.characterType === 'outside_character' ? 'outside_character' : 'game_character';
  const key = `${type}:${character?.characterId}`;
  return lookup.get(key) || key;
}

function getVideoPerformerNames(video) {
  return (video.performerExtraction?.performers || []).join(' / ');
}

function columnName(index) {
  let value = index + 1;
  let name = '';
  while (value > 0) {
    const remainder = (value - 1) % 26;
    name = String.fromCharCode(65 + remainder) + name;
    value = Math.floor((value - 1) / 26);
  }
  return name;
}

function styleSheet(sheet, title, note, headers, rows, tableName, widths, dateColumns = []) {
  const lastColumn = columnName(headers.length - 1);
  const lastRow = rows.length + 4;
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastColumn}1`).merge();
  sheet.getRange('A1').values = [[title]];
  sheet.getRange(`A2:${lastColumn}2`).merge();
  sheet.getRange('A2').values = [[note]];
  sheet.getRange(`A4:${lastColumn}${lastRow}`).values = [headers, ...rows];

  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: '#1668DC',
    font: { bold: true, color: '#FFFFFF', size: 16 },
    verticalAlignment: 'center',
  };
  sheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 30;
  sheet.getRange(`A2:${lastColumn}2`).format = {
    fill: '#EAF2FF',
    font: { color: '#33557A', italic: true, size: 10 },
    verticalAlignment: 'center',
  };
  sheet.getRange(`A2:${lastColumn}2`).format.rowHeight = 24;
  sheet.getRange(`A4:${lastColumn}4`).format = {
    fill: '#DCEAFF',
    font: { bold: true, color: '#173A63' },
    borders: { preset: 'doubleBottom', style: 'thin', color: '#8FB4E5' },
    verticalAlignment: 'center',
  };
  sheet.getRange(`A4:${lastColumn}4`).format.rowHeight = 24;
  sheet.getRange(`A5:${lastColumn}${lastRow}`).format = {
    verticalAlignment: 'center',
    borders: {
      insideHorizontal: { style: 'thin', color: '#E8EDF3' },
    },
  };
  dateColumns.forEach(column => sheet.getRange(`${column}5:${column}${lastRow}`).setNumberFormat('yyyy-mm-dd'));
  widths.forEach((width, index) => {
    sheet.getRange(`${columnName(index)}1:${columnName(index)}${lastRow}`).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(2);
  const table = sheet.tables.add(`A4:${lastColumn}${lastRow}`, true, tableName);
  table.style = 'TableStyleMedium2';
  table.showFilterButton = true;
  table.showBandedColumns = false;
  return { lastColumn, lastRow };
}


const [songs, database, aliases, gameCharacters, outsideCharacters] = await Promise.all([
  loadJson('output/combined_music_data.json'),
  loadJson('output/database_v2.json'),
  loadJson('output/aliases.json'),
  loadJson('sekai-master-db-diff-main/gameCharacters.json'),
  loadJson('sekai-master-db-diff-main/outsideCharacters.json'),
]);

const characterLookup = buildCharacterLookup(gameCharacters, outsideCharacters);
const supplementalByMusicId = new Map((database.songs || []).map(song => [Number(song.sekaiMusicId), song]));

const songRows = songs.map(song => {
  const supplemental = supplementalByMusicId.get(Number(song.id));
  const unitTags = (song.tags || []).filter(tag => UNIT_LABELS[tag]).map(tag => UNIT_LABELS[tag]);
  const displayTags = (song.tags || []).filter(tag => tag !== 'all').map(tag => UNIT_LABELS[tag] || tag);
  return [
    song.id,
    song.title,
    SONG_TYPE_LABELS[song.songType] || song.songType,
    song.creators?.creatorArtistName || '',
    song.creators?.lyricist || '',
    song.creators?.composer || '',
    song.creators?.arranger || '',
    unitTags.join(' / '),
    displayTags.join(' / '),
    (song.categories || []).join(' / '),
    toDate(song.releasedAt),
    toDate(song.publishedAt),
    song.originalVideoLink || '',
    (song.vocals || []).length,
    (supplemental?.videos || []).length,
    supplemental?.sekaiMusicId || song.id,
    (aliases[String(song.id)] || []).join(' / '),
    (supplemental?.videoVersionSummary?.labels || []).join(' / '),
  ];
});

const vocalRows = songs.flatMap(song => (song.vocals || []).map(vocal => [
  song.id,
  song.title,
  SONG_TYPE_LABELS[song.songType] || song.songType,
  vocal.id,
  VOCAL_TYPE_LABELS[vocal.musicVocalType] || vocal.musicVocalType,
  vocal.caption || '',
  (vocal.characters || []).map(character => getCharacterName(character, characterLookup)).join(' / '),
  vocal.assetbundleName || '',
]));

const videoRows = [];
const staffRows = [];
for (const song of songs) {
  const supplemental = supplementalByMusicId.get(Number(song.id));
  for (const video of supplemental?.videos || []) {
    videoRows.push([
      song.id,
      song.title,
      SONG_TYPE_LABELS[song.songType] || song.songType,
      video.type || '',
      video.variant || '',
      video.version?.base || '',
      (video.version?.special || []).join(' / '),
      video.version?.label || '',
      video.videoId || '',
      video.title || '',
      video.channelTitle || '',
      toDate(video.uploadDate),
      video.viewCount ?? null,
      video.likeCount ?? null,
      getVideoPerformerNames(video),
      video.url || '',
      video.sourceName || '',
      video.sourceUrl || '',
    ]);

    const staff = video.staff || {};
    for (const contributor of staff.contributors || staff.allContributors || []) {
      staffRows.push([
        song.id,
        song.title,
        video.videoId || '',
        video.type || '',
        video.title || '',
        contributor.role || '',
        contributor.roleRaw || '',
        contributor.name || '',
        contributor.nameRaw || '',
        contributor.sourceLine || '',
      ]);
    }
    for (const sourceLine of staff.unknownRoleLines || []) {
      staffRows.push([song.id, song.title, video.videoId || '', video.type || '', video.title || '', 'unknown', '', '', '', sourceLine]);
    }
    for (const sourceLine of staff.unparsedLines || []) {
      staffRows.push([song.id, song.title, video.videoId || '', video.type || '', video.title || '', 'unparsed', '', '', '', sourceLine]);
    }
  }
}

const workbook = Workbook.create();
const songSheet = workbook.worksheets.add('歌曲总览');
const vocalSheet = workbook.worksheets.add('歌声版本');
const videoSheet = workbook.worksheets.add('视频');
const staffSheet = workbook.worksheets.add('Staff');

styleSheet(
  songSheet,
  'Project Sekai 歌曲全量数据',
  `共 ${songRows.length} 首歌曲；“视频网站投稿时间”优先采用已关联本家 MV 的最早上传日期，翻唱曲因此显示原曲投稿时间。`,
  ['歌曲ID', '歌名', '歌曲类型', '创作者', '作词', '作曲', '编曲', '团队', '全部标签', 'MV类型', '视频网站投稿时间', '实装时间', '原曲链接', '歌声版本数', '视频数', 'Sekai Music ID', '别称', '视频版本'],
  songRows,
  'SongsTable',
  [10, 28, 10, 18, 18, 18, 18, 24, 28, 16, 16, 14, 38, 12, 10, 14, 24, 26],
  ['K', 'L'],
);
styleSheet(
  vocalSheet,
  '歌声版本明细',
  `共 ${vocalRows.length} 个歌声版本；角色列保留到单个角色粒度。`,
  ['歌曲ID', '歌名', '歌曲类型', 'Vocal ID', '歌声版本类型', '版本说明', '角色', 'Asset Bundle'],
  vocalRows,
  'VocalsTable',
  [10, 28, 10, 12, 18, 24, 34, 22],
);
styleSheet(
  videoSheet,
  '视频明细',
  `共 ${videoRows.length} 个已关联视频；日期为视频自身上传时间。`,
  ['歌曲ID', '歌名', '歌曲类型', '视频类型', '变体', '版本基础', '特殊版本', '版本标签', 'Video ID', '视频标题', '频道', '上传时间', '播放量', '点赞数', '演唱者', '视频链接', '数据源', '数据源链接'],
  videoRows,
  'VideosTable',
  [10, 28, 10, 16, 18, 14, 16, 18, 16, 38, 24, 16, 14, 12, 24, 38, 24, 38],
  ['L'],
);
styleSheet(
  staffSheet,
  'Staff 明细',
  `共 ${staffRows.length} 条贡献者与待整理原始行；保留标准角色、原始角色和来源文本。`,
  ['歌曲ID', '歌名', 'Video ID', '视频类型', '视频标题', '标准角色', '原始角色', '姓名', '原始姓名', '来源文本'],
  staffRows,
  'StaffTable',
  [10, 28, 16, 16, 38, 16, 18, 22, 22, 64],
);

await fs.mkdir(PREVIEW_DIR, { recursive: true });
const sheetChecks = [
  ['歌曲总览', 'A1:R14'],
  ['歌声版本', 'A1:H14'],
  ['视频', 'A1:R14'],
  ['Staff', 'A1:J14'],
];
for (const [sheetName, range] of sheetChecks) {
  const check = await workbook.inspect({
    kind: 'table',
    range: `${sheetName}!${range.split('!').pop()}`,
    include: 'values,formulas',
    tableMaxRows: 14,
    tableMaxCols: 18,
    maxChars: 6000,
  });
  console.log(`INSPECT ${sheetName}\n${check.ndjson}`);
  const preview = await workbook.render({ sheetName, range, scale: 1.2, format: 'png' });
  await fs.writeFile(path.join(PREVIEW_DIR, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const errors = await workbook.inspect({
  kind: 'match',
  searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',
  options: { useRegex: true, maxResults: 300 },
  summary: 'final formula error scan',
});
console.log(`FORMULA_ERRORS\n${errors.ndjson}`);

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(OUTPUT_FILE);

console.log(JSON.stringify({
  output: OUTPUT_FILE,
  counts: {
    songs: songRows.length,
    vocals: vocalRows.length,
    videos: videoRows.length,
    staff: staffRows.length,
  },
}, null, 2));
