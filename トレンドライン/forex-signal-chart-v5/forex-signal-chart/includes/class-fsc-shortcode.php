<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class FSC_Shortcode {
    public function __construct() {
        add_shortcode( 'fx_chart',    [ $this, 'render' ] );
        add_shortcode( 'forex_chart', [ $this, 'render' ] );
        add_action( 'wp_enqueue_scripts', [ $this, 'reg' ] );
    }
    public function reg(): void {
        wp_register_style(  'fx-sc', FSC_URL.'assets/css/chart.css', [], FSC_VER );
        wp_register_script( 'fx-sc', FSC_URL.'assets/js/chart.js',  [], FSC_VER, true );
    }
    public function render( array $atts ): string {
        $atts = shortcode_atts([
            'symbol'       => get_option('fsc_default_symbol','USD/JPY'),
            'interval'     => get_option('fsc_default_tf','15min'),
            'height'       => get_option('fsc_height',440),
            'show_signals' => get_option('fsc_signals',1),
            'auto_refresh' => get_option('fsc_refresh',60),
        ], $atts, 'fx_chart');

        $sym  = sanitize_text_field($atts['symbol']);
        $tf   = sanitize_text_field($atts['interval']);
        $h    = absint($atts['height']);
        $sigs = (bool)$atts['show_signals'];
        $ar   = absint($atts['auto_refresh']);
        $uid  = 'fsc'.substr(md5(uniqid()),0,8);

        wp_enqueue_style('fx-sc');
        wp_enqueue_script('fx-sc');
        if(!wp_script_is('fx-sc','done')){
            wp_localize_script('fx-sc','fscCfg',[
                'rest'    => esc_url_raw(rest_url('fx-signal-chart/v1/candles')),
                'nonce'   => wp_create_nonce('wp_rest'),
                'instrs'  => FSC_Data::instruments(),
                'intvals' => FSC_Data::intervals(),
            ]);
        }

        $instrs = FSC_Data::instruments();
        $intvals = FSC_Data::intervals();
        $groups = [];
        foreach($instrs as $k=>$v) $groups[$v['group']][$k]=$v;

        ob_start(); ?>
        <div id="<?=esc_attr($uid)?>" class="fsc-w"
             data-sym="<?=esc_attr($sym)?>" data-tf="<?=esc_attr($tf)?>"
             data-h="<?=esc_attr($h)?>" data-sp="<?=$sigs?'1':'0'?>" data-ar="<?=esc_attr($ar)?>">

            <div class="fsc-hdr">
                <div class="fsc-sb">
                    <?php foreach($groups as $g=>$items): ?>
                    <span class="fsc-gl"><?=esc_html($g)?></span>
                    <?php foreach($items as $k=>$v): ?>
                    <button class="fsc-syb<?=$k===$sym?' on':''?>" data-sym="<?=esc_attr($k)?>" data-dec="<?=esc_attr($v['dec'])?>"><?=esc_html($v['label'])?></button>
                    <?php endforeach; endforeach; ?>
                </div>
                <div class="fsc-tb">
                    <?php foreach($intvals as $k=>$l): ?>
                    <button class="fsc-tfb<?=$k===$tf?' on':''?>" data-tf="<?=esc_attr($k)?>"><?=esc_html($l)?></button>
                    <?php endforeach; ?>
                </div>
            </div>

            <div class="fsc-stats">
                <div class="fsc-st"><span class="fsc-sl" data-s="nm"><?=esc_html($instrs[$sym]['label']??$sym)?></span><span class="fsc-sv fsc-pr" data-s="px">--</span></div>
                <div class="fsc-st"><span class="fsc-sl">前足比</span><span class="fsc-sv" data-s="ch">--</span></div>
                <div class="fsc-st"><span class="fsc-sl">高値</span><span class="fsc-sv" data-s="hi">--</span></div>
                <div class="fsc-st"><span class="fsc-sl">安値</span><span class="fsc-sv" data-s="lo">--</span></div>
                <div class="fsc-st"><span class="fsc-sl">シグナル</span><span class="fsc-sv" data-s="sg">--</span></div>
                <div class="fsc-st"><span class="fsc-sl">トレンド</span><span class="fsc-sv" data-s="tr">--</span></div>
                <div class="fsc-st fsc-meta"><span class="fsc-sl" data-s="pv">Yahoo Finance</span><span class="fsc-sv fsc-xs" data-s="ts">--</span></div>
            </div>

            <div class="fsc-box" style="height:<?=esc_attr($h)?>px">
                <canvas class="fsc-cv" role="img" aria-label="<?=esc_attr(($instrs[$sym]['label']??$sym).' チャート')?>"></canvas>
                <div class="fsc-ov fsc-ld"><span class="fsc-sp"></span> データ読み込み中...</div>
                <div class="fsc-ov fsc-er" style="display:none"></div>
            </div>

            <div class="fsc-leg">
                <span><i class="fsc-dot" style="background:#1D9E75"></i>買いシグナル</span>
                <span><i class="fsc-dot" style="background:#D85A30"></i>売りシグナル</span>
                <span><i class="fsc-bar" style="background:rgba(55,138,221,.7)"></i>サポート</span>
                <span><i class="fsc-bar" style="background:rgba(226,75,74,.7)"></i>レジスタンス</span>
            </div>

            <div class="fsc-ctrl">
                <button class="fsc-btn fsc-rbtn">🔄 更新</button>
                <label class="fsc-ck"><input type="checkbox" data-o="trend"   checked>トレンドライン</label>
                <label class="fsc-ck"><input type="checkbox" data-o="sr"      checked>サポレジ</label>
                <label class="fsc-ck"><input type="checkbox" data-o="signals" checked>シグナル</label>
                <?php if($ar>0): ?><span class="fsc-cd">次回更新 <strong data-s="cd"><?=esc_html($ar)?></strong>秒後</span><?php endif; ?>
            </div>

            <?php if($sigs): ?>
            <div class="fsc-spanel">
                <p class="fsc-sptitle">📊 検出シグナル</p>
                <div class="fsc-slist"><p class="fsc-nsp">ロード中...</p></div>
            </div>
            <?php endif; ?>
        </div>
        <?php return ob_get_clean();
    }
}
