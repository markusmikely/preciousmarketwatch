(function($) {
    'use strict';

    $(document).ready(function() {
        if (typeof pmwAgentUpload === 'undefined') return;

        $(document).on('click', '.pmw-avatar-upload-btn', function() {
            var $btn = $(this);
            var $container = $btn.closest('.pmw-avatar-upload');
            var $fileInput = $container.find('.pmw-avatar-file-input');
            var $status = $container.find('.pmw-upload-status');
            var action = $container.data('action');
            var meta = $container.data('meta');
            var file = $fileInput[0].files[0];

            if (!file) {
                $status.text('Please select a file first.').css('color', '#b32d2e');
                return;
            }
            

            $btn.prop('disabled', true);
            $status.text('Uploading…').css('color', '');

            var formData = new FormData();
            formData.append('action', action);
            formData.append('nonce', pmwAgentUpload.nonce);
            formData.append('post_id', pmwAgentUpload.postId);
            formData.append('file', file);

            $.ajax({
                url: pmwAgentUpload.ajaxUrl,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false
            })
            .done(function(res) {
                if (res.success && res.data) {
                    var url = res.data.avatar_image_url || res.data.avatar_video_url;
                    if (url) {
                        $container.find('input[type="hidden"]').val(url);
                        if (meta === 'pmw_avatar_image_url') {
                            var $img = $container.find('img.pmw-current-preview');
                            if ($img.length) {
                                $img.attr('src', url);
                            } else {
                                $container.find('.pmw-avatar-file-input').closest('p').before(
                                    $('<p/>').append($('<img/>', { src: url, alt: '', class: 'pmw-current-preview', style: 'max-width: 150px; height: auto; display: block; margin-bottom: 8px;' }))
                                );
                            }
                        }
                        var $current = $container.find('.pmw-current-url');
                        if ($current.length) {
                            $current.text('Current: ' + url);
                        } else {
                            $container.find('.pmw-avatar-file-input').closest('p').before(
                                $('<p class="description pmw-current-url">Current: ' + url + '</p>')
                            );
                        }
                    }
                    $status.text('Uploaded.').css('color', '#00a32a');
                    $fileInput.val('');
                } else {
                    $status.text(res.data && res.data.message ? res.data.message : 'Upload failed.').css('color', '#b32d2e');
                }
            })
            .fail(function(xhr, status, err) {
                var msg = (xhr.responseJSON && xhr.responseJSON.data && xhr.responseJSON.data.message)
                    ? xhr.responseJSON.data.message
                    : (err || 'Upload failed.');
                $status.text(msg).css('color', '#b32d2e');
            })
            .always(function() {
                $btn.prop('disabled', false);
            });
        });
    });
})(jQuery);
