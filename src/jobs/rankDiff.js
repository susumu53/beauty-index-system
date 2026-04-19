// src/jobs/rankDiff.js
// 前日のランキングと比較して順位変動を計算する
//
// 変動の種類:
//   "new"    → 前日ランク外（新規ランクイン）
//   "up"     → 順位が上がった  (+N)
//   "down"   → 順位が下がった  (-N)
//   "same"   → 変動なし       (0)

import { getDb } from '../db/schema.js';

/**
 * 指定日と前日のランキングを比較し、video_id ベースで変動を付与する
 * @param {string} date       - 比較対象の日付 YYYY-MM-DD
 * @param {string} [platform] - 省略時は全プラットフォーム
 * @returns {RankingRow[]}    - prev_rank / diff フィールドを追加したレコード配列
 */
export function getRankingsWithDiff(date, platform) {
  const db = getDb();

  // 前日の日付を計算
  const prevDate = getPrevDate(date);

  // 当日と前日のデータを取得
  const todayRows = queryRankings(db, date, platform);
  const prevRows  = queryRankings(db, prevDate, platform);

  // 前日: video_id → rank のマップを作成
  const prevMap = new Map(prevRows.map(r => [r.video_id, r.rank]));

  return todayRows.map(row => {
    const prevRank = prevMap.get(row.video_id) ?? null;

    let diffType, diffValue;
    if (prevRank === null) {
      diffType  = 'new';
      diffValue = null;
    } else if (prevRank > row.rank) {
      diffType  = 'up';
      diffValue = prevRank - row.rank;   // 正の数＝上昇幅
    } else if (prevRank < row.rank) {
      diffType  = 'down';
      diffValue = prevRank - row.rank;   // 負の数＝下降幅
    } else {
      diffType  = 'same';
      diffValue = 0;
    }

    // extra_json を展開してフラットに返す
    let extra = {};
    try { extra = JSON.parse(row.extra_json ?? '{}'); } catch {}

    return {
      ...row,
      extra_json: undefined,
      ...extra,
      prev_rank:  prevRank,
      diff_type:  diffType,
      diff_value: diffValue,
    };
  });
}

/**
 * プラットフォームをまたいだ総合ランキングを再計算する
 * 指標: view_count 降順でソートし直して overall_rank を付与
 */
export function getOverallRanking(date, limit = 50) {
  const db = getDb();
  const prevDate = getPrevDate(date);

  const todayRows = queryRankings(db, date, null);
  const prevRows  = queryRankings(db, prevDate, null);

  // 総合順位: 再生数降順
  const sorted = [...todayRows].sort((a, b) => b.view_count - a.view_count);

  const prevOverallMap = buildOverallMap(prevRows);

  return sorted.slice(0, limit).map((row, index) => {
    const overallRank = index + 1;
    const prevOverall = prevOverallMap.get(row.video_id) ?? null;

    let diffType  = prevOverall === null ? 'new' : 'same';
    let diffValue = 0;
    if (prevOverall !== null && prevOverall !== overallRank) {
      diffType  = prevOverall > overallRank ? 'up' : 'down';
      diffValue = prevOverall - overallRank;
    }

    let extra = {};
    try { extra = JSON.parse(row.extra_json ?? '{}'); } catch {}

    return {
      ...row,
      extra_json:    undefined,
      ...extra,
      overall_rank:  overallRank,
      prev_rank:     prevOverall,
      diff_type:     diffType,
      diff_value:    diffValue,
    };
  });
}

// ── 内部ユーティリティ ───────────────────────────────────────────────────

function queryRankings(db, date, platform) {
  if (platform) {
    return db.prepare(
      'SELECT * FROM rankings WHERE date = ? AND platform = ? ORDER BY rank ASC'
    ).all(date, platform);
  }
  return db.prepare(
    'SELECT * FROM rankings WHERE date = ? ORDER BY platform, rank ASC'
  ).all(date);
}

function buildOverallMap(rows) {
  // 前日の総合順位マップ: video_id → overall_rank
  const sorted = [...rows].sort((a, b) => b.view_count - a.view_count);
  return new Map(sorted.map((r, i) => [r.video_id, i + 1]));
}

function getPrevDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}
