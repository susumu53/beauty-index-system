// src/index.js
// エントリーポイント: 3 サービスのランキングを並列取得して DB に保存する
//
// 使い方:
//   node src/index.js            # 今日の JST 日付でデータ取得
//   node src/index.js 2025-04-01 # 指定日で取得（リトライ用）

import 'dotenv/config';
import { fetchYouTube  } from './fetchers/youtube.js';
import { fetchTwitch   } from './fetchers/twitch.js';
import { fetchNiconico } from './fetchers/niconico.js';

/** JST の今日日付を YYYY-MM-DD で返す */
function todayJST() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000)
    .toISOString().slice(0, 10);
}

async function main() {
  const date = process.argv[2] ?? todayJST();
  console.log(`\n🚀 ランキング取得開始: ${date}\n`);

  const results = await Promise.allSettled([
    fetchYouTube(date),
    fetchTwitch(date),
    fetchNiconico(date),
  ]);

  console.log('\n── 結果サマリー ─────────────────────────────');

  const labels = ['YouTube', 'Twitch', 'ニコニコ'];
  let success = 0;

  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    if (r.status === 'fulfilled') {
      console.log(`  ✅ ${labels[i]}: ${r.value} 件`);
      success++;
    } else {
      console.error(`  ❌ ${labels[i]}: ${r.reason?.message ?? r.reason}`);
    }
  }

  console.log(`─────────────────────────────────────────────`);
  console.log(`  完了: ${success} / ${results.length} サービス\n`);

  if (success === 0) {
    console.error('全てのサービスで失敗しました。');
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('予期しないエラー:', err);
  process.exit(1);
});
