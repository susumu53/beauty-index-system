/* FX Signal Chart v5 */
(function(){
'use strict';

/* ── パターン検出 ─────────────────────────────── */
function detectPatterns(cs){
  const out=[];
  for(let i=2;i<cs.length;i++){
    const c=cs[i],p=cs[i-1],pp=cs[i-2];
    const body=Math.abs(c.close-c.open),range=c.high-c.low;
    if(range<1e-9)continue;
    const upW=c.high-Math.max(c.open,c.close),dnW=Math.min(c.open,c.close)-c.low;
    const pb=Math.abs(p.close-p.open);
    const bu=c.close>c.open,pbu=p.close>p.open,ppbu=pp.close>pp.open;
    if(body<range*.08){out.push({i,t:'n',name:'十字線(Doji)',desc:'方向感なし・転換注意',s:1});continue;}
    if(dnW>body*2.2&&upW<body*.5&&!bu){out.push({i,t:!pbu?'b':'n',name:'ハンマー',desc:'下降末期の底打ち',s:2});continue;}
    if(upW>body*2.2&&dnW<body*.5&&bu){out.push({i,t:'s',name:'シューティングスター',desc:'上昇末期の天井',s:2});continue;}
    if(bu&&!pbu&&c.close>p.open&&c.open<p.close&&body>pb*1.05){out.push({i,t:'b',name:'陽の包み足',desc:'強い上昇転換',s:3});continue;}
    if(!bu&&pbu&&c.close<p.open&&c.open>p.close&&body>pb*1.05){out.push({i,t:'s',name:'陰の包み足',desc:'強い下降転換',s:3});continue;}
    if(!ppbu&&Math.abs(p.close-p.open)<(p.high-p.low)*.35&&bu&&c.close>pp.open+(pp.open-pp.close)*.5){out.push({i,t:'b',name:'明けの明星',desc:'強力な底打ち3本線',s:3});continue;}
    if(ppbu&&Math.abs(p.close-p.open)<(p.high-p.low)*.35&&!bu&&c.close<pp.open-(pp.close-pp.open)*.5){out.push({i,t:'s',name:'宵の明星',desc:'強力な天井3本線',s:3});continue;}
    if(bu&&pbu&&ppbu&&c.open>p.open&&p.open>pp.open&&upW<body*.3){out.push({i,t:'b',name:'赤三兵',desc:'連続上昇・強気継続',s:2});continue;}
    if(!bu&&!pbu&&!ppbu&&c.open<p.open&&p.open<pp.open&&dnW<body*.3){out.push({i,t:'s',name:'黒三兵',desc:'連続下降・弱気継続',s:2});continue;}
    const a5=cs.slice(Math.max(0,i-5),i).reduce((s,x)=>s+Math.abs(x.close-x.open),0)/5;
    if(bu&&body>range*.78&&c.close>p.high&&body>a5*1.8)out.push({i,t:'b',name:'大陽線ブレイク',desc:'上方ブレイク・強モメンタム',s:3});
    else if(!bu&&body>range*.78&&c.close<p.low&&body>a5*1.8)out.push({i,t:'s',name:'大陰線ブレイク',desc:'下方ブレイク・強モメンタム',s:3});
  }
  return out;
}

function pivots(cs,lb){lb=lb||3;const H=[],L=[];for(let i=lb;i<cs.length-lb;i++){let hi=true,lo=true;for(let j=i-lb;j<=i+lb;j++){if(j===i)continue;if(cs[j].high>=cs[i].high)hi=false;if(cs[j].low<=cs[i].low)lo=false;}if(hi)H.push({i,p:cs[i].high});if(lo)L.push({i,p:cs[i].low});}return{H,L};}

function buildTL(cs){
  const{H,L}=pivots(cs,3),n=cs.length,lines=[];
  function tryLine(pts,type){for(let a=0;a<pts.length-1;a++)for(let b=a+1;b<pts.length;b++){if(pts[b].i-pts[a].i<4)continue;const sl=(pts[b].p-pts[a].p)/(pts[b].i-pts[a].i);let ok=true;for(let k=pts[a].i;k<n;k++){const pr=pts[a].p+sl*(k-pts[a].i);if(type==='R'&&cs[k].high>pr*1.001){ok=false;break;}if(type==='S'&&cs[k].low<pr*.999){ok=false;break;}}if(ok)lines.push({type,sl,x1:pts[a].i,p1:pts[a].p,x2:n-1,p2:pts[a].p+sl*(n-1-pts[a].i)});}}
  tryLine(H,'R');tryLine(L,'S');lines.sort((a,b)=>Math.abs(b.sl)-Math.abs(a.sl));return lines.slice(0,8);
}

function buildSR(cs){
  const{H,L}=pivots(cs,2),all=[...H.map(h=>({p:h.p,t:'R'})),...L.map(l=>({p:l.p,t:'S'}))];
  const avg=cs.reduce((s,c)=>s+c.high-c.low,0)/cs.length,m=[];
  all.forEach(pt=>{const ex=m.find(x=>Math.abs(x.p-pt.p)<avg*3);if(ex){ex.n++;ex.p=(ex.p+pt.p)/2;}else m.push({...pt,n:1});});
  return m.filter(x=>x.n>=2).sort((a,b)=>b.n-a.n).slice(0,8);
}

/* ── 描画 ────────────────────────────────────── */
const P={t:22,r:82,b:36,l:8};
function cx(i,n,cw){return P.l+i*cw+cw/2;}
function py(p,mn,mx,H){return P.t+(mx-p)/(mx-mn)*(H-P.t-P.b);}

function drawChart(canvas,cs,sigs,tls,srs,opts){
  const ctx=canvas.getContext('2d');
  const W=canvas.width,H=canvas.height,n=cs.length;
  if(!n)return;
  const cw=(W-P.l-P.r)/n;
  const dark=matchMedia('(prefers-color-scheme:dark)').matches;
  const mn=Math.min(...cs.map(c=>c.low))*.9994,mx=Math.max(...cs.map(c=>c.high))*1.0006;
  const tc=dark?'rgba(200,198,192,.85)':'rgba(50,50,48,.85)';
  ctx.clearRect(0,0,W,H);
  // grid
  for(let s=0;s<=6;s++){const y=P.t+(H-P.t-P.b)*s/6;ctx.strokeStyle=dark?'rgba(255,255,255,.04)':'rgba(0,0,0,.05)';ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(W-P.r,y);ctx.stroke();const pr=mx-(mx-mn)*s/6;ctx.fillStyle=tc;ctx.font='10px sans-serif';ctx.textAlign='left';ctx.fillText(pr.toFixed(opts.dec),W-P.r+4,y+3.5);}
  // SR
  if(opts.sr)srs.forEach(sr=>{const y=py(sr.p,mn,mx,H);ctx.strokeStyle=sr.t==='R'?'rgba(226,75,74,.4)':'rgba(55,138,221,.4)';ctx.lineWidth=1;ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(W-P.r,y);ctx.stroke();});
  ctx.setLineDash([]);
  // TL
  if(opts.trend)tls.forEach(tl=>{ctx.strokeStyle=tl.type==='R'?'rgba(226,75,74,.8)':'rgba(55,138,221,.8)';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(cx(tl.x1,n,cw),py(tl.p1,mn,mx,H));ctx.lineTo(cx(tl.x2,n,cw),py(tl.p2,mn,mx,H));ctx.stroke();});
  // candles
  cs.forEach((c,idx)=>{const x=cx(idx,n,cw),bu=c.close>=c.open,col=bu?(dark?'#5DCAA5':'#1D9E75'):(dark?'#F0997B':'#D85A30');ctx.strokeStyle=col;ctx.lineWidth=1;ctx.setLineDash([]);ctx.beginPath();ctx.moveTo(x,py(c.high,mn,mx,H));ctx.lineTo(x,py(c.low,mn,mx,H));ctx.stroke();const bw=Math.max(1,cw*.65),by=Math.min(py(c.open,mn,mx,H),py(c.close,mn,mx,H)),bh=Math.max(1,Math.abs(py(c.open,mn,mx,H)-py(c.close,mn,mx,H)));ctx.fillStyle=col;ctx.fillRect(x-bw/2,by,bw,bh);if(bh>2)ctx.strokeRect(x-bw/2,by,bw,bh);});
  // signals
  if(opts.signals)sigs.forEach(sig=>{const c=cs[sig.i];if(!c)return;const x=cx(sig.i,n,cw);ctx.setLineDash([]);if(sig.t==='b'){const y=py(c.low,mn,mx,H)+13;ctx.fillStyle='#1D9E75';ctx.beginPath();ctx.moveTo(x,y-11);ctx.lineTo(x-6,y);ctx.lineTo(x+6,y);ctx.closePath();ctx.fill();}else if(sig.t==='s'){const y=py(c.high,mn,mx,H)-13;ctx.fillStyle='#D85A30';ctx.beginPath();ctx.moveTo(x,y+11);ctx.lineTo(x-6,y);ctx.lineTo(x+6,y);ctx.closePath();ctx.fill();}else{ctx.fillStyle='#888780';ctx.beginPath();ctx.arc(x,py((c.high+c.low)/2,mn,mx,H),4,0,Math.PI*2);ctx.fill();}});
  // x-axis
  ctx.fillStyle=tc;ctx.textAlign='center';ctx.font='10px sans-serif';
  const step=Math.max(1,Math.floor(n/9));
  for(let i=0;i<n;i+=step){const t=cs[i].time||'',x=cx(i,n,cw);ctx.fillText(t.slice(5,10),x,H-20);if(t.length>10)ctx.fillText(t.slice(11,16),x,H-8);}
}

/* ── ウィジェット ─────────────────────────────── */
function initWidget(el){
  let sym=el.dataset.sym||'USD/JPY',tf=el.dataset.tf||'15min';
  const h=parseInt(el.dataset.h||'440',10),ar=parseInt(el.dataset.ar||'60',10),sp=el.dataset.sp!=='0';
  const cv=el.querySelector('.fsc-cv'),ld=el.querySelector('.fsc-ld'),er=el.querySelector('.fsc-er'),sl=el.querySelector('.fsc-slist');
  const cfg=window.fscCfg||{};
  const ins=cfg.instrs||{};
  let cs=[],sigs=[],tls=[],srs=[],dec=ins[sym]?.dec??5,cdT=null,cd=ar;
  const opts={trend:true,sr:true,signals:true,dec};

  function resize(){cv.width=cv.parentElement.clientWidth;cv.height=h;if(cs.length)drawChart(cv,cs,sigs,tls,srs,opts);}
  function sv(k,v){const e=el.querySelector('[data-s="'+k+'"]');if(e)e.textContent=v;}

  function updateStats(){
    if(!cs.length)return;
    const last=cs[cs.length-1],prev=cs[cs.length-2]||last;
    const chg=last.close-prev.close,pct=prev.close?(chg/prev.close*100).toFixed(2):'0.00';
    const ma=cs.slice(-10).reduce((s,c)=>s+c.close,0)/Math.min(10,cs.length);
    const ls=sigs.length?sigs[sigs.length-1]:null;
    sv('nm',ins[sym]?.label||sym);sv('px',last.close.toFixed(dec));sv('hi',last.high.toFixed(dec));sv('lo',last.low.toFixed(dec));sv('ts',last.time.slice(5,16));
    const ce=el.querySelector('[data-s="ch"]');if(ce){ce.textContent=(chg>=0?'+':'')+chg.toFixed(dec)+' ('+pct+'%)';ce.className='fsc-sv '+(chg>=0?'up':'dn');}
    const se=el.querySelector('[data-s="sg"]');if(se){se.textContent=ls?(ls.t==='b'?'▲ 買い':ls.t==='s'?'▼ 売り':'→ 中立'):'なし';se.className='fsc-sv '+(ls?.t==='b'?'up':ls?.t==='s'?'dn':'');}
    const te=el.querySelector('[data-s="tr"]');if(te){const up=last.close>ma;te.textContent=up?'↑ 上昇':'↓ 下降';te.className='fsc-sv '+(up?'up':'dn');}
  }

  function updateSig(){
    if(!sl)return;
    const rec=sigs.slice(-12).reverse();
    if(!rec.length){sl.innerHTML='<p class="fsc-nsp">シグナルなし</p>';return;}
    sl.innerHTML=rec.map(s=>{const c=cs[s.i];const cls=s.t==='b'?'sb':s.t==='s'?'ss':'sn';return`<div class="fsc-si fsc-${cls}"><span class="fsc-sd"></span><span class="fsc-sn">${s.name}</span><span class="fsc-sdesc">${s.desc}</span><span class="fsc-sstr">${'●'.repeat(s.s||1)}</span><span class="fsc-stime">${c?.time?.slice(5,16)||''}</span></div>`;}).join('');
  }

  async function load(show=true){
    if(show){ld.style.display='flex';er.style.display='none';}
    const url=(cfg.rest||'/wp-json/fx-signal-chart/v1/candles')+'?symbol='+encodeURIComponent(sym)+'&interval='+encodeURIComponent(tf)+'&limit=80';
    try{
      const r=await fetch(url,{headers:{'Accept':'application/json'}});
      const d=await r.json();
      if(!d.success)throw new Error(d.message||'データ取得失敗');
      cs=d.candles;dec=d.dec??ins[sym]?.dec??5;opts.dec=dec;
      sigs=detectPatterns(cs);tls=buildTL(cs);srs=buildSR(cs);
      ld.style.display='none';resize();updateStats();updateSig();
      sv('pv',d.provider||'Yahoo Finance');
    }catch(e){
      ld.style.display='none';er.style.display='flex';
      er.innerHTML='<div style="text-align:center;padding:20px"><div style="font-size:36px;margin-bottom:8px">⚠️</div><div style="font-weight:500;margin-bottom:6px;font-size:14px">データを取得できませんでした</div><div style="font-size:12px;opacity:.75;margin-bottom:14px;max-width:360px">'+e.message+'</div><button onclick="this.closest(\'.fsc-w\').querySelector(\'.fsc-rbtn\').click()" style="padding:5px 18px;border:1px solid currentColor;border-radius:6px;background:transparent;cursor:pointer;font-size:12px">再試行</button></div>';
    }
  }

  function startCD(){if(cdT)clearInterval(cdT);if(!ar)return;cd=ar;cdT=setInterval(()=>{cd--;const e=el.querySelector('[data-s="cd"]');if(e)e.textContent=cd;if(cd<=0){cd=ar;load(false);}},1000);}

  el.querySelectorAll('.fsc-syb').forEach(b=>b.addEventListener('click',()=>{el.querySelectorAll('.fsc-syb').forEach(x=>x.classList.remove('on'));b.classList.add('on');sym=b.dataset.sym;dec=parseInt(b.dataset.dec||'5',10);opts.dec=dec;load();cd=ar;}));
  el.querySelectorAll('.fsc-tfb').forEach(b=>b.addEventListener('click',()=>{el.querySelectorAll('.fsc-tfb').forEach(x=>x.classList.remove('on'));b.classList.add('on');tf=b.dataset.tf;load();cd=ar;}));
  el.querySelectorAll('input[data-o]').forEach(c=>c.addEventListener('change',()=>{opts[c.dataset.o]=c.checked;drawChart(cv,cs,sigs,tls,srs,opts);}));
  el.querySelector('.fsc-rbtn')?.addEventListener('click',()=>{load();cd=ar;});
  window.addEventListener('resize',resize);
  resize();load();startCD();
}

function boot(){document.querySelectorAll('.fsc-w').forEach(initWidget);}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot):boot();
})();
