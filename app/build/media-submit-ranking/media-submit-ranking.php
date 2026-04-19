<?php
/**
 * Plugin Name: Media Submit & Ranking
 * Description: 閲覧者がアプリ・MP3を投稿でき、ランキング表示できるプラグイン
 * Version: 1.0.0
 * Author: Custom Plugin
 * Text Domain: msr
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'MSR_VERSION', '1.0.0' );
define( 'MSR_PATH', plugin_dir_path( __FILE__ ) );
define( 'MSR_URL', plugin_dir_url( __FILE__ ) );

// Include files
require_once MSR_PATH . 'includes/class-msr-post-type.php';
require_once MSR_PATH . 'includes/class-msr-shortcodes.php';
require_once MSR_PATH . 'includes/class-msr-ajax.php';
require_once MSR_PATH . 'includes/class-msr-admin.php';

// Activation
register_activation_hook( __FILE__, 'msr_activate' );
function msr_activate() {
    MSR_Post_Type::register();
    flush_rewrite_rules();
}

register_deactivation_hook( __FILE__, function() {
    flush_rewrite_rules();
});

// Init
add_action( 'init', [ 'MSR_Post_Type', 'register' ] );
add_action( 'init', [ 'MSR_Shortcodes', 'init' ] );
add_action( 'init', [ 'MSR_Ajax', 'init' ] );
add_action( 'admin_menu', [ 'MSR_Admin', 'add_menu' ] );
// admin_post_* フックは admin_menu より前に実行されるため、
// MSR_Admin::init() を別途 admin_init で呼ぶ
add_action( 'admin_init', [ 'MSR_Admin', 'init' ] );
// 設定保存
add_action( 'admin_init', [ 'MSR_Admin', 'save_settings' ] );

// Enqueue scripts
add_action( 'wp_enqueue_scripts', 'msr_enqueue_assets' );
function msr_enqueue_assets() {
    wp_enqueue_style( 'msr-style', MSR_URL . 'assets/css/style.css', [], MSR_VERSION );
    wp_enqueue_script( 'msr-script', MSR_URL . 'assets/js/script.js', ['jquery'], MSR_VERSION, true );
    wp_localize_script( 'msr-script', 'MSR', [
        'ajax_url' => admin_url( 'admin-ajax.php' ),
        'nonce'    => wp_create_nonce( 'msr_nonce' ),
    ]);
}
