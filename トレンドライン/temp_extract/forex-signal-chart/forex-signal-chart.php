<?php
/**
 * Plugin Name: FX Signal Chart
 * Description: Yahoo Finance APIでFX・ゴールド・原油のリアルタイムチャートを表示。自動トレンドライン＆ローソク足シグナル検出。
 * Version:     5.0.0
 * Author:      Claude / Anthropic
 * License:     GPL v2 or later
 * Text Domain: fx-signal-chart
 */
if ( ! defined( 'ABSPATH' ) ) exit;

define( 'FSC_VER',  '5.0.1' );
define( 'FSC_DIR',  plugin_dir_path( __FILE__ ) );
define( 'FSC_URL',  plugin_dir_url( __FILE__ ) );
define( 'FSC_BASE', plugin_basename( __FILE__ ) );

add_action( 'plugins_loaded', function () {
    require_once FSC_DIR . 'includes/class-fsc-data.php';
    require_once FSC_DIR . 'includes/class-fsc-admin.php';
    require_once FSC_DIR . 'includes/class-fsc-shortcode.php';
    new FSC_Admin();
    new FSC_Shortcode();
} );

register_activation_hook( __FILE__, function () {
    add_option( 'fsc_cache_ttl',      120    );
    add_option( 'fsc_default_symbol', 'USD/JPY' );
    add_option( 'fsc_default_tf',     '15min'   );
    add_option( 'fsc_height',         440    );
    add_option( 'fsc_signals',        1      );
    add_option( 'fsc_refresh',        60     );
} );

register_deactivation_hook( __FILE__, 'fsc_purge_cache' );
function fsc_purge_cache(): void {
    global $wpdb;
    $wpdb->query( "DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_fsc_%' OR option_name LIKE '_transient_timeout_fsc_%'" );
}
register_uninstall_hook( __FILE__, 'fsc_purge_cache' );
