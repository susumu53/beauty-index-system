/* FX Desk v4.0 - fx-desk.js */
/* global FXDESK, Chart */
(function () {
'use strict';

/* ── 定数 ──────────────────────────────────────────────────────── */
var SCHED = [
  {t:'08:00',h:8, m:0, s:'asia',  e:'オセアニア市場開始',   d:'NZ・豪州勢の参入。週明けは窓開けに注意',imp:1},
  {t:'09:00',h:9, m:0, s:'asia',  e:'東京市場オープン',     d:'日本の銀行が窓口営業開始。仲値へのポジション構築',imp:2},
  {t:'09:55',h:9, m:55,s:'asia',  e:'東京仲値',             d:'五十日はドル不足によるドル買いが集中。最重要',imp:4},
  {t:'10:30',h:10,m:30,s:'asia',  e:'中国市場オープン',     d:'上海・香港株に連動。豪ドルや円が反応',imp:2},
  {t:'14:00',h:14,m:0, s:'asia',  e:'東京午後の波',         d:'機関投資家の最終調整。欧州勢の打診売り開始',imp:1},
  {t:'14:55',h:14,m:55,s:'asia',  e:'東京オプションカット', d:'行使価格への引き寄せ、防戦売りが発生',imp:2},
  {t:'15:00',h:15,m:0, s:'europe',e:'欧州アーリーバード',   d:'ロンドン・フランクフルト投機筋参入',imp:3},
  {t:'15:15',h:15,m:15,s:'europe',e:'欧州実需始動',         d:'ECB参照レートに向けたフロー',imp:2},
  {t:'16:00',h:16,m:0, s:'europe',e:'ロンドン市場オープン', d:'世界最大の取引量。00分・30分に急変多い',imp:4},
  {t:'16:30',h:16,m:30,s:'europe',e:'独・英 経済指標',      d:'PMI等の発表。ポンド・ユーロが急変',imp:3},
  {t:'17:00',h:17,m:0, s:'europe',e:'ユーロ圏指標発表',     d:'欧州全体の景気指標',imp:3},
  {t:'18:00',h:18,m:0, s:'europe',e:'欧州昼休み調整',       d:'ロンドン午前のトレンドが一服',imp:1},
  {t:'21:00',h:21,m:0, s:'ny',    e:'NY勢本格参入',         d:'米国トレーダーが活動開始',imp:3},
  {t:'21:15',h:21,m:15,s:'ny',    e:'ECB参照レート公表',    d:'欧州版仲値確定。確定後の買い戻し発生',imp:3},
  {t:'21:30',h:21,m:30,s:'ny',    e:'米国主要指標発表',     d:'雇用統計・CPI・GDP等。市場が最も激しく動く',imp:4},
  {t:'22:30',h:22,m:30,s:'ny',    e:'NY株式市場オープン',   d:'米国株の寄り付き',imp:3},
  {t:'23:00',h:23,m:0, s:'ny',    e:'NYオプションカット',   d:'通貨オプション最大の行使期限',imp:4},
  {t:'00:00',h:0, m:0, s:'ny',    e:'ロンドンフィキシング', d:'実需の最大山場。月末は巨額リバランスで異常変動',imp:4},
  {t:'01:00',h:1, m:0, s:'close', e:'ロンドンランチタイム', d:'欧州勢の離脱による一時的な落ち着き',imp:1},
  {t:'02:00',h:2, m:0, s:'close', e:'欧州市場クローズ',     d:'欧州勢の最終決済',imp:2},
  {t:'03:00',h:3, m:0, s:'close', e:'米国午後の取引',       d:'米債券市場の利回りに合わせた緩やかなトレンド',imp:1},
  {t:'05:00',h:5, m:0, s:'close', e:'NY市場クローズ',       d:'1日の終値確定。スプレッドが急拡大',imp:2}
];
var SESS = {
  asia:  {c:'#3fb950',label:'🌸 東京・アジア'},
  europe:{c:'#58a6ff',label:'🏰 欧州・ロンドン'},
  ny:    {c:'#f0883e',label:'🗽 ニューヨーク'},
  close: {c:'#484f58',label:'🌙 クローズ'}
};
var IMP_C = ['','#484f58','#d29922','#f0883e','#f85149'];
var IMP_L = ['','低','中','高','最重要'];
var DOCS = {
  dow:{title:'ダウ理論',
    overview:'19世紀末にチャールズ・ダウが提唱した相場分析の基礎理論。すべてのテクニカル分析の出発点とされる。上昇トレンドは高値と安値がともに切り上がっていく状態。下降トレンドは高値と安値がともに切り下がっていく状態。明確な転換シグナルが出るまでトレンドは継続する。',
    logic:'直近20本と前20本の最高値・最安値を比較。ともに切り上がれば上昇（買い）、ともに切り下がれば下降（売り）、どちらかが不一致ならレンジ（中立）と判定。',
    tip:'日足・週足など長い時間軸で特に有効。レンジ相場では機能しにくい。グランビルの法則と組み合わせてエントリーポイントを絞るのが定番。'},
  ma:{title:'移動平均線',
    overview:'一定期間の終値平均を線で結んだ最もシンプルなトレンド指標。短期MA(20)が長期MA(50)を上抜けると「ゴールデンクロス」（買い）、下抜けると「デッドクロス」（売り）。',
    logic:'MA20とMA50のクロスを判定。クロス発生時を特に強いシグナルとして扱う。継続時はMA20とMA50の位置関係でトレンド継続を確認。',
    tip:'トレンド相場では有効だがレンジ相場ではだましが頻発する。MACDと組み合わせると精度が向上する。'},
  gran:{title:'グランビルの法則',
    overview:'ジョセフ・グランビルが1960年代に提唱。移動平均線と現在価格の位置関係・MAの方向性から8つの売買シグナルを定義する理論。特に「押し目買い」と「戻り売り」のタイミングが重要。',
    logic:'MA20の方向（上昇中か下降中か）と現在価格がMA20の上か下かの組み合わせで判定。MA上昇中に価格がMA20を一時的に下回れば押し目買い候補。',
    tip:'「MA20上昇中に価格がMA20を下回ってから反発する」タイミングが最も信頼性の高い買いシグナル。MA方向の確認を怠ると逆張りになるので注意。'},
  bb:{title:'ボリンジャーバンド',
    overview:'ジョン・ボリンジャーが1980年代に考案。移動平均線を中心に±2σのバンドを表示。統計的に価格の約95%が±2σ内に収まる。価格がバンドを突き抜けた状態は行き過ぎとして逆張りの根拠になる。',
    logic:'価格が+2σを突破で買われすぎ（売り）。-2σを突破で売られすぎ（買い）。バンド内は方向性待ち（中立）と判定。',
    tip:'バンドが収縮した後は大きな値動きが起きやすい。バンドウォーク時は逆張りが危険。RSIと組み合わせて確度を高めるのが定番。'},
  rsi:{title:'RSI (14)',
    overview:'J・W・ワイルダーが1978年に開発した相対力指数。14日間の上昇幅の合計÷（上昇幅＋下落幅の合計）×100で算出。0〜100の値で相場の過熱・冷却度を表す。',
    logic:'RSI が70超で買われすぎ（売りシグナル）。30未満で売られすぎ（買いシグナル）。30〜70は中立ゾーン。',
    tip:'強トレンド中はRSIが70以上でも上昇が続くことがある。価格が新高値を更新してもRSIが更新しないダイバージェンスはトレンド転換の強力なシグナル。'},
  macd:{title:'MACD',
    overview:'ジェラルド・アペルが開発したトレンドフォロー型指標。短期EMA(12)と長期EMA(26)の差がMACDライン。そのEMA(9)がシグナルライン。モメンタムとトレンド方向を同時に把握できる。',
    logic:'MACDラインがシグナルラインを上抜けでゴールデンクロス（買い）。下抜けでデッドクロス（売り）。ゼロライン上のクロスはより信頼性が高い。',
    tip:'ヒストグラムの縮小はモメンタムの低下を意味し転換の予兆になる。週足など上位足でのクロスは特に強力なシグナル。'},
  stoch:{title:'ストキャスティクス',
    overview:'ジョージ・レーンが開発したオシレーター系指標。直近N日間の最高値・最安値の範囲で現在価格がどの位置にいるかを0〜100で表示。%K（14日）と%D（3日移動平均）で構成。',
    logic:'%K が80超で買われすぎ（売り）。20未満で売られすぎ（買い）。%Kが%Dを上抜けで買い方向、下抜けで売り方向。',
    tip:'RSIより反応が速く短期トレードに向いている。ダウ理論でトレンド方向を確認してからタイミングを計るのが効果的。'}
};

/* ── State ──────────────────────────────────────────────────────── */
var tradeDir = 'buy';
var trades   = JSON.parse(localStorage.getItem('fxdesk_trades') || '[]');
var fxAlerts = JSON.parse(localStorage.getItem('fxdesk_alerts') || '{}');
var firedAlerts = {};
var sxChartP  = null;
var sxChartR  = null;
var sxFetching = false;
var sxCurrentTf    = '1d';
var sxCurrentRange = '2y';
var sxOpenDocId    = null;

var fxNewsLog = JSON.parse(localStorage.getItem('fxdesk_news_log') || '{}');
var fxNewsOn = false;
var fxSpeechQueue = [];
var fxIsSpeaking = false;
var fxNewsTimer = null;
var fxCalCache = null;
var fxDailyReadDate = localStorage.getItem('fxdesk_daily_read') || '';

/* ── Helpers ────────────────────────────────────────────────────── */
function jst() {
  return new Date(new Date().toLocaleString('en-US', {timeZone: 'Asia/Tokyo'}));
}
function toMin(h, m) { return h * 60 + m; }
function nowMin() { var n = jst(); return toMin(n.getHours(), n.getMinutes()); }
function fmtDec(v) { return v >= 1000 ? v.toFixed(2) : v >= 100 ? v.toFixed(3) : v >= 10 ? v.toFixed(4) : v.toFixed(5); }
function pad(v) { return String(v).padStart(2, '0'); }

function getSess() {
  var m = nowMin();
  if (m >= 480 && m < 900)  return 'asia';
  if (m >= 900 && m < 1260) return 'europe';
  if (m >= 1260 || m < 300) return 'ny';
  return 'close';
}
function nextEv() {
  var now = nowMin(), best = null, bd = 99999;
  for (var i = 0; i < SCHED.length; i++) {
    var ev = SCHED[i];
    var em = toMin(ev.h, ev.m);
    var diff = em > now ? em - now : em + 1440 - now;
    if (diff < bd && diff > 0) { bd = diff; best = {t:ev.t,e:ev.e,imp:ev.imp,diff:diff}; }
  }
  return best;
}
function fmtCd(m) {
  if (m <= 0) return 'まもなく';
  var h = Math.floor(m / 60), r = m % 60;
  return h ? h + '時間' + r + '分後' : r + '分後';
}
function el(id) { return document.getElementById(id); }

function yahooFetch(url) {
  var isXml = url.indexOf('news.google.com') !== -1;
  var proxyUrl = FXDESK.ajaxUrl
    + '?action=fxdesk_proxy'
    + '&nonce='  + encodeURIComponent(FXDESK.nonce)
    + '&url='    + encodeURIComponent(url);
  return fetch(proxyUrl).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return isXml ? r.text() : r.json();
  });
}

/* ── Sound ──────────────────────────────────────────────────────── */
function playSound(imp) {
  try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var patterns = {
      1: [{f:440,d:0.3}],
      2: [{f:520,d:0.3},{f:660,d:0.3}],
      3: [{f:660,d:0.25},{f:880,d:0.25},{f:660,d:0.25}],
      4: [{f:880,d:0.2},{f:1100,d:0.2},{f:880,d:0.2},{f:1100,d:0.3}]
    };
    var seq = patterns[Math.min(Math.max(imp,1),4)] || patterns[2];
    var t = ctx.currentTime + 0.05;
    seq.forEach(function(x) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = 'sine'; o.frequency.value = x.f;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.3, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.001, t + x.d);
      o.start(t); o.stop(t + x.d + 0.05);
      t += x.d + 0.08;
    });
  } catch(e) {}
}
function fxTestSound() { playSound(4); }

/* ── Tab ────────────────────────────────────────────────────────── */
function fxTab(id, btn) {
  document.querySelectorAll('#fxdesk .fx-tab').forEach(function(t){ t.classList.remove('active'); });
  document.querySelectorAll('#fxdesk .fx-nav button').forEach(function(b){ b.classList.remove('active'); });
  el('fx-tab-' + id).classList.add('active');
  btn.classList.add('active');
}

/* ── Schedule & Clock ───────────────────────────────────────────── */
function renderClock() {
  var n = jst();
  el('fx-clock').textContent = pad(n.getHours()) + ':' + pad(n.getMinutes()) + ':' + pad(n.getSeconds());
  var sess = getSess(), sd = SESS[sess];
  var badge = el('fx-badge');
  badge.textContent = sd.label;
  badge.style.cssText = 'background:' + sd.c + '22;color:' + sd.c + ';border:1px solid ' + sd.c;
  el('fx-sess-name').textContent = sd.label;
  el('fx-sess-name').style.color = sd.c;
  el('fx-sess-card').style.borderLeftColor = sd.c;
  var nv = nextEv();
  if (nv) {
    el('fx-next-name').style.color = IMP_C[nv.imp];
    el('fx-next-name').textContent = nv.e;
    el('fx-next-time').textContent = nv.t + ' JST — ' + fmtCd(nv.diff);
  }
}

function renderSchedule() {
  var now = nowMin(), nv = nextEv();
  el('fx-sched-list').innerHTML = SCHED.map(function(ev) {
    var em = toMin(ev.h, ev.m);
    var isPast = em <= now && (now - em) > 0 && (now - em) < 1440;
    var isNext = nv && nv.t === ev.t;
    var sd = SESS[ev.s];
    return '<div class="fx-sched-row' + (isPast ? ' is-past' : '') + '"'
      + ' style="background:' + (isNext ? sd.c + '11' : 'transparent') + ';border-left-color:' + (isNext ? sd.c : 'transparent') + '">'
      + '<span class="fx-sched-time" style="color:' + sd.c + '">' + ev.t + '</span>'
      + '<span class="fx-sched-dot" style="background:' + IMP_C[ev.imp] + '"></span>'
      + '<span style="flex:1;min-width:0">'
      + '<div style="font-size:13px;color:' + (isPast ? 'var(--muted)' : 'var(--text)') + ';font-weight:' + (isNext ? 700 : 400) + '">' + ev.e + '</div>'
      + '<div class="fx-sched-detail">' + ev.d + '</div></span>'
      + '<span class="fx-sched-imp" style="color:' + IMP_C[ev.imp] + '">' + IMP_L[ev.imp] + '</span>'
      + '</div>';
  }).join('');
}

/* ── Journal ─────────────────────────────────────────────────────── */
function saveTrades() { localStorage.setItem('fxdesk_trades', JSON.stringify(trades)); }

function fxDir(d) {
  tradeDir = d;
  el('fj-buy').style.cssText  = 'flex:1;padding:7px;border:none;border-radius:6px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit;'
    + 'background:' + (d === 'buy' ? 'var(--green)' : 'var(--card2)') + ';color:' + (d === 'buy' ? '#000' : 'var(--muted)');
  el('fj-sell').style.cssText = 'flex:1;padding:7px;border:none;border-radius:6px;cursor:pointer;font-weight:700;font-size:12px;font-family:inherit;'
    + 'background:' + (d === 'sell' ? 'var(--red)' : 'var(--card2)') + ';color:' + (d === 'sell' ? '#000' : 'var(--muted)');
}

function fxToggleForm() {
  var f = el('fx-trade-form');
  f.style.display = f.style.display === 'none' ? 'block' : 'none';
  el('fj-date').value = new Date().toISOString().split('T')[0];
}

function fxAddTrade() {
  var pair  = el('fj-pair').value;
  var entry = parseFloat(el('fj-entry').value);
  var exit  = parseFloat(el('fj-exit').value);
  var lots  = parseFloat(el('fj-lots').value);
  var notes = el('fj-notes').value;
  var date  = el('fj-date').value;
  if (!entry || !exit || !lots) return;
  // 通貨ペアの特性を動的判定
  var isJpy = pair.indexOf('JPY') !== -1;
  var pip   = isJpy ? 0.01 : 0.0001;
  var pm    = (exit - entry) / pip;
  var pips  = tradeDir === 'buy' ? pm : -pm;
  var pnl   = Math.round(pips * (isJpy ? 1000 : 10 * 149.5) * lots);
  trades.unshift({id: Date.now(), pair: pair, dir: tradeDir, entry: entry, exit: exit, lots: lots, pips: Math.round(pips * 10) / 10, pnl: pnl, notes: notes, date: date});
  saveTrades();
  ['fj-entry','fj-exit','fj-notes'].forEach(function(id){ el(id).value = ''; });
  el('fx-trade-form').style.display = 'none';
  renderJournal();
}

function fxDeleteTrade(id) {
  trades = trades.filter(function(t){ return t.id !== id; });
  saveTrades(); renderJournal();
}

function renderJournal() {
  var sum = el('fx-j-summary');
  if (trades.length) {
    var total = trades.reduce(function(s, t){ return s + t.pnl; }, 0);
    var wr    = Math.round(trades.filter(function(t){ return t.pnl > 0; }).length / trades.length * 100);
    sum.style.display = 'grid';
    sum.innerHTML = '<div><span class="fx-lbl">総損益（概算）</span><div class="fx-summary-val" style="color:' + (total >= 0 ? 'var(--green)' : 'var(--red)') + '">' + (total >= 0 ? '+' : '') + total.toLocaleString() + '円</div></div>'
      + '<div><span class="fx-lbl">勝率</span><div class="fx-summary-val">' + wr + '%</div></div>'
      + '<div><span class="fx-lbl">記録数</span><div class="fx-summary-val">' + trades.length + '回</div></div>';
  } else { sum.style.display = 'none'; }
  el('fx-trade-list').innerHTML = trades.length ? trades.map(function(tr) {
    // 小数点桁数を価格から動的判定
    var pDec = tr.entry >= 1000 ? 2 : tr.entry >= 100 ? 3 : 5;
    return '<div class="fx-card" style="border-left:3px solid ' + (tr.pnl >= 0 ? 'var(--green)' : 'var(--red)') + ';margin-bottom:8px">'
      + '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">'
      + '<div style="flex:1;min-width:0">'
      + '<div style="display:flex;gap:7px;align-items:center;flex-wrap:wrap">'
      + '<span style="font-weight:700">' + tr.pair + '</span>'
      + '<span class="fx-dir-badge ' + (tr.dir === 'buy' ? 'fx-badge-buy' : 'fx-badge-sell') + '">' + (tr.dir === 'buy' ? '▲ BUY' : '▼ SELL') + '</span>'
      + '<span style="font-size:11px;color:var(--muted)">' + tr.lots + 'lot</span>'
      + '<span style="font-size:10px;color:var(--muted)">' + tr.date + '</span></div>'
      + '<div style="font-size:12px;color:var(--dim);margin-top:4px">' + tr.entry.toFixed(pDec) + ' → ' + tr.exit.toFixed(pDec)
      + '<span style="margin-left:8px;color:' + (tr.pips >= 0 ? 'var(--green)' : 'var(--red)') + ';font-weight:700">' + (tr.pips >= 0 ? '+' : '') + tr.pips + 'pip</span></div>'
      + (tr.notes ? '<div style="font-size:11px;color:var(--muted);margin-top:3px">📝 ' + tr.notes + '</div>' : '')
      + '</div>'
      + '<div style="text-align:right;flex-shrink:0">'
      + '<div style="font-weight:700;font-size:17px;color:' + (tr.pnl >= 0 ? 'var(--green)' : 'var(--red)') + '">' + (tr.pnl >= 0 ? '+' : '') + tr.pnl.toLocaleString() + '円</div>'
      + '<button class="fx-btn-sm" onclick="fxDeleteTrade(' + tr.id + ')" style="color:var(--red);border:none;margin-top:4px">削除</button>'
      + '</div></div></div>';
  }).join('') : '<div class="fx-card" style="text-align:center;padding:36px;color:var(--muted)">📋 まだ記録がありません</div>';
}

/* ── Alerts ──────────────────────────────────────────────────────── */
function saveAlerts() { localStorage.setItem('fxdesk_alerts', JSON.stringify(fxAlerts)); }

function fxToggleAlert(t) { fxAlerts[t] = !fxAlerts[t]; saveAlerts(); renderAlerts(); }

function renderAlerts() {
  var now = nowMin();
  var sorted = SCHED.map(function(ev) {
    var em = toMin(ev.h, ev.m);
    return {t:ev.t,e:ev.e,s:ev.s,imp:ev.imp, diff: em > now ? em - now : em + 1440 - now};
  }).sort(function(a,b){ return a.diff - b.diff; });
  el('fx-alert-list').innerHTML = sorted.map(function(ev) {
    var sd = SESS[ev.s], on = !!fxAlerts[ev.t], isVC = ev.diff <= 15, isClose = ev.diff <= 60;
    return '<div class="fx-card" style="margin-bottom:6px;border-left:3px solid ' + (isVC ? IMP_C[ev.imp] : isClose ? sd.c : 'var(--border)') + ';background:' + (isVC ? sd.c + '11' : 'var(--card)') + '">'
      + '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
      + '<div style="flex:1;min-width:0">'
      + '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">'
      + '<span style="color:' + sd.c + ';font-weight:700">' + ev.t + '</span>'
      + '<span>' + ev.e + '</span>'
      + '<span style="font-size:10px;color:' + IMP_C[ev.imp] + ';font-weight:700">' + IMP_L[ev.imp] + '</span></div>'
      + '<div style="font-size:11px;color:' + (isVC ? IMP_C[ev.imp] : 'var(--muted)') + ';margin-top:3px;font-weight:' + (isVC ? 700 : 400) + '">'
      + (isVC ? '⚡ ' : '') + fmtCd(ev.diff)
      + (on ? '<span style="margin-left:8px;color:var(--orange)">→ ' + fmtCd(Math.max(0, ev.diff - 5)) + 'に鳴動</span>' : '')
      + '</div></div>'
      + '<button class="fx-btn-sm' + (on ? ' fx-alert-on' : '') + '" onclick="fxToggleAlert(\'' + ev.t + '\')">' + (on ? '🔔 ON' : '🔕 OFF') + '</button>'
      + '</div></div>';
  }).join('');
}

function checkAlerts() {
  var n = jst(); if (n.getSeconds() !== 0) return;
  var nowM = nowMin(), dk = n.toISOString().slice(0, 10);
  SCHED.forEach(function(ev) {
    if (!fxAlerts[ev.t]) return;
    var em   = toMin(ev.h, ev.m);
    var diff = em > nowM ? em - nowM : em + 1440 - nowM;
    if (diff === 5) {
      var key = ev.t + '_' + dk;
      if (!firedAlerts[key]) { firedAlerts[key] = true; playSound(ev.imp); }
    }
  });
}

/* ── シグナル計算 ─────────────────────────────────────────────────── */
function sxSMA(a, k) {
  return a.map(function(_, i) {
    if (i < k - 1) return null;
    var s = 0; for (var j = i - k + 1; j <= i; j++) s += a[j]; return s / k;
  });
}
function sxEMA(a, k) {
  var m = 2 / (k + 1), e = a[0];
  return a.map(function(v) { e = v * m + e * (1 - m); return e; });
}
function sxRSI(a) {
  var k = 14, r = a.map(function(){ return null; });
  var ag = 0, al = 0;
  for (var i = 1; i <= k; i++) { var d0 = a[i] - a[i-1]; if (d0 > 0) ag += d0; else al -= d0; }
  ag /= k; al /= k;
  r[k] = al ? 100 - 100 / (1 + ag / al) : 100;
  for (var i2 = k + 1; i2 < a.length; i2++) {
    var d1 = a[i2] - a[i2-1];
    ag = (ag * (k-1) + (d1 > 0 ? d1 : 0)) / k;
    al = (al * (k-1) + (d1 < 0 ? -d1 : 0)) / k;
    r[i2] = al ? 100 - 100 / (1 + ag / al) : 100;
  }
  return r;
}
function sxBB(a) {
  var k = 20, m = 2, md = sxSMA(a, k), up = [], lo = [];
  for (var i = 0; i < a.length; i++) {
    if (i < k - 1) { up.push(null); lo.push(null); continue; }
    var sl = a.slice(i - k + 1, i + 1), mn = md[i];
    var std = Math.sqrt(sl.reduce(function(s,v){ return s + (v-mn)*(v-mn); }, 0) / k);
    up.push(mn + m * std); lo.push(mn - m * std);
  }
  return {up:up, lo:lo, mid:md};
}
function sxMACD(a) {
  var fe = sxEMA(a, 12), se = sxEMA(a, 26);
  var ml = fe.map(function(v, i){ return v - se[i]; });
  return {ml:ml, sl:sxEMA(ml, 9)};
}
function sxStoch(a) {
  var kv = a.map(function(_, i) {
    if (i < 13) return null;
    var sl = a.slice(i - 13, i + 1);
    var hi = Math.max.apply(null, sl), lo = Math.min.apply(null, sl);
    return hi === lo ? 50 : ((a[i] - lo) / (hi - lo)) * 100;
  });
  var dv = kv.map(function(_, i) {
    if (i < 15) return null;
    var sl = kv.slice(i - 2, i + 1);
    if (sl.some(function(v){ return v === null; })) return null;
    return sl.reduce(function(s,v){ return s + v; }, 0) / 3;
  });
  return {k:kv, d:dv};
}

function computeSigs(prices) {
  var n = prices.length;
  var ma20 = sxSMA(prices, 20), ma50 = sxSMA(prices, 50);
  var bb   = sxBB(prices);
  var rsi  = sxRSI(prices);
  var macd = sxMACD(prices);
  var stoch= sxStoch(prices);
  var last = prices[n-1];
  var l20=ma20[n-1], l50=ma50[n-1], p20=ma20[n-2], p50=ma50[n-2];
  var lBBU=bb.up[n-1], lBBL=bb.lo[n-1], lBBM=bb.mid[n-1];
  var lRSI=rsi[n-1];
  var lML=macd.ml[n-1], lSL=macd.sl[n-1], pML=macd.ml[n-2], pSL=macd.sl[n-2];
  var lK=stoch.k[n-1], lD=stoch.d[n-1];
  var r20hi=Math.max.apply(null,prices.slice(n-20)), r20lo=Math.min.apply(null,prices.slice(n-20));
  var o20hi=Math.max.apply(null,prices.slice(n-40,n-20)), o20lo=Math.min.apply(null,prices.slice(n-40,n-20));

  var dowS,dowR;
  if (r20hi>o20hi&&r20lo>o20lo){dowS='buy';dowR='高値・安値ともに切り上げ（上昇トレンド）';}
  else if(r20hi<o20hi&&r20lo<o20lo){dowS='sell';dowR='高値・安値ともに切り下げ（下降トレンド）';}
  else{dowS='neutral';dowR='トレンド不明確（レンジ相場）';}

  var maS,maR;
  if(l20>l50&&p20<=p50){maS='buy';maR='ゴールデンクロス発生（MA20がMA50を上抜け）';}
  else if(l20<l50&&p20>=p50){maS='sell';maR='デッドクロス発生（MA20がMA50を下抜け）';}
  else if(l20>l50){maS='buy';maR='MA20 > MA50（上昇トレンド継続）';}
  else{maS='sell';maR='MA20 < MA50（下降トレンド継続）';}

  var maRising = l20 > ma20[n-5];
  var grS,grR;
  if(last>l20&&maRising){grS='buy';grR='価格 > MA20 かつ MA20上昇（買い継続）';}
  else if(last<l20&&maRising){grS='buy';grR='MA20上昇中の押し目（押し目買い候補）';}
  else if(last<l20&&!maRising){grS='sell';grR='価格 < MA20 かつ MA20下落（売り継続）';}
  else{grS='neutral';grR='MA20下落中の戻り（様子見）';}

  var bbS,bbR;
  if(last<lBBL){bbS='buy';bbR='価格が -2σ(' + fmtDec(lBBL) + ') を下抜け（売られすぎ）';}
  else if(last>lBBU){bbS='sell';bbR='価格が +2σ(' + fmtDec(lBBU) + ') を上抜け（買われすぎ）';}
  else if(last<lBBM){bbS='neutral';bbR='バンド内・中心線より下（方向待ち）';}
  else{bbS='neutral';bbR='バンド内・中心線より上（方向待ち）';}

  var rsiS,rsiR;
  if(lRSI<30){rsiS='buy';rsiR='RSI ' + lRSI.toFixed(1) + ' ── 売られすぎ（30以下）';}
  else if(lRSI>70){rsiS='sell';rsiR='RSI ' + lRSI.toFixed(1) + ' ── 買われすぎ（70以上）';}
  else{rsiS='neutral';rsiR='RSI ' + lRSI.toFixed(1) + ' ── 中立ゾーン';}

  var macdS,macdR;
  if(lML>lSL&&pML<=pSL){macdS='buy';macdR='MACDがシグナル線を上抜け（買いクロス）';}
  else if(lML<lSL&&pML>=pSL){macdS='sell';macdR='MACDがシグナル線を下抜け（売りクロス）';}
  else if(lML>lSL){macdS='buy';macdR='MACD > シグナル線（上昇の勢い継続）';}
  else{macdS='sell';macdR='MACD < シグナル線（下落の勢い継続）';}

  var stS,stR;
  if(lK<20){stS='buy';stR='%K ' + lK.toFixed(1) + ' ── 売られすぎゾーン（20以下）';}
  else if(lK>80){stS='sell';stR='%K ' + lK.toFixed(1) + ' ── 買われすぎゾーン（80以上）';}
  else if(lK>lD){stS='buy';stR='%K(' + lK.toFixed(0) + ') > %D(' + (lD ? lD.toFixed(0) : '—') + ') ── 上昇方向';}
  else{stS='sell';stR='%K(' + lK.toFixed(0) + ') < %D(' + (lD ? lD.toFixed(0) : '—') + ') ── 下落方向';}

  return [
    {id:'dow',  name:'ダウ理論',          sig:dowS,  reason:dowR},
    {id:'ma',   name:'移動平均線',         sig:maS,   reason:maR},
    {id:'gran', name:'グランビルの法則',   sig:grS,   reason:grR},
    {id:'bb',   name:'ボリンジャーバンド', sig:bbS,   reason:bbR},
    {id:'rsi',  name:'RSI (14)',           sig:rsiS,  reason:rsiR},
    {id:'macd', name:'MACD',               sig:macdS, reason:macdR},
    {id:'stoch',name:'ストキャスティクス', sig:stS,   reason:stR}
  ];
}

/* ── シグナルチャート ─────────────────────────────────────────────── */
function sxDrawCharts(labels, prices, ma20, ma50, bb, rsi) {
  var N   = Math.min(prices.length, 80);
  var lbs = labels.slice(-N);
  var dPr = prices.slice(-N), dMA20=ma20.slice(-N), dMA50=ma50.slice(-N);
  var dBBU=bb.up.slice(-N), dBBL=bb.lo.slice(-N), dRSI=rsi.slice(-N);
  var gc='rgba(255,255,255,0.04)', tc='#484f58';
  var dec = prices[0] >= 1000 ? 2 : prices[0] >= 100 ? 3 : 5;
  var yDec = Math.max(0, dec - 1);

  if (sxChartP) { try { sxChartP.destroy(); } catch(e){} }
  sxChartP = new Chart(el('sx-cPrice'), {
    type: 'line',
    data: { labels: lbs, datasets: [
      {label:'BB下限',data:dBBL,borderColor:'rgba(88,166,255,.2)',borderWidth:0.7,fill:false,pointRadius:0,tension:0.2},
      {label:'BB上限',data:dBBU,borderColor:'rgba(88,166,255,.2)',borderWidth:0.7,fill:'-1',backgroundColor:'rgba(88,166,255,.07)',pointRadius:0,tension:0.2},
      {label:'MA50', data:dMA50,borderColor:'#bc8cff',borderWidth:1,borderDash:[5,3],fill:false,pointRadius:0,tension:0.2},
      {label:'MA20', data:dMA20,borderColor:'#f0883e',borderWidth:1.2,fill:false,pointRadius:0,tension:0.2},
      {label:'価格',  data:dPr,  borderColor:'#58a6ff',borderWidth:1.8,fill:false,pointRadius:0,tension:0.2}
    ]},
    options: {
      responsive:true, maintainAspectRatio:false,
      interaction:{intersect:false,mode:'index'},
      plugins:{
        legend:{display:false},
        tooltip:{backgroundColor:'rgba(13,17,23,.97)',titleColor:'#8b949e',bodyColor:'#e6edf3',borderColor:'#30363d',borderWidth:1,
          callbacks:{label:function(c){if(c.parsed.y==null)return null;return ' '+c.dataset.label+': '+c.parsed.y.toFixed(dec);}}}
      },
      scales:{
        x:{grid:{color:gc},ticks:{font:{size:9},color:tc,maxTicksLimit:8,maxRotation:0}},
        y:{grid:{color:gc},ticks:{font:{size:9},color:tc,maxTicksLimit:5,callback:function(v){return v.toFixed(yDec);}}}
      }
    }
  });

  if (sxChartR) { try { sxChartR.destroy(); } catch(e){} }
  sxChartR = new Chart(el('sx-cRsi'), {
    type: 'line',
    data: { labels: lbs, datasets: [
      {label:'RSI',data:dRSI,borderColor:'#3fb950',borderWidth:1.2,fill:false,pointRadius:0,tension:0.2},
      {label:'70', data:Array(N).fill(70),borderColor:'rgba(248,81,73,.45)',borderWidth:0.7,borderDash:[4,2],fill:false,pointRadius:0},
      {label:'30', data:Array(N).fill(30),borderColor:'rgba(63,185,80,.45)', borderWidth:0.7,borderDash:[4,2],fill:false,pointRadius:0}
    ]},
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{enabled:false}},
      scales:{
        x:{display:false},
        y:{min:0,max:100,grid:{color:gc},ticks:{font:{size:9},color:tc,
          callback:function(v){return [0,30,70,100].indexOf(v) > -1 ? String(v) : '';}}}
      }
    }
  });
}

function sxDrawOverall(sigs) {
  var buys  = sigs.filter(function(s){ return s.sig==='buy'; }).length;
  var sells = sigs.filter(function(s){ return s.sig==='sell'; }).length;
  var neus  = sigs.filter(function(s){ return s.sig==='neutral'; }).length;
  var oe = el('sx-os');
  if(buys>=sells+2){oe.textContent='📈 買いシグナル優勢';oe.style.color='var(--green)';}
  else if(sells>=buys+2){oe.textContent='📉 売りシグナル優勢';oe.style.color='var(--red)';}
  else if(buys>sells){oe.textContent='↗ やや買い優勢';oe.style.color='#86efac';}
  else if(sells>buys){oe.textContent='↘ やや売り優勢';oe.style.color='#fca5a5';}
  else{oe.textContent='↔ 中立・様子見';oe.style.color='var(--dim)';}
  el('sx-sb').style.flex  = String(buys  || 0.001);
  el('sx-sne').style.flex = String(neus  || 0.001);
  el('sx-ss').style.flex  = String(sells || 0.001);
  el('sx-sct').textContent = '買い' + buys + ' 中立' + neus + ' 売り' + sells;
  el('sx-ov').style.display = 'flex';
}

function sxDrawCards(sigs) {
  var icon = {buy:'▲ 買い', sell:'▼ 売り', neutral:'─ 中立'};
  el('sx-sg').innerHTML = sigs.map(function(s) {
    return '<div class="sx-scard ' + s.sig + '" onclick="sxToggleDoc(\'' + s.id + '\')">'
      + '<div class="sx-sn">' + s.name + '</div>'
      + '<div class="sx-sv ' + s.sig + '">' + icon[s.sig] + '</div>'
      + '<div class="sx-sr">' + s.reason + '</div>'
      + '<div class="sx-hint">タップで詳細解説 ▸</div>'
      + '</div>';
  }).join('');
  el('sx-disc').style.display = 'block';
}

function sxToggleDoc(id) {
  var panel = el('sx-doc-panel');
  if (sxOpenDocId === id) { panel.classList.remove('open'); sxOpenDocId = null; return; }
  var doc = DOCS[id]; if (!doc) return;
  sxOpenDocId = id;
  el('sx-doc-title').textContent = doc.title;
  el('sx-doc-body').innerHTML =
    '<div class="sx-doc-sec">📊 この指標について</div><div class="sx-doc-txt">' + doc.overview + '</div>'
    + '<div class="sx-doc-sec">⚙️ 判定ロジック</div><div class="sx-doc-txt">' + doc.logic + '</div>'
    + '<div class="sx-doc-sec">💡 使い方のヒント</div><div class="sx-doc-txt">' + doc.tip + '</div>';
  panel.classList.add('open');
  panel.scrollIntoView({behavior:'smooth', block:'nearest'});
}
function sxCloseDoc() { el('sx-doc-panel').classList.remove('open'); sxOpenDocId = null; }

function sxSetTf(btn) {
  document.querySelectorAll('#fxdesk .sx-tfb').forEach(function(b){ b.classList.remove('act'); });
  btn.classList.add('act');
  sxCurrentTf    = btn.getAttribute('data-tf');
  sxCurrentRange = btn.getAttribute('data-range');
  sxRender();
}

/* ── シグナルメイン ───────────────────────────────────────────────── */
function sxRender() {
  if (sxFetching) return;
  sxFetching = true; sxCloseDoc();
  var spin    = el('sx-spin');
  var errEl   = el('sx-err');
  var innerEl = el('sx-chart-inner');
  spin.classList.add('sx-spin');
  errEl.style.display  = 'none';
  innerEl.style.display = 'block';
  el('sx-ov').style.display   = 'none';
  el('sx-disc').style.display = 'none';
  el('sx-sg').innerHTML = '';

  var sym = el('sx-ps').value;
  var url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + sym
    + '?interval=' + sxCurrentTf + '&range=' + sxCurrentRange;

  function sxShowErr(msg) {
    errEl.innerHTML = '⚠️ ' + msg + '<br><button class="fx-btn" onclick="sxRender()" style="margin-top:12px;font-size:12px;padding:6px 16px">再試行</button>';
    errEl.style.display  = 'block';
    innerEl.style.display = 'none';
    spin.classList.remove('sx-spin');
    sxFetching = false;
  }

  function loadChartJs(cb) {
    if (window.Chart) { cb(); return; }
    var sc = document.createElement('script');
    sc.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js';
    sc.onload = cb;
    sc.onerror = function() { sxShowErr('Chart.js の読み込みに失敗しました'); };
    document.head.appendChild(sc);
  }

  yahooFetch(url).then(function(json) {
    var res = json && json.chart && json.chart.result && json.chart.result[0];
    if (!res) throw new Error('データが取得できませんでした');

    var meta = res.meta || {};
    var curPrice  = meta.regularMarketPrice  || meta.chartPreviousClose || 0;
    var prevClose = meta.chartPreviousClose  || curPrice;
    var chg = curPrice - prevClose, chgPct = prevClose ? (chg / prevClose) * 100 : 0;
    var dec = curPrice >= 1000 ? 2 : curPrice >= 100 ? 3 : 5;

    el('sx-pv').textContent = curPrice.toFixed(dec);
    var pcEl = el('sx-pc');
    pcEl.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(dec) + ' (' + (chg >= 0 ? '+' : '') + chgPct.toFixed(2) + '%)';
    pcEl.className = 'sx-pc ' + (chg >= 0 ? 'sx-up' : 'sx-down');

    var timestamps = res.timestamp || [];
    var closes = (res.indicators && res.indicators.quote && res.indicators.quote[0] && res.indicators.quote[0].close) || [];
    var cleanPrices = [], cleanLabels = [];
    timestamps.forEach(function(ts, i) {
      if (closes[i] == null) return;
      cleanPrices.push(closes[i]);
      var d = new Date(ts * 1000);
      if (sxCurrentTf === '1d' || sxCurrentTf === '1wk') {
        cleanLabels.push((d.getMonth() + 1) + '/' + d.getDate());
      } else {
        cleanLabels.push(pad(d.getHours()) + ':' + pad(d.getMinutes()));
      }
    });

    if (cleanPrices.length < 50) throw new Error('データが不足しています（' + cleanPrices.length + '本）。別の時間軸をお試しください。');

    var ma20 = sxSMA(cleanPrices, 20), ma50 = sxSMA(cleanPrices, 50);
    var bb   = sxBB(cleanPrices);
    var rsi  = sxRSI(cleanPrices);

    loadChartJs(function() {
      sxDrawCharts(cleanLabels, cleanPrices, ma20, ma50, bb, rsi);
      var sigs = computeSigs(cleanPrices);
      sxDrawOverall(sigs);
      sxDrawCards(sigs);
      spin.classList.remove('sx-spin');
      sxFetching = false;
    });
  }).catch(function(e) {
    sxShowErr(e.message || '不明なエラー');
  });
}

/* ── Tick & Init ─────────────────────────────────────────────────── */
function tick() {
  renderClock(); renderSchedule(); renderAlerts(); checkAlerts();
  if (fxNewsOn && !fxIsSpeaking && fxSpeechQueue.length > 0) {
    speakNext();
  }
}

/* ── ニュース・音声合成モジュール ───────────────────────────────────── */
function saveNewsLog() { localStorage.setItem('fxdesk_news_log', JSON.stringify(fxNewsLog)); }

function fxToggleNews() {
  fxNewsOn = !fxNewsOn;
  var btn = el('fx-news-btn');
  var st = el('fx-news-status');
  if (fxNewsOn) {
    btn.textContent = '読み上げをOFFにする';
    btn.style.background = 'var(--dim)';
    st.textContent = '🔊 読み上げON（監視中）';
    st.style.color = 'var(--green)';
    // 初回権限取得のためのダミー音声（無音）
    var u = new SpeechSynthesisUtterance('');
    window.speechSynthesis.speak(u);
    
    // すぐに処理開始
    fxFetchNewsWorkflow();
    // 3分おきにフェッチ
    fxNewsTimer = setInterval(fxFetchNewsWorkflow, 180000);
  } else {
    btn.textContent = '自動読み上げをONにする';
    btn.style.background = '';
    st.textContent = '🔇 読み上げOFF';
    st.style.color = '';
    clearInterval(fxNewsTimer);
    window.speechSynthesis.cancel();
    fxSpeechQueue = [];
    fxIsSpeaking = false;
  }
}

function fxClearNewsLog() {
  fxNewsLog = {}; saveNewsLog();
  localStorage.removeItem('fxdesk_daily_read');
  fxDailyReadDate = '';
  renderNewsList();
  alert('履歴をリセットしました。次の更新時に再読み上げされます。');
}

function fxFetchNewsWorkflow() {
  var todayStr = new Date().toISOString().slice(0, 10);
  
  // 1. Google ニュース
  var q = el('fx-news-query').value || '為替';
  var gUrl = 'https://news.google.com/rss/search?q=' + encodeURIComponent(q) + '&hl=ja&gl=JP&ceid=JP:ja';
  yahooFetch(gUrl).then(function(xmlText) {
    var dp = new DOMParser();
    var xml = dp.parseFromString(xmlText, 'text/xml');
    var items = xml.querySelectorAll('item');
    var limit = fxDailyReadDate ? 3 : 10; // 初回以降は直近3件を監視
    for (var i = 0; i < Math.min(items.length, limit); i++) {
      var item = items[i];
      var guid = item.querySelector('guid').textContent;
      if (!fxNewsLog[guid]) {
        var title = item.querySelector('title').textContent;
        // 「 - メディア名」を削って聞きやすくする
        var cleanTitle = title.replace(/\s-\s[^\s]+$/, '');
        fxNewsLog[guid] = {title: title, time: new Date().getTime(), type: 'news'};
        queueSpeech('関連ニュースです。' + cleanTitle);
      }
    }
    saveNewsLog();
    renderNewsList();
  }).catch(function(e){ console.warn('News Fetch Error', e); });

  // 2. ForexFactory (JSON)
  var ffUrl = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json';
  yahooFetch(ffUrl).then(function(json) {
    fxCalCache = json;
    
    // 朝（またはON時最初）のスケジュール読み上げ
    if (fxDailyReadDate !== todayStr) {
      fxReadTodaySchedule(true);
      fxDailyReadDate = todayStr;
      localStorage.setItem('fxdesk_daily_read', todayStr);
    }

    // 予想 vs 結果の監視
    var nowStr = new Date().toISOString();
    json.forEach(function(ev) {
      var evId = 'ff_' + ev.title + '_' + ev.date;
      var impact = ev.impact; // High, Medium, Low
      if (impact === 'High' && ev.actual && ev.forecast) {
        if (!fxNewsLog[evId]) {
          var text = '重要指標の結果が発表されました。' + ev.country + 'の' + ev.title + 'です。';
          text += '予想' + ev.forecast + 'に対し、結果は' + ev.actual + 'でした。';
          if (ev.previous) text += 'ちなみに前回は' + ev.previous + 'でした。';
          
          fxNewsLog[evId] = {title: text, time: new Date().getTime(), type: 'alert'};
          saveNewsLog();
          queueSpeech(text, true); // 最優先
        }
      }
    });
    renderNewsList();
  }).catch(function(e){ console.warn('Calendar Fetch Error', e); });
}

function fxReadTodaySchedule(isAuto) {
  if (!fxCalCache) {
    if (!isAuto) alert('カレンダーデータを取得中です。数秒後にお試しください。');
    return;
  }
  var today = new Date();
  var todayStr = today.toISOString().slice(0, 10);
  
  var todaysEvs = fxCalCache.filter(function(ev) {
    return ev.date.indexOf(todayStr) === 0 && ev.impact === 'High';
  });
  
  if (todaysEvs.length === 0) {
    queueSpeech('本日の重要指標予定は、特にありません。');
  } else {
    var t = '本日の重要指標スケジュールをお知らせします。';
    todaysEvs.forEach(function(ev) {
      var d = new Date(ev.date);
      var h = d.getHours(); var m = d.getMinutes();
      t += h + '時';
      if (m > 0) t += m + '分';
      t += 'に、' + ev.country + 'の' + ev.title + '。';
    });
    t += '以上が予定されています。';
    queueSpeech(t, true);
  }
}

function queueSpeech(text, isHighPriority) {
  if (isHighPriority) {
    fxSpeechQueue.unshift(text);
  } else {
    fxSpeechQueue.push(text);
  }
}

function speakNext() {
  if (fxSpeechQueue.length === 0) return;
  var text = fxSpeechQueue.shift();
  fxIsSpeaking = true;
  
  var u = new SpeechSynthesisUtterance(text);
  u.lang = 'ja-JP';
  u.rate = 1.05; // 少しだけ速く
  u.pitch = 1.0;
  
  // 利用可能な音声リストから、最も高音質なものを探す（EdgeのNatural音声や、ChromeのGoogle音声）
  var voices = window.speechSynthesis.getVoices();
  var jaVoices = voices.filter(function(v) { return v.lang.indexOf('ja') !== -1; });
  if (jaVoices.length > 0) {
    // 1. Edgeの高音質クラウド音声 (Nanami, Keita 等) を最優先
    var bestVoice = jaVoices.find(function(v) { return v.name.indexOf('Natural') !== -1 || v.name.indexOf('Online') !== -1; });
    // 2. なければChrome標準のGoogle日本語音声を優先
    if (!bestVoice) bestVoice = jaVoices.find(function(v) { return v.name.indexOf('Google') !== -1; });
    // 3. なければ最初に見つかった日本語音声
    if (!bestVoice) bestVoice = jaVoices[0];
    
    u.voice = bestVoice;
  }
  
  u.onend = function() {
    fxIsSpeaking = false;
    // ちょっとだけ間を開ける
    setTimeout(function() {
      if (fxNewsOn && fxSpeechQueue.length > 0) speakNext();
    }, 1000);
  };
  u.onerror = function() {
    fxIsSpeaking = false;
  }
  
  window.speechSynthesis.speak(u);
}

function renderNewsList() {
  if (!el('fx-news-list')) return;
  var arr = Object.values(fxNewsLog).sort(function(a,b){ return b.time - a.time; });
  el('fx-news-list').innerHTML = arr.length ? arr.map(function(item) {
    var d = new Date(item.time);
    var h = pad(d.getHours()); var m = pad(d.getMinutes());
    var ic = item.type === 'alert' ? '📢' : '📰';
    var color = item.type === 'alert' ? 'var(--orange)' : 'var(--text)';
    return '<div class="fx-card" style="padding:10px;margin-bottom:6px;display:flex;gap:10px;align-items:flex-start">'
      + '<span style="font-size:12px;color:var(--muted);white-space:nowrap">' + h + ':' + m + '</span>'
      + '<div style="flex:1;font-size:12px;color:' + color + '">' + ic + ' ' + item.title + '</div>'
      + '</div>';
  }).join('') : '<div style="padding:20px;text-align:center;color:var(--muted)">まだデータがありません</div>';
}

/* グローバルに公開（HTML の onclick から呼ぶため） */
window.fxTab        = fxTab;
window.fxDir        = fxDir;
window.fxToggleForm = fxToggleForm;
window.fxAddTrade   = fxAddTrade;
window.fxDeleteTrade= fxDeleteTrade;
window.fxToggleAlert= fxToggleAlert;
window.fxTestSound  = fxTestSound;
window.fxToggleNews = fxToggleNews;
window.fxClearNewsLog = fxClearNewsLog;
window.fxReadTodaySchedule = fxReadTodaySchedule;
window.sxRender     = sxRender;
window.sxSetTf      = sxSetTf;
window.sxToggleDoc  = sxToggleDoc;
window.sxCloseDoc   = sxCloseDoc;

/* DOM 構築完了後に実行 */
document.addEventListener('DOMContentLoaded', function() {
  if (!document.getElementById('fxdesk')) return;
  renderJournal();
  sxRender();
  setInterval(tick, 1000);
});

}());
