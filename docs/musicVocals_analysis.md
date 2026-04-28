# musicVocals.json 结构分析

**总记录数：1580 条**

---

## musicVocalType 所有可能值

| musicVocalType | 数量 | caption（描述） | 含义 |
|---|---|---|---|
| `another_vocal` | 527 | アナザーボーカルver. | **换人唱版本** — 同一首歌让不同角色演唱 |
| `sekai` | 382 | セカイver. 等8种 | **世界版本** — 游戏角色 + V家歌手共同演唱 |
| `original_song` | 370 | バーチャル・シンガーver. | **原唱版本** — V家歌手（初音、MEIKO等）演唱 |
| `virtual_singer` | 266 | バーチャル・シンガーver. / COLORFUL LIVE ver. | **虚拟歌手版** — 多个V家歌手合唱 |
| `april_fool_2022` | 17 | エイプリルフールver. | **2022愚人节限定版本** |
| `streaming_live` | 10 | コネクトライブver. (DAY1/DAY2 昼/夜) | **Connect Live线上演唱会版本** |
| `instrumental` | 8 | Inst.ver. | **纯音乐版本** — characters数组为空 |

---

## sekai 类型的 caption 子类

`sekai` 最多样，有 **8 种 caption**：

| caption | 含义 |
|---|---|
| セカイver. | 标准世界版本 |
| Leo/need ver. | Leo/need组合版本 |
| MORE MORE JUMP! ver. | MMJ组合版本 |
| Vivid BAD SQUAD ver. | VBS组合版本 |
| ワンダーランズ×ショウタイム ver. | WxS组合版本 |
| 25時、ナイトコードで。ver. | N25组合版本 |
| 「劇場版プロジェクトセカイ」ver. | 剧场版版本 |
| あんさんぶるスターズ！！コラボver. | 偶像梦幻祭联动版本 |

---

## characterType 可能值

| characterType | 出现在 | 含义 |
|---|---|---|
| `game_character` | 所有类型 | 游戏内角色（ID 1~20 为人类角色，21~26 为V家歌手） |
| `outside_character` | `original_song`, `sekai`, `virtual_singer`, `streaming_live` | 游戏外角色（特邀嘉宾、联动角色等） |

---

## 关键结构特点

1. **一首歌可以有多个vocal版本** — 通过 `musicId` 关联，同一 `musicId` 可对应多条记录
2. **`instrumental` 没有角色** — `characters` 为空数组
3. **`seq` 字段决定在同一首歌内的排序** — 通常 `original_song` 是 seq=1，`sekai` 是 seq=2/3
4. **`assetbundleName` 格式** — 按类型有不同前缀：
   - `original_song`: `"0001_01"` (无前缀)
   - `sekai`: `"0002_02"` (无前缀)
   - `another_vocal`: `"an_0006_01"` (前缀 `an_`)
   - `virtual_singer`: `"vs_0052_02"` (前缀 `vs_`)
   - `instrumental`: `"in_0162_01"` (前缀 `in_`)
   - `april_fool_2022`: `"af_0093_01"` (前缀 `af_`)
   - `streaming_live`: `"cl_0006_01"` (前缀 `cl_`，cl = Connect Live)
5. **部分类型有额外字段** — `april_fool_2022` 有 `specialSeasonId` 和 `archiveDisplayType`；`streaming_live` 有 `archiveDisplayType`

---

## 实际数据示例

### ① original_song — 原唱版本

> Tell Your World (musicId=1)，初音ミク (characterId=21) 独唱

```json
{
  "id": 1,
  "musicId": 1,
  "musicVocalType": "original_song",
  "seq": 1,
  "releaseConditionId": 5,
  "caption": "バーチャル・シンガーver.",
  "characters": [
    {
      "id": 1, "musicId": 1, "musicVocalId": 1,
      "characterType": "game_character",
      "characterId": 21, "seq": 10
    }
  ],
  "assetbundleName": "0001_01",
  "archivePublishedAt": 1233284400000
}
```

### ② sekai — 世界版本

> ブレス・ユア・ブレス (musicId=2)，初音ミク (21) + 星乃一歌 (1) 合唱

```json
{
  "id": 3,
  "musicId": 2,
  "musicVocalType": "sekai",
  "seq": 2,
  "releaseConditionId": 5,
  "caption": "セカイver.",
  "characters": [
    {
      "id": 3, "musicId": 2, "musicVocalId": 3,
      "characterType": "game_character",
      "characterId": 21, "seq": 21
    },
    {
      "id": 4, "musicId": 2, "musicVocalId": 3,
      "characterType": "game_character",
      "characterId": 1, "seq": 22
    }
  ],
  "assetbundleName": "0002_02",
  "archivePublishedAt": 1233284400000
}
```

### ③ another_vocal — 换人唱版本

> ハジメテノオト (musicId=6)，星乃一歌 (1) 独唱的another版本

```json
{
  "id": 80,
  "musicId": 6,
  "musicVocalType": "another_vocal",
  "seq": 3,
  "releaseConditionId": 9,
  "caption": "アナザーボーカルver.",
  "characters": [
    {
      "id": 175, "musicId": 6, "musicVocalId": 80,
      "characterType": "game_character",
      "characterId": 1, "seq": 63
    }
  ],
  "assetbundleName": "an_0006_01",
  "archivePublishedAt": 1233284400000
}
```

### ④ virtual_singer — 虚拟歌手合唱版

> Blessing (musicId=52)，5位V家歌手 (KAITO=23, MEIKO=25, 巡音ルカ=24, 鏡音リン=26, 初音ミク=21) 合唱

```json
{
  "id": 72,
  "musicId": 52,
  "musicVocalType": "virtual_singer",
  "seq": 2,
  "releaseConditionId": 5,
  "caption": "バーチャル・シンガーver.",
  "characters": [
    { "id": 162, "characterType": "game_character", "characterId": 23, "seq": 525 },
    { "id": 494, "characterType": "game_character", "characterId": 25, "seq": 528 },
    { "id": 495, "characterType": "game_character", "characterId": 24, "seq": 529 },
    { "id": 496, "characterType": "game_character", "characterId": 26, "seq": 530 },
    { "id": 497, "characterType": "game_character", "characterId": 21, "seq": 531 }
  ],
  "assetbundleName": "vs_0052_02",
  "archivePublishedAt": 1233284400000
}
```

### ⑤ instrumental — 纯音乐版

> musicId=162，无演唱角色，characters 为空数组

```json
{
  "id": 353,
  "musicId": 162,
  "musicVocalType": "instrumental",
  "seq": 1,
  "releaseConditionId": 5,
  "caption": "Inst.ver.",
  "characters": [],
  "assetbundleName": "in_0162_01",
  "archivePublishedAt": 1233284400000
}
```

### ⑥ april_fool_2022 — 愚人节限定版

> musicId=93，5位角色混唱。注意**额外字段** `specialSeasonId` 和 `archiveDisplayType`

```json
{
  "id": 570,
  "musicId": 93,
  "musicVocalType": "april_fool_2022",
  "seq": 10,
  "releaseConditionId": 6,
  "caption": "エイプリルフールver.",
  "characters": [
    { "id": 1056, "characterType": "game_character", "characterId": 21, "seq": 932 },
    { "id": 1057, "characterType": "game_character", "characterId": 1, "seq": 933 },
    { "id": 1058, "characterType": "game_character", "characterId": 2, "seq": 934 },
    { "id": 1059, "characterType": "game_character", "characterId": 7, "seq": 935 },
    { "id": 1060, "characterType": "game_character", "characterId": 19, "seq": 936 }
  ],
  "assetbundleName": "af_0093_01",
  "specialSeasonId": 1,
  "archiveDisplayType": "none",
  "archivePublishedAt": 1233284400000
}
```

### ⑦ streaming_live — 线上演唱会版

> ハジメテノオト (musicId=6)，初音ミク (21) + 2位 outside_character 合唱。注意**额外字段** `archiveDisplayType`，且无 `archivePublishedAt`

```json
{
  "id": 1486,
  "musicId": 6,
  "musicVocalType": "streaming_live",
  "seq": 601,
  "releaseConditionId": 11,
  "caption": "コネクトライブver.",
  "characters": [
    { "id": 2669, "characterType": "game_character", "characterId": 21, "seq": 66 },
    { "id": 2670, "characterType": "outside_character", "characterId": 25, "seq": 67 },
    { "id": 2671, "characterType": "outside_character", "characterId": 27, "seq": 68 }
  ],
  "assetbundleName": "cl_0006_01",
  "archiveDisplayType": "none"
}
```

---

## 字段一览

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | int | 歌声版本唯一ID |
| `musicId` | int | 关联的音乐ID → `musics.json` |
| `musicVocalType` | string | 歌声类型（见上表） |
| `seq` | int | 在同一首歌中的排序 |
| `releaseConditionId` | int | 解锁条件ID |
| `caption` | string | 版本描述 |
| `characters` | object[] | 演唱角色列表（嵌套对象） |
| `characters[].id` | int | 角色-歌声关联记录ID |
| `characters[].musicId` | int | 关联音乐ID |
| `characters[].musicVocalId` | int | 关联歌声版本ID |
| `characters[].characterType` | string | `"game_character"` / `"outside_character"` |
| `characters[].characterId` | int | 角色ID |
| `characters[].seq` | int | 角色排序 |
| `assetbundleName` | string | 音频资源包名，如 `"0001_01"` |
| `archivePublishedAt` | long | 音乐归档发布时间戳（毫秒） |
