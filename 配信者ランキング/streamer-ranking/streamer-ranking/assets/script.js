(function () {
    'use strict';

    var allData = [];
    var sortState = { col: 'rank', dir: 'asc' };
    var filterState = 'all';

    /* ---- helpers ---- */
    function fmt(n) {
        if (n === null || n === undefined || n === '') return '—';
        n = parseFloat(n);
        if (isNaN(n)) return '—';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'B';
        if (n >= 1)    return n.toFixed(1) + 'M';
        return (n * 1000).toFixed(0) + 'K';
    }

    function fmtV(n) {
        if (n === null || n === undefined || n === '') return '—';
        n = parseFloat(n);
        if (isNaN(n)) return '—';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'M';
        return Math.round(n) + 'K';
    }

    function esc(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    /* ---- render ---- */
    function renderTable() {
        var data = allData.filter(function (d) {
            return filterState === 'all' || d.platform === filterState;
        });

        var col = sortState.col;
        var dir = sortState.dir === 'asc' ? 1 : -1;

        data.sort(function (a, b) {
            var av = a[col], bv = b[col];
            if (typeof av === 'string') return dir * String(av).localeCompare(String(bv));
            return dir * ((parseFloat(av) || 0) - (parseFloat(bv) || 0));
        });

        var tbody = document.getElementById('sr-tbody');
        if (!tbody) return;

        tbody.innerHTML = data.map(function (d, i) {
            var rank = i + 1;
            var rankClass = rank <= 3 ? ' sr-rank-' + rank : '';
            var platform = esc(d.platform || '');
            var badgeClass = platform === 'Twitch' ? 'sr-badge-twitch' : 'sr-badge-youtube';
            return '<tr>' +
                '<td class="sr-rank' + rankClass + '">' + rank + '</td>' +
                '<td class="sr-name">' + esc(d.name || '') + '</td>' +
                '<td><span class="sr-badge ' + badgeClass + '">' + platform + '</span></td>' +
                '<td class="sr-num-cell">' + fmt(d.followers) + '</td>' +
                '<td class="sr-num-cell">' + fmtV(d.peak_viewers) + '</td>' +
                '<td class="sr-category">' + esc(d.category || '') + '</td>' +
                '</tr>';
        }).join('');
    }

    /* ---- sort icons ---- */
    function updateSortIcons(col, dir) {
        var headers = document.querySelectorAll('.sr-sortable');
        for (var i = 0; i < headers.length; i++) {
            var th = headers[i];
            var c = th.getAttribute('data-col');
            var span = th.querySelector('.sr-sort-icon');
            if (!span) {
                span = document.createElement('span');
                span.className = 'sr-sort-icon';
                th.appendChild(span);
            }
            if (c === col) {
                span.textContent = dir === 'asc' ? ' ↑' : ' ↓';
                span.classList.add('active');
            } else {
                span.textContent = ' ↕';
                span.classList.remove('active');
            }
        }
    }

    /* ---- sort handler ---- */
    function handleSort(e) {
        var th = e.currentTarget;
        var col = th.getAttribute('data-col');
        if (!col) return;
        if (sortState.col === col) {
            sortState.dir = sortState.dir === 'asc' ? 'desc' : 'asc';
        } else {
            sortState.col = col;
            sortState.dir = (col === 'followers' || col === 'peak_viewers') ? 'desc' : 'asc';
        }
        updateSortIcons(sortState.col, sortState.dir);
        renderTable();
    }

    /* ---- filter ---- */
    window.srFilterPlatform = function (p) {
        filterState = p;
        var btns = document.querySelectorAll('.sr-btn');
        for (var i = 0; i < btns.length; i++) {
            btns[i].classList.toggle('active', btns[i].getAttribute('data-p') === p);
        }
        if (allData.length) renderTable();
    };

    /* ---- fetch ---- */
    function showLoading(msg) {
        var el = document.getElementById('sr-loading-msg');
        if (el) el.textContent = msg || 'データを検索中...';
        var l = document.getElementById('sr-loading');
        var e = document.getElementById('sr-error');
        var t = document.getElementById('sr-table-wrap');
        if (l) l.style.display = '';
        if (e) e.style.display = 'none';
        if (t) t.style.display = 'none';
    }

    function showError(msg) {
        var l = document.getElementById('sr-loading');
        var e = document.getElementById('sr-error');
        var em = document.getElementById('sr-error-msg');
        if (l) l.style.display = 'none';
        if (e) e.style.display = '';
        if (em) em.textContent = msg;
    }

    function showTable() {
        var l = document.getElementById('sr-loading');
        var e = document.getElementById('sr-error');
        var t = document.getElementById('sr-table-wrap');
        if (l) l.style.display = 'none';
        if (e) e.style.display = 'none';
        if (t) t.style.display = '';
    }

    function fetchData() {
        if (typeof srConfig === 'undefined') return;

        showLoading('データを検索中...');

        var msgs = ['データを検索中...', 'ランキングを分析中...', 'データを整理中...'];
        var mi = 0;
        var interval = setInterval(function () {
            mi = (mi + 1) % msgs.length;
            var el = document.getElementById('sr-loading-msg');
            if (el) el.textContent = msgs[mi];
        }, 2000);

        var url = srConfig.restUrl +
            '?platform=' + encodeURIComponent(srConfig.platform || 'all') +
            '&limit='    + encodeURIComponent(srConfig.limit    || 20);

        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.setRequestHeader('X-WP-Nonce', srConfig.nonce || '');
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) return;
            clearInterval(interval);
            if (xhr.status !== 200) {
                var errMsg = 'データの取得に失敗しました。';
                try {
                    var res = JSON.parse(xhr.responseText);
                    if (res && res.message) errMsg = res.message;
                } catch (e) {}
                showError(errMsg);
                return;
            }
            try {
                var data = JSON.parse(xhr.responseText);
                allData = data.streamers || [];

                var sub = document.getElementById('sr-last-updated');
                if (sub) sub.textContent = 'データ取得: ' + (data.updated || '2025') + ' | 出典: ' + (data.source || 'ウェブ検索');

                var note = document.getElementById('sr-note');
                if (note) note.textContent = '※ データはAIによるウェブ検索結果です。実際の数値と異なる場合があります。';

                updateSortIcons(sortState.col, sortState.dir);
                renderTable();
                showTable();
            } catch (e) {
                showError('データの解析に失敗しました: ' + e.message);
            }
        };
        xhr.send();
    }

    window.srRetry = function () { fetchData(); };

    /* ---- init ---- */
    document.addEventListener('DOMContentLoaded', function () {
        /* sort */
        var headers = document.querySelectorAll('.sr-sortable');
        for (var i = 0; i < headers.length; i++) {
            headers[i].addEventListener('click', handleSort);
        }

        /* filter buttons */
        var btns = document.querySelectorAll('.sr-btn');
        for (var j = 0; j < btns.length; j++) {
            (function (btn) {
                btn.addEventListener('click', function () {
                    window.srFilterPlatform(btn.getAttribute('data-p') || 'all');
                });
            })(btns[j]);
        }

        fetchData();
    });
})();
