<?php
/*
Plugin Name: AI Beauty Index Portal
Description: AI解析リクエストフォーム、ランキング表示、自動連携機能を備えた美人指数ポータル。
Version: 2.0
Author: Antigravity
*/

if (!defined('ABSPATH')) exit;

class AI_Beauty_Portal {
    public function __construct() {
        // 管理画面
        add_action('admin_menu', [$this, 'add_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        
        // 公開側フォーム & AJAX
        add_shortcode('beauty_portal', [$this, 'render_portal']);
        add_action('wp_ajax_trigger_beauty_analysis', [$this, 'handle_public_trigger']);
        add_action('wp_ajax_nopriv_trigger_beauty_analysis', [$this, 'handle_public_trigger']);
        
        // 自動挿入機能 (解析記事の冒頭にフォームを表示)
        add_filter('the_content', [$this, 'auto_inject_form']);

        // フロントエンド用JS/CSS
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
    }

    public function add_menu() {
        add_menu_page('美人指数ポータル', '美人指数ポータル', 'manage_options', 'beauty-portal-settings', [$this, 'render_settings_page'], 'dashicons-art');
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
            </div>
        </div>
        <?php
    }

    public function render_portal() {
        ob_start();
        $this->render_form_html();
        echo '<div class="beauty-ranking-section">';
        $this->render_ranking_content();
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
        // ランキング記事のコンテンツを取得
        $ranking_post = get_page_by_path('official-beauty-ranking', OBJECT, ['post', 'page']);
        if ($ranking_post) {
            echo '<h2>🏆 美人指数 総合ランキング</h2>';
            echo apply_filters('the_content', $ranking_post->post_content);
        } else {
            echo '<p>ランキングデータは現在集計中です。</p>';
        }
    }

    public function auto_inject_form($content) {
        if (!is_single()) return $content;
        
        // タグで判定
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

        if ($count >= 3) {
            wp_send_json_error(['message' => 'リクエスト制限を超えました。1時間後にもう一度お試しください。']);
        }

        // GitHub Actions 起動
        $result_msg = $this->trigger_github_action($name, $category);

        if (strpos($result_msg, '成功') !== false) {
            // カウントアップ (有効期限1時間)
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
        $body = json_encode([
            'event_type' => 'start-analysis',
            'client_payload' => ['name' => $name, 'category' => $category]
        ]);

        $args = [
            'body' => $body,
            'headers' => [
                'Authorization' => 'token ' . $token,
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
        return ($code == 204) ? '成功' : 'エラー (' . $code . ')';
    }
}

new AI_Beauty_Portal();
