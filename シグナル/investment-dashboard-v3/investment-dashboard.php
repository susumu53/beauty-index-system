<?php
/**
 * Plugin Name: Investment Dashboard
 * Plugin URI:  https://example.com
 * Description: リアルタイム投資判断ダッシュボード。Yahoo Finance（crumb認証対応）で実価格・5分足チャートを取得。
 * Version:     3.0.0
 * Author:      Your Name
 * License:     GPL-2.0+
 * Text Domain: investment-dashboard
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'INVD_VERSION', '3.0.0' );
define( 'INVD_DIR',     plugin_dir_path( __FILE__ ) );
define( 'INVD_URL',     plugin_dir_url( __FILE__ ) );

require_once INVD_DIR . 'includes/class-yahoo-finance.php';

define( 'INVD_SYMBOLS', [
    'nk225'  => [ 'yf' => '^N225',    'label' => '日経平均',  'sym' => 'N225',    'pfx' => '¥',  'dec' => 0 ],
    'sp500'  => [ 'yf' => '^GSPC',    'label' => 'S&P 500',  'sym' => 'SPX',     'pfx' => '$',  'dec' => 2 ],
    'usdjpy' => [ 'yf' => 'USDJPY=X', 'label' => 'USD/JPY',  'sym' => 'USDJPY',  'pfx' => '',   'dec' => 3 ],
    'gold'   => [ 'yf' => 'GC=F',     'label' => 'ゴールド',  'sym' => 'XAU/USD', 'pfx' => '$',  'dec' => 2 ],
    'oil'    => [ 'yf' => 'CL=F',     'label' => 'WTI原油',   'sym' => 'WTI',     'pfx' => '$',  'dec' => 2 ],
] );

class Investment_Dashboard {

    public function __construct() {
        add_action( 'wp_enqueue_scripts',         [ $this, 'enqueue_assets' ] );
        add_shortcode( 'investment_dashboard',    [ $this, 'render_shortcode' ] );
        add_action( 'admin_menu',                 [ $this, 'add_admin_menu' ] );
        add_action( 'admin_init',                 [ $this, 'register_settings' ] );
        add_action( 'admin_post_invd_clear_cache',[ $this, 'clear_cache' ] );

        add_action( 'wp_ajax_invd_prices',         [ $this, 'ajax_prices' ] );
        add_action( 'wp_ajax_nopriv_invd_prices',  [ $this, 'ajax_prices' ] );
        add_action( 'wp_ajax_invd_history',        [ $this, 'ajax_history' ] );
        add_action( 'wp_ajax_nopriv_invd_history', [ $this, 'ajax_history' ] );
    }

    public function enqueue_assets() {
        wp_enqueue_script( 'chartjs', 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js', [], '4.4.1', true );
        wp_enqueue_style(  'invd-style',  INVD_URL . 'assets/dashboard.css', [], INVD_VERSION );
        wp_enqueue_script( 'invd-script', INVD_URL . 'assets/dashboard.js', ['chartjs'], INVD_VERSION, true );

        wp_localize_script( 'invd-script', 'INVD_CONFIG', [
            'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
            'nonce'    => wp_create_nonce( 'invd_nonce' ),
            'symbols'  => INVD_SYMBOLS,
            'interval' => intval( get_option( 'invd_interval', 15000 ) ),
            'theme'    => get_option( 'invd_theme', 'dark' ),
        ] );
    }

    /* ── AJAX: all quotes ── */
    public function ajax_prices() {
        check_ajax_referer( 'invd_nonce', 'nonce' );
        $yf_syms = array_column( INVD_SYMBOLS, 'yf' );
        $quotes  = INVD_Yahoo_Finance::get_quotes( $yf_syms );

        /* Re-key by plugin id */
        $result = [];
        foreach ( INVD_SYMBOLS as $id => $info ) {
            $q = $quotes[ $info['yf'] ] ?? null;
            if ( $q ) $result[ $id ] = $q;
        }
        if ( $result ) {
            wp_send_json_success( $result );
        } else {
            wp_send_json_error( [ 'message' => 'Yahoo Finance からデータを取得できませんでした。' ] );
        }
    }

    /* ── AJAX: 5-min chart history ── */
    public function ajax_history() {
        check_ajax_referer( 'invd_nonce', 'nonce' );
        $id = sanitize_key( $_GET['id'] ?? '' );
        if ( ! isset( INVD_SYMBOLS[ $id ] ) ) wp_send_json_error( 'invalid id' );

        $data = INVD_Yahoo_Finance::get_chart( INVD_SYMBOLS[ $id ]['yf'], '5d', '5m' );
        if ( $data ) {
            wp_send_json_success( $data );
        } else {
            wp_send_json_error( [ 'message' => 'チャートデータを取得できませんでした。' ] );
        }
    }

    /* ── Shortcode ── */
    public function render_shortcode( $atts ) {
        $atts = shortcode_atts( [
            'theme'    => get_option( 'invd_theme', 'dark' ),
            'interval' => get_option( 'invd_interval', '15000' ),
        ], $atts );
        ob_start();
        ?>
        <div class="invd-wrap invd-theme-<?php echo esc_attr($atts['theme']); ?>"
             data-interval="<?php echo intval($atts['interval']); ?>"
             data-theme="<?php echo esc_attr($atts['theme']); ?>">

            <div class="invd-header">
                <span class="invd-logo">投資判断ダッシュボード</span>
                <span class="invd-live"><span class="invd-dot"></span><span id="invd-status">接続中...</span></span>
            </div>

            <div class="invd-tabs" id="invd-tabs"></div>

            <div class="invd-price-row">
                <span class="invd-sym"  id="invd-sym">-</span>
                <span class="invd-pval" id="invd-pval">-</span>
                <span class="invd-pchg" id="invd-pchg"></span>
            </div>

            <div class="invd-charts">
                <div class="invd-chart-box">
                    <div class="invd-chart-header">
                        <span class="invd-chart-title">PRICE · EMA · BOLLINGER BANDS（5分足 5日間）</span>
                        <span class="invd-legend">
                            <span class="invd-li" style="--c:#79c0ff">価格</span>
                            <span class="invd-li" style="--c:#ffa657">EMA20</span>
                            <span class="invd-li" style="--c:#f85149">EMA50</span>
                            <span class="invd-li" style="--c:rgba(191,145,243,.6)">BB</span>
                        </span>
                    </div>
                    <div class="invd-canvas-wrap" style="height:200px"><canvas id="invd-price"></canvas></div>
                </div>
                <div class="invd-chart-sub">
                    <div class="invd-chart-box">
                        <div class="invd-chart-title">RSI (14)</div>
                        <div class="invd-canvas-wrap" style="height:90px"><canvas id="invd-rsi"></canvas></div>
                    </div>
                    <div class="invd-chart-box">
                        <div class="invd-chart-title">MACD (12, 26, 9)</div>
                        <div class="invd-canvas-wrap" style="height:90px"><canvas id="invd-macd"></canvas></div>
                    </div>
                </div>
            </div>

            <div class="invd-signal-bar">
                <div>
                    <div class="invd-sb-label">複合シグナルスコア</div>
                    <div class="invd-sb-score" id="invd-score">-</div>
                </div>
                <div class="invd-sb-meter"><div class="invd-sb-fill" id="invd-meter"></div></div>
                <div class="invd-sb-verdict" id="invd-verdict">-</div>
            </div>

            <div class="invd-theory-panel">
                <div class="invd-theory-header">
                    <span>相場判定 (ダウ & レンジ)</span>
                    <span id="invd-market-phase" class="invd-phase-badge">-</span>
                </div>
                <div class="invd-theory-grid">
                    <div class="invd-theory-item">
                        <div class="invd-theory-label">ダウ理論構造</div>
                        <div id="invd-dow-status" class="invd-theory-val">-</div>
                    </div>
                    <div class="invd-theory-item">
                        <div class="invd-theory-label">レンジ判定</div>
                        <div id="invd-range-status" class="invd-theory-val">-</div>
                    </div>
                    <div class="invd-theory-item">
                        <div class="invd-theory-label">Wemof 異常値判定</div>
                        <div id="invd-wemof-status" class="invd-theory-val">-</div>
                    </div>
                </div>
            </div>

            <div class="invd-ind-grid" id="invd-ind-grid"></div>

            <div class="invd-log-title">テクニカル・シグナル履歴 (Trendline & Granville)</div>
            <div class="invd-signal-log" id="invd-signal-log">
                <div class="invd-log-empty">シグナル待機中...</div>
            </div>


            <div class="invd-footer">
                <span id="invd-updated"></span>&nbsp;·&nbsp;データ提供: Yahoo Finance
            </div>
        </div>
        <?php
        return ob_get_clean();
    }

    /* ── Admin ── */
    public function add_admin_menu() {
        add_options_page( '投資ダッシュボード設定', '投資ダッシュボード', 'manage_options',
            'investment-dashboard', [ $this, 'render_admin_page' ] );
    }

    public function register_settings() {
        register_setting( 'invd_settings', 'invd_theme' );
        register_setting( 'invd_settings', 'invd_interval' );
    }

    public function clear_cache() {
        if ( ! current_user_can('manage_options') ) wp_die('権限がありません');
        check_admin_referer('invd_clear_cache');
        global $wpdb;
        $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_invd_%' OR option_name LIKE '_transient_timeout_invd_%'");
        wp_redirect( add_query_arg(['page'=>'investment-dashboard','cleared'=>1], admin_url('options-general.php')) );
        exit;
    }

    public function render_admin_page() { ?>
        <div class="wrap">
            <h1>投資ダッシュボード 設定</h1>

            <?php if ( isset($_GET['cleared']) ) : ?>
            <div class="notice notice-success"><p>キャッシュを削除しました。</p></div>
            <?php endif; ?>

            <div class="notice notice-info">
                <p><strong>ショートコード:</strong> <code>[investment_dashboard]</code></p>
                <p>例: <code>[investment_dashboard theme="light" interval="30000"]</code></p>
            </div>

            <form method="post" action="options.php">
                <?php settings_fields('invd_settings'); ?>
                <table class="form-table">
                    <tr>
                        <th>テーマ</th>
                        <td>
                            <select name="invd_theme">
                                <option value="dark"  <?php selected(get_option('invd_theme','dark'),'dark'); ?>>ダーク</option>
                                <option value="light" <?php selected(get_option('invd_theme','dark'),'light'); ?>>ライト</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th>更新間隔</th>
                        <td>
                            <select name="invd_interval">
                                <option value="10000" <?php selected(get_option('invd_interval','15000'),'10000'); ?>>10秒</option>
                                <option value="15000" <?php selected(get_option('invd_interval','15000'),'15000'); ?>>15秒（推奨）</option>
                                <option value="30000" <?php selected(get_option('invd_interval','15000'),'30000'); ?>>30秒</option>
                                <option value="60000" <?php selected(get_option('invd_interval','15000'),'60000'); ?>>1分</option>
                            </select>
                        </td>
                    </tr>
                </table>
                <?php submit_button('設定を保存'); ?>
            </form>

            <hr>
            <h2>キャッシュ管理</h2>
            <p>価格が古い・チャートが表示されない場合はキャッシュを削除してください。</p>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
                <input type="hidden" name="action" value="invd_clear_cache">
                <?php wp_nonce_field('invd_clear_cache'); ?>
                <?php submit_button('キャッシュを削除', 'secondary'); ?>
            </form>

            <hr>
            <h2>仕組み</h2>
            <p>
                ブラウザ → WordPress（PHP） → Yahoo Finance（cookie + crumb認証）<br>
                サーバーサイドで認証するためAPIキーは不要です。<br>
                crumbは1時間、チャートは60秒、価格は8秒キャッシュされます。
            </p>
        </div>
    <?php }
}

new Investment_Dashboard();
