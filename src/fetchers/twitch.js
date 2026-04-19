// src/fetchers/twitch.js
// Twitch Helix API で急上昇ストリーム（日本語 / 全体）を取得する
//
// 必要な環境変数:
//   TWITCH_CLIENT_ID     — Twitch Developer Console で取得
//   TWITCH_CLIENT_SECRET — 同上

import fetch from 'node-fetch';
import { upsertRankings } from '../db/schema.js';

const AUTH_URL = 'https://id.twitch.tv/oauth2/token';
const API_BASE = 'https://api.twitch.tv/helix';

let _token = null;
let _tokenExpiresAt = 0;

/**
 * Client Credentials フローで Bearer トークンを取得（キャッシュ付き）
 */
async function getToken(clientId, clientSecret) {
  if (_token && Date.now() < _tokenExpiresAt) return _token;

  const res = await fetch(AUTH_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id:     clientId,
      client_secret: clientSecret,
      grant_type:    'client_credentials',
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Twitch 認証エラー ${res.status}: ${body}`);
  }

  const json = await res.json();
  _token = json.access_token;
  // 10 秒の余裕を持って期限をセット
  _tokenExpiresAt = Date.now() + (json.expires_in - 10) * 1000;
  return _token;
}

/**
 * Twitch の急上昇ストリームを取得して DB に保存する
 * @param {string} date - 保存する日付 YYYY-MM-DD
 * @param {number} [total=100] - 取得件数（最大 100）
 * @returns {Promise<number>} 保存した件数
 */
export async function fetchTwitch(date, total = 100) {
  const clientId     = process.env.TWITCH_CLIENT_ID;
  const clientSecret = process.env.TWITCH_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    throw new Error('TWITCH_CLIENT_ID または TWITCH_CLIENT_SECRET が設定されていません');
  }

  console.log('🎮 Twitch: 急上昇ストリームを取得中...');

  const token = await getToken(clientId, clientSecret);

  const headers = {
    'Client-Id':    clientId,
    'Authorization': `Bearer ${token}`,
  };

  const allStreams = [];
  let cursor = '';

  while (allStreams.length < total) {
    const params = new URLSearchParams({ first: '100' });
    if (cursor) params.set('after', cursor);

    const res = await fetch(`${API_BASE}/streams?${params}`, { headers });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Twitch API エラー ${res.status}: ${body}`);
    }

    const json = await res.json();
    const items = json.data ?? [];

    allStreams.push(...items);
    cursor = json.pagination?.cursor ?? '';
    if (!cursor || !items.length) break;
  }

  if (!allStreams.length) {
    console.log('  ⚠️  Twitch: ストリームが取得できませんでした');
    return 0;
  }

  const rows = allStreams.slice(0, total).map((stream, index) => {
    // サムネイルURLのサイズを指定（320x180）
    const thumbnail = (stream.thumbnail_url ?? '')
      .replace('{width}', '320')
      .replace('{height}', '180');

    return {
      date,
      platform:   'twitch',
      rank:       index + 1,
      video_id:   stream.id,
      title:      stream.title ?? '',
      channel:    stream.user_name ?? '',
      thumbnail,
      view_count: stream.viewer_count ?? 0,
      like_count: 0,  // Twitch はいいね数なし
      extra_json: JSON.stringify({
        game_id:      stream.game_id ?? '',
        game_name:    stream.game_name ?? '',
        language:     stream.language ?? '',
        started_at:   stream.started_at ?? '',
        user_id:      stream.user_id ?? '',
        user_login:   stream.user_login ?? '',
        is_mature:    stream.is_mature ?? false,
        url: `https://www.twitch.tv/${stream.user_login ?? ''}`,
      }),
    };
  });

  upsertRankings(rows);
  console.log(`  ✅ Twitch: ${rows.length} 件取得完了`);
  return rows.length;
}
