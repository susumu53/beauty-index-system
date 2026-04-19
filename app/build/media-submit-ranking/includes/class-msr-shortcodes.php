<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class MSR_Shortcodes {

    public static function init() {
        add_shortcode( 'msr_submit_form', [ __CLASS__, 'submit_form' ] );
        add_shortcode( 'msr_ranking',     [ __CLASS__, 'ranking' ] );
        add_shortcode( 'msr_list',        [ __CLASS__, 'list_items' ] );
    }

    // ======= 投稿フォーム =======
    public static function submit_form( $atts ) {
        ob_start();
        ?>
        <div class="msr-submit-wrap">
            <h2 class="msr-form-title">📤 作品を投稿する</h2>
            <div id="msr-submit-message" class="msr-alert" style="display:none;"></div>
            <form id="msr-submit-form" enctype="multipart/form-data">
                <div class="msr-field">
                    <label>メディアタイプ <span class="msr-required">*</span></label>
                    <div class="msr-type-toggle">
                        <label class="msr-toggle-btn active" data-type="app">
                            <input type="radio" name="media_type" value="app" checked> 📱 アプリ
                        </label>
                        <label class="msr-toggle-btn" data-type="mp3">
                            <input type="radio" name="media_type" value="mp3"> 🎵 MP3
                        </label>
                    </div>
                </div>

                <div class="msr-field">
                    <label>タイトル <span class="msr-required">*</span></label>
                    <input type="text" name="title" placeholder="作品名を入力" maxlength="100" required>
                </div>

                <div class="msr-field">
                    <label>説明</label>
                    <textarea name="description" rows="4" placeholder="作品の説明を入力（任意）" maxlength="1000"></textarea>
                </div>

                <div class="msr-field">
                    <label>投稿者名</label>
                    <input type="text" name="author_name" placeholder="ニックネーム（省略可）" maxlength="50">
                </div>

                <!-- アプリ用 -->
                <div class="msr-field msr-app-field">
                    <label>アプリURL / ストアURL</label>
                    <input type="url" name="link_url" placeholder="https://example.com/your-app">
                </div>

                <div class="msr-field">
                    <label>アフィリエイトリンク（任意）</label>
                    <input type="url" name="affiliate_url" placeholder="https://example.com/affiliate-link">
                </div>

                <!-- MP3用 -->
                <div class="msr-field msr-mp3-field" style="display:none;">
                    <label>MP3ファイル <span class="msr-required">*</span></label>
                    <div class="msr-file-drop" id="msr-file-drop">
                        <span>🎵 ここにMP3をドロップ または クリックして選択</span>
                        <input type="file" name="mp3_file" id="msr-mp3-file" accept=".mp3,audio/mpeg" style="display:none;">
                    </div>
                    <div id="msr-file-name" class="msr-file-name"></div>
                    <small>最大ファイルサイズ: 50MB</small>
                </div>

                <div class="msr-field">
                    <label>サムネイル画像（任意）</label>
                    <input type="file" name="thumbnail" accept="image/*">
                </div>

                <button type="submit" class="msr-btn msr-btn-primary" id="msr-submit-btn">
                    投稿する
                </button>
            </form>
        </div>
        <?php
        return ob_get_clean();
    }

    // ======= ランキング =======
    public static function ranking( $atts ) {
        $atts = shortcode_atts([
            'type'  => 'all',   // all / app / mp3
            'by'    => 'likes', // likes / downloads / views
            'limit' => 10,
        ], $atts );

        $meta_key = '_msr_' . $atts['by'];
        $args = [
            'post_type'      => 'msr_media',
            'post_status'    => 'publish',
            'posts_per_page' => intval( $atts['limit'] ),
            'meta_key'       => $meta_key,
            'orderby'        => 'meta_value_num',
            'order'          => 'DESC',
        ];

        if ( $atts['type'] !== 'all' ) {
            $args['tax_query'] = [[
                'taxonomy' => 'msr_type',
                'field'    => 'slug',
                'terms'    => $atts['type'],
            ]];
        }

        $query = new WP_Query( $args );
        $by_labels = ['likes' => 'いいね', 'downloads' => 'DL数', 'views' => '閲覧数'];
        $by_label  = $by_labels[ $atts['by'] ] ?? 'いいね';

        ob_start();
        ?>
        <div class="msr-ranking-wrap">
            <div class="msr-ranking-header">
                <h2>🏆 ランキング <span class="msr-ranking-by">（<?= esc_html($by_label) ?>順）</span></h2>
                <div class="msr-ranking-tabs">
                    <button class="msr-tab active" data-by="likes">❤️ いいね</button>
                    <button class="msr-tab" data-by="downloads">⬇️ DL数</button>
                    <button class="msr-tab" data-by="views">👁 閲覧数</button>
                </div>
            </div>
            <div class="msr-ranking-list" id="msr-ranking-list">
                <?php if ( $query->have_posts() ) : $rank = 1; ?>
                    <?php while ( $query->have_posts() ) : $query->the_post(); ?>
                        <?php self::render_ranking_item( get_the_ID(), $rank++, $atts['by'] ); ?>
                    <?php endwhile; ?>
                <?php else : ?>
                    <p class="msr-empty">まだ投稿がありません。</p>
                <?php endif; ?>
            </div>
        </div>
        <?php
        wp_reset_postdata();
        return ob_get_clean();
    }

    // ランキングアイテム描画
    private static function render_ranking_item( $post_id, $rank, $by = 'likes' ) {
        $likes     = intval( get_post_meta( $post_id, '_msr_likes', true ) );
        $downloads = intval( get_post_meta( $post_id, '_msr_downloads', true ) );
        $views     = intval( get_post_meta( $post_id, '_msr_views', true ) );
        $author        = get_post_meta( $post_id, '_msr_author_name', true ) ?: '匿名';
        $link_url      = get_post_meta( $post_id, '_msr_link_url', true );
        $mp3_url       = get_post_meta( $post_id, '_msr_mp3_url', true );
        $affiliate_url = get_post_meta( $post_id, '_msr_affiliate_url', true );

        $terms = get_the_terms( $post_id, 'msr_type' );
        $type  = ( $terms && ! is_wp_error($terms) ) ? $terms[0]->slug : 'app';
        $icon  = $type === 'mp3' ? '🎵' : '📱';

        $medal = ['🥇','🥈','🥉'][$rank - 1] ?? "#{$rank}";
        $score = $by === 'likes' ? $likes : ( $by === 'downloads' ? $downloads : $views );
        $score_label = $by === 'likes' ? "❤️ {$likes}" : ( $by === 'downloads' ? "⬇️ {$downloads}" : "👁 {$views}" );
        ?>
        <div class="msr-rank-item" data-id="<?= $post_id ?>">
            <div class="msr-rank-medal"><?= $medal ?></div>
            <div class="msr-rank-thumb">
                <?php if ( has_post_thumbnail($post_id) ) : ?>
                    <?= get_the_post_thumbnail($post_id, [60,60]) ?>
                <?php else : ?>
                    <div class="msr-thumb-placeholder"><?= $icon ?></div>
                <?php endif; ?>
            </div>
            <div class="msr-rank-info">
                <div class="msr-rank-title"><?= esc_html(get_the_title($post_id)) ?></div>
                <div class="msr-rank-meta">
                    <span class="msr-type-badge msr-type-<?= esc_attr($type) ?>"><?= $icon ?> <?= esc_html($terms[0]->name ?? '') ?></span>
                    <span class="msr-author">by <?= esc_html($author) ?></span>
                </div>
            </div>
            <div class="msr-rank-stats">
                <div class="msr-score-main"><?= $score_label ?></div>
                <div class="msr-score-sub">
                    <?php if ($by !== 'likes') : ?><span>❤️ <?= $likes ?></span><?php endif; ?>
                    <?php if ($by !== 'downloads') : ?><span>⬇️ <?= $downloads ?></span><?php endif; ?>
                </div>
            </div>
            <div class="msr-rank-actions">
                <?php if ( $affiliate_url ) : ?>
                    <a href="<?= esc_url($affiliate_url) ?>" class="msr-btn msr-btn-link msr-btn-affiliate" target="_blank" rel="noopener">💰 応援リンク</a>
                <?php endif; ?>
                <?php if ( $mp3_url ) : ?>
                    <button class="msr-btn msr-btn-dl msr-download-btn" data-id="<?= $post_id ?>" data-url="<?= esc_url($mp3_url) ?>">▶ 再生</button>
                <?php elseif ( $link_url ) : ?>
                    <a href="<?= esc_url($link_url) ?>" class="msr-btn msr-btn-link" target="_blank" rel="noopener">🔗 開く</a>
                <?php endif; ?>
                <button class="msr-like-btn <?= in_array($_SERVER['REMOTE_ADDR'], get_post_meta($post_id,'_msr_liked_ips',true) ?: []) ? 'liked' : '' ?>" data-id="<?= $post_id ?>">
                    ❤️ <span class="msr-like-count"><?= $likes ?></span>
                </button>
            </div>
        </div>
        <?php
    }

    // ======= 一覧表示 =======
    public static function list_items( $atts ) {
        $atts = shortcode_atts([
            'type'   => 'all',
            'limit'  => 12,
            'cols'   => 3,
        ], $atts );

        $args = [
            'post_type'      => 'msr_media',
            'post_status'    => 'publish',
            'posts_per_page' => intval( $atts['limit'] ),
            'orderby'        => 'date',
            'order'          => 'DESC',
        ];

        if ( $atts['type'] !== 'all' ) {
            $args['tax_query'] = [[
                'taxonomy' => 'msr_type',
                'field'    => 'slug',
                'terms'    => $atts['type'],
            ]];
        }

        $query = new WP_Query( $args );

        ob_start();
        ?>
        <div class="msr-list-wrap">
            <div class="msr-filter-bar">
                <button class="msr-filter active" data-type="all">すべて</button>
                <button class="msr-filter" data-type="app">📱 アプリ</button>
                <button class="msr-filter" data-type="mp3">🎵 MP3</button>
            </div>
            <div class="msr-grid msr-cols-<?= intval($atts['cols']) ?>">
            <?php if ( $query->have_posts() ) : ?>
                <?php while ( $query->have_posts() ) : $query->the_post(); ?>
                    <?php self::render_card( get_the_ID() ); ?>
                <?php endwhile; ?>
            <?php else : ?>
                <p class="msr-empty">まだ投稿がありません。</p>
            <?php endif; ?>
            </div>
        </div>
        <?php
        wp_reset_postdata();
        return ob_get_clean();
    }

    // カード描画
    private static function render_card( $post_id ) {
        $likes     = intval( get_post_meta( $post_id, '_msr_likes', true ) );
        $downloads = intval( get_post_meta( $post_id, '_msr_downloads', true ) );
        $author        = get_post_meta( $post_id, '_msr_author_name', true ) ?: '匿名';
        $link_url      = get_post_meta( $post_id, '_msr_link_url', true );
        $mp3_url       = get_post_meta( $post_id, '_msr_mp3_url', true );
        $affiliate_url = get_post_meta( $post_id, '_msr_affiliate_url', true );

        $terms = get_the_terms( $post_id, 'msr_type' );
        $type  = ( $terms && ! is_wp_error($terms) ) ? $terms[0]->slug : 'app';
        $icon  = $type === 'mp3' ? '🎵' : '📱';

        // ビュー数を増やす（ページ読み込み時ではなくカード表示時にカウント）
        ?>
        <div class="msr-card" data-type="<?= esc_attr($type) ?>" data-id="<?= $post_id ?>">
            <div class="msr-card-thumb">
                <?php if ( has_post_thumbnail($post_id) ) : ?>
                    <?= get_the_post_thumbnail($post_id, [300,200]) ?>
                <?php else : ?>
                    <div class="msr-thumb-placeholder large"><?= $icon ?></div>
                <?php endif; ?>
                <span class="msr-type-badge msr-type-<?= esc_attr($type) ?>"><?= $icon ?> <?= esc_html($terms[0]->name ?? '') ?></span>
            </div>
            <div class="msr-card-body">
                <h3 class="msr-card-title"><?= esc_html(get_the_title($post_id)) ?></h3>
                <p class="msr-card-desc"><?= esc_html( wp_trim_words(get_the_content(), 20, '...') ) ?></p>
                <div class="msr-card-author">by <?= esc_html($author) ?></div>
            </div>
            <div class="msr-card-footer">
                <div class="msr-card-stats">
                    <span>❤️ <?= $likes ?></span>
                    <span>⬇️ <?= $downloads ?></span>
                </div>
                <div class="msr-card-actions">
                    <?php if ( $affiliate_url ) : ?>
                        <a href="<?= esc_url($affiliate_url) ?>" class="msr-btn msr-btn-sm msr-btn-link msr-btn-affiliate" target="_blank" rel="noopener">💰 応援リンク</a>
                    <?php endif; ?>
                    <?php if ( $mp3_url ) : ?>
                        <button class="msr-btn msr-btn-sm msr-btn-dl msr-download-btn" data-id="<?= $post_id ?>" data-url="<?= esc_url($mp3_url) ?>">▶ 再生</button>
                    <?php elseif ( $link_url ) : ?>
                        <a href="<?= esc_url($link_url) ?>" class="msr-btn msr-btn-sm msr-btn-link" target="_blank" rel="noopener">🔗 開く</a>
                    <?php endif; ?>
                    <button class="msr-like-btn <?= in_array($_SERVER['REMOTE_ADDR'], get_post_meta($post_id,'_msr_liked_ips',true) ?: []) ? 'liked' : '' ?>" data-id="<?= $post_id ?>">
                        ❤️ <span class="msr-like-count"><?= $likes ?></span>
                    </button>
                </div>
            </div>
        </div>
        <?php
    }
}
