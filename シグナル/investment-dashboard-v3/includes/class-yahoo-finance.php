<?php
/**
 * Yahoo Finance API helper with crumb/cookie authentication.
 * Yahoo Finance requires:
 *   1. GET finance.yahoo.com  → receive session cookies (A3, etc.)
 *   2. GET /v1/test/getcrumb  → receive crumb string
 *   3. All subsequent API calls must include cookie + crumb param
 */
class INVD_Yahoo_Finance {

    const CRUMB_CACHE_KEY   = 'invd_yf_crumb';
    const COOKIE_CACHE_KEY  = 'invd_yf_cookie';
    const CRUMB_TTL         = 3600;  // 1 hour
    const QUOTE_TTL         = 8;     // 8 seconds
    const CHART_TTL         = 60;    // 60 seconds

    private static function get_cookie_and_crumb() {
        $crumb  = get_transient( self::CRUMB_CACHE_KEY );
        $cookie = get_transient( self::COOKIE_CACHE_KEY );
        if ( $crumb && $cookie ) return [ $cookie, $crumb ];

        /* Step 1: hit Yahoo Finance to collect cookies */
        $r1 = wp_remote_get( 'https://finance.yahoo.com/', [
            'timeout'    => 10,
            'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers'    => [ 'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' ],
        ] );
        if ( is_wp_error( $r1 ) ) return [ null, null ];

        /* Extract cookies using WP helper */
        $cookies = wp_remote_retrieve_cookies( $r1 );
        $cookies_arr = [];
        foreach ( $cookies as $cookie ) {
            $cookies_arr[] = $cookie->name . '=' . $cookie->value;
        }
        $set_cookie = implode( '; ', $cookies_arr );

        /* Step 2: fetch crumb using same cookies */
        $r2 = wp_remote_get( 'https://query2.finance.yahoo.com/v1/test/getcrumb', [
            'timeout'    => 10,
            'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers'    => [
                'Accept' => '*/*',
                'Cookie' => $set_cookie,
            ],
        ] );
        if ( is_wp_error( $r2 ) ) return [ null, null ];

        $crumb = trim( wp_remote_retrieve_body( $r2 ) );
        if ( ! $crumb || strlen( $crumb ) < 3 ) return [ null, null ];

        set_transient( self::COOKIE_CACHE_KEY, $set_cookie, self::CRUMB_TTL );
        set_transient( self::CRUMB_CACHE_KEY,  $crumb,      self::CRUMB_TTL );

        return [ $set_cookie, $crumb ];
    }

    private static function yf_get( $url ) {
        [ $cookie, $crumb ] = self::get_cookie_and_crumb();
        if ( ! $crumb ) return null;

        // Append crumb
        $url .= ( strpos( $url, '?' ) !== false ? '&' : '?' ) . 'crumb=' . rawurlencode( $crumb );

        $resp = wp_remote_get( $url, [
            'timeout'    => 10,
            'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers'    => [
                'Accept' => 'application/json',
                'Cookie' => $cookie,
            ],
        ] );
        if ( is_wp_error( $resp ) ) return null;
        $code = wp_remote_retrieve_response_code( $resp );
        if ( $code === 401 || $code === 403 ) {
            static $retried = false;
            // Crumb expired — bust cache and retry once
            delete_transient( self::CRUMB_CACHE_KEY );
            delete_transient( self::COOKIE_CACHE_KEY );
            
            if ( ! $retried ) {
                $retried = true;
                // remove old crumb param before retrying
                $clean_url = preg_replace('/([?&])crumb=[^&]*(&|$)/', '$1', $url);
                $clean_url = rtrim($clean_url, '?&');
                return self::yf_get( $clean_url );
            }
            return null;
        }
        return json_decode( wp_remote_retrieve_body( $resp ), true );
    }

    /** Fetch current quote for multiple symbols */
    public static function get_quotes( array $symbols ) {
        $sym_str   = implode( ',', array_map( 'rawurlencode', $symbols ) );
        $cache_key = 'invd_quotes_' . md5( $sym_str );
        $cached    = get_transient( $cache_key );
        if ( $cached !== false ) return $cached;

        $url  = 'https://query2.finance.yahoo.com/v7/finance/quote?symbols=' . $sym_str
              . '&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketPreviousClose';
        $body = self::yf_get( $url );

        $result = [];
        $rows   = $body['quoteResponse']['result'] ?? [];
        foreach ( $rows as $q ) {
            $result[ $q['symbol'] ] = [
                'price'     => round( $q['regularMarketPrice']             ?? 0, 5 ),
                'change'    => round( $q['regularMarketChange']            ?? 0, 5 ),
                'changePct' => round( $q['regularMarketChangePercent']     ?? 0, 3 ),
                'prevClose' => round( $q['regularMarketPreviousClose']     ?? 0, 5 ),
            ];
        }

        if ( $result ) set_transient( $cache_key, $result, self::QUOTE_TTL );
        return $result;
    }

    /** Fetch intraday 5-min chart data */
    public static function get_chart( $symbol, $range = '5d', $interval = '5m' ) {
        $cache_key = 'invd_chart_' . md5( $symbol . $range . $interval );
        $cached    = get_transient( $cache_key );
        if ( $cached !== false ) return $cached;

        $url  = 'https://query2.finance.yahoo.com/v8/finance/chart/' . rawurlencode( $symbol )
              . '?interval=' . $interval . '&range=' . $range;
        $body = self::yf_get( $url );

        $res = $body['chart']['result'][0] ?? null;
        if ( ! $res ) return null;

        $q      = $res['indicators']['quote'][0] ?? [];
        $closes = array_values( array_filter( $q['close'] ?? [], 'is_numeric' ) );
        $opens  = array_values( array_filter( $q['open']  ?? [], 'is_numeric' ) );
        $highs  = array_values( array_filter( $q['high']  ?? [], 'is_numeric' ) );
        $lows   = array_values( array_filter( $q['low']   ?? [], 'is_numeric' ) );

        if ( count( $closes ) < 10 ) return null;

        $out = [
            'closes' => array_map( fn($v) => round($v, 5), $closes ),
            'opens'  => array_map( fn($v) => round($v, 5), $opens  ),
            'highs'  => array_map( fn($v) => round($v, 5), $highs  ),
            'lows'   => array_map( fn($v) => round($v, 5), $lows   ),
            'count'  => count( $closes ),
        ];

        if ( $out ) set_transient( $cache_key, $out, self::CHART_TTL );
        return $out;
    }
}
