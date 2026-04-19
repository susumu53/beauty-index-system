<?php
/*
Plugin Name: AI Beauty Index Generator (GitHub Actions Edition)
Description: 1人の人物をAIで解析し、美人指数レポートを自動生成します（GitHub Actions経由）。
Version: 1.0
Author: Antigravity
*/

if (!defined('ABSPATH')) exit;

class AI_Beauty_Generator {
    public function __construct() {
        add_action('admin_menu', [$this, 'add_menu']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    public function add_menu() {
        add_menu_page(
            '美人指数生成',
            '美人指数生成',
            'manage_options',
            'beauty-generator',
            [$this, 'render_admin_page'],
            'dashicons-art'
        );
    }

    public function register_settings() {
        register_setting('beauty_gen_settings', 'beauty_gh_owner');
        register_setting('beauty_gen_settings', 'beauty_gh_repo');
        register_setting('beauty_gen_settings', 'beauty_gh_token');
    }

    public function render_admin_page() {
        $message = '';
        if (isset($_POST['subject_name'])) {
            $message = $this->trigger_github_action($_POST['subject_name'], $_POST['category']);
        }

        $owner = get_option('beauty_gh_owner');
        $repo = get_option('beauty_gh_repo');
        $token = get_option('beauty_gh_token');

        ?>
        <div class="wrap">
            <h1>AI 美人指数 生成パネル (GitHub)</h1>
            
            <?php if ($message): ?>
                <div class="notice notice-info is-dismissible"><p><?php echo esc_html($message); ?></p></div>
            <?php endif; ?>

            <div class="card" style="max-width: 600px; padding: 20px;">
                <h2>解析リクエスト</h2>
                <form method="post">
                    <p>
                        <label>人物名:</label><br>
                        <input type="text" name="subject_name" class="regular-text" placeholder="例: 河北彩伽" required>
                    </p>
                    <p>
                        <label>カテゴリ:</label><br>
                        <select name="category">
                            <option value="3D">3D (実写)</option>
                            <option value="2D">2D (アニメ・キャラ)</option>
                        </select>
                    </p>
                    <p>
                        <input type="submit" class="button button-primary button-large" value="解析を開始する">
                    </p>
                    <p style="font-size: 0.9em; color: #666;">※ボタンを押すとGitHub Actionsが起動し、数分後に記事が投稿されます。</p>
                </form>
            </div>

            <hr>

            <h2>GitHub 連携設定</h2>
            <form method="post" action="options.php">
                <?php settings_fields('beauty_gen_settings'); ?>
                <table class="form-table">
                    <tr>
                        <th scope="row">GitHub 所有者 (User/Org)</th>
                        <td><input type="text" name="beauty_gh_owner" value="<?php echo esc_attr($owner); ?>" class="regular-text"></td>
                    </tr>
                    <tr>
                        <th scope="row">リポジトリ名</th>
                        <td><input type="text" name="beauty_gh_repo" value="<?php echo esc_attr($repo); ?>" class="regular-text"></td>
                    </tr>
                    <tr>
                        <th scope="row">Personal Access Token (PAT)</th>
                        <td><input type="password" name="beauty_gh_token" value="<?php echo esc_attr($token); ?>" class="regular-text">
                        <br><small>※「repository_dispatch」の権限(repo)が必要です。</small></td>
                    </tr>
                </table>
                <?php submit_button('設定を保存'); ?>
            </form>
        </div>
        <?php
    }

    private function trigger_github_action($name, $category) {
        $owner = get_option('beauty_gh_owner');
        $repo  = get_option('beauty_gh_repo');
        $token = get_option('beauty_gh_token');

        if (!$owner || !$repo || !$token) return 'GitHubの設定が未完了です。';

        $url = "https://api.github.com/repos/{$owner}/{$repo}/dispatches";
        $body = json_encode([
            'event_type' => 'start-analysis',
            'client_payload' => [
                'name' => $name,
                'category' => $category
            ]
        ]);

        $args = [
            'body'        => $body,
            'headers'     => [
                'Authorization' => 'token ' . $token,
                'Accept'        => 'application/vnd.github.v3+json',
                'Content-Type'  => 'application/json',
                'User-Agent'    => 'WordPress-Beauty-Generator'
            ],
            'method'      => 'POST',
            'data_format' => 'body'
        ];

        $response = wp_remote_post($url, $args);

        if (is_wp_error($response)) {
            return 'エラー: ' . $response->get_error_message();
        }

        $code = wp_remote_retrieve_response_code($response);
        if ($code == 204) {
            return "成功！GitHub Actionsを起動しました。解析完了までしばらくお待ちください。";
        } else {
            return "失敗 (HTTP {$code}): " . wp_remote_retrieve_response_message($response);
        }
    }
}

new AI_Beauty_Generator();
