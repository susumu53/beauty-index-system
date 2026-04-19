<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class MSR_Ajax {

    public static function init() {
        // 投稿送信 (ログイン不要)
        add_action( 'wp_ajax_msr_submit',        [ __CLASS__, 'handle_submit' ] );
        add_action( 'wp_ajax_nopriv_msr_submit', [ __CLASS__, 'handle_submit' ] );

        // いいね
        add_action( 'wp_ajax_msr_like',        [ __CLASS__, 'handle_like' ] );
        add_action( 'wp_ajax_nopriv_msr_like', [ __CLASS__, 'handle_like' ] );

        // ダウンロードカウント
        add_action( 'wp_ajax_msr_download',        [ __CLASS__, 'handle_download' ] );
        add_action( 'wp_ajax_nopriv_msr_download', [ __CLASS__, 'handle_download' ] );
    }

    // ---- 投稿送信 ----
    public static function handle_submit() {
        check_ajax_referer( 'msr_nonce', 'nonce' );

        $title         = sanitize_text_field( $_POST['title'] ?? '' );
        $description   = sanitize_textarea_field( $_POST['description'] ?? '' );
        $author_name   = sanitize_text_field( $_POST['author_name'] ?? '匿名' );
        $media_type    = sanitize_key( $_POST['media_type'] ?? 'app' );
        $link_url      = esc_url_raw( $_POST['link_url'] ?? '' );
        $affiliate_url = esc_url_raw( $_POST['affiliate_url'] ?? '' );

        if ( empty( $title ) ) {
            wp_send_json_error( ['message' => 'タイトルは必須です。'] );
        }

        // 投稿を作成（レビュー待ちの場合は pending, 即時公開は publish）
        $status = get_option( 'msr_auto_publish', '0' ) === '1' ? 'publish' : 'pending';

        $post_id = wp_insert_post([
            'post_title'   => $title,
            'post_content' => $description,
            'post_status'  => $status,
            'post_type'    => 'msr_media',
            'post_author'  => 0,
        ]);

        if ( is_wp_error( $post_id ) ) {
            wp_send_json_error( ['message' => '投稿に失敗しました。'] );
        }

        // メタデータ保存
        update_post_meta( $post_id, '_msr_author_name', $author_name );
        update_post_meta( $post_id, '_msr_link_url', $link_url );
        update_post_meta( $post_id, '_msr_affiliate_url', $affiliate_url );
        update_post_meta( $post_id, '_msr_likes', 0 );
        update_post_meta( $post_id, '_msr_downloads', 0 );
        update_post_meta( $post_id, '_msr_views', 0 );

        // ファイルアップロード (MP3)
        if ( ! empty( $_FILES['mp3_file']['name'] ) && $media_type === 'mp3' ) {
            if ( ! function_exists( 'wp_handle_upload' ) ) {
                require_once ABSPATH . 'wp-admin/includes/file.php';
            }
            $file = $_FILES['mp3_file'];
            $allowed_types = ['audio/mpeg', 'audio/mp3'];
            if ( in_array( $file['type'], $allowed_types ) && $file['size'] <= 50 * 1024 * 1024 ) {
                $uploaded = wp_handle_upload( $file, ['test_form' => false] );
                if ( isset( $uploaded['url'] ) ) {
                    update_post_meta( $post_id, '_msr_mp3_url', $uploaded['url'] );
                }
            }
        }

        // タクソノミー設定
        $term = get_term_by( 'slug', $media_type, 'msr_type' );
        if ( $term ) {
            wp_set_post_terms( $post_id, [$term->term_id], 'msr_type' );
        }

        $message = $status === 'publish'
            ? '投稿が公開されました！'
            : '投稿を受け付けました。管理者の承認後に公開されます。';

        wp_send_json_success( ['message' => $message] );
    }

    // ---- いいね ----
    public static function handle_like() {
        check_ajax_referer( 'msr_nonce', 'nonce' );

        $post_id = intval( $_POST['post_id'] ?? 0 );
        if ( ! $post_id ) wp_send_json_error();

        // IP ベースの重複防止
        $ip   = $_SERVER['REMOTE_ADDR'];
        $key  = '_msr_liked_ips';
        $ips  = get_post_meta( $post_id, $key, true ) ?: [];

        if ( in_array( $ip, $ips ) ) {
            wp_send_json_error( ['message' => 'すでにいいね済みです。'] );
        }

        $ips[] = $ip;
        update_post_meta( $post_id, $key, $ips );

        $likes = intval( get_post_meta( $post_id, '_msr_likes', true ) ) + 1;
        update_post_meta( $post_id, '_msr_likes', $likes );

        wp_send_json_success( ['likes' => $likes] );
    }

    // ---- ダウンロードカウント ----
    public static function handle_download() {
        check_ajax_referer( 'msr_nonce', 'nonce' );

        $post_id  = intval( $_POST['post_id'] ?? 0 );
        if ( ! $post_id ) wp_send_json_error();

        $downloads = intval( get_post_meta( $post_id, '_msr_downloads', true ) ) + 1;
        update_post_meta( $post_id, '_msr_downloads', $downloads );

        wp_send_json_success( ['downloads' => $downloads] );
    }
}
