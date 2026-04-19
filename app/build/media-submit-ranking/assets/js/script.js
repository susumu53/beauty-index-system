jQuery(function($) {
    'use strict';

    // ===== 投稿フォーム: タイプ切り替え =====
    $(document).on('click', '.msr-toggle-btn', function() {
        const type = $(this).data('type');
        $('.msr-toggle-btn').removeClass('active');
        $(this).addClass('active');
        $('input[name="media_type"]').val(type);

        if (type === 'mp3') {
            $('.msr-app-field').hide();
            $('.msr-mp3-field').show();
        } else {
            $('.msr-app-field').show();
            $('.msr-mp3-field').hide();
        }
    });

    // MP3ファイルドロップ
    const $drop = $('#msr-file-drop');
    if ($drop.length) {
        $drop.on('click', function() { $('#msr-mp3-file').click(); });
        $drop.on('dragover', function(e) { e.preventDefault(); $(this).addClass('drag-over'); });
        $drop.on('dragleave', function() { $(this).removeClass('drag-over'); });
        $drop.on('drop', function(e) {
            e.preventDefault();
            $(this).removeClass('drag-over');
            const file = e.originalEvent.dataTransfer.files[0];
            if (file) {
                $('#msr-mp3-file')[0].files = e.originalEvent.dataTransfer.files;
                $('#msr-file-name').text('✅ ' + file.name);
            }
        });
        $('#msr-mp3-file').on('change', function() {
            if (this.files[0]) $('#msr-file-name').text('✅ ' + this.files[0].name);
        });
    }

    // ===== 投稿送信 =====
    $(document).on('submit', '#msr-submit-form', function(e) {
        e.preventDefault();
        const $btn = $('#msr-submit-btn');
        $btn.prop('disabled', true).text('送信中...');

        const formData = new FormData(this);
        formData.append('action', 'msr_submit');
        formData.append('nonce', MSR.nonce);

        $.ajax({
            url: MSR.ajax_url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(res) {
                const $msg = $('#msr-submit-message');
                if (res.success) {
                    $msg.removeClass('error').addClass('success msr-alert').text(res.data.message).show();
                    $('#msr-submit-form')[0].reset();
                    $('#msr-file-name').text('');
                    // フォームをリセット
                    $('.msr-toggle-btn').first().click();
                } else {
                    $msg.removeClass('success').addClass('error msr-alert').text(res.data.message).show();
                }
                $('html,body').animate({ scrollTop: $msg.offset().top - 60 }, 300);
            },
            error: function() {
                $('#msr-submit-message').addClass('error msr-alert').text('通信エラーが発生しました。').show();
            },
            complete: function() {
                $btn.prop('disabled', false).text('投稿する');
            }
        });
    });

    // ===== いいね =====
    $(document).on('click', '.msr-like-btn', function() {
        const $btn = $(this);
        if ($btn.hasClass('liked') || $btn.data('pending')) return;
        $btn.data('pending', true);

        const postId = $btn.data('id');
        $.post(MSR.ajax_url, {
            action: 'msr_like',
            nonce: MSR.nonce,
            post_id: postId
        }, function(res) {
            if (res.success) {
                $btn.addClass('liked').data('pending', false);
                // 同じ投稿の全いいねボタンを更新
                $(`.msr-like-btn[data-id="${postId}"] .msr-like-count`).text(res.data.likes);
            } else {
                alert(res.data.message);
                $btn.data('pending', false);
            }
        });
    });

    // ===== ランキングタブ切り替え =====
    $(document).on('click', '.msr-tab', function() {
        const $wrap = $(this).closest('.msr-ranking-wrap');
        $wrap.find('.msr-tab').removeClass('active');
        $(this).addClass('active');

        const by = $(this).data('by');
        const $list = $wrap.find('#msr-ranking-list');
        $list.css('opacity', .5);

        $.post(MSR.ajax_url, {
            action: 'msr_get_ranking',
            nonce: MSR.nonce,
            by: by
        }, function(res) {
            if (res.success) {
                $list.html(res.data.html).css('opacity', 1);
                // ランキングラベル更新
                const labels = { likes: 'いいね', downloads: 'DL数', views: '閲覧数' };
                $wrap.find('.msr-ranking-by').text('（' + labels[by] + '順）');
            }
        });
    });

    // ===== 一覧フィルター =====
    $(document).on('click', '.msr-filter', function() {
        $(this).closest('.msr-list-wrap').find('.msr-filter').removeClass('active');
        $(this).addClass('active');

        const type = $(this).data('type');
        const $cards = $(this).closest('.msr-list-wrap').find('.msr-card');

        $cards.each(function() {
            if (type === 'all' || $(this).data('type') === type) {
                $(this).fadeIn(200);
            } else {
                $(this).fadeOut(200);
            }
        });
    });

    // ===== MP3 プレーヤー =====
    // プレーヤーバーを追加
    if ($('.msr-download-btn').length) {
        $('body').append(`
            <div class="msr-player-bar" id="msr-player-bar">
                <div class="msr-player-title" id="msr-player-title">🎵 Now Playing...</div>
                <audio id="msr-audio-player" controls></audio>
                <button class="msr-player-close" id="msr-player-close">✕</button>
            </div>
        `);
    }

    $(document).on('click', '.msr-download-btn', function() {
        const postId = $(this).data('id');
        const url    = $(this).data('url');
        const title  = $(this).closest('.msr-rank-item, .msr-card').find('.msr-rank-title, .msr-card-title').text();

        // カウント
        $.post(MSR.ajax_url, { action: 'msr_download', nonce: MSR.nonce, post_id: postId });

        // プレーヤー起動
        const $player = $('#msr-player-bar');
        const $audio  = $('#msr-audio-player');
        $('#msr-player-title').text('🎵 ' + title);
        $audio.attr('src', url)[0].play();
        $player.addClass('active');
    });

    $(document).on('click', '#msr-player-close', function() {
        $('#msr-audio-player')[0].pause();
        $('#msr-player-bar').removeClass('active');
    });
});
