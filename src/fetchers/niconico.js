// src/fetchers/niconico.js
// ニコニコ動画の急上昇ランキングを RSS 2.0 から取得する（認証不要）
//
// RSS エンドポイント:
//   https://www.nicovideo.jp/ranking/genre/all?term=24h&rss=2.0&lang=ja-jp

import fetch from 'node-fetch';
import { XMLParser } from 'fast-xml-parser';
import { upsertRankings } from '../db/schema.js';

const RSS_URL = 'https://www.nicovideo.jp/ranking/genre/all?term=24h&rss=2.0&lang=ja-jp';

const PARSER = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  isArray: (name) => name === 'item',
});

/**
 * ニコニコ動画の急上昇ランキングを取得して DB に保存する
 * @param {string} date - 保存する日付 YYYY-MM-DD
 * @returns {Promise<number>} 保存した件数
 */
export async function fetchNiconico(date) {
  console.log('🎌 ニコニコ: 急上昇ランキングを取得中...');

  const res = await fetch(RSS_URL, {
    headers: {
      'User-Agent': 'trending-ranker/1.0 (github.com/youruser/trending-ranker)',
      'Accept': 'application/rss+xml, application/xml, text/xml',
    },
  });

  if (!res.ok) {
    throw new Error(`ニコニコ RSS エラー ${res.status}: ${res.statusText}`);
  }

  const xml  = await res.text();
  const feed = PARSER.parse(xml);
  const items = feed?.rss?.channel?.item ?? [];

  if (!items.length) {
    console.log('  ⚠️  ニコニコ: アイテムが取得できませんでした');
    return 0;
  }

  const rows = items.map((item, index) => {
    const link       = item.link ?? '';
    const videoId    = extractNicoVideoId(link);

    // タイトルから順位プレフィックスを除去（例: "第1位：動画タイトル"）
    const rawTitle   = String(item.title ?? '');
    const title      = rawTitle.replace(/^第\d+位[：:]\s*/, '');

    // description に含まれる再生数・コメント数などを解析
    const desc       = String(item.description ?? '');
    const viewCount  = extractNumber(desc, /再生[:：](\d[\d,]*)/);
    const likeCount  = extractNumber(desc, /(?:マイリスト|いいね)[:：](\d[\d,]*)/);
    const commentCount = extractNumber(desc, /コメント[:：](\d[\d,]*)/);

    // サムネイル: enclosure か description の img タグから取得
    const thumbnail  = item.enclosure?.['@_url'] ?? extractThumbnail(desc, videoId);

    return {
      date,
      platform:   'niconico',
      rank:       index + 1,
      video_id:   videoId,
      title,
      channel:    extractChannel(desc),
      thumbnail,
      view_count: viewCount,
      like_count: likeCount,
      extra_json: JSON.stringify({
        pub_date:      item.pubDate ?? '',
        comment_count: commentCount,
        url:           link,
        guid:          item.guid?.['#text'] ?? item.guid ?? link,
      }),
    };
  });

  upsertRankings(rows);
  console.log(`  ✅ ニコニコ: ${rows.length} 件取得完了`);
  return rows.length;
}

// ── ユーティリティ ────────────────────────────────────────────────────────

function extractNicoVideoId(url) {
  const m = url.match(/\/(sm\d+|nm\d+|so\d+|lv\d+)/);
  return m ? m[1] : url.split('/').pop() ?? url;
}

function extractNumber(text, regex) {
  const m = text.match(regex);
  if (!m) return 0;
  return parseInt(m[1].replace(/,/g, ''), 10);
}

function extractThumbnail(desc, videoId) {
  const m = desc.match(/<img[^>]+src="([^"]+)"/i);
  if (m) return m[1];
  if (videoId) return `https://nicovideo.cdn.nimg.jp/thumbnails/${videoId.replace(/\D/g, '')}/${videoId.replace(/\D/g, '')}.M`;
  return '';
}

function extractChannel(desc) {
  const m = desc.match(/投稿者[:：]\s*([^\s<]+)/);
  return m ? m[1] : '';
}
