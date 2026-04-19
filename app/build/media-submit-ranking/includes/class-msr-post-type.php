<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class MSR_Post_Type {

    public static function register() {
        // カスタム投稿タイプ: メディア投稿
        register_post_type( 'msr_media', [
            'labels' => [
                'name'          => 'メディア投稿',
                'singular_name' => 'メディア',
                'add_new_item'  => '新しいメディアを追加',
                'edit_item'     => 'メディアを編集',
                'view_item'     => 'メディアを表示',
                'search_items'  => 'メディアを検索',
            ],
            'public'       => true,
            'has_archive'  => true,
            'show_in_menu' => false,
            'supports'     => ['title', 'editor', 'thumbnail'],
            'rewrite'      => ['slug' => 'msr-media'],
        ]);

        // タクソノミー: メディアタイプ (app / mp3)
        register_taxonomy( 'msr_type', 'msr_media', [
            'labels' => [
                'name'          => 'メディアタイプ',
                'singular_name' => 'タイプ',
            ],
            'hierarchical' => true,
            'public'       => true,
            'rewrite'      => ['slug' => 'msr-type'],
        ]);

        // デフォルトタームの作成
        if ( ! term_exists( 'app', 'msr_type' ) ) {
            wp_insert_term( 'アプリ', 'msr_type', ['slug' => 'app'] );
        }
        if ( ! term_exists( 'mp3', 'msr_type' ) ) {
            wp_insert_term( 'MP3', 'msr_type', ['slug' => 'mp3'] );
        }
    }
}
