# trending-backend

YouTube・Twitch・ニコニコ動画の急上昇ランキングを毎日取得してSQLiteに保存するバックエンド。

## セットアップ

```bash
cp .env.example .env   # 環境変数ファイルを作成
# .env にAPIキーを記入する（下記「APIキーの取得」参照）
npm install
node src/index.js      # 今日分を手動取得
```

## ファイル構成

```
src/
  fetchers/
    youtube.js    YouTube Data API v3
    twitch.js     Twitch Helix API（OAuthトークン自動管理）
    niconico.js   ニコニコ RSS（認証不要）
  db/
    schema.js     SQLiteスキーマ定義 & 保存/取得関数
  index.js        エントリーポイント（3サービス並列取得）

.github/workflows/
  fetch-ranking.yml  GitHub Actions スケジューラ（毎朝0時 JST）

data/
  ranking.db      SQLiteデータベース（自動生成）
```

## APIキーの取得

### YouTube Data API v3
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を有効化
3. 「認証情報」→「APIキーを作成」

### Twitch Helix API
1. [Twitch Developer Console](https://dev.twitch.tv/console) でアプリ登録
2. Client ID と Client Secret を取得
3. OAuth Redirect URL は `http://localhost` でOK（Client Credentialsフローのため使わない）

### ニコニコ動画
認証不要。RSS フィードを直接取得しているため APIキーは不要。

## GitHub Actions での自動実行

リポジトリの Settings → Secrets and variables → Actions で以下を登録：

| Secret名              | 内容                    |
|-----------------------|-------------------------|
| `YOUTUBE_API_KEY`     | YouTube APIキー         |
| `TWITCH_CLIENT_ID`    | Twitch Client ID        |
| `TWITCH_CLIENT_SECRET`| Twitch Client Secret    |

## クォータ使用量（1日あたり）

| サービス   | 消費量                        | 無料枠          |
|-----------|-------------------------------|-----------------|
| YouTube   | 約100ユニット/回              | 10,000ユニット/日 |
| Twitch    | レート制限800req/分           | 無料            |
| ニコニコ  | RSS取得のみ                   | 無料            |
