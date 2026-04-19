// src/db/schema.js
// SQLite スキーマ定義と DB アクセス関数
//
// テーブル: rankings
//   id          INTEGER PRIMARY KEY AUTOINCREMENT
//   date        TEXT    YYYY-MM-DD
//   platform    TEXT    youtube / twitch / niconico
//   rank        INTEGER プラットフォーム内順位 (1始まり)
//   video_id    TEXT    各プラットフォームの動画/ストリーム ID
//   title       TEXT    動画タイトル
//   channel     TEXT    チャンネル名 / 配信者名
//   thumbnail   TEXT    サムネイル URL
//   view_count  INTEGER 再生数 / 視聴者数
//   like_count  INTEGER いいね数 (取得できない場合は 0)
//   extra_json  TEXT    プラットフォーム固有の追加データ (JSON 文字列)
//
// インデックス: (date, platform, rank) で高速検索

import Database from 'better-sqlite3';
import path     from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_DIR    = path.resolve(__dirname, '../../data');
const DB_PATH   = path.join(DB_DIR, 'rankings.db');

let _db = null;

/** DB インスタンスを返す（シングルトン） */
export function getDb() {
  if (_db) return _db;

  // data/ ディレクトリが無ければ作成
  if (!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });

  _db = new Database(DB_PATH);
  _db.pragma('journal_mode = WAL');
  _db.pragma('foreign_keys = ON');

  initSchema(_db);
  return _db;
}

/** テーブルとインデックスを作成（冪等） */
function initSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS rankings (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      date        TEXT    NOT NULL,
      platform    TEXT    NOT NULL,
      rank        INTEGER NOT NULL,
      video_id    TEXT    NOT NULL,
      title       TEXT    NOT NULL DEFAULT '',
      channel     TEXT    NOT NULL DEFAULT '',
      thumbnail   TEXT    NOT NULL DEFAULT '',
      view_count  INTEGER NOT NULL DEFAULT 0,
      like_count  INTEGER NOT NULL DEFAULT 0,
      extra_json  TEXT    NOT NULL DEFAULT '{}'
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_rankings_unique
      ON rankings (date, platform, video_id);

    CREATE INDEX IF NOT EXISTS idx_rankings_date_platform
      ON rankings (date, platform, rank);
  `);
}

/**
 * ランキングデータを一括 upsert する
 * @param {Array<{
 *   date: string,
 *   platform: string,
 *   rank: number,
 *   video_id: string,
 *   title: string,
 *   channel: string,
 *   thumbnail: string,
 *   view_count: number,
 *   like_count: number,
 *   extra_json: string,
 * }>} rows
 */
export function upsertRankings(rows) {
  const db = getDb();

  const stmt = db.prepare(`
    INSERT INTO rankings
      (date, platform, rank, video_id, title, channel, thumbnail, view_count, like_count, extra_json)
    VALUES
      (@date, @platform, @rank, @video_id, @title, @channel, @thumbnail, @view_count, @like_count, @extra_json)
    ON CONFLICT (date, platform, video_id) DO UPDATE SET
      rank        = excluded.rank,
      title       = excluded.title,
      channel     = excluded.channel,
      thumbnail   = excluded.thumbnail,
      view_count  = excluded.view_count,
      like_count  = excluded.like_count,
      extra_json  = excluded.extra_json
  `);

  const insertMany = db.transaction((items) => {
    for (const row of items) stmt.run(row);
  });

  insertMany(rows);
  console.log(`  💾 ${rows[0]?.platform ?? '?'}: ${rows.length} 件を保存`);
}
