// src/api/server.js
// 急上昇ランキングを返す REST API サーバー
//
// エンドポイント一覧:
//   GET /api/ranking                    全プラットフォーム総合（再生数順）
//   GET /api/ranking?platform=youtube   プラットフォーム別
//   GET /api/ranking?date=2025-04-01    指定日
//   GET /api/ranking?limit=20           件数制限
//   GET /api/dates                      データが存在する日付一覧
//   GET /api/summary?date=YYYY-MM-DD    日別サマリー統計
//   GET /healthz                        ヘルスチェック

import express from 'express';
import cors    from 'cors';
import 'dotenv/config';

import { getRankingsWithDiff, getOverallRanking } from '../jobs/rankDiff.js';
import { getDb } from '../db/schema.js';

const app  = express();
const PORT = process.env.PORT ?? 3000;

// ── ミドルウェア ──────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());

// レスポンスを整形するヘルパー
const ok  = (res, data, meta = {}) => res.json({ ok: true, ...meta, data });
const err = (res, status, message) => res.status(status).json({ ok: false, message });

// クエリパラメータのバリデーション
function parseDate(str) {
  if (!str) return todayJST();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(str)) return null;
  return str;
}

function todayJST() {
  // JST (UTC+9) の現在日付
  return new Date(Date.now() + 9 * 60 * 60 * 1000)
    .toISOString().slice(0, 10);
}

// ── ルート ────────────────────────────────────────────────────────────────

// GET /healthz
app.get('/healthz', (_req, res) => {
  res.json({ ok: true, ts: new Date().toISOString() });
});

// GET /api/ranking
// クエリ: date, platform, limit, sort
app.get('/api/ranking', (req, res) => {
  const date     = parseDate(req.query.date);
  const platform = req.query.platform;   // 'youtube' | 'twitch' | 'niconico' | 省略
  const limit    = Math.min(parseInt(req.query.limit ?? '50', 10), 200);

  if (!date) return err(res, 400, 'date は YYYY-MM-DD 形式で指定してください');

  const validPlatforms = ['youtube', 'twitch', 'niconico'];
  if (platform && !validPlatforms.includes(platform)) {
    return err(res, 400, `platform は ${validPlatforms.join(' / ')} のいずれかです`);
  }

  try {
    let rows;
    if (platform) {
      // プラットフォーム別: platform 内での rank 順
      rows = getRankingsWithDiff(date, platform).slice(0, limit);
    } else {
      // 総合: 再生数で全サービスを合算してランク付け
      rows = getOverallRanking(date, limit);
    }

    ok(res, rows, {
      date,
      platform: platform ?? 'all',
      count: rows.length,
    });
  } catch (e) {
    console.error(e);
    err(res, 500, 'データ取得に失敗しました');
  }
});

// GET /api/dates
// データが存在する日付の一覧（新しい順）
app.get('/api/dates', (_req, res) => {
  try {
    const db   = getDb();
    const rows = db.prepare(
      `SELECT date, COUNT(*) as count,
              GROUP_CONCAT(DISTINCT platform) as platforms
       FROM rankings
       GROUP BY date
       ORDER BY date DESC
       LIMIT 90`
    ).all();

    ok(res, rows);
  } catch (e) {
    console.error(e);
    err(res, 500, 'データ取得に失敗しました');
  }
});

// GET /api/summary?date=YYYY-MM-DD
// 日別のサマリー統計（プラットフォームごとの件数・合計再生数など）
app.get('/api/summary', (req, res) => {
  const date = parseDate(req.query.date);
  if (!date) return err(res, 400, 'date は YYYY-MM-DD 形式で指定してください');

  try {
    const db = getDb();

    const byPlatform = db.prepare(`
      SELECT
        platform,
        COUNT(*)        AS video_count,
        SUM(view_count) AS total_views,
        MAX(view_count) AS max_views,
        SUM(CASE WHEN prev_rank_exists = 0 THEN 1 ELSE 0 END) AS new_entries
      FROM (
        SELECT r.platform, r.view_count,
               CASE WHEN p.video_id IS NULL THEN 0 ELSE 1 END AS prev_rank_exists
        FROM rankings r
        LEFT JOIN rankings p
          ON p.video_id = r.video_id
          AND p.date = date(r.date, '-1 day')
        WHERE r.date = ?
      )
      GROUP BY platform
    `).all(date);

    const total = db.prepare(`
      SELECT
        COUNT(*)        AS video_count,
        SUM(view_count) AS total_views
      FROM rankings
      WHERE date = ?
    `).get(date);

    ok(res, { date, total, by_platform: byPlatform });
  } catch (e) {
    console.error(e);
    err(res, 500, 'データ取得に失敗しました');
  }
});

// GET /api/video/:videoId/history
// 特定動画の過去30日ランク推移
app.get('/api/video/:videoId/history', (req, res) => {
  const { videoId } = req.params;

  try {
    const db   = getDb();
    const rows = db.prepare(`
      SELECT date, platform, rank, view_count, like_count
      FROM rankings
      WHERE video_id = ?
      ORDER BY date DESC
      LIMIT 30
    `).all(videoId);

    if (!rows.length) return err(res, 404, '指定された動画が見つかりません');

    ok(res, rows, { videoId });
  } catch (e) {
    console.error(e);
    err(res, 500, 'データ取得に失敗しました');
  }
});

// ── 起動 ──────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 APIサーバー起動: http://localhost:${PORT}`);
  console.log('  GET /api/ranking           全プラットフォーム総合');
  console.log('  GET /api/ranking?platform=youtube');
  console.log('  GET /api/ranking?date=YYYY-MM-DD');
  console.log('  GET /api/dates             データ存在日一覧');
  console.log('  GET /api/summary           日別サマリー');
  console.log('  GET /api/video/:id/history 動画別ランク推移\n');
});

export default app;
