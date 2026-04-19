<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class FSC_Admin {

    public function __construct() {
        add_action( 'admin_menu',    [ $this, 'menu' ] );
        add_action( 'admin_init',    [ $this, 'settings' ] );
        add_action( 'rest_api_init', [ $this, 'routes' ] );
        add_filter( 'plugin_action_links_' . FSC_BASE, [ $this, 'links' ] );
    }

    public function menu(): void {
        add_options_page( 'FX Signal Chart', 'FX Signal Chart', 'manage_options', 'fx-signal-chart', [ $this, 'page' ] );
    }

    public function settings(): void {
        foreach ( [
            'fsc_cache_ttl'      => 'absint',
            'fsc_default_symbol' => 'sanitize_text_field',
            'fsc_default_tf'     => 'sanitize_text_field',
            'fsc_height'         => 'absint',
            'fsc_signals'        => 'absint',
            'fsc_refresh'        => 'absint',
        ] as $k => $cb ) register_setting( 'fsc_opts', $k, [ 'sanitize_callback' => $cb ] );

        add_settings_section( 's1', 'データ設定', null, 'fx-sc' );
        add_settings_section( 's2', '表示設定',   null, 'fx-sc' );
        add_settings_field( 'fsc_cache_ttl',      'キャッシュ時間（秒）',   [ $this, 'f_cache' ],   'fx-sc', 's1' );
        add_settings_field( 'fsc_default_symbol', 'デフォルト銘柄',         [ $this, 'f_sym' ],     'fx-sc', 's2' );
        add_settings_field( 'fsc_default_tf',     'デフォルト時間足',       [ $this, 'f_tf' ],      'fx-sc', 's2' );
        add_settings_field( 'fsc_height',         'チャート高さ (px)',      [ $this, 'f_height' ],  'fx-sc', 's2' );
        add_settings_field( 'fsc_signals',        'シグナルパネル',         [ $this, 'f_sig' ],     'fx-sc', 's2' );
        add_settings_field( 'fsc_refresh',        '自動更新間隔（秒）',     [ $this, 'f_refresh' ], 'fx-sc', 's2' );
    }

    public function f_cache():   void { $v=get_option('fsc_cache_ttl',120);    echo '<input type="number" name="fsc_cache_ttl" value="'.esc_attr($v).'" min="30" max="3600" step="10" style="width:80px"> 秒 <span class="description">（60〜300推奨）</span>'; }
    public function f_height():  void { $v=get_option('fsc_height',440);        echo '<input type="number" name="fsc_height" value="'.esc_attr($v).'" min="280" max="900" step="10" style="width:80px"> px'; }
    public function f_refresh(): void { $v=get_option('fsc_refresh',60);        echo '<input type="number" name="fsc_refresh" value="'.esc_attr($v).'" min="0" max="3600" step="10" style="width:80px"> 秒 <span class="description">（0=無効）</span>'; }
    public function f_sig():     void { $v=get_option('fsc_signals',1);         echo '<label><input type="checkbox" name="fsc_signals" value="1" '.checked(1,$v,false).'> シグナルパネルを表示する</label>'; }

    public function f_sym(): void {
        $v = get_option('fsc_default_symbol','USD/JPY');
        $g = [];
        foreach ( FSC_Data::instruments() as $k => $i ) $g[$i['group']][$k]=$i['label'];
        echo '<select name="fsc_default_symbol">';
        foreach ( $g as $grp => $items ) {
            echo '<optgroup label="'.esc_attr($grp).'">';
            foreach ( $items as $k => $l ) echo '<option value="'.esc_attr($k).'" '.selected($v,$k,false).'>'.esc_html($l).'</option>';
            echo '</optgroup>';
        }
        echo '</select>';
    }

    public function f_tf(): void {
        $v = get_option('fsc_default_tf','15min');
        echo '<select name="fsc_default_tf">';
        foreach ( FSC_Data::intervals() as $k => $l ) echo '<option value="'.esc_attr($k).'" '.selected($v,$k,false).'>'.esc_html($l).'</option>';
        echo '</select>';
    }

    public function page(): void {
        if ( ! current_user_can('manage_options') ) return;
        $nonce = wp_create_nonce('wp_rest');
        $base  = rest_url('fx-signal-chart/v1/');
        ?>
        <div class="wrap">
        <h1>⚡ FX Signal Chart <small style="font-size:13px;font-weight:400;color:#777">v<?php echo FSC_VER; ?> — Yahoo Finance</small></h1>

        <div style="background:#fff;border:1px solid #c3c4c7;border-radius:4px;padding:16px 20px;margin:0 0 20px;max-width:800px">
            <h3 style="margin-top:0">🔍 接続診断</h3>
            <p style="color:#555;margin-top:0">「診断実行」でサーバーから Yahoo Finance への接続状況を詳しく確認できます。<br>
            <strong>チャートが表示されない場合は必ずここで診断してください。</strong></p>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button id="btn_diag"  class="button button-primary">診断実行</button>
                <button id="btn_test"  class="button">データ取得テスト (USD/JPY)</button>
                <button id="btn_clear" class="button">キャッシュクリア</button>
            </div>
            <div id="diag_result" style="margin-top:14px"></div>
        </div>

        <form method="post" action="options.php">
            <?php settings_fields('fsc_opts'); do_settings_sections('fx-sc'); submit_button('設定を保存'); ?>
        </form>
        <hr>
        <h2>ショートコード</h2>
        <table class="widefat" style="max-width:780px"><thead><tr><th>例</th><th>説明</th></tr></thead><tbody>
        <tr><td><code>[fx_chart]</code></td><td>デフォルト設定で表示</td></tr>
        <tr><td><code>[fx_chart symbol="XAU/USD" interval="4h"]</code></td><td>ゴールド 4時間足</td></tr>
        <tr><td><code>[fx_chart symbol="WTI" interval="1day"]</code></td><td>原油(WTI) 日足</td></tr>
        <tr><td><code>[fx_chart symbol="USD/JPY" interval="15min" auto_refresh="30"]</code></td><td>30秒自動更新</td></tr>
        </tbody></table>
        </div>

        <style>
        .fsc-row{display:flex;gap:10px;padding:8px 12px;border-radius:4px;margin:0 0 6px;font-size:13px;align-items:flex-start;line-height:1.5}
        .fsc-ok{background:#eaf5ea;border:1px solid #7ec97e}
        .fsc-err{background:#fbeaea;border:1px solid #e07b7b}
        .fsc-warn{background:#fef9e7;border:1px solid #f0c36d}
        .fsc-ico{flex-shrink:0;font-size:16px;width:20px;text-align:center}
        .fsc-pre{margin:4px 0 0;background:#f6f6f6;border:1px solid #ddd;border-radius:3px;padding:6px 10px;font-size:11px;white-space:pre-wrap;word-break:break-all;max-height:100px;overflow:auto}
        </style>
        <script>
        (function(){
            const nonce = <?php echo json_encode($nonce); ?>;
            const base  = <?php echo json_encode($base); ?>;
            const out   = document.getElementById('diag_result');
            const H     = {'X-WP-Nonce':nonce};

            function load(t){ out.innerHTML='<p style="color:#555">⏳ '+t+'</p>'; }

            function renderDiag(data){
                let html='';
                for(const[k,v] of Object.entries(data)){
                    const cls=v.ok?'fsc-ok':'fsc-err';
                    const ico=v.ok?'✅':'❌';
                    html+=`<div class="fsc-row ${cls}"><span class="fsc-ico">${ico}</span><div><strong>${k}</strong><br>${v.msg}`;
                    if(v.fix) html+=`<br><em style="color:#7a5c00">💡 ${v.fix}</em>`;
                    if(v.body_preview) html+=`<pre class="fsc-pre">${v.body_preview}</pre>`;
                    html+=`</div></div>`;
                }
                out.innerHTML = html || '<p>データなし</p>';
            }

            document.getElementById('btn_diag').onclick=async function(){
                this.disabled=true; load('診断中（最大40秒かかる場合があります）...');
                try{
                    const r=await fetch(base+'diagnose',{headers:H});
                    renderDiag(await r.json());
                }catch(e){out.innerHTML='<p style="color:red">❌ '+e.message+'</p>';}
                finally{this.disabled=false;}
            };

            document.getElementById('btn_test').onclick=async function(){
                this.disabled=true; load('USD/JPY データ取得中...');
                try{
                    const r=await fetch(base+'candles?symbol=USD%2FJPY&interval=15min&limit=5',{headers:H});
                    const d=await r.json();
                    if(d.success){
                        const last=d.candles[d.candles.length-1];
                        out.innerHTML=`<div class="fsc-row fsc-ok"><span class="fsc-ico">✅</span><div>
                            <strong>取得成功</strong><br>
                            ${d.candles.length}件 | 最新: <strong>${last.close}</strong> (${last.time})<br>
                            プロバイダー: ${d.provider} | 使用エンドポイント: Yahoo Finance
                        </div></div>`;
                    } else {
                        out.innerHTML=`<div class="fsc-row fsc-err"><span class="fsc-ico">❌</span><div><strong>失敗</strong><br>${d.message}</div></div>`;
                    }
                }catch(e){out.innerHTML='<p style="color:red">❌ '+e.message+'</p>';}
                finally{this.disabled=false;}
            };

            document.getElementById('btn_clear').onclick=async function(){
                this.disabled=true; load('クリア中...');
                try{
                    const r=await fetch(base+'clear',{method:'POST',headers:H});
                    const d=await r.json();
                    out.innerHTML=d.success
                        ?`<div class="fsc-row fsc-ok"><span class="fsc-ico">✅</span><div>キャッシュをクリアしました（${d.deleted}件削除）</div></div>`
                        :`<div class="fsc-row fsc-err"><span class="fsc-ico">❌</span><div>${d.message||'失敗'}</div></div>`;
                }catch(e){out.innerHTML='<p style="color:red">❌ '+e.message+'</p>';}
                finally{this.disabled=false;}
            };
        })();
        </script>
        <?php
    }

    /* ── REST routes ───────────────────────── */
    public function routes(): void {
        $ns = 'fx-signal-chart/v1';
        register_rest_route( $ns, '/candles', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'r_candles' ],
            'permission_callback' => '__return_true',
            'args' => [
                'symbol'   => [ 'default' => get_option('fsc_default_symbol','USD/JPY'), 'sanitize_callback' => 'sanitize_text_field' ],
                'interval' => [ 'default' => get_option('fsc_default_tf','15min'),        'sanitize_callback' => 'sanitize_text_field' ],
                'limit'    => [ 'default' => 80, 'sanitize_callback' => 'absint' ],
            ],
        ] );
        register_rest_route( $ns, '/diagnose', [
            'methods'             => 'GET',
            'callback'            => fn() => new WP_REST_Response( FSC_Data::diagnose(), 200 ),
            'permission_callback' => fn() => current_user_can('manage_options'),
        ] );
        register_rest_route( $ns, '/clear', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'r_clear' ],
            'permission_callback' => fn() => current_user_can('manage_options'),
        ] );
    }

    public function r_candles( WP_REST_Request $req ): WP_REST_Response {
        $data = new FSC_Data();
        $result = $data->get_candles( $req['symbol'], $req['interval'], (int)$req['limit'] );
        if ( is_wp_error( $result ) ) return new WP_REST_Response( [ 'success' => false, 'message' => $result->get_error_message() ], 400 );
        return new WP_REST_Response( $result, 200 );
    }

    public function r_clear(): WP_REST_Response {
        global $wpdb;
        $n = (int)$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_fsc_%' OR option_name LIKE '_transient_timeout_fsc_%'");
        return new WP_REST_Response( [ 'success' => true, 'deleted' => $n ], 200 );
    }

    public function links( array $links ): array {
        array_unshift( $links, '<a href="'.esc_url(admin_url('options-general.php?page=fx-signal-chart')).'">設定</a>' );
        return $links;
    }
}
