/**
 * Toast notification system
 * Універсальна система сповіщень
 */

(function() {
    'use strict';

    class ToastManager {
        constructor() {
            this.container = null;
            this.init();
        }

        init() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        }

        show(message, type = 'success', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `toast toast--${type}`;
            
            const icon = this.getIcon(type);
            toast.innerHTML = `
                <span class="toast__icon">${icon}</span>
                <span class="toast__message">${this.escapeHtml(message)}</span>
            `;
            
            this.container.appendChild(toast);
            
            requestAnimationFrame(() => {
                toast.classList.add('toast--show');
            });
            
            setTimeout(() => {
                toast.classList.remove('toast--show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        getIcon(type) {
            const icons = {
                'success': '✓',
                'error': '✕',
                'warning': '⚠',
                'info': 'ℹ'
            };
            return icons[type] || icons.info;
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        success(message, duration) {
            this.show(message, 'success', duration);
        }

        error(message, duration) {
            this.show(message, 'error', duration);
        }

        warning(message, duration) {
            this.show(message, 'warning', duration);
        }

        info(message, duration) {
            this.show(message, 'info', duration);
        }
    }

    const toastManager = new ToastManager();

    window.showToast = (message, type, duration) => toastManager.show(message, type, duration);
    window.Toast = {
        show: (message, type, duration) => toastManager.show(message, type, duration),
        success: (message, duration) => toastManager.success(message, duration),
        error: (message, duration) => toastManager.error(message, duration),
        warning: (message, duration) => toastManager.warning(message, duration),
        info: (message, duration) => toastManager.info(message, duration)
    };
})();

