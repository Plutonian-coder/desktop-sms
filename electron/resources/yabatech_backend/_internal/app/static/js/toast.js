/**
 * Toast Notification System — v2
 * 
 * Supports two calling conventions:
 *   showToast('Title', 'Message', 'success')   — legacy (students.js, sessions.js)
 *   showToast('Message', 'success')             — new (attendance.js, etc.)
 */
(function () {
    'use strict';

    const VALID_TYPES = ['success', 'error', 'warning', 'info'];

    const ICONS = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };

    const DURATIONS = {
        success: 3500,
        error: 5000,
        warning: 4500,
        info: 4000
    };

    /**
     * Show a toast notification.
     * @param {string} titleOrMessage - Title (if 3 args) or Message (if 2 args)
     * @param {string} [messageOrType] - Message (if 3 args) or Type (if 2 args)
     * @param {string} [type] - Toast type when using 3-arg form
     */
    window.showToast = function (titleOrMessage, messageOrType, type) {
        let title, message, toastType;

        // Detect calling convention
        if (type && VALID_TYPES.includes(type)) {
            // 3-arg: showToast('Title', 'Message', 'type')
            title = titleOrMessage;
            message = messageOrType;
            toastType = type;
        } else if (messageOrType && VALID_TYPES.includes(messageOrType)) {
            // 2-arg: showToast('Message', 'type')
            title = null;
            message = titleOrMessage;
            toastType = messageOrType;
        } else {
            // Fallback: just a message
            title = null;
            message = titleOrMessage;
            toastType = 'info';
        }

        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${toastType}`;

        const icon = document.createElement('span');
        icon.className = 'material-symbols-outlined toast-icon';
        icon.textContent = ICONS[toastType] || ICONS.info;

        const textWrap = document.createElement('div');
        textWrap.className = 'toast-text-wrap';
        textWrap.style.flex = '1';

        if (title) {
            const titleEl = document.createElement('div');
            titleEl.className = 'toast-title';
            titleEl.style.fontWeight = '600';
            titleEl.style.fontSize = '13px';
            titleEl.style.marginBottom = '2px';
            titleEl.textContent = title;
            textWrap.appendChild(titleEl);
        }

        const msgEl = document.createElement('span');
        msgEl.className = 'toast-message';
        msgEl.textContent = message;
        textWrap.appendChild(msgEl);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '<span class="material-symbols-outlined">close</span>';
        closeBtn.addEventListener('click', () => dismissToast(toast));

        toast.appendChild(icon);
        toast.appendChild(textWrap);
        toast.appendChild(closeBtn);
        container.appendChild(toast);

        // Trigger entrance animation
        requestAnimationFrame(() => {
            toast.classList.add('toast-show');
        });

        // Auto-dismiss
        const dismissTime = DURATIONS[toastType] || 4000;
        const timer = setTimeout(() => dismissToast(toast), dismissTime);
        toast.dataset.timer = timer;
    };

    function dismissToast(toast) {
        if (toast.dataset.dismissed) return;
        toast.dataset.dismissed = 'true';
        clearTimeout(parseInt(toast.dataset.timer));
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');
        toast.addEventListener('animationend', () => toast.remove(), { once: true });
        // Fallback removal
        setTimeout(() => toast.remove(), 500);
    }
})();
