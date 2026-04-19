<?php
/**
 * Plugin Name: FX Desk
 * Plugin URI:  https://example.com/fx-desk
 * Description: FXダッシュボード（スケジュール・シグナル・日誌・アラート）ショートコード [fx_desk] で設置。
 * Version:     4.0.0
 * Author:      FX Desk
 * License:     GPL2
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'FXDESK_VERSION', '4.0.0' );
define( 'FXDESK_DIR', plugin_dir_path( __FILE__ ) );
define( 'FXDESK_URL', plugin_dir_url( __FILE__ ) );

/* ============================================================
   1. WordPress サーバーサイドプロキシ（CORS完全回避）
   ============================================================ */
add_action( 'wp_ajax_fxdesk_proxy',        'fxdesk_proxy' );
add_action( 'wp_ajax_nopriv_fxdesk_proxy', 'fxdesk_proxy' );

function fxdesk_proxy() {
    if ( ! check_ajax_referer( 'fxdesk_nonce', 'nonce', false ) ) {
        wp_send_json_error( array( 'message' => 'Security check failed' ), 403 );
    }

    $raw = isset( $_GET['url'] ) ? urldecode( wp_unslash( $_GET['url'] ) ) : '';
    $url = esc_url_raw( $raw );

    // 許可するドメイン（Yahoo Finance, Google News, ForexFactory）
    if ( ! preg_match( '#^https://((query1|query2)\.finance\.yahoo\.com|news\.google\.com|nfs\.faireconomy\.media)/#', $url ) ) {
        wp_send_json_error( array( 'message' => 'URL not allowed' ), 403 );
    }

    $args = array(
        'timeout'   => 20,
        'sslverify' => false,
        'headers'   => array(
            'User-Agent' => 'Mozilla/5.0 (compatible; FXDesk/4.0)',
        ),
    );
    // News.google.comとForexFactoryの場合はAcceptを変える
    if ( strpos($url, 'news.google.com') !== false ) {
        $args['headers']['Accept'] = 'application/rss+xml, application/xml, text/xml';
    } else {
        $args['headers']['Accept'] = 'application/json';
    }

    $resp = wp_remote_get( $url, $args );

    if ( is_wp_error( $resp ) ) {
        wp_send_json_error( array( 'message' => $resp->get_error_message() ), 500 );
    }

    $code = wp_remote_retrieve_response_code( $resp );
    $body = wp_remote_retrieve_body( $resp );
    $type = wp_remote_retrieve_header( $resp, 'content-type' );

    status_header( $code );
    if ( $type ) {
        header( 'Content-Type: ' . $type );
    } else {
        header( 'Content-Type: application/json; charset=utf-8' );
    }
    header( 'Cache-Control: no-cache' );
    echo $body; // phpcs:ignore WordPress.Security.EscapeOutput
    wp_die();
}

/* ============================================================
   2. アセット登録（外部ファイルとして正規に読み込む）
   ============================================================ */
add_action( 'wp_enqueue_scripts', 'fxdesk_enqueue' );

function fxdesk_enqueue() {
    // フォント
    wp_enqueue_style(
        'fxdesk-fonts',
        'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+JP:wght@400;700&display=swap',
        array(),
        null
    );

    // CSS
    wp_enqueue_style(
        'fxdesk-style',
        FXDESK_URL . 'assets/fx-desk.css',
        array( 'fxdesk-fonts' ),
        FXDESK_VERSION
    );

    // JS（defer で読み込み、jQueryに依存しない）
    wp_enqueue_script(
        'fxdesk-script',
        FXDESK_URL . 'assets/fx-desk.js',
        array(),
        FXDESK_VERSION,
        true  // フッターに出力
    );

    // PHP → JS へ安全にデータを渡す（wp_localize_script）
    wp_localize_script( 'fxdesk-script', 'FXDESK', array(
        'ajaxUrl' => admin_url( 'admin-ajax.php' ),
        'nonce'   => wp_create_nonce( 'fxdesk_nonce' ),
    ) );
}

/* ============================================================
   3. ショートコード [fx_desk]
   ============================================================ */
add_shortcode( 'fx_desk', 'fxdesk_shortcode' );

function fxdesk_shortcode() {
    ob_start();
    ?>
<div id="fxdesk">

  <header class="fx-header">
    <div style="display:flex;align-items:center">
      <span class="fx-logo">FX DESK</span>
      <span class="fx-session-badge" id="fx-badge"></span>
    </div>
    <div>
      <span class="fx-clock-label">JST</span>
      <span class="fx-clock" id="fx-clock">--:--:--</span>
    </div>
  </header>

  <nav class="fx-nav">
    <button class="active" onclick="fxTab('schedule',this)">📅 スケジュール</button>
    <button onclick="fxTab('signals',this)">📈 シグナル</button>
    <button onclick="fxTab('journal',this)">📝 日誌</button>
    <button onclick="fxTab('alerts',this)">⏰ アラート</button>
    <button onclick="fxTab('news',this)">📻 ニュース</button>
  </nav>

  <div class="fx-main">

    <!-- SCHEDULE -->
    <div id="fx-tab-schedule" class="fx-tab active">
      <div class="fx-card" id="fx-sess-card" style="border-left:3px solid var(--green)">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
          <div>
            <span class="fx-lbl">現在のセッション</span>
            <div id="fx-sess-name" style="font-size:22px;font-weight:700"></div>
          </div>
          <div style="text-align:right">
            <span class="fx-lbl">次のイベント</span>
            <div id="fx-next-name" style="font-weight:700;font-size:14px"></div>
            <div id="fx-next-time" style="font-size:11px;color:var(--dim);margin-top:2px"></div>
          </div>
        </div>
      </div>
      <div class="fx-card">
        <span class="fx-lbl" style="margin-bottom:12px">24時間スケジュール（JST・夏時間基準）</span>
        <div id="fx-sched-list"></div>
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:flex;gap:14px;flex-wrap:wrap;font-size:10px">
          <span style="color:var(--muted)">● 低</span>
          <span style="color:var(--yellow)">● 中</span>
          <span style="color:var(--orange)">● 高</span>
          <span style="color:var(--red)">● 最重要</span>
        </div>
      </div>
    </div>

    <!-- SIGNALS -->
    <div id="fx-tab-signals" class="fx-tab">
      <div class="sx-hd">
        <div class="sx-lhd">
          <select id="sx-ps" class="sx-pair-sel" onchange="sxRender()">
            <option value="USDJPY=X">USD/JPY</option>
            <option value="EURUSD=X">EUR/USD</option>
            <option value="GBPJPY=X">GBP/JPY</option>
            <option value="AUDUSD=X">AUD/USD</option>
            <option value="EURJPY=X">EUR/JPY</option>
            <option value="GBPUSD=X">GBP/USD</option>
            <option value="CL=F">WTI原油</option>
            <option value="GC=F">金（ゴールド）</option>
          </select>
          <span class="sx-badge">Yahoo Finance</span>
        </div>
        <div class="sx-pinfo">
          <div class="sx-pv" id="sx-pv">—</div>
          <div class="sx-pc" id="sx-pc">—</div>
        </div>
      </div>
      <div class="sx-tf-row">
        <button class="sx-tfb" data-tf="1m"  data-range="5d"  onclick="sxSetTf(this)">1分</button>
        <button class="sx-tfb" data-tf="5m"  data-range="60d" onclick="sxSetTf(this)">5分</button>
        <button class="sx-tfb" data-tf="15m" data-range="60d" onclick="sxSetTf(this)">15分</button>
        <button class="sx-tfb" data-tf="60m" data-range="730d" onclick="sxSetTf(this)">1時間</button>
        <button class="sx-tfb act" data-tf="1d" data-range="2y" onclick="sxSetTf(this)">日足</button>
        <div class="sx-spacer"></div>
        <button class="sx-ref-btn" onclick="sxRender()"><span id="sx-spin">↻</span> 更新</button>
      </div>
      <div class="sx-chart-card">
        <div class="sx-err" id="sx-err" style="display:none"></div>
        <div id="sx-chart-inner">
          <div class="sx-leg">
            <span><span class="sx-ll" style="background:#58a6ff"></span>価格</span>
            <span><span class="sx-ll" style="background:#f0883e"></span>MA20</span>
            <span><span class="sx-ll" style="background:#bc8cff;border-top:1.5px dashed #bc8cff;height:0"></span>MA50</span>
            <span><span class="sx-la"></span>BB ±2σ</span>
          </div>
          <div class="sx-cw"><canvas id="sx-cPrice"></canvas></div>
          <div class="sx-ch-lbl">RSI (14) ─── 70 ─── 30</div>
          <div class="sx-cw2"><canvas id="sx-cRsi"></canvas></div>
        </div>
      </div>
      <div class="sx-sec">総合シグナル</div>
      <div class="sx-ov" id="sx-ov" style="display:none">
        <div class="sx-ov-sig" id="sx-os">—</div>
        <div class="sx-track">
          <div class="sx-tbuy"  id="sx-sb"  style="flex:0"></div>
          <div class="sx-tneu"  id="sx-sne" style="flex:1"></div>
          <div class="sx-tsell" id="sx-ss"  style="flex:0"></div>
        </div>
        <div class="sx-ct" id="sx-sct">—</div>
      </div>
      <div class="sx-sec">各指標シグナル <span style="font-size:9px;text-transform:none;font-weight:400;color:var(--muted)">カードをクリックで詳細解説</span></div>
      <div class="sx-grid" id="sx-sg"></div>
      <div class="sx-doc-panel" id="sx-doc-panel">
        <div class="sx-doc-panel-head">
          <div class="sx-doc-title" id="sx-doc-title"></div>
          <button class="sx-doc-close" onclick="sxCloseDoc()">✕ 閉じる</button>
        </div>
        <div id="sx-doc-body"></div>
      </div>
      <div class="sx-disc" id="sx-disc" style="display:none">
        ※ Yahoo Finance データをWordPressサーバー経由で取得。投資判断の保証はしません。
      </div>
    </div>

    <!-- JOURNAL -->
    <div id="fx-tab-journal" class="fx-tab">
      <div class="fx-card fx-summary" id="fx-j-summary" style="display:none"></div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span class="fx-lbl" style="margin-bottom:0">トレード日誌</span>
        <button class="fx-btn" style="padding:6px 14px;font-size:12px" onclick="fxToggleForm()">+ 新規記録</button>
      </div>
      <div class="fx-card" id="fx-trade-form" style="display:none;border-color:var(--border2)">
        <div class="fx-grid2">
          <div><span class="fx-lbl">通貨ペア</span>
            <select id="fj-pair">
              <option>USD/JPY</option><option>EUR/JPY</option><option>GBP/JPY</option>
              <option>AUD/JPY</option><option>EUR/USD</option><option>GBP/USD</option>
            </select>
          </div>
          <div><span class="fx-lbl">方向</span>
            <div style="display:flex;gap:6px">
              <button id="fj-buy"  onclick="fxDir('buy')"  style="flex:1;padding:7px;border:none;border-radius:6px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit;background:var(--green);color:#000">▲ BUY</button>
              <button id="fj-sell" onclick="fxDir('sell')" style="flex:1;padding:7px;border:none;border-radius:6px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit;background:var(--card2);color:var(--muted)">▼ SELL</button>
            </div>
          </div>
          <div><span class="fx-lbl">エントリー価格</span><input type="number" id="fj-entry" step="0.001" placeholder="149.500"></div>
          <div><span class="fx-lbl">エグジット価格</span><input type="number" id="fj-exit"  step="0.001" placeholder="149.800"></div>
          <div><span class="fx-lbl">ロット数</span><input type="number" id="fj-lots" step="0.01" value="0.1"></div>
          <div><span class="fx-lbl">日付</span><input type="date" id="fj-date"></div>
        </div>
        <div style="margin-top:8px"><span class="fx-lbl">メモ（任意）</span><input type="text" id="fj-notes" placeholder="エントリー根拠・反省など"></div>
        <button class="fx-btn" style="margin-top:12px" onclick="fxAddTrade()">記録する</button>
      </div>
      <div id="fx-trade-list"></div>
    </div>

    <!-- ALERTS -->
    <div id="fx-tab-alerts" class="fx-tab">
      <div class="fx-card" style="background:rgba(240,136,62,.06);border-color:var(--orange);margin-bottom:12px">
        <div style="color:var(--orange);font-weight:700;margin-bottom:6px">⏰ 重要時間帯アラート（5分前に音が鳴ります）</div>
        <div style="color:var(--muted);font-size:11px;line-height:1.8">
          🔔をONにすると<strong style="color:var(--text)">5分前にビープ音</strong>が鳴ります。<br>
          重要度 最重要→4回、高→3回、中→2回、低→1回。<br>
          ⚠️ タブをアクティブにしておく必要があります。
        </div>
        <button class="fx-btn-sm" onclick="fxTestSound()" style="margin-top:10px;color:var(--orange);border-color:var(--orange)">🔊 テスト音を鳴らす</button>
      </div>
      <span class="fx-lbl">次の24時間のイベント（直近順）</span>
      <div id="fx-alert-list" style="margin-top:8px"></div>
    </div>

    <!-- NEWS -->
    <div id="fx-tab-news" class="fx-tab">
      <div class="fx-card" style="border-left:3px solid var(--green);margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <div style="font-weight:700;font-size:16px"><span id="fx-news-status">🔇 読み上げOFF</span></div>
          <div style="font-size:11px;color:var(--muted);margin-top:4px">
            自動取得＆音声読み上げ（バックグラウンド動作）。<br>
            ※ONにするには一度画面をクリックしてください。
          </div>
        </div>
        <div style="display:flex;gap:8px">
          <button id="fx-news-btn" class="fx-btn" onclick="fxToggleNews()">自動読み上げをONにする</button>
        </div>
      </div>
      
      <div class="fx-grid2" style="margin-bottom:12px;gap:8px">
        <div class="fx-card" style="padding:10px">
          <span class="fx-lbl" style="margin-bottom:4px">Googleニュース 検索キーワード</span>
          <input type="text" id="fx-news-query" value="為替 OR FRB OR 日銀 OR 円安" style="width:100%;font-size:11px">
          <div style="font-size:10px;color:var(--muted);margin-top:4px">複数ワードは「OR」やスペースで区切る</div>
        </div>
        <div class="fx-card" style="padding:10px;display:flex;flex-direction:column;justify-content:center">
          <button class="fx-btn-sm" onclick="fxReadTodaySchedule()" style="margin-bottom:6px">📢 今日の予定を読み上げ (手動)</button>
          <button class="fx-btn-sm" style="color:var(--dim);border-color:var(--border)" onclick="fxClearNewsLog()">履歴をリセットして全件再読み上げ</button>
        </div>
      </div>

      <span class="fx-lbl">最新のニュースと指標結果ログ</span>
      <div id="fx-news-list"></div>
    </div>

  </div>
</div>
    <?php
    return ob_get_clean();
}
