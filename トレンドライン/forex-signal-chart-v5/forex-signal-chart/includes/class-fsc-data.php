<?php
/**
 * FSC_Data – Yahoo Finance データ取得クラス
 *
 * 戦略（上から順に試す）:
 *   1. Yahoo Finance v8 chart API – query1（crumb不要 ヘッダー方式）
 *   2. Yahoo Finance v8 chart API – query2（フォールバック）
 *   3. Yahoo Finance v7 chart API – query1（旧エンドポイント）
 *   4. Yahoo Finance v7 chart API – query2
 *
 * wp_remote_get のみ使用（cURL直接呼び出し不要）。
 * サーバーが Yahoo Finance に到達できない場合は診断で明示する。
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class FSC_Data {

    /* ── 銘柄マスター ─────────────────────────── */
    public static function instruments(): array {
        return [
            'USD/JPY' => [ 'label' => 'USD/JPY',   'group' => 'FX',        'ticker' => 'USDJPY=X', 'dec' => 3 ],
            'EUR/USD' => [ 'label' => 'EUR/USD',   'group' => 'FX',        'ticker' => 'EURUSD=X', 'dec' => 5 ],
            'GBP/USD' => [ 'label' => 'GBP/USD',   'group' => 'FX',        'ticker' => 'GBPUSD=X', 'dec' => 5 ],
            'AUD/USD' => [ 'label' => 'AUD/USD',   'group' => 'FX',        'ticker' => 'AUDUSD=X', 'dec' => 5 ],
            'EUR/JPY' => [ 'label' => 'EUR/JPY',   'group' => 'FX',        'ticker' => 'EURJPY=X', 'dec' => 3 ],
            'GBP/JPY' => [ 'label' => 'GBP/JPY',   'group' => 'FX',        'ticker' => 'GBPJPY=X', 'dec' => 3 ],
            'USD/CHF' => [ 'label' => 'USD/CHF',   'group' => 'FX',        'ticker' => 'USDCHF=X', 'dec' => 5 ],
            'NZD/USD' => [ 'label' => 'NZD/USD',   'group' => 'FX',        'ticker' => 'NZDUSD=X', 'dec' => 5 ],
            'XAU/USD' => [ 'label' => 'ゴールド',  'group' => 'Commodity', 'ticker' => 'GC=F',     'dec' => 2 ],
            'WTI'     => [ 'label' => '原油(WTI)', 'group' => 'Commodity', 'ticker' => 'CL=F',     'dec' => 2 ],
        ];
    }

    public static function intervals(): array {
        return [
            '5min'  => '5分足',
            '15min' => '15分足',
            '30min' => '30分足',
            '1h'    => '1時間足',
            '4h'    => '4時間足',
            '1day'  => '日足',
        ];
    }

    /* ── 時間足 → Yahoo パラメータ ───────────── */
    private static function tf_params( string $tf ): array {
        return match ( $tf ) {
            '5min'  => [ 'interval' => '5m',  'range' => '5d'  ],
            '15min' => [ 'interval' => '15m', 'range' => '10d' ],
            '30min' => [ 'interval' => '30m', 'range' => '20d' ],
            '1h'    => [ 'interval' => '60m', 'range' => '1mo' ],
            '4h'    => [ 'interval' => '1h',  'range' => '3mo' ],
            '1day'  => [ 'interval' => '1d',  'range' => '1y'  ],
            default => [ 'interval' => '15m', 'range' => '10d' ],
        };
    }

    const CRUMB_CACHE_KEY  = 'fsc_yf_crumb';
    const COOKIE_CACHE_KEY = 'fsc_yf_cookie';
    const CRUMB_TTL        = 3600;

    private static function get_cookie_and_crumb() {
        $crumb  = get_transient( self::CRUMB_CACHE_KEY );
        $cookie = get_transient( self::COOKIE_CACHE_KEY );
        if ( $crumb && $cookie ) return [ $cookie, $crumb ];

        $r1 = wp_remote_get( 'https://finance.yahoo.com/', [
            'timeout'    => 10,
            'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        ] );
        if ( is_wp_error( $r1 ) ) return [ null, null ];

        $cookies = wp_remote_retrieve_cookies( $r1 );
        $cookies_arr = [];
        foreach ( $cookies as $c ) $cookies_arr[] = $c->name . '=' . $c->value;
        $set_cookie = implode( '; ', $cookies_arr );

        $r2 = wp_remote_get( 'https://query2.finance.yahoo.com/v1/test/getcrumb', [
            'timeout'    => 10,
            'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'headers'    => [ 'Cookie' => $set_cookie ],
        ] );
        if ( is_wp_error( $r2 ) ) return [ null, null ];

        $crumb = trim( wp_remote_retrieve_body( $r2 ) );
        if ( ! $crumb || strlen( $crumb ) < 3 ) return [ null, null ];

        set_transient( self::COOKIE_CACHE_KEY, $set_cookie, self::CRUMB_TTL );
        set_transient( self::CRUMB_CACHE_KEY,  $crumb,      self::CRUMB_TTL );

        return [ $set_cookie, $crumb ];
    }

    /* ── 共通リクエストヘッダー ──────────────── */
    private static function headers( string $ticker = '', string $cookie = '' ): array {
        return [
            'User-Agent'      => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept'          => 'application/json, text/plain, */*',
            'Accept-Language' => 'en-US,en;q=0.9',
            'Accept-Encoding' => 'gzip, deflate',
            'Referer'         => 'https://finance.yahoo.com/quote/' . rawurlencode( $ticker ),
            'Origin'          => 'https://finance.yahoo.com',
            'Cookie'          => $cookie ?: 'B=0',
        ];
    }

    /* ── メイン: ローソク足データ取得 ───────── */
    public function get_candles( string $symbol, string $tf, int $limit = 80 ): array|WP_Error {
        $cache_key = 'fsc_' . md5( $symbol . $tf . $limit );
        $cached    = get_transient( $cache_key );
        if ( $cached !== false ) return $cached;

        $instr  = self::instruments();
        $ticker = $instr[ $symbol ]['ticker'] ?? strtoupper( str_replace( '/', '', $symbol ) ) . '=X';
        $params = self::tf_params( $tf );
        $qs     = http_build_query( [
            'interval'       => $params['interval'],
            'range'          => $params['range'],
            'includePrePost' => 'false',
            'events'         => 'div|split',
            'corsDomain'     => 'finance.yahoo.com',
        ] );

        [ $cookie, $crumb ] = self::get_cookie_and_crumb();
        if ( $crumb ) {
            $qs .= '&crumb=' . rawurlencode( $crumb );
        }

        // 試すエンドポイント（v8優先、v7フォールバック）
        $endpoints = [
            "https://query1.finance.yahoo.com/v8/finance/chart/{$ticker}?{$qs}",
            "https://query2.finance.yahoo.com/v8/finance/chart/{$ticker}?{$qs}",
            "https://query1.finance.yahoo.com/v7/finance/chart/{$ticker}?{$qs}",
            "https://query2.finance.yahoo.com/v7/finance/chart/{$ticker}?{$qs}",
        ];

        $last_error = null;

        foreach ( $endpoints as $url ) {
            $resp = wp_remote_get( $url, [
                'timeout'     => 20,
                'redirection' => 3,
                'headers'     => self::headers( $ticker, $cookie ?? '' ),
                'sslverify'   => true,
            ] );

            // 接続失敗
            if ( is_wp_error( $resp ) ) {
                $last_error = new WP_Error(
                    'connect_error',
                    'サーバーから Yahoo Finance へ接続できません: ' . $resp->get_error_message() .
                    '。ホスティング会社のファイアウォール設定をご確認ください。'
                );
                continue;
            }

            $code = wp_remote_retrieve_response_code( $resp );
            $body = wp_remote_retrieve_body( $resp );

            // 401/403: 認証問題
            if ( in_array( $code, [ 401, 403 ], true ) ) {
                delete_transient( self::CRUMB_CACHE_KEY );
                delete_transient( self::COOKIE_CACHE_KEY );
                $last_error = new WP_Error( 'auth_error', "Yahoo Finance 認証エラー (HTTP {$code})。次のエンドポイントを試します。" );
                continue;
            }

            // その他エラー
            if ( $code !== 200 ) {
                $last_error = new WP_Error( 'http_error', "Yahoo Finance HTTP {$code} エラー。次のエンドポイントを試します。" );
                continue;
            }

            // 成功 → パース
            $parsed = $this->parse( $body, $symbol, $tf, $limit );
            if ( is_wp_error( $parsed ) ) {
                $last_error = $parsed;
                continue;
            }

            // キャッシュして返す
            $ttl = (int) get_option( 'fsc_cache_ttl', 120 );
            set_transient( $cache_key, $parsed, $ttl );
            return $parsed;
        }

        // 全エンドポイント失敗
        return $last_error ?? new WP_Error( 'all_failed', '全てのYahoo Financeエンドポイントへの接続に失敗しました。' );
    }

    /* ── JSONパース ───────────────────────────── */
    private function parse( string $body, string $symbol, string $tf, int $limit ): array|WP_Error {
        if ( empty( $body ) ) {
            return new WP_Error( 'empty_body', 'Yahoo Finance から空のレスポンスが返りました。' );
        }

        $json = json_decode( $body, true );
        if ( json_last_error() !== JSON_ERROR_NONE ) {
            // HTMLが返ってきた場合（ブロックされている）
            if ( str_contains( $body, '<html' ) ) {
                return new WP_Error( 'blocked', 'Yahoo Finance からHTMLが返りました。サーバーのIPがブロックされている可能性があります。' );
            }
            return new WP_Error( 'json_error', 'JSONパース失敗: ' . json_last_error_msg() );
        }

        // API エラーチェック
        if ( ! empty( $json['chart']['error'] ) ) {
            $msg = $json['chart']['error']['description'] ?? '不明なエラー';
            $code = $json['chart']['error']['code'] ?? '';
            return new WP_Error( 'api_error', "Yahoo Finance API エラー [{$code}]: {$msg}" );
        }

        $result = $json['chart']['result'][0] ?? null;
        if ( ! $result ) {
            return new WP_Error( 'no_result', '取得できませんでした。銘柄コードを確認するか、市場が開いている時間に再試行してください。' );
        }

        $timestamps = $result['timestamp'] ?? [];
        $quote      = $result['indicators']['quote'][0] ?? [];

        if ( empty( $timestamps ) ) {
            return new WP_Error( 'no_data', 'データが0件です。市場が閉じている可能性があります。' );
        }

        $candles = [];
        foreach ( $timestamps as $i => $ts ) {
            $o = $quote['open'][$i]  ?? null;
            $h = $quote['high'][$i]  ?? null;
            $l = $quote['low'][$i]   ?? null;
            $c = $quote['close'][$i] ?? null;
            if ( $o === null || $c === null || ( $o == 0 && $c == 0 ) ) continue;
            $candles[] = [
                'time'  => gmdate( 'Y-m-d H:i', (int) $ts ),
                'open'  => (float) $o,
                'high'  => (float) $h,
                'low'   => (float) $l,
                'close' => (float) $c,
            ];
        }

        $candles = array_values( array_slice( $candles, -$limit ) );
        if ( empty( $candles ) ) {
            return new WP_Error( 'empty_candles', 'ローソク足データが0件です。' );
        }

        $instr = self::instruments();
        return [
            'success'    => true,
            'candles'    => $candles,
            'symbol'     => $symbol,
            'interval'   => $tf,
            'dec'        => $instr[$symbol]['dec'] ?? 5,
            'provider'   => 'Yahoo Finance',
            'meta'       => $result['meta'] ?? [],
            'fetched_at' => current_time( 'mysql' ),
        ];
    }

    /* ── 診断: 接続状況を詳細チェック ──────── */
    public static function diagnose(): array {
        $out = [];

        // 1. WordPress HTTP API で Yahoo Finance に到達できるか
        $yahoo_home = wp_remote_get( 'https://finance.yahoo.com/', [
            'timeout' => 10,
            'headers' => [ 'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' ],
        ] );
        if ( is_wp_error( $yahoo_home ) ) {
            $out['Yahoo Finance (finance.yahoo.com)'] = [
                'ok'  => false,
                'msg' => '❌ 接続不可: ' . $yahoo_home->get_error_message(),
                'fix' => 'ホスティング会社に「外部HTTPS接続（ポート443）の許可」を依頼してください。特にYahoo Finance (finance.yahoo.com) へのアクセスが必要です。',
            ];
        } else {
            $code = wp_remote_retrieve_response_code( $yahoo_home );
            $out['Yahoo Finance (finance.yahoo.com)'] = [
                'ok'  => $code >= 200 && $code < 400,
                'msg' => "HTTP {$code}",
            ];
        }

        [ $cookie, $crumb ] = self::get_cookie_and_crumb();
        $crumb_param = $crumb ? '&crumb=' . rawurlencode( $crumb ) : '';

        // 2. query1 (v8 API) に到達できるか
        $test_ticker = 'USDJPY=X';
        $q1 = wp_remote_get( "https://query1.finance.yahoo.com/v8/finance/chart/{$test_ticker}?interval=1d&range=5d{$crumb_param}", [
            'timeout' => 12,
            'headers' => self::headers( $test_ticker, $cookie ?? '' ),
        ] );
        if ( is_wp_error( $q1 ) ) {
            $out['Yahoo Finance API (query1, v8)'] = [
                'ok'  => false,
                'msg' => '❌ 接続不可: ' . $q1->get_error_message(),
                'fix' => 'query1.finance.yahoo.com への接続がブロックされています。',
            ];
        } else {
            $code = wp_remote_retrieve_response_code( $q1 );
            $body = wp_remote_retrieve_body( $q1 );
            $has_data = str_contains( $body, 'timestamp' );
            $out['Yahoo Finance API (query1, v8)'] = [
                'ok'  => $code === 200 && $has_data,
                'msg' => "HTTP {$code}" . ( $has_data ? ' ✅ データあり' : ' ⚠ データなし（認証ブロックの可能性）' ),
                'body_preview' => substr( $body, 0, 200 ),
            ];
        }

        // 3. query2 (v8 API)
        $q2 = wp_remote_get( "https://query2.finance.yahoo.com/v8/finance/chart/{$test_ticker}?interval=1d&range=5d{$crumb_param}", [
            'timeout' => 12,
            'headers' => self::headers( $test_ticker, $cookie ?? '' ),
        ] );
        if ( is_wp_error( $q2 ) ) {
            $out['Yahoo Finance API (query2, v8)'] = [
                'ok'  => false,
                'msg' => '❌ 接続不可: ' . $q2->get_error_message(),
            ];
        } else {
            $code = wp_remote_retrieve_response_code( $q2 );
            $body = wp_remote_retrieve_body( $q2 );
            $has_data = str_contains( $body, 'timestamp' );
            $out['Yahoo Finance API (query2, v8)'] = [
                'ok'  => $code === 200 && $has_data,
                'msg' => "HTTP {$code}" . ( $has_data ? ' ✅ データあり' : ' ⚠ データなし' ),
                'body_preview' => substr( $body, 0, 200 ),
            ];
        }

        // 4. query1 v7 API
        $q1v7 = wp_remote_get( "https://query1.finance.yahoo.com/v7/finance/chart/{$test_ticker}?interval=1d&range=5d{$crumb_param}", [
            'timeout' => 12,
            'headers' => self::headers( $test_ticker, $cookie ?? '' ),
        ] );
        if ( is_wp_error( $q1v7 ) ) {
            $out['Yahoo Finance API (query1, v7)'] = [
                'ok'  => false,
                'msg' => '❌ 接続不可: ' . $q1v7->get_error_message(),
            ];
        } else {
            $code = wp_remote_retrieve_response_code( $q1v7 );
            $body = wp_remote_retrieve_body( $q1v7 );
            $has_data = str_contains( $body, 'timestamp' );
            $out['Yahoo Finance API (query1, v7)'] = [
                'ok'  => $code === 200 && $has_data,
                'msg' => "HTTP {$code}" . ( $has_data ? ' ✅ データあり' : ' ⚠ データなし' ),
                'body_preview' => substr( $body, 0, 200 ),
            ];
        }

        // 5. サーバー情報
        $out['サーバー情報'] = [
            'ok'  => true,
            'msg' => 'PHP ' . PHP_VERSION . ' | WordPress ' . get_bloginfo('version') . ' | サーバーIP: ' . ( $_SERVER['SERVER_ADDR'] ?? gethostbyname( gethostname() ) ),
        ];

        return $out;
    }
}
