=== Streamer Ranking ===
Contributors: yourname
Tags: streaming, twitch, youtube, ranking, shortcode
Requires at least: 5.8
Tested up to: 6.7
Requires PHP: 7.4
Stable tag: 1.0.0
License: GPL-2.0+

TwitchとYouTubeの配信者ランキングをAI検索で自動取得し、並び替え可能な表で表示します。

== インストール方法 ==

1. ZIPファイルをアップロードし、有効化する
2. 管理画面 > 設定 > 配信者ランキング で Anthropic APIキーを入力
3. 投稿・固定ページに [streamer_ranking] を貼り付ける

== ショートコード ==

基本:
  [streamer_ranking]

オプション:
  [streamer_ranking platform="Twitch" limit="10"]

  platform: all / Twitch / YouTube (デフォルト: all)
  limit: 表示件数 1〜30 (デフォルト: 20)

== 必要なもの ==

- Anthropic APIキー（https://console.anthropic.com/ で取得）
- WordPressのREST APIが有効であること（デフォルトで有効）
- PHPのcURL拡張が有効であること

== Changelog ==

= 1.0.0 =
* 初回リリース
