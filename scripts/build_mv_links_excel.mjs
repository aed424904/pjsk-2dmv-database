import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const outputDir = path.join(root, "outputs", "mv_links_excel");
const outputPath = path.join(outputDir, "Project_Sekai_全服务器_MV链接与创作者汇总.xlsx");

const servers = {
  JP: path.join(root, "sekai-master-db-diff-main"),
  CN: path.join(root, "sekai-master-db-cn-diff-main"),
};

const allowedHosts = new Set([
  "youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com",
  "nicovideo.jp", "www.nicovideo.jp", "nico.ms",
  "bilibili.com", "www.bilibili.com", "b23.tv",
]);

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

function cleanUrl(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  try {
    const url = new URL(value.trim());
    return allowedHosts.has(url.hostname.toLowerCase()) ? value.trim() : null;
  } catch {
    return null;
  }
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

const serverData = {};
for (const [server, folder] of Object.entries(servers)) {
  const [musics, artists, originals] = await Promise.all([
    readJson(path.join(folder, "musics.json")),
    readJson(path.join(folder, "musicArtists.json")),
    readJson(path.join(folder, "musicOriginals.json")),
  ]);
  const artistMap = new Map(artists.map((item) => [item.id, item.name || ""]));
  const originalMap = new Map();
  for (const item of originals) {
    const url = cleanUrl(item.videoLink);
    if (!url) continue;
    if (!originalMap.has(item.musicId)) originalMap.set(item.musicId, []);
    originalMap.get(item.musicId).push(url);
  }
  serverData[server] = { musics, artistMap, originalMap };
}

const database = await readJson(path.join(root, "output", "database_v2.json"));
const videosById = new Map();
const videosByTitle = new Map();
const unitsById = new Map();
const unitsByTitle = new Map();
function bucket(map, key) {
  if (!map.has(key)) map.set(key, { original: [], mv2d: [] });
  return map.get(key);
}
for (const song of database.songs || []) {
  const units = Array.isArray(song.classification?.units) ? song.classification.units : [];
  const unitsText = unique(units).join(" / ") || "-";
  unitsByTitle.set(song.titleJp || song.title || "", unitsText);
  if (song.sekaiMusicId != null) unitsById.set(song.sekaiMusicId, unitsText);
  const destinations = [bucket(videosByTitle, song.titleJp || song.title || "")];
  if (song.sekaiMusicId != null) destinations.push(bucket(videosById, song.sekaiMusicId));
  for (const video of song.videos || []) {
    const url = cleanUrl(video.url);
    const kind = video.type === "official_2dmv" ? "mv2d" : video.type === "original_mv" ? "original" : null;
    if (!url || !kind) continue;
    for (const destination of destinations) destination[kind].push(url);
  }
}

const headers = [
  "服务器", "游戏音乐ID", "歌名", "所属团队", "原曲MV链接", "2DMV链接",
  "游戏内创作者", "作词", "作曲", "编曲", "链接平台",
];
const rows = [];
for (const [server, data] of Object.entries(serverData)) {
  for (const music of data.musics) {
    const info = Array.isArray(music.infos) && music.infos[0] ? music.infos[0] : {};
    const title = music.title || "";
    const byId = videosById.get(music.id) || { original: [], mv2d: [] };
    const byTitle = videosByTitle.get(title) || { original: [], mv2d: [] };
    const original = unique([...(data.originalMap.get(music.id) || []), ...byId.original, ...byTitle.original]);
    const mv2d = unique([...byId.mv2d, ...byTitle.mv2d]);
    if (!original.length && !mv2d.length) continue;
    const allLinks = [...original, ...mv2d];
    const platforms = unique(allLinks.map((link) => {
      const host = new URL(link).hostname.toLowerCase();
      if (host.includes("youtu")) return "YouTube";
      if (host.includes("nico")) return "niconico";
      if (host.includes("bilibili") || host === "b23.tv") return "bilibili";
      return host;
    }));
    rows.push([
      server,
      music.id,
      title,
      unitsById.get(music.id) || unitsByTitle.get(title) || "-",
      original.join("\n"),
      mv2d.join("\n"),
      info.creator || data.artistMap.get(music.creatorArtistId) || "-",
      info.lyricist || music.lyricist || "-",
      info.composer || music.composer || "-",
      info.arranger || music.arranger || "-",
      platforms.join(" / "),
    ]);
  }
}
rows.sort((a, b) => a[0].localeCompare(b[0]) || a[1] - b[1]);

const workbook = Workbook.create();
const summary = workbook.worksheets.add("说明与统计");
const dataSheet = workbook.worksheets.add("MV链接汇总");

summary.showGridLines = false;
summary.getRange("A1:F1").merge();
summary.getRange("A1").values = [["Project Sekai 全服务器 MV 链接与创作者汇总"]];
summary.getRange("A1:F1").format = {
  fill: "#17365D",
  font: { bold: true, color: "#FFFFFF", size: 18 },
  verticalAlignment: "center",
};
summary.getRange("A1:F1").format.rowHeight = 34;
summary.getRange("A3:B8").values = [
  ["项目", "内容"],
  ["数据日期", "2026-07-20"],
  ["服务器", "JP（日服）、CN（国服）"],
  ["有效记录数", rows.length],
  ["JP 记录数", rows.filter((row) => row[0] === "JP").length],
  ["CN 记录数", rows.filter((row) => row[0] === "CN").length],
];
summary.getRange("A3:B3").format = { fill: "#D9EAF7", font: { bold: true, color: "#17365D" } };
summary.getRange("A3:B8").format.borders = { preset: "insideHorizontal", style: "thin", color: "#D9E1F2" };
summary.getRange("A10:F10").merge();
summary.getRange("A10").values = [["使用说明"]];
summary.getRange("A10:F10").format = { fill: "#D9EAF7", font: { bold: true, color: "#17365D" } };
summary.getRange("A11:F14").merge(true);
summary.getRange("A11:A14").values = [[
  "1. “MV链接汇总”工作表每个服务器—歌曲占一行，可直接筛选、排序和编辑。",
], [
  "2. 多个链接使用换行分隔；仅收录 YouTube、niconico、bilibili。",
], [
  "3. 原曲 MV 合并 Master musicOriginals 与项目本家 MV 数据；2DMV 使用官方 2DMV 数据。",
], [
  "4. 国服 Master 当前没有独立 musicOriginals，因此同 ID 歌曲使用对应作品的公共 MV 链接。",
]];
summary.getRange("A11:F14").format = { wrapText: true, verticalAlignment: "center", font: { size: 10 } };
summary.getRange("A:A").format.columnWidth = 18;
summary.getRange("B:B").format.columnWidth = 32;
summary.getRange("C:F").format.columnWidth = 14;

const lastRow = rows.length + 1;
dataSheet.getRange(`A1:K${lastRow}`).values = [headers, ...rows];
dataSheet.showGridLines = false;
dataSheet.freezePanes.freezeRows(1);
dataSheet.freezePanes.freezeColumns(3);
dataSheet.getRange("A1:K1").format = {
  fill: "#17365D",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
};
dataSheet.getRange("A1:J1").format.rowHeight = 28;
dataSheet.getRange(`A2:K${lastRow}`).format = {
  verticalAlignment: "top",
  wrapText: true,
  font: { size: 9 },
};
dataSheet.getRange(`A2:B${lastRow}`).format.horizontalAlignment = "center";
dataSheet.getRange(`A2:A${lastRow}`).format.fill = "#F2F6FA";
dataSheet.getRange(`A1:K${lastRow}`).format.borders = {
  insideHorizontal: { style: "thin", color: "#E2E8F0" },
  bottom: { style: "thin", color: "#CBD5E1" },
};
const widths = [10, 12, 28, 24, 44, 44, 22, 20, 20, 20, 15];
for (let i = 0; i < widths.length; i++) {
  dataSheet.getRangeByIndexes(0, i, lastRow, 1).format.columnWidth = widths[i];
}
dataSheet.getRange(`B2:B${lastRow}`).format.numberFormat = "0";
dataSheet.tables.add(`A1:K${lastRow}`, true, "MvLinksTable");

await fs.mkdir(outputDir, { recursive: true });
const summaryPreview = await workbook.render({ sheetName: "说明与统计", range: "A1:F14", scale: 1.2, format: "png" });
await fs.writeFile(path.join(outputDir, "summary_preview.png"), new Uint8Array(await summaryPreview.arrayBuffer()));
const preview = await workbook.render({ sheetName: "MV链接汇总", range: "A1:K18", scale: 1.2, format: "png" });
await fs.writeFile(path.join(outputDir, "preview.png"), new Uint8Array(await preview.arrayBuffer()));

const inspection = await workbook.inspect({
  kind: "table",
  range: "MV链接汇总!A1:K8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 11,
  maxChars: 7000,
});
console.log(inspection.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(JSON.stringify({ outputPath, rows: rows.length }));
