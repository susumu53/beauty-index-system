<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class MSR_Admin {

    /**
     * admin_post_* フックは admin_menu より前に実行されるため、
     * 独立した init() メソッドで登録する必要がある
     */
    public static function init() {
        // 承認・却下アクション（admin-post.php経由）
        add_action( 'admin_post_msr_approve', [ __CLASS__, 'approve_post' ] );
        add_action( 'admin_post_msr_reject',  [ __CLASS__, 'reject_post' ] );
    }

    public static function add_menu() {
        add_menu_page(
            'Media Submit & Ranking',
            '📦 メディア投稿',
            'manage_options',
            'msr-admin',
            [ __CLASS__, 'page_dashboard' ],
            'dashicons-album',
            30
        );
        add_submenu_page( 'msr-admin', '投稿管理', '投稿管理', 'manage_options', 'msr-admin', [ __CLASS__, 'page_dashboard' ] );
        add_submenu_page( 'msr-admin', '設定', '設定', 'manage_options', 'msr-settings', [ __CLASS__, 'page_settings' ] );
        add_submenu_page( 'msr-admin', '使い方', '使い方', 'manage_options', 'msr-howto', [ __CLASS__, 'page_howto' ] );
    }

    // ======= ダッシュボード =======
    public static function page_dashboard() {
        // 統計
        $total     = wp_count_posts( 'msr_media' );
        $published = $total->publish ?? 0;
        $pending   = $total->pending ?? 0;

        // 承認待ち一覧
        $pending_posts = get_posts([
            'post_type'   => 'msr_media',
            'post_status' => 'pending',
            'numberposts' => 20,
        ]);

        // 公開済み一覧
        $published_posts = get_posts([
            'post_type'      => 'msr_media',
            'post_status'    => 'publish',
            'numberposts'    => 20,
            'meta_key'       => '_msr_likes',
            'orderby'        => 'meta_value_num',
            'order'          => 'DESC',
        ]);
        ?>
        <div class="wrap msr-admin-wrap">
            <h1>📦 メディア投稿 管理画面</h1>

            <?php if ( isset($_GET['approved']) ) : ?>
                <div class="notice notice-success is-dismissible"><p>✅ 投稿を承認しました。</p></div>
            <?php elseif ( isset($_GET['rejected']) ) : ?>
                <div class="notice notice-info is-dismissible"><p>🗑 投稿を削除しました。</p></div>
            <?php elseif ( isset($_GET['error']) ) : ?>
                <div class="notice notice-error is-dismissible"><p>❌ エラーが発生しました: <?= esc_html($_GET['error']) ?></p></div>
            <?php endif; ?>

            <div class="msr-admin-stats">
                <div class="msr-stat-box">
                    <div class="msr-stat-num"><?= $published ?></div>
                    <div class="msr-stat-label">公開中</div>
                </div>
                <div class="msr-stat-box orange">
                    <div class="msr-stat-num"><?= $pending ?></div>
                    <div class="msr-stat-label">承認待ち</div>
                </div>
            </div>

            <?php if ( $pending_posts ) : ?>
            <h2>⏳ 承認待ち投稿</h2>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>タイトル</th><th>投稿者</th><th>タイプ</th><th>日時</th><th>操作</th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $pending_posts as $p ) : ?>
                    <?php
                    $author = get_post_meta( $p->ID, '_msr_author_name', true ) ?: '匿名';
                    $terms  = get_the_terms( $p->ID, 'msr_type' );
                    $type   = ( $terms && ! is_wp_error($terms) ) ? $terms[0]->name : '-';
                    $approve_url = wp_nonce_url( admin_url("admin-post.php?action=msr_approve&post_id={$p->ID}"), 'msr_approve_'.$p->ID );
                    $reject_url  = wp_nonce_url( admin_url("admin-post.php?action=msr_reject&post_id={$p->ID}"),  'msr_reject_'.$p->ID );
                    ?>
                    <tr>
                        <td><strong><?= esc_html($p->post_title) ?></strong><br><small><?= esc_html( wp_trim_words($p->post_content, 15) ) ?></small></td>
                        <td><?= esc_html($author) ?></td>
                        <td><?= esc_html($type) ?></td>
                        <td><?= get_the_date('Y/m/d H:i', $p->ID) ?></td>
                        <td>
                            <a href="<?= $approve_url ?>" class="button button-primary">✅ 承認</a>
                            <a href="<?= $reject_url ?>" class="button" onclick="return confirm('この投稿を削除しますか？')">❌ 却下</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
            <?php endif; ?>

            <h2>📊 公開中（いいね順）</h2>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>タイトル</th><th>タイプ</th><th>❤️ いいね</th><th>⬇️ DL数</th><th>👁 閲覧</th><th>操作</th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $published_posts as $p ) : ?>
                    <?php
                    $likes     = get_post_meta( $p->ID, '_msr_likes', true );
                    $downloads = get_post_meta( $p->ID, '_msr_downloads', true );
                    $views     = get_post_meta( $p->ID, '_msr_views', true );
                    $terms     = get_the_terms( $p->ID, 'msr_type' );
                    $type      = ( $terms && ! is_wp_error($terms) ) ? $terms[0]->name : '-';
                    $edit_url  = get_edit_post_link( $p->ID );
                    $trash_url = get_delete_post_link( $p->ID );
                    ?>
                    <tr>
                        <td><a href="<?= $edit_url ?>"><?= esc_html($p->post_title) ?></a></td>
                        <td><?= esc_html($type) ?></td>
                        <td><?= intval($likes) ?></td>
                        <td><?= intval($downloads) ?></td>
                        <td><?= intval($views) ?></td>
                        <td>
                            <a href="<?= $edit_url ?>" class="button">編集</a>
                            <a href="<?= $trash_url ?>" class="button" onclick="return confirm('削除しますか？')">削除</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>

        <style>
        .msr-admin-stats { display:flex; gap:16px; margin: 16px 0; }
        .msr-stat-box { background:#fff; border-left:4px solid #0073aa; padding:16px 24px; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,.1); }
        .msr-stat-box.orange { border-color:#f0a500; }
        .msr-stat-num { font-size:2rem; font-weight:700; color:#0073aa; }
        .msr-stat-box.orange .msr-stat-num { color:#f0a500; }
        .msr-stat-label { color:#666; font-size:.9rem; }
        </style>
        <?php
    }

    // ======= 設定ページ =======
    public static function page_settings() {
        $auto = get_option( 'msr_auto_publish', '0' );
        ?>
        <div class="wrap">
            <h1>⚙️ Media Submit & Ranking 設定</h1>
            <?php if ( isset($_GET['saved']) ) : ?>
                <div class="notice notice-success"><p>設定を保存しました。</p></div>
            <?php endif; ?>
            <form method="post" action="<?= admin_url('admin-post.php') ?>">
                <?php wp_nonce_field('msr_save_settings'); ?>
                <input type="hidden" name="action" value="msr_save_settings_form">
                <table class="form-table">
                    <tr>
                        <th>投稿の自動公開</th>
                        <td>
                            <label><input type="checkbox" name="msr_auto_publish" value="1" <?= checked($auto,'1',false) ?>> 管理者承認なしで即時公開する</label>
                            <p class="description">チェックを外すと、投稿は承認待ちになります。</p>
                        </td>
                    </tr>
                </table>
                <p class="submit"><input type="submit" class="button-primary" value="設定を保存"></p>
            </form>

            <hr>
            <h2>ショートコード一覧</h2>
            <table class="wp-list-table widefat">
                <tr><th style="width:300px">ショートコード</th><th>説明</th></tr>
                <tr><td><code>[msr_submit_form]</code></td><td>投稿フォームを表示</td></tr>
                <tr><td><code>[msr_ranking]</code></td><td>ランキングを表示（デフォルト：いいね順・10件）</td></tr>
                <tr><td><code>[msr_ranking by="downloads" limit="5"]</code></td><td>DL数ランキング5件</td></tr>
                <tr><td><code>[msr_ranking type="mp3"]</code></td><td>MP3のみのランキング</td></tr>
                <tr><td><code>[msr_list]</code></td><td>投稿一覧をカード形式で表示</td></tr>
                <tr><td><code>[msr_list type="app" cols="2"]</code></td><td>アプリのみ2カラム表示</td></tr>
            </table>
        </div>
        <?php
    }

    // ======= 使い方 =======
    public static function page_howto() {
        ?>
        <div class="wrap">
            <h1>📖 使い方</h1>
            <ol style="font-size:15px;line-height:2">
                <li>WordPressの固定ページ or 投稿に <code>[msr_submit_form]</code> を追加すると<strong>投稿フォーム</strong>が表示されます。</li>
                <li>閲覧者がアプリURLまたはMP3ファイルを投稿します。</li>
                <li>承認待ちの場合は「投稿管理」から承認してください。</li>
                <li>ランキングページに <code>[msr_ranking]</code> を追加するとランキングが表示されます。</li>
                <li><code>[msr_list]</code> で一覧（カード形式）が表示されます。</li>
            </ol>
        </div>
        <?php
    }

    public static function save_settings() {
        if ( ! isset($_POST['action']) || $_POST['action'] !== 'msr_save_settings_form' ) return;
        check_admin_referer('msr_save_settings');
        update_option( 'msr_auto_publish', isset($_POST['msr_auto_publish']) ? '1' : '0' );
        wp_redirect( admin_url('admin.php?page=msr-settings&saved=1') );
        exit;
    }

    public static function approve_post() {
        // 管理者権限チェック
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_die( __( '権限がありません。' ) );
        }

        $post_id = intval( $_GET['post_id'] ?? 0 );
        if ( ! $post_id ) {
            wp_redirect( admin_url( 'admin.php?page=msr-admin&error=invalid_post' ) );
            exit;
        }

        check_admin_referer( 'msr_approve_' . $post_id );

        // サムネイル画像がアップロードされていれば処理
        if ( ! empty( $_FILES['thumbnail']['name'] ) ) {
            if ( ! function_exists( 'wp_handle_upload' ) ) {
                require_once ABSPATH . 'wp-admin/includes/file.php';
            }
            if ( ! function_exists( 'media_handle_upload' ) ) {
                require_once ABSPATH . 'wp-admin/includes/media.php';
                require_once ABSPATH . 'wp-admin/includes/image.php';
            }
            $attachment_id = media_handle_upload( 'thumbnail', $post_id );
            if ( ! is_wp_error( $attachment_id ) ) {
                set_post_thumbnail( $post_id, $attachment_id );
            }
        }

        $result = wp_update_post( [ 'ID' => $post_id, 'post_status' => 'publish' ], true );

        if ( is_wp_error( $result ) ) {
            wp_redirect( admin_url( 'admin.php?page=msr-admin&error=update_failed' ) );
        } else {
            wp_redirect( admin_url( 'admin.php?page=msr-admin&approved=1' ) );
        }
        exit;
    }

    public static function reject_post() {
        // 管理者権限チェック
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_die( __( '権限がありません。' ) );
        }

        $post_id = intval( $_GET['post_id'] ?? 0 );
        if ( ! $post_id ) {
            wp_redirect( admin_url( 'admin.php?page=msr-admin&error=invalid_post' ) );
            exit;
        }

        check_admin_referer( 'msr_reject_' . $post_id );
        wp_delete_post( $post_id, true );
        wp_redirect( admin_url( 'admin.php?page=msr-admin&rejected=1' ) );
        exit;
    }
}
