// src/fetchers/youtube.js
// YouTube Data API v3 で急上昇動画（mostPopular）を取得する
//
// 必要な環境変数:
//   YOUTUBE_API_KEY — Google Cloud Console で取得した API キー

import fetch from 'node-fetch';
import { upsertRankings } from '../db/schema.js';

const API_BASE = 'https://www.googleapis.com/youtube/v3';

/**
 * YouTube の急上昇動画ランキングを取得して DB に保存する
 * @param {string} date - 保存する日付 YYYY-MM-DD
 * @param {string} [regionCode='JP'] - 対象リージョン
 * @returns {Promise<number>} 保存した件数
 */
export async function fetchYouTube(date, regionCode = 'JP') {
  const apiKey = process.env.YOUTUBE_API_KEY;
  if (!apiKey) {
    throw new Error('YOUTUBE_API_KEY が設定されていません');
  }

  console.log('📺 YouTube: 急上昇動画を取得中...');

  const allVideos = [];
  let pageToken = '';
  let page = 0;

  // 最大 2 ページ（1 ページ 50 件 = 合計 100 件）取得
  while (page < 2) {
    const params = new URLSearchParams({
      part:       'snippet,statistics,contentDetails',
      chart:      'mostPopular',
      regionCode,
      maxResults: '50',
      key:        apiKey,
    });
    if (pageToken) params.set('pageToken', pageToken);

    const url = `${API_BASE}/videos?${params}`;
    const res  = await fetch(url);

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`YouTube API エラー ${res.status}: ${body}`);
    }

    const json = await res.json();

    if (json.error) {
      throw new Error(`YouTube API エラー: ${json.error.message}`);
    }

    allVideos.push(...(json.items ?? []));
    pageToken = json.nextPageToken ?? '';
    page++;

    if (!pageToken) break;
  }

  if (!allVideos.length) {
    console.log('  ⚠️  YouTube: 動画が取得できませんでした');
    return 0;
  }

  // DB 用データに変換
  const rows = allVideos.map((item, index) => {
    const sn    = item.snippet;
    const stats = item.statistics ?? {};
    const cd    = item.contentDetails ?? {};

    return {
      date,
      platform:   'youtube',
      rank:       index + 1,
      video_id:   item.id,
      title:      sn.title ?? '',
      channel:    sn.channelTitle ?? '',
      thumbnail:  sn.thumbnails?.high?.url ?? sn.thumbnails?.default?.url ?? '',
      view_count: parseInt(stats.viewCount ?? '0', 10),
      like_count: parseInt(stats.likeCount ?? '0', 10),
      extra_json: JSON.stringify({
        description:       sn.description?.slice(0, 200) ?? '',
        published_at:      sn.publishedAt ?? '',
        category_id:       sn.categoryId ?? '',
        duration:          cd.duration ?? '',
        comment_count:     parseInt(stats.commentCount ?? '0', 10),
        favorite_count:    parseInt(stats.favoriteCount ?? '0', 10),
        channel_id:        sn.channelId ?? '',
        url: `https://www.youtube.com/watch?v=${item.id}`,
      }),
    };
  });

  upsertRankings(rows);
  console.log(`  ✅ YouTube: ${rows.length} 件取得完了`);
  return rows.length;
}
