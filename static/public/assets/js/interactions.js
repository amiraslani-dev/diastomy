
function submitComment(slug, type='serial') {
    if (!window.APP_STATE.isAuthenticated) {
        Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.loginRequired);
        return;
    }

    const textarea = document.getElementById('comment-text');
    const text = textarea.value.trim();
    const parentId = document.getElementById('comment-parent-id').value;

    if (!text) {
        Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.emptyComment);
        return;
    }

    const btn = window.event ? window.event.currentTarget : null;
    if (btn) {
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    }

    const formData = new FormData();
    formData.append('text', text);
    if (parentId) {
        formData.append('parent_id', parentId);
    }
    formData.append('csrfmiddlewaretoken', window.APP_STATE.csrfToken);

    
    const urlType = type === 'serial' ? 'series' : 'movie';
    fetch(`/movie/${urlType}/${slug}/comment/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            Alpine.store('globalModal').show('success', window.APP_STATE.translations.success, data.message);
            const cancelBtn = document.getElementById('cancel-reply-btn');
            if (cancelBtn) cancelBtn.style.display = 'none';
            textarea.value = '';
            document.getElementById('comment-parent-id').value = '';
            textarea.placeholder = window.APP_STATE.translations.writeComment;
        } else {
            Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, data.message);
        }
    })
    .catch(error => {
        Alpine.store('globalToast').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.serverError);
    })
    .finally(() => {
        if (btn) {
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    });
}

function replyTo(commentId, username) {
    document.getElementById('comment-parent-id').value = commentId;
    const textarea = document.getElementById('comment-text');
    textarea.placeholder = window.APP_STATE.translations.replyTo + ' ' + username + '...';
    textarea.focus();
    
    // Scroll to comments tab if not already there
    // If Alpine is handling the activeTab, this might need custom logic depending on the page
    // but focusing the textarea usually works.
}

function toggleCommentLike(commentId, action, type='serial') {
    if (!window.APP_STATE.isAuthenticated) {
        Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.loginRequired);
        return;
    }

    const btn = window.event ? window.event.currentTarget : null;
    if (btn) {
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    }

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', window.APP_STATE.csrfToken);

    
    const urlPrefix = type === 'serial' ? 'comment' : 'movie-comment';
    fetch(`/movie/${urlPrefix}/${commentId}/${action}/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            document.getElementById('likes-count-' + commentId).innerText = data.likes;
            document.getElementById('dislikes-count-' + commentId).innerText = data.dislikes;
            
            // Toggle active classes
            const likeBtn = document.getElementById('like-btn-' + commentId);
            const dislikeBtn = document.getElementById('dislike-btn-' + commentId);
            
            if (action === 'like') {
                if (data.is_liked) {
                    likeBtn.classList.add('text-green-500', 'fill-green-500');
                    dislikeBtn.classList.remove('text-red-500', 'fill-red-500');
                } else {
                    likeBtn.classList.remove('text-green-500', 'fill-green-500');
                }
            } else {
                if (data.is_disliked) {
                    dislikeBtn.classList.add('text-red-500', 'fill-red-500');
                    likeBtn.classList.remove('text-green-500', 'fill-green-500');
                } else {
                    dislikeBtn.classList.remove('text-red-500', 'fill-red-500');
                }
            }
        } else {
            Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, data.message || 'خطایی رخ داد');
        }
    })
    .finally(() => {
        if (btn) {
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    });
}

function likeItem(slug, type, btn) {
    if (!window.APP_STATE.isAuthenticated) {
        Alpine.store('globalModal').show('error', window.APP_STATE.translations.unauthorized, window.APP_STATE.translations.loginRequired);
        return Promise.resolve(undefined);
    }

    if (btn) {
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    }
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', window.APP_STATE.csrfToken);

    return fetch(`/movie/${type}/${slug}/like/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(res => {
        if (res.status === 'success') {
            return res.liked;
        } else {
            Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, res.message || 'خطایی رخ داد');
        }
    })
    .catch(err => {
        Alpine.store('globalToast').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.serverError);
    })
    .finally(() => {
        if (btn) {
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    });
}

function saveItem(slug, type, btn) {
    if (!window.APP_STATE.isAuthenticated) {
        Alpine.store('globalModal').show('error', window.APP_STATE.translations.unauthorized, window.APP_STATE.translations.loginRequired);
        return Promise.resolve(undefined);
    }

    if (btn) {
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.5';
    }
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', window.APP_STATE.csrfToken);

    return fetch(`/movie/${type}/${slug}/save/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(res => {
        if (res.status === 'success') {
            return res.saved;
        } else {
            Alpine.store('globalModal').show('error', window.APP_STATE.translations.error, res.message || 'خطایی رخ داد');
        }
    })
    .catch(err => {
        Alpine.store('globalToast').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.serverError);
    })
    .finally(() => {
        if (btn) {
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    });
}

function shareItem() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        }).catch(err => {
            console.error("Share API failed, falling back to clipboard", err);
            copyToClipboardFallback();
        });
    } else {
        copyToClipboardFallback();
    }
}

function copyToClipboardFallback() {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(window.location.href).then(() => {
            Alpine.store('globalToast').show('success', window.APP_STATE.translations.success, window.APP_STATE.translations.linkCopied);
        }).catch(err => {
            Alpine.store('globalToast').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.copyFailed);
        });
    } else {
        // Fallback for very old browsers or insecure contexts (HTTP)
        const input = document.createElement('input');
        input.value = window.location.href;
        document.body.appendChild(input);
        input.select();
        try {
            document.execCommand('copy');
            Alpine.store('globalToast').show('success', window.APP_STATE.translations.success, window.APP_STATE.translations.linkCopied);
        } catch (err) {
            Alpine.store('globalToast').show('error', window.APP_STATE.translations.error, window.APP_STATE.translations.copyNotSupported);
        }
        document.body.removeChild(input);
    }
}
