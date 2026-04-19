<?php
/**
 * Plugin Name: Streamer Ranking
 * Plugin URI:  https://example.com/
 * Description: TwitchとYouTubeの配信者ランキングをAI検索で自動取得し、並び替え可能な表で表示します。ショートコード [streamer_ranking] で埋め込み可能。
 * Version:     1.0.0
 * Author:      Your Name
 * License:     GPL-2.0+
 * Text Domain: streamer-ranking
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'SR_VERSION',    '1.0.0' );
define( 'SR_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'SR_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

/* -------------------------------------------------------
   1. 設定ページ
------------------------------------------------------- */
add_action( 'admin_menu', 'sr_add_admin_menu' );
function sr_add_admin_menu() {
    add_options_page(
        '配信者ランキング設定',
        '配信者ランキング',
        'manage_options',
        'streamer-ranking',
        'sr_settings_page'
    );
}

add_action( 'admin_init', 'sr_register_settings' );
function sr_register_settings() {
    register_setting( 'sr_settings_group', 'sr_api_url', [
        'sanitize_callback' => 'esc_url_raw',
    ] );
    register_setting( 'sr_settings_group', 'sr_cache_minutes', [
        'sanitize_callback' => 'absint',
        'default'           => 60,
    ] );
}

function sr_settings_page() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    ?>
    <div class="wrap">
        <h1>配信者ランキング設定</h1>
        <form method="post" action="options.php">
            <?php settings_fields( 'sr_settings_group' ); ?>
            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row"><label for="sr_api_url">APIエンドポイントURL</label></th>
                    <td>
                        <input
                            type="url"
                            id="sr_api_url"
                            name="sr_api_url"
                            value="<?php echo esc_attr( get_option( 'sr_api_url', 'http://localhost:3000/api/ranking' ) ); ?>"
                            class="regular-text"
                        />
                        <p class="description">
                            自動でランキングデータを取得するためのAPIURL（例: http://localhost:3000/api/ranking）を指定してください。
                        </p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="sr_cache_minutes">キャッシュ時間（分）</label></th>
                    <td>
                        <input
                            type="number"
                            id="sr_cache_minutes"
                            name="sr_cache_minutes"
                            value="<?php echo esc_attr( get_option( 'sr_cache_minutes', 60 ) ); ?>"
                            min="5"
                            max="1440"
                            class="small-text"
                        />
                        <p class="description">APIの呼び出し頻度を抑えるためにデータをキャッシュします（推奨: 60分）。</p>
                    </td>
                </tr>
            </table>
            <?php submit_button( '設定を保存' ); ?>
        </form>
        <hr>
        <h2>使い方</h2>
        <p>投稿・固定ページにショートコードを貼り付けるだけで表示されます：</p>
        <code>[streamer_ranking]</code>
        <p>オプション付きの例：</p>
        <code>[streamer_ranking platform="Twitch" limit="10"]</code>
        <p><strong>platform</strong>: <code>all</code> / <code>Twitch</code> / <code>YouTube</code>（デフォルト: all）<br>
           <strong>limit</strong>: 表示件数（デフォルト: 20）</p>
    </div>
    <?php
}

/* -------------------------------------------------------
   2. REST API エンドポイント（APIコールはサーバーサイド）
------------------------------------------------------- */
add_action( 'rest_api_init', 'sr_register_rest_route' );
function sr_register_rest_route() {
    register_rest_route( 'streamer-ranking/v1', '/fetch', [
        'methods'             => 'GET',
        'callback'            => 'sr_rest_fetch',
        'permission_callback' => '__return_true',
        'args'                => [
            'platform' => [
                'default'           => 'all',
                'sanitize_callback' => 'sanitize_text_field',
            ],
            'limit' => [
                'default'           => 20,
                'sanitize_callback' => 'absint',
            ],
        ],
    ] );
}

function sr_rest_fetch( WP_REST_Request $request ) {
    $platform = $request->get_param( 'platform' );
    $limit    = min( (int) $request->get_param( 'limit' ), 30 );

    $cache_key = 'sr_data_' . md5( $platform . '_' . $limit );
    $cached    = get_transient( $cache_key );
    if ( $cached !== false ) {
        return rest_ensure_response( $cached );
    }

    $api_url = get_option( 'sr_api_url', 'http://localhost:3000/api/ranking' );
    if ( empty( $api_url ) ) {
        return new WP_Error( 'no_api', 'APIエンドポイントURLが設定されていません。', [ 'status' => 500 ] );
    }

    $query_args = [
        'limit' => $limit,
        'date'  => gmdate( 'Y-m-d', time() + 9 * 3600 ), // JSTの日付（バックエンドの仕様に合わせる）
    ];
    if ( $platform !== 'all' ) {
        $query_args['platform'] = strtolower( $platform );
    }

    $request_url = add_query_arg( $query_args, $api_url );
    $response = wp_remote_get( $request_url, [ 'timeout' => 15 ] );

    if ( is_wp_error( $response ) ) {
        return new WP_Error( 'api_error', '自動取得APIへの接続に失敗しました: ' . $response->get_error_message(), [ 'status' => 502 ] );
    }

    $status = wp_remote_retrieve_response_code( $response );
    if ( $status !== 200 ) {
        return new WP_Error( 'api_error', "自動取得API エラー ({$status})", [ 'status' => $status ] );
    }

    $body = json_decode( wp_remote_retrieve_body( $response ), true );
    if ( ! isset( $body['ok'] ) || ! isset( $body['data'] ) || ! is_array( $body['data'] ) ) {
        return new WP_Error( 'parse_error', 'APIから有効なデータが返されませんでした。', [ 'status' => 500 ] );
    }

    $streamers = [];
    foreach ( $body['data'] as $index => $item ) {
        // Node.js側が返す「動画ランキング仕様」のデータを、配信者ランキングのデザイン仕様にマップする
        $streamers[] = [
            'rank'         => isset($item['overall_rank']) ? $item['overall_rank'] : ($item['rank'] ?? ($index + 1)),
            'name'         => $item['title'] ?? '不明',
            'platform'     => ucfirst( $item['platform'] ?? 'Unknown' ),
            'followers'    => floor( ($item['view_count'] ?? 0) / 10000 ),   // 再生数（万）をフォロワー列に流用
            'peak_viewers' => floor( ($item['like_count'] ?? 0) / 1000 ),    // いいね数（千）を最高視聴者数列に流用
            'category'     => isset($item['diff_type']) ? '変動: ' . $item['diff_type'] : '-',
        ];
    }

    $parsed = [
        'updated' => date('Y-m'),
        'source'  => 'Local API',
        'streamers' => $streamers
    ];

    $cache_minutes = (int) get_option( 'sr_cache_minutes', 60 );
    set_transient( $cache_key, $parsed, $cache_minutes * MINUTE_IN_SECONDS );

    return rest_ensure_response( $parsed );
}

/* -------------------------------------------------------
   3. ショートコード
------------------------------------------------------- */
add_shortcode( 'streamer_ranking', 'sr_shortcode' );
function sr_shortcode( $atts ) {
    $atts = shortcode_atts( [
        'platform' => 'all',
        'limit'    => 20,
    ], $atts, 'streamer_ranking' );

    $platform = sanitize_text_field( $atts['platform'] );
    $limit    = absint( $atts['limit'] );

    wp_enqueue_style(  'sr-style',  SR_PLUGIN_URL . 'assets/style.css',  [], SR_VERSION );
    wp_enqueue_script( 'sr-script', SR_PLUGIN_URL . 'assets/script.js', [], SR_VERSION, true );

    wp_localize_script( 'sr-script', 'srConfig', [
        'restUrl'  => esc_url_raw( rest_url( 'streamer-ranking/v1/fetch' ) ),
        'nonce'    => wp_create_nonce( 'wp_rest' ),
        'platform' => $platform,
        'limit'    => $limit,
    ] );

    ob_start();
    ?>
    <div id="sr-widget" class="sr-widget" data-platform="<?php echo esc_attr( $platform ); ?>" data-limit="<?php echo esc_attr( $limit ); ?>">
        <div class="sr-header">
            <div class="sr-title-wrap">
                <h2 class="sr-title">配信者ランキング</h2>
                <p class="sr-subtitle" id="sr-last-updated">取得中...</p>
            </div>
            <div class="sr-filters" id="sr-filters">
                <?php if ( $platform === 'all' ) : ?>
                <button class="sr-btn active" data-p="all">すべて</button>
                <button class="sr-btn" data-p="Twitch">Twitch</button>
                <button class="sr-btn" data-p="YouTube">YouTube</button>
                <?php endif; ?>
            </div>
        </div>

        <div class="sr-loading" id="sr-loading">
            <div class="sr-spinner"></div>
            <p id="sr-loading-msg">データを検索中...</p>
        </div>

        <div class="sr-error" id="sr-error" style="display:none;">
            <p id="sr-error-msg"></p>
            <button class="sr-retry-btn" onclick="srRetry()">再取得</button>
        </div>

        <div id="sr-table-wrap" style="display:none;">
            <div class="sr-table-scroll">
                <table class="sr-table">
                    <thead>
                        <tr>
                            <th class="sr-sortable" data-col="rank">#</th>
                            <th class="sr-sortable" data-col="name">配信者名</th>
                            <th class="sr-sortable" data-col="platform">プラットフォーム</th>
                            <th class="sr-sortable sr-num" data-col="followers">フォロワー</th>
                            <th class="sr-sortable sr-num" data-col="peak_viewers">最高視聴者数</th>
                            <th class="sr-sortable" data-col="category">カテゴリ</th>
                        </tr>
                    </thead>
                    <tbody id="sr-tbody"></tbody>
                </table>
            </div>
            <p class="sr-note" id="sr-note"></p>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
