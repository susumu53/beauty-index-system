/* Investment Dashboard v3 – Real prices via WP AJAX + Yahoo Finance (crumb auth) */
(function () {
    'use strict';
    if (typeof INVD_CONFIG === 'undefined') return;

    const CFG=INVD_CONFIG, SYMBOLS=CFG.symbols, IDS=Object.keys(SYMBOLS);

    function ema(d,p){if(!d||d.length<2)return(d||[]).slice();const k=2/(p+1),e=[d[0]];for(let i=1;i<d.length;i++)e.push(d[i]*k+e[i-1]*(1-k));return e;}
    function rsi(c,p=14){if(!c||c.length<p+2)return new Array((c||[]).length).fill(null);const out=new Array(p).fill(null);let ag=0,al=0;for(let i=1;i<=p;i++){const d=c[i]-c[i-1];ag+=Math.max(d,0);al+=Math.max(-d,0);}ag/=p;al/=p;out.push(al===0?100:100-100/(1+ag/al));for(let i=p+1;i<c.length;i++){const d=c[i]-c[i-1];ag=(ag*(p-1)+Math.max(d,0))/p;al=(al*(p-1)+Math.max(-d,0))/p;out.push(al===0?100:100-100/(1+ag/al));}return out;}
    function macd(c,f=12,s=26,sig=9){if(!c||c.length<s+sig)return{line:[],signal:[]};const ef=ema(c,f),es=ema(c,s),line=ef.map((v,i)=>v-es[i]),sl=ema(line.slice(s-1),sig);return{line,signal:new Array(s-1).fill(null).concat(sl)};}
    function bb(c,p=20,m=2,m2=3){const u=[],l=[],u3=[],l3=[],mid=[];if(!c)return{u,l,u3,l3,mid};for(let i=0;i<c.length;i++){if(i<p-1){u.push(null);l.push(null);u3.push(null);l3.push(null);mid.push(null);continue;}const sl=c.slice(i-p+1,i+1),mn=sl.reduce((a,b)=>a+b)/p,sd=Math.sqrt(sl.reduce((a,b)=>a+(b-mn)**2,0)/p);mid.push(mn);u.push(mn+m*sd);l.push(mn-m*sd);u3.push(mn+m2*sd);l3.push(mn-m2*sd);}return{u,l,u3,l3,mid};}

    /* ── Technical Theories ── */
    function findPivots(d,w=2){const ph=[],pl=[];for(let i=w;i<d.length-w;i++){let h=true,l=true;for(let j=1;j<=w;j++){if(d[i]<=d[i-j]||d[i]<=d[i+j])h=false;if(d[i]>=d[i-j]||d[i]>=d[i+j])l=false;}if(h)ph.push({i,v:d[i]});if(l)pl.push({i,v:d[i]});}return{ph,pl};}
    function getLines(p,n){if(p.length<2)return null;const l2=p[p.length-1],l1=p[p.length-2],m=(l2.v-l1.v)/(l2.i-l1.i),b=l2.v-m*l2.i;const pts=[];for(let i=0;i<n;i++)pts.push(i<l1.i?null:m*i+b);return{pts,m,lastV:m*(n-1)+b};}
    function detectDow(ph,pl){if(ph.length<2||pl.length<2)return"解析中 (データ蓄積中)";const h2=ph[ph.length-1],h1=ph[ph.length-2],l2=pl[pl.length-1],l1=pl[pl.length-2];if(h2.v>h1.v&&l2.v>l1.v)return"上昇トレンド構造";if(h2.v<h1.v&&l2.v<l1.v)return"下降トレンド構造";return"レンジ/転換中";}
    function checkGranville(p,e,pp,pe){if(!p||!e||!pp||!pe)return null;const up=e>pe;if(!up&&pp<pe&&p>e)return{t:"買い①",m:"突破"};if(up&&pp>pe&&p<e)return{t:"買い②",m:"押し目"};if(up&&p>e&&p<pp)return{t:"買い③",m:"接近"};if(!up&&p<e&&e-p>(e*0.005))return{t:"買い④",m:"自律反発"};if(up&&pp>pe&&p<e)return{t:"売り①",m:"突破"};if(!up&&pp<pe&&p>e)return{t:"売り②",m:"戻り売り"};if(!up&&p<e&&p>pp)return{t:"売り③",m:"接近"};if(up&&p>e&&p-e>(e*0.005))return{t:"売り④",m:"自律反落"};return null;}

    function calcSignals(closes){
        if(!closes||closes.length<20) return null;
        const n=closes.length-1,R=rsi(closes),M=macd(closes),B=bb(closes),E20=ema(closes,20),E50=ema(closes,50);
        const pNow=closes[n],pPrev=closes[n-1],e20=E20[n],e20P=E20[n-1],e50=E50[n],rNow=R[n],mN=M.line[n],mS=M.signal[n];
        
        const pivots=findPivots(closes, 2);
        const resLine=getLines(pivots.ph, closes.length), supLine=getLines(pivots.pl, closes.length);
        const dow=detectDow(pivots.ph, pivots.pl);
        const gran=checkGranville(pNow, e20, pPrev, e20P);
        
        const bbW=(B.u[n]-B.l[n])/B.mid[n]*100;
        const isRange=bbW<0.7; // Slightly more inclusive for range
        
        let brk=null;
        if(resLine&&pPrev<=resLine.pts[n-1]&&pNow>resLine.pts[n])brk={t:"上放れ",d:"Resistance Break"};
        if(supLine&&pPrev>=supLine.pts[n-1]&&pNow<supLine.pts[n])brk={t:"下放れ",d:"Support Break"};

        const wemof=pNow>B.u3[n]?{t:"逆張り売り",m:"3σ突破(過熱)"}:pNow<B.l3[n]?{t:"逆張り買い",m:"3σ突破(暴落)"}:null;
        
        const rScore=rNow!=null?(rNow<30?1:rNow>70?-1:(50-rNow)/25):0;
        const mScore=mS!=null?(mN>mS?0.7:-0.7):0;
        const bScore=B.l[n]!=null?(pNow<B.l[n]?1:pNow>B.u[n]?-1:(B.mid[n]-pNow)/((B.u[n]-B.mid[n])||0.001)):0;
        const eScore=e20>e50?0.5:-0.5;

        return{
            rsiArr:R,macdLine:M.line,macdSig:M.signal,bbU:B.u,bbL:B.l,bbU3:B.u3,bbL3:B.l3,e20:E20,e50:E50,
            resLine:resLine?.pts,supLine:supLine?.pts,
            rNow,mDiff:mS!=null?mN-mS:0,bbPos:B.l[n]!=null?(pNow-B.l[n])/(B.u[n]-B.l[n])*100:50,
            dow,gran,isRange,brk,bbW,wemof,
            composite:rScore*30+mScore*25+bScore*20+eScore*15+(brk?10:0)+(wemof?15:0),
            rScore,mScore,bScore,eScore
        };
    }

    function verdict(s){if(s>40)return{t:'強い買い',c:'#3fb950'};if(s>15)return{t:'買い',c:'#56d364'};if(s>-15)return{t:'様子見',c:'#7d8590'};if(s>-40)return{t:'売り',c:'#f0883e'};return{t:'強い売り',c:'#f85149'};}
    function fmtPrice(v,info){if(v==null)return'-';if(info.dec==0)return info.pfx+Math.round(v).toLocaleString('ja-JP');return info.pfx+(+v).toFixed(info.dec);}
    function badgeCls(sc){if(sc>.2)return['invd-b-buy','買い'];if(sc<-.2)return['invd-b-sell','売り'];return['invd-b-neutral','中立'];}
    function sl(arr,n=65){return arr?arr.slice(-n):[];}
    function baseOpts(){return{responsive:true,maintainAspectRatio:false,animation:{duration:300},plugins:{legend:{display:false},tooltip:{enabled:false}},elements:{point:{radius:0},line:{borderCapStyle:'round'}}};}
    function makeScales(isDark,min,max,ticks=3){const gc=isDark?'rgba(255,255,255,.05)':'rgba(0,0,0,.05)',tc=isDark?'rgba(255,255,255,.3)':'rgba(0,0,0,.3)';return{x:{display:false},y:{position:'right',min,max,grid:{color:gc,drawBorder:false},ticks:{font:{size:9},color:tc,maxTicksLimit:ticks},border:{display:false}}};}

    function initInstance(wrap){
        const isDark=wrap.dataset.theme!=='light', interval=parseInt(wrap.dataset.interval,10)||15000;
        const labels=Array.from({length:65},(_,i)=>i);
        let curId=IDS[0], prices={}, history={}, charts={}, timer=null, errorEl=null, lastSignals=new Set();

        function addLog(badge, msg, color){
            const log=wrap.querySelector('#invd-signal-log'); if(!log)return;
            const empty=log.querySelector('.invd-log-empty'); if(empty)empty.remove();
            const time=new Date().toLocaleTimeString('ja-JP',{hour:'2-digit',minute:'2-digit'});
            const item=document.createElement('div'); item.className='invd-log-item';
            item.innerHTML=`<span class="invd-log-time">${time}</span><span class="invd-log-badge" style="background:${color}">${badge}</span><span class="invd-log-msg">${msg}</span>`;
            log.prepend(item);
            if(log.children.length>20)log.lastElementChild.remove();
        }

        function showError(msg){
            if(!errorEl){errorEl=document.createElement('div');errorEl.className='invd-error';wrap.querySelector('#invd-tabs').after(errorEl);}
            errorEl.textContent='⚠ '+msg; errorEl.style.display='block';
            const s=wrap.querySelector('#invd-status'); if(s){s.textContent='エラー';s.style.color='#f85149';}
        }
        function clearError(){if(errorEl)errorEl.style.display='none';}
        function setStatus(msg){const s=wrap.querySelector('#invd-status');if(s){s.textContent=msg;s.style.color='';}}

        async function ajaxGet(action,extra={}){
            const p=new URLSearchParams({action,nonce:CFG.nonce,...extra});
            const r=await fetch(CFG.ajaxUrl+'?'+p,{cache:'no-store'});
            if(!r.ok)throw new Error('HTTP '+r.status);
            const j=await r.json();
            if(!j.success)throw new Error(j.data?.message||'APIエラー');
            return j.data;
        }

        async function fetchPrices(){
            try{
                const data=await ajaxGet('invd_prices');
                prices=data; clearError(); updatePriceDisplay();
                refreshCharts(false);
                const el=wrap.querySelector('#invd-updated');
                if(el)el.textContent='最終更新: '+new Date().toLocaleTimeString('ja-JP');
                setStatus('リアルタイム');
            }catch(e){showError('価格取得失敗: '+e.message);}
        }

        async function fetchHistory(id){
            if(history[id])return true;
            try{
                setStatus('チャート読み込み中...');
                const data=await ajaxGet('invd_history',{id});
                history[id]=data;
                if(prices[id])history[id].closes.push(prices[id].price);
                clearError(); return true;
            }catch(e){showError('チャートデータ取得失敗: '+e.message);return false;}
        }

        function updatePriceDisplay(){
            const info=SYMBOLS[curId], p=prices[curId];
            if(!p||!info)return;
            wrap.querySelector('#invd-sym').textContent=info.sym;
            wrap.querySelector('#invd-pval').textContent=fmtPrice(p.price,info);
            const pchg=wrap.querySelector('#invd-pchg');
            pchg.textContent=(p.changePct>=0?'+':'')+p.changePct.toFixed(2)+'%';
            pchg.className='invd-pchg '+(p.changePct>=0?'invd-up':'invd-dn');
        }

        function scanHistorySignals(){
            const closes=history[curId]?.closes; if(!closes||closes.length<20)return;
            const log=wrap.querySelector('#invd-signal-log'); if(log)log.innerHTML='<div class="invd-log-empty">スキャン中...</div>';
            
            // Scan last 100 candles for signals
            const depth = Math.min(closes.length - 1, 100);
            let found = false;
            for(let i=closes.length-depth; i<=closes.length; i++){
                if(i<20)continue;
                const sub=closes.slice(0, i);
                const s=calcSignals(sub); if(!s)continue;
                const sk=sub.length+curId;
                if(s.brk && !lastSignals.has(sk+"brk")){
                    addLog(s.brk.t, `${SYMBOLS[curId].label}: トレンドラインをブレイク`, "#388bfd");
                    lastSignals.add(sk+"brk"); found = true;
                }
                if(s.gran && !lastSignals.has(sk+"gran"+s.gran.t)){
                    addLog(s.gran.t, `${SYMBOLS[curId].label}: ${s.gran.m} (グランビル)`, s.gran.t.includes('買い')?"#238636":"#da3633");
                    lastSignals.add(sk+"gran"+s.gran.t); found = true;
                }
                if(s.wemof && !lastSignals.has(sk+"wemof"+s.wemof.t)){
                    addLog('WEMOF', `${SYMBOLS[curId].label}: ${s.wemof.t} - ${s.wemof.m}`, s.wemof.t.includes('買い')?"#3fb950":"#f85149");
                    lastSignals.add(sk+"wemof"+s.wemof.t); found = true;
                }
            }
            if(!found && log) {
                log.innerHTML='<div class="invd-log-empty">直近のシグナルはありません (待機中...)</div>';
            }
        }

        function refreshCharts(rebuild){
            try {
                let closes=history[curId]?.closes;
                if(!closes||closes.length<20) {
                    setStatus('データ不足 (' + (closes?.length||0) + '件)');
                    return; 
                }

                // Use current price as the "last forming bar" for real-time feel
                if(prices[curId]) {
                    closes = [...closes];
                    closes[closes.length-1] = prices[curId].price;
                }
                
                if(rebuild) scanHistorySignals();

                const sigs=calcSignals(closes); if(!sigs)return;
                
                const v=verdict(sigs.composite), sc=Math.max(-100,Math.min(100,sigs.composite));
                const elScore=wrap.querySelector('#invd-score'), elVerdict=wrap.querySelector('#invd-verdict'), elMeter=wrap.querySelector('#invd-meter');
                if(elScore){ elScore.textContent=(sc>0?'+':'')+sc.toFixed(0); elScore.style.color=v.c; }
                if(elVerdict){ elVerdict.textContent=v.t; elVerdict.style.color=v.c; }
                if(elMeter){ elMeter.style.width=((sc+100)/2)+'%'; elMeter.style.background=v.c; }

                const ph=wrap.querySelector('#invd-market-phase'), ds=wrap.querySelector('#invd-dow-status'), rs=wrap.querySelector('#invd-range-status'), ws=wrap.querySelector('#invd-wemof-status');
                if(ph){
                    ph.textContent=sigs.isRange?'レンジ相場':(sigs.composite>20?'上昇トレンド':sigs.composite<-20?'下降トレンド':'均衡状態');
                    ph.style.background=sigs.isRange?'#7d8590':(sigs.composite>20?'#238636':sigs.composite<-20?'#da3633':'#1f6feb');
                }
                if(ds) ds.textContent=sigs.dow;
                if(rs) rs.textContent=sigs.isRange?'低ボラティリティ (レンジ)':'トレンド進行中 ('+(Number(sigs.bbW)||0).toFixed(1)+'%)';
                if(ws) {
                    ws.textContent=sigs.wemof?sigs.wemof.t+' ('+sigs.wemof.m+')':'正常値 (±3σ内)';
                    ws.style.color=sigs.wemof?(sigs.wemof.t.includes('売り')?'#f85149':'#3fb950'):'';
                }

                const tm=isDark?'#e6edf3':'#1a1a2e';
                const rC=sigs.rNow<30?'#3fb950':sigs.rNow>70?'#f85149':tm;
                const mC=sigs.mDiff>0?'#3fb950':'#f85149';
                const bC=sigs.bbPos<20?'#3fb950':sigs.bbPos>80?'#f85149':tm;
                const [rb,rl]=badgeCls(sigs.rScore),[mb,ml]=badgeCls(sigs.mScore),[bb2,bl]=badgeCls(sigs.bScore),[eb,el]=badgeCls(sigs.eScore);
                
                const grid=wrap.querySelector('#invd-ind-grid');
                if(grid){
                    grid.innerHTML=`
                      <div class="invd-ind-card"><div class="invd-ind-name">RSI (14)</div><div class="invd-ind-val" style="color:${rC}">${sigs.rNow!=null?sigs.rNow.toFixed(1):'-'}</div><span class="invd-ind-badge ${rb}">${rl}</span></div>
                      <div class="invd-ind-card"><div class="invd-ind-name">MACD乖離</div><div class="invd-ind-val" style="color:${mC}">${sigs.mDiff>0?'▲':'▼'} ${Math.abs(sigs.mDiff).toFixed(3)}</div><span class="invd-ind-badge ${mb}">${ml}</span></div>
                      <div class="invd-ind-card"><div class="invd-ind-name">BB位置</div><div class="invd-ind-val" style="color:${bC}">${sigs.bbPos.toFixed(0)}%</div><span class="invd-ind-badge ${bb2}">${bl}</span></div>
                      <div class="invd-ind-card"><div class="invd-ind-name">EMA乖離</div><div class="invd-ind-val" style="color:${sigs.eScore>0?'#3fb950':'#f85149'}">${sigs.eScore>0?'強気':'弱気'}</div><span class="invd-ind-badge ${eb}">${el}</span></div>`;
                }

                // Signal Logging logic
                const sigKey=closes.length+curId;
                if(sigs.brk && !lastSignals.has(sigKey+"brk")){
                    addLog(sigs.brk.t, `${SYMBOLS[curId].label}: トレンドラインをブレイクしました`, "#388bfd");
                    lastSignals.add(sigKey+"brk");
                    wrap.classList.add('invd-breakout-flash'); setTimeout(()=>wrap.classList.remove('invd-breakout-flash'),3000);
                }
                if(sigs.gran && !lastSignals.has(sigKey+"gran"+sigs.gran.t)){
                    addLog(sigs.gran.t, `${SYMBOLS[curId].label}: ${sigs.gran.m} (グランビル)`, sigs.gran.t.includes('買い')?"#238636":"#da3633");
                    lastSignals.add(sigKey+"gran"+sigs.gran.t);
                }
                if(sigs.wemof && !lastSignals.has(sigKey+"wemof"+sigs.wemof.t)){
                    addLog('WEMOF', `${SYMBOLS[curId].label}: ${sigs.wemof.t} - ${sigs.wemof.m}`, sigs.wemof.t.includes('買い')?"#3fb950":"#f85149");
                    lastSignals.add(sigKey+"wemof"+sigs.wemof.t);
                }
                if(lastSignals.size>100)lastSignals.clear();

                if(rebuild)buildCharts(sigs); else updateChartData(sigs);
            } catch(e) {
                showError('UI描画エラー: ' + e.message);
                console.error(e);
            }
        }

        function buildCharts(sigs){
            ['price','rsi','macd'].forEach(k=>{if(charts[k])charts[k].destroy();});
            const closes=history[curId]?.closes||[];
            charts.price=new Chart(wrap.querySelector('#invd-price'),{type:'line',data:{labels,datasets:[
                {data:sl(closes),   borderColor:'#79c0ff',              borderWidth:1.5,fill:false,tension:.3,z:10},
                {data:sl(sigs.bbU), borderColor:'rgba(191,145,243,.25)',borderWidth:1,borderDash:[3,3],fill:false,tension:.3},
                {data:sl(sigs.bbL), borderColor:'rgba(191,145,243,.25)',borderWidth:1,borderDash:[3,3],fill:false,tension:.3},
                {data:sl(sigs.bbU3),borderColor:'rgba(248,81,73,.15)',  borderWidth:1,borderDash:[2,2],fill:false,tension:.3},
                {data:sl(sigs.bbL3),borderColor:'rgba(63,185,80,.15)', borderWidth:1,borderDash:[2,2],fill:false,tension:.3},
                {data:sl(sigs.e20), borderColor:'rgba(255,166,87,.6)',  borderWidth:1,fill:false,tension:.3},
                {data:sl(sigs.e50), borderColor:'rgba(248,81,73,.5)',   borderWidth:1,fill:false,tension:.3},
                {data:sl(sigs.resLine), borderColor:'#f85149',         borderWidth:1,borderDash:[5,5],fill:false,tension:0,pointRadius:0},
                {data:sl(sigs.supLine), borderColor:'#3fb950',         borderWidth:1,borderDash:[5,5],fill:false,tension:0,pointRadius:0},
            ]},options:{...baseOpts(),scales:makeScales(isDark)}});
            charts.rsi=new Chart(wrap.querySelector('#invd-rsi'),{type:'line',data:{labels,datasets:[
                {data:sl(sigs.rsiArr),borderColor:'#ffa657',borderWidth:1.5,fill:false,tension:.3},
                {data:Array(65).fill(70),borderColor:'rgba(248,81,73,.3)',borderWidth:1,borderDash:[4,4],fill:false},
                {data:Array(65).fill(30),borderColor:'rgba(63,185,80,.3)', borderWidth:1,borderDash:[4,4],fill:false},
            ]},options:{...baseOpts(),scales:makeScales(isDark,0,100,3)}});
            charts.macd=new Chart(wrap.querySelector('#invd-macd'),{type:'line',data:{labels,datasets:[
                {data:sl(sigs.macdLine),borderColor:'#39d353',borderWidth:1.5,fill:false,tension:.3},
                {data:sl(sigs.macdSig), borderColor:'#f85149',borderWidth:1,  fill:false,tension:.3},
            ]},options:{...baseOpts(),scales:makeScales(isDark)}});
        }

        function updateChartData(sigs){
            if(!charts.price)return;
            const closes=history[curId]?.closes||[];
            charts.price.data.datasets[0].data=sl(closes);
            charts.price.data.datasets[1].data=sl(sigs.bbU);
            charts.price.data.datasets[2].data=sl(sigs.bbL);
            charts.price.data.datasets[3].data=sl(sigs.bbU3);
            charts.price.data.datasets[4].data=sl(sigs.bbL3);
            charts.price.data.datasets[5].data=sl(sigs.e20);
            charts.price.data.datasets[6].data=sl(sigs.e50);
            charts.price.data.datasets[7].data=sl(sigs.resLine);
            charts.price.data.datasets[8].data=sl(sigs.supLine);
            charts.price.update('none');
            charts.rsi.data.datasets[0].data=sl(sigs.rsiArr); charts.rsi.update('none');
            charts.macd.data.datasets[0].data=sl(sigs.macdLine);
            charts.macd.data.datasets[1].data=sl(sigs.macdSig); charts.macd.update('none');
        }


        function buildTabs(){
            wrap.querySelector('#invd-tabs').innerHTML=IDS.map(id=>
                `<button class="invd-tab${id===curId?' active':''}" data-id="${id}">${SYMBOLS[id].label}</button>`
            ).join('');
            wrap.querySelectorAll('.invd-tab').forEach(btn=>{
                btn.addEventListener('click',async()=>{
                    curId=btn.dataset.id; buildTabs(); updatePriceDisplay();
                    const ok=await fetchHistory(curId); if(ok)refreshCharts(true);
                });
            });
        }

        async function boot(){
            buildTabs(); setStatus('接続中...');
            await fetchPrices();
            const ok=await fetchHistory(curId);
            if(ok)refreshCharts(true);
            timer=setInterval(fetchPrices,interval);
            setInterval(async()=>{
                const ok=await fetchHistory(curId);
                if(ok) refreshCharts(false);
            }, 60000); // Sync history every 60s
        }
        boot().catch(e=>showError(e.message));
    }

    function bootAll(){document.querySelectorAll('.invd-wrap').forEach(initInstance);}
    if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',bootAll);}else{bootAll();}
})();
