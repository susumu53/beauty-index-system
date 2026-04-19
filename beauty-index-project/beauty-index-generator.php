<?php
/*
Plugin Name: AI Beauty Index Portal
Description: AI解析リクエストフォーム、ランキング表示、自動連携機能を備えた美人指数ポータル。
Version: 2.1
Author: Antigravity
*/

if (!defined('ABSPATH')) exit;

class AI_Beauty_Portal {

    public function __construct() {
        // 管理画面
        add_action('admin_menu', [$this, 'add_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        
        // REST API (Pythonからのスコア受取)
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        
        // 公開側フォーム & AJAX
        add_shortcode('beauty_portal', [$this, 'render_portal']);
        add_shortcode('beauty_ranking', [$this, 'render_dynamic_ranking']);
        add_action('wp_ajax_trigger_beauty_analysis', [$this, 'handle_public_trigger']);
        add_action('wp_ajax_nopriv_trigger_beauty_analysis', [$this, 'handle_public_trigger']);
        
        // 自動挿入機能 (解析記事の冒頭にフォームを表示)
        add_filter('the_content', [$this, 'auto_inject_form']);

        // フロントエンド用JS/CSS
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
    }

    public function add_menu() {
        add_menu_page('美人指数', '美人指数', 'manage_options', 'beauty-portal-settings', [$this, 'render_settings_page'], 'dashicons-art');
        add_submenu_page('beauty-portal-settings', '基本設定', '基本設定', 'manage_options', 'beauty-portal-settings', [$this, 'render_settings_page']);
        add_submenu_page('beauty-portal-settings', 'ランキング管理', 'ランキング管理', 'manage_options', 'beauty-ranking-manager', [$this, 'render_ranking_manager_page']);
    }

    public function register_settings() {
        register_setting('beauty_portal_settings', 'beauty_gh_owner');
        register_setting('beauty_portal_settings', 'beauty_gh_repo');
        register_setting('beauty_portal_settings', 'beauty_gh_token');
        register_setting('beauty_portal_settings', 'beauty_analysis_tag_id', ['default' => '999']);
    }

    public function enqueue_assets() {
        wp_register_style('beauty-portal-css', false);
        wp_enqueue_style('beauty-portal-css');
        wp_add_inline_style('beauty-portal-css', "
            .beauty-portal-card { background: #ffffff; color: #333; padding: 30px; border-radius: 15px; border: 2px solid #ff2d55; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(255,45,85,0.1); }
            .beauty-portal-form h2 { color: #ff2d55; margin-top: 0; font-weight: bold; }
            .beauty-input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #ddd; background: #fff; color: #333; }
            .beauty-submit { background: linear-gradient(45deg, #ff2d55, #ff7171); color: white; border: none; padding: 15px 30px; border-radius: 30px; cursor: pointer; font-weight: bold; width: 100%; transition: transform 0.2s; }
            .beauty-submit:hover { transform: scale(1.02); }
            .beauty-submit:disabled { background: #555; cursor: not-allowed; }
            #beauty-result { margin-top: 15px; font-weight: bold; text-align: center; }
            .beauty-ranking-section { margin-top: 40px; border-top: 1px solid #333; padding-top: 30px; }
        ");
        wp_enqueue_script('jquery');
    }

    public function render_settings_page() {
        ?>
        <div class="wrap">
            <h1>美人指数ポータル 設定</h1>
            <form method="post" action="options.php">
                <?php settings_fields('beauty_portal_settings'); do_settings_sections('beauty-portal-settings'); ?>
                <table class="form-table">
                    <tr><th>GitHub 所有者</th><td><input type="text" name="beauty_gh_owner" value="<?php echo esc_attr(get_option('beauty_gh_owner', 'susumu53')); ?>" class="regular-text"></td></tr>
                    <tr><th>リポジトリ名</th><td><input type="text" name="beauty_gh_repo" value="<?php echo esc_attr(get_option('beauty_gh_repo', 'beauty-index-system')); ?>" class="regular-text"></td></tr>
                    <tr><th>GitHub トークン (PAT)</th><td><input type="password" name="beauty_gh_token" value="<?php echo esc_attr(get_option('beauty_gh_token')); ?>" class="regular-text"><br><small>※すでに動作している場合は空欄でも問題ありませんが、必要に応じて設定してください。</small></td></tr>
                    <tr><th>解析記事 判別タグID</th><td><input type="text" name="beauty_analysis_tag_id" value="<?php echo esc_attr(get_option('beauty_analysis_tag_id', '999')); ?>" class="small-text"><br><small>Python側で付与しているタグIDと一致させてください。</small></td></tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <div class="card">
                <h2>使い方</h2>
                <p>固定ページや投稿にショートコード <code>[beauty_portal]</code> を貼り付けると、解析リクエストフォームとランキングがセットで表示されます。</p>
                <p>また、指定年のランキングのみを表示する場合は <code>[beauty_ranking year="2026"]</code> と記述してください。</p>
            </div>
        </div>
        <?php
    }

    // --- REST API 実装 ---
    public function register_rest_routes() {
        register_rest_route('beauty-index/v1', '/update-score', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_score_update'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route('beauty-index/v1', '/delete-entry', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_delete_entry'],
            'permission_callback' => '__return_true',
        ]);
    }

    public function handle_rest_score_update($request) {
        $params = $request->get_json_params();
        $name = sanitize_text_field($params['name'] ?? '');
        $score = floatval($params['score'] ?? 0);
        $category = sanitize_text_field($params['category'] ?? '');
        $url = esc_url_raw($params['affiliate_url'] ?? '');
        $article_url = esc_url_raw($params['article_url'] ?? '');
        $image_url = esc_url_raw($params['image_url'] ?? '');
        $year = isset($params['year']) ? intval($params['year']) : intval(date('Y'));

        if (empty($name)) return new WP_Error('invalid_data', 'Name is required', ['status' => 400]);

        $ranking = get_option('beauty_index_annual_ranking', []);
        if (!isset($ranking[$year])) $ranking[$year] = [];

        // 同一人物（同カテゴリ）がいれば更新、いなければ追加
        $found = false;
        foreach ($ranking[$year] as &$entry) {
            if ($entry['name'] === $name && $entry['category'] === $category) {
                if ($score > $entry['score']) {
                    $entry['score'] = $score;
                    $entry['affiliate_url'] = $url;
                    if ($article_url) $entry['article_url'] = $article_url;
                    if ($image_url) $entry['image_url'] = $image_url;
                }
                $found = true;
                break;
            }
        }
        if (!$found) {
            $ranking[$year][] = [
                'name' => $name,
                'score' => $score,
                'category' => $category,
                'affiliate_url' => $url,
                'article_url' => $article_url,
                'image_url' => $image_url,
                'created_at' => current_time('mysql')
            ];
        }

        // スコア順にソート
        usort($ranking[$year], function($a, $b) {
            return $b['score'] <=> $a['score'];
        });

        update_option('beauty_index_annual_ranking', $ranking);
        return rest_ensure_response(['success' => true, 'message' => 'Ranking updated for ' . $year]);
    }

    public function handle_rest_delete_entry($request) {
        $params = $request->get_json_params();
        $name = sanitize_text_field($params['name']);
        $year = isset($params['year']) ? intval($params['year']) : intval(date('Y'));
        
        if (empty($name)) return new WP_Error('invalid_data', 'Name is required', ['status' => 400]);
        
        $this->delete_ranking_entry($year, $name);
        return rest_ensure_response(['success' => true, 'message' => 'Entry deleted for ' . $name]);
    }

    // --- 管理画面: ランキング管理 ---
    public function render_ranking_manager_page() {
        if (isset($_POST['delete_entry'])) {
            check_admin_referer('beauty_delete_entry');
            $this->delete_ranking_entry(intval($_POST['year']), sanitize_text_field($_POST['name']));
            echo '<div class="updated"><p>エントリを削除しました。</p></div>';
        }

        $ranking = get_option('beauty_index_annual_ranking', []);
        $years = array_keys($ranking);
        rsort($years);
        $current_view_year = isset($_GET['view_year']) ? intval($_GET['view_year']) : (isset($years[0]) ? $years[0] : date('Y'));
        ?>
        <div class="wrap">
            <h1>美人指数 ランキング管理</h1>
            <p>こちらから年度別のランキングを確認・削除できます。</p>

            <form method="get">
                <input type="hidden" name="page" value="beauty-ranking-manager">
                表示年度: 
                <select name="view_year" onchange="this.form.submit()">
                    <?php if (empty($years)): ?><option value="<?php echo date('Y'); ?>"><?php echo date('Y'); ?></option><?php endif; ?>
                    <?php foreach ($years as $y): ?>
                        <option value="<?php echo $y; ?>" <?php selected($current_view_year, $y); ?>><?php echo $y; ?>年</option>
                    <?php endforeach; ?>
                </select>
            </form>

            <table class="wp-list-table widefat fixed striped" style="margin-top: 20px;">
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>サムネイル</th>
                        <th>名前</th>
                        <th>カテゴリー</th>
                        <th>スコア</th>
                        <th>記事URL</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <?php 
                    $list = isset($ranking[$current_view_year]) ? $ranking[$current_view_year] : [];
                    if (empty($list)): ?>
                        <tr><td colspan="7">データがありません。</td></tr>
                    <?php else: 
                        foreach ($list as $index => $entry): ?>
                        <tr>
                            <td><?php echo $index + 1; ?>位</td>
                            <td><?php echo !empty($entry['image_url']) ? '<img src="'.esc_url($entry['image_url']).'" style="height:32px; width:32px; border-radius:50%; object-fit:cover;">' : '-'; ?></td>
                            <td><strong><?php echo esc_html($entry['name']); ?></strong></td>
                            <td><?php echo esc_html($entry['category']); ?></td>
                            <td><?php echo esc_html($entry['score']); ?> pt</td>
                            <td><?php echo !empty($entry['article_url']) ? '<a href="'.esc_url($entry['article_url']).'" target="_blank">記事</a>' : (!empty($entry['affiliate_url']) ? '<a href="'.esc_url($entry['affiliate_url']).'" target="_blank">商品</a>' : '-'); ?></td>
                            <td>
                                <form method="post" style="display:inline;" onsubmit="return confirm('本当に削除しますか？');">
                                    <?php wp_nonce_field('beauty_delete_entry'); ?>
                                    <input type="hidden" name="year" value="<?php echo $current_view_year; ?>">
                                    <input type="hidden" name="name" value="<?php echo esc_attr($entry['name']); ?>">
                                    <input type="submit" name="delete_entry" class="button button-link-delete" value="削除">
                                </form>
                            </td>
                        </tr>
                    <?php endforeach; endif; ?>
                </tbody>
            </table>
        </div>
        <?php
    }

    private function delete_ranking_entry($year, $name) {
        $ranking = get_option('beauty_index_annual_ranking', []);
        if (isset($ranking[$year])) {
            $ranking[$year] = array_filter($ranking[$year], function($e) use ($name) {
                return $e['name'] !== $name;
            });
            $ranking[$year] = array_values($ranking[$year]); // インデックス振り直し
            update_option('beauty_index_annual_ranking', $ranking);
        }
    }

    // --- ショートコード & 表示 ---
    public function render_portal() {
        ob_start();
        $this->render_form_html();
        echo '<div class="beauty-ranking-section">';
        // 旧ランキングではなく、最新の動的ランキングを表示する
        echo $this->render_dynamic_ranking([]);
        echo '</div>';
        return ob_get_clean();
    }

    public function render_dynamic_ranking($atts) {
        $atts = shortcode_atts(['year' => date('Y')], $atts, 'beauty_ranking');
        $year = intval($atts['year']);
        $ranking = get_option('beauty_index_annual_ranking', []);
        
        ob_start();
        echo '<div class="beauty-dynamic-ranking">';
        echo '<h2>🏆 ' . esc_html($year) . '年 美人指数ランキング</h2>';
        
        if (empty($ranking[$year])) {
            echo '<p>現在、' . esc_html($year) . '年のランキングデータは集計中です。</p>';
        } else {
            // ランキングに「アフィリエイト画像」と「記事リンク」の列を追加し、見た目も整える
            echo '<table class="wp-list-table widefat fixed striped beauty-ranking-table" style="margin-top: 20px; text-align: center; border-collapse: collapse; width: 100%;">';
            echo '<thead><tr style="background-color: #ff2d55; color: white;"><th>順位</th><th style="padding-left:15px; text-align:left;">アイドル</th><th>カテゴリー</th><th>スコア</th><th>解析記事</th></tr></thead>';
            echo '<tbody>';
            foreach ($ranking[$year] as $index => $entry) {
                $rank = $index + 1;
                $name = esc_html($entry['name'] ?? '');
                $category = esc_html($entry['category'] ?? '');
                $score = esc_html($entry['score'] ?? 0);
                $aff_url = !empty($entry['affiliate_url']) ? esc_url($entry['affiliate_url']) : '#';
                $img_url = !empty($entry['image_url']) ? esc_url($entry['image_url']) : '';
                $art_url = !empty($entry['article_url']) ? esc_url($entry['article_url']) : '';
                
                // 画像タグ（アフィリエイトリンク付き）
                $img_tag = $img_url ? "<a href='{$aff_url}' target='_blank' style='display:inline-block;'><img src='{$img_url}' alt='{$name}' style='width: 60px; height: 60px; object-fit: cover; border-radius: 50%; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 2px solid #ff2d55; transition: transform 0.2s;' onmouseover=\"this.style.transform='scale(1.1)'\" onmouseout=\"this.style.transform='scale(1)'\"></a>" : "<div style='width: 60px; height: 60px; border-radius: 50%; background: #eee; border: 2px solid #ccc; display:flex; align-items:center; justify-content:center; color:#aaa; font-size:10px;'>No Image</div>";

                echo "<tr style='vertical-align: middle;'>";
                echo "<td><span style='font-size: 1.3em; font-weight: bold; color: #ff2d55;'>{$rank}</span>位</td>";
                echo "<td style='text-align: left; padding-left: 15px;'><div style='display: flex; align-items: center; gap: 15px;'>{$img_tag} <span style='font-size: 1.1em; font-weight: bold; color: #333;'>{$name}</span></div></td>";
                echo "<td><span style='background: #f1f1f1; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; color: #666;'>{$category}</span></td>";
                echo "<td><span style='font-size: 1.25em; font-weight: bold; color: #333;'>{$score} <small style='font-size: 0.6em; color: #888;'>pt</small></span></td>";
                
                // 記事リンクボタン
                if ($art_url) {
                    echo "<td><a href='{$art_url}' target='_blank' style='display:inline-block; width: 130px; padding: 10px 0; background: linear-gradient(45deg, #ff2d55, #ff7171); color: white; border-radius: 25px; text-decoration: none; font-size: 0.9em; font-weight: bold; box-shadow: 0 4px 10px rgba(255,45,85,0.3); transition: transform 0.2s;' onmouseover=\"this.style.transform='scale(1.05)'\" onmouseout=\"this.style.transform='scale(1)'\">詳細を読む  ▶</a></td>";
                } else {
                    echo "<td><span style='display:inline-block; width: 130px; padding: 10px 0; background: #e0e0e0; color: #888; border-radius: 25px; font-size: 0.9em; font-weight: bold; border: 1px solid #ccc;'>準備中</span></td>";
                }
                echo '</tr>';
            }
            echo '</tbody></table>';
        }
        echo '</div>';
        return ob_get_clean();
    }

    private function render_form_html() {
        $nonce = wp_create_nonce('beauty_trigger_nonce');
        ?>
        <div class="beauty-portal-card beauty-portal-form">
            <h2>✨ AI美人指数 解析リクエスト</h2>
            <p>客観的な進化心理学に基づき、AIがあなたの指定した人物を徹底分析します。</p>
            <form id="beauty-analysis-request-form">
                <input type="text" id="subject_name" class="beauty-input" placeholder="解析したい人物の名前 (例: 河北彩伽)" required>
                <select id="category" class="beauty-input">
                    <option value="3D">実写 (3D)</option>
                    <option value="2D">キャラクター (2D)</option>
                </select>
                <button type="submit" id="beauty-submit-btn" class="beauty-submit">解析を開始する</button>
                <div id="beauty-result"></div>
            </form>
        </div>
        <script>
        jQuery(document).ready(function($) {
            $('#beauty-analysis-request-form').on('submit', function(e) {
                e.preventDefault();
                const btn = $('#beauty-submit-btn');
                const result = $('#beauty-result');
                
                btn.prop('disabled', true).text('リクエスト送信中...');
                result.text('').css('color', '#333');

                $.ajax({
                    url: '<?php echo admin_url('admin-ajax.php'); ?>',
                    type: 'POST',
                    data: {
                        action: 'trigger_beauty_analysis',
                        nonce: '<?php echo $nonce; ?>',
                        name: $('#subject_name').val(),
                        category: $('#category').val()
                    },
                    success: function(response) {
                        if (response.success) {
                            result.text(response.data.message).css('color', '#ff2d55').css('font-weight', 'bold');
                            btn.text('送信完了');
                        } else {
                            result.text(response.data.message).css('color', '#e60000');
                            btn.prop('disabled', false).text('解析を開始する');
                        }
                    },
                    error: function() {
                        result.text('サーバー通信エラーが発生しました。').css('color', '#e60000');
                        btn.prop('disabled', false).text('解析を開始する');
                    }
                });
            });
        });
        </script>
        <?php
    }

    private function render_ranking_content() {
        $ranking_post = get_page_by_path('official-beauty-ranking', OBJECT, ['post', 'page']);
        if ($ranking_post) {
            echo '<h2>🏆 美人指数 総合ランキング (旧)</h2>';
            echo apply_filters('the_content', $ranking_post->post_content);
        } else {
            echo '<p>ランキングデータは現在集計中です。</p>';
        }
    }

    public function auto_inject_form($content) {
        if (!is_single()) return $content;
        
        $tag_id = (int)get_option('beauty_analysis_tag_id', 999);
        if (has_tag($tag_id)) {
            $form = '<div style="margin-bottom: 40px; border-bottom: 2px solid #eee; padding-bottom: 20px;">' . $this->render_mini_form() . '</div>';
            return $form . $content;
        }
        return $content;
    }

    private function render_mini_form() {
        ob_start();
        ?>
        <div style="background: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #ff2d55;">
            <p style="margin: 0 0 10px 0; font-weight: bold;">この記事を読んだあなたへ：次に解析してほしいのは誰ですか？</p>
            <div id="mini-form-container">
                <?php $this->render_form_html(); ?>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }

    public function handle_public_trigger() {
        check_ajax_referer('beauty_trigger_nonce', 'nonce');

        $name = sanitize_text_field($_POST['name']);
        $category = sanitize_text_field($_POST['category']);

        if (empty($name)) {
            wp_send_json_error(['message' => '名前を入力してください。']);
        }

        // --- イタズラ対策: レートリミット (IPベース) ---
        $ip = $_SERVER['REMOTE_ADDR'];
        $limit_key = 'beauty_limit_' . md5($ip);
        $count = (int)get_transient($limit_key);

        if ($count >= 100) {
            wp_send_json_error(['message' => 'リクエスト制限を超えました。しばらく経ってからお試しください。']);
        }

        $result_msg = $this->trigger_github_action($name, $category);

        if (strpos($result_msg, '成功') !== false || strpos($result_msg, 'Accepted') !== false) {
            set_transient($limit_key, $count + 1, HOUR_IN_SECONDS);
            wp_send_json_success(['message' => 'リクエストを承りました！数分以内に解析記事が公開されます。']);
        } else {
            wp_send_json_error(['message' => 'GitHub連携エラー: ' . $result_msg]);
        }
    }

    private function trigger_github_action($name, $category) {
        $owner = get_option('beauty_gh_owner', 'susumu53');
        $repo  = get_option('beauty_gh_repo', 'beauty-index-system');
        $token = get_option('beauty_gh_token');

        if (!$owner || !$repo || !$token) return 'GitHubの設定が未完了です。';

        $url = "https://api.github.com/repos/{$owner}/{$repo}/dispatches";
        $body = wp_json_encode([
            'event_type' => 'start-analysis',
            'client_payload' => ['name' => $name, 'category' => $category, 'target_year' => date('Y')]
        ]);

        $args = [
            'body' => $body,
            'headers' => [
                'Authorization' => 'Bearer ' . $token,
                'Accept' => 'application/vnd.github.v3+json',
                'Content-Type' => 'application/json',
                'User-Agent' => 'WordPress-Beauty-Portal'
            ],
            'method' => 'POST',
            'data_format' => 'body'
        ];

        $response = wp_remote_post($url, $args);
        if (is_wp_error($response)) return $response->get_error_message();

        $code = wp_remote_retrieve_response_code($response);
        return ($code >= 200 && $code < 300) ? '成功' : 'エラー (' . $code . ')';
    }
}

new AI_Beauty_Portal();
