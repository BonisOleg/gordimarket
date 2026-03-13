/**
 * Wishlist functionality
 * Управління списком бажань з AJAX та анімаціями
 */

class WishlistManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.fetchWishlistCount().then(count => {
            this.updateBadgesDOM(count);
        });
        this.initializeWishlistState();
        this.setupStorageListener();
    }

    setupStorageListener() {
        window.addEventListener('storage', (event) => {
            if (event.key === 'wishlist_count') {
                const count = parseInt(event.newValue) || 0;
                this.updateBadgesDOM(count);
            }
        });
    }

    async initializeWishlistState() {
        // Отримуємо поточний стан wishlist з сервера
        try {
            const response = await fetch('/wishlist/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            
            if (response.ok) {
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const wishlistItems = doc.querySelectorAll('.wishlist-item, .product-card[data-product-id]');
                
                // Створюємо Set з ID товарів у wishlist
                const wishlistProductIds = new Set();
                wishlistItems.forEach(item => {
                    const productId = item.dataset.productId;
                    if (productId) {
                        wishlistProductIds.add(productId);
                    }
                });
                
                // Оновлюємо стан всіх кнопок wishlist на сторінці
                this.updateButtonStates(wishlistProductIds);
            }
        } catch (error) {
            console.error('Failed to initialize wishlist state:', error);
        }
    }

    updateButtonStates(wishlistProductIds) {
        const wishlistButtons = document.querySelectorAll(
            '.btn-toggle-wishlist, .wishlist-toggle, .btn-wishlist, .wishlist-btn, .product-card__wishlist'
        );
        
        wishlistButtons.forEach(button => {
            const productId = button.dataset.productId;
            if (productId && wishlistProductIds.has(productId)) {
                button.classList.add('active');
                this.updateButtonIcon(button, true);
            } else {
                button.classList.remove('active');
                this.updateButtonIcon(button, false);
            }
        });
    }

    updateButtonIcon(button, isActive) {
        // Для різних типів кнопок різна логіка оновлення іконки
        const iconElement = button.querySelector('svg, .icon-heart, .product-card__wishlist-icon');
        
        if (button.classList.contains('product-card__wishlist')) {
            // Для кнопок в product-card використовуємо text content
            const iconSpan = button.querySelector('.product-card__wishlist-icon');
            if (iconSpan) {
                iconSpan.textContent = isActive ? '♥' : '♡';
            }
        } else if (iconElement && iconElement.tagName === 'svg') {
            // Для SVG іконок
            if (isActive) {
                iconElement.innerHTML = '<path d="M20.84 4.61C20.3292 4.099 19.7228 3.69364 19.0554 3.41708C18.3879 3.14052 17.6725 2.99817 16.95 2.99817C16.2275 2.99817 15.5121 3.14052 14.8446 3.41708C14.1772 3.69364 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.1283 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.1283 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2728 22.0329 10.6054C22.3095 9.93789 22.4518 9.22248 22.4518 8.5C22.4518 7.77752 22.3095 7.06211 22.0329 6.39464C21.7564 5.72718 21.351 5.12084 20.84 4.61Z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
            } else {
                iconElement.innerHTML = '<path d="M20.84 4.61C20.3292 4.099 19.7228 3.69364 19.0554 3.41708C18.3879 3.14052 17.6725 2.99817 16.95 2.99817C16.2275 2.99817 15.5121 3.14052 14.8446 3.41708C14.1772 3.69364 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.1283 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.1283 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2728 22.0329 10.6054C22.3095 9.93789 22.4518 9.22248 22.4518 8.5C22.4518 7.77752 22.3095 7.06211 22.0329 6.39464C21.7564 5.72718 21.351 5.12084 20.84 4.61Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
            }
        } else if (iconElement && iconElement.classList.contains('icon-heart')) {
            // Для text-based іконок
            iconElement.textContent = isActive ? '♥' : '♡';
        }
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            const wishlistBtn = e.target.closest(
                '.btn-toggle-wishlist, .wishlist-toggle, .btn-wishlist, .wishlist-btn, .product-card__wishlist'
            );
            if (wishlistBtn) {
                e.preventDefault();
                e.stopImmediatePropagation();
                this.toggleWishlist(wishlistBtn);
            }

            // Видалення з wishlist (на сторінці wishlist)
            const removeBtn = e.target.closest('.btn-remove-wishlist');
            if (removeBtn) {
                e.preventDefault();
                this.removeFromWishlist(removeBtn);
            }
        });
    }

    async toggleWishlist(button) {
        const productId = button.dataset.productId;
        const isInWishlist = button.classList.contains('active');
        const productCard = button.closest('.product-card');
        const isOnWishlistPage = document.querySelector('.wishlist-page') !== null;
        
        button.disabled = true;

        try {
            const url = isInWishlist 
                ? `/wishlist/remove/${productId}/`
                : `/wishlist/add/${productId}/`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success) {
                if (isInWishlist && isOnWishlistPage && productCard) {
                    productCard.style.transition = 'all 0.3s ease';
                    productCard.style.opacity = '0';
                    productCard.style.transform = 'scale(0.95)';
                    
                    setTimeout(() => {
                        productCard.remove();
                        
                        const remainingItems = document.querySelectorAll('.wishlist-page .product-card');
                        if (remainingItems.length === 0) {
                            location.reload();
                        }
                    }, 300);
                } else {
                    button.classList.toggle('active');
                    this.updateButtonIcon(button, button.classList.contains('active'));
                    
                    button.classList.add('animate-heart');
                    setTimeout(() => button.classList.remove('animate-heart'), 300);
                }

                this.updateBadgesDOM(data.count);
                this.showNotification(data.message);
            }
        } catch (error) {
            console.error('Wishlist error:', error);
            this.showNotification('Виникла помилка. Спробуйте ще раз.', 'error');
        } finally {
            button.disabled = false;
        }
    }

    async removeFromWishlist(button) {
        const productId = button.dataset.productId;
        const wishlistItem = button.closest('.wishlist-item, .product-card');

        button.disabled = true;

        try {
            const response = await fetch(`/wishlist/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success) {
                wishlistItem.style.transition = 'all 0.3s ease';
                wishlistItem.style.opacity = '0';
                wishlistItem.style.transform = 'scale(0.95)';
                
                setTimeout(() => {
                    wishlistItem.remove();
                    
                    const remainingItems = document.querySelectorAll('.wishlist-page .product-card');
                    if (remainingItems.length === 0) {
                        location.reload();
                    }
                }, 300);

                this.updateBadgesDOM(data.count);
                this.showNotification(data.message);
            }
        } catch (error) {
            console.error('Remove from wishlist error:', error);
            this.showNotification('Виникла помилка. Спробуйте ще раз.', 'error');
            button.disabled = false;
        }
    }

    async fetchWishlistCount() {
        try {
            const response = await fetch('/wishlist/api/count/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                console.warn('Failed to fetch wishlist count');
                return 0;
            }

            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error('Error fetching wishlist count:', error);
            return 0;
        }
    }

    updateWishlistBadges(count = null) {
        if (count === null) {
            this.fetchWishlistCount().then(fetchedCount => {
                this.updateBadgesDOM(fetchedCount);
            });
            return;
        }
        
        this.updateBadgesDOM(count);
    }

    updateBadgesDOM(count) {
        requestAnimationFrame(() => {
            document.querySelectorAll('.wishlist-link .badge, .wishlist-badge').forEach(badge => {
                if (count > 0) {
                    badge.textContent = count;
                    badge.classList.remove('badge-hidden', 'hidden');
                } else {
                    badge.textContent = '';
                    badge.classList.add('hidden');
                }
            });

            document.querySelectorAll('.nav-item-wishlist .nav-badge').forEach(badge => {
                if (count > 0) {
                    badge.textContent = count;
                    badge.classList.remove('nav-badge-hidden');
                } else {
                    badge.textContent = '';
                    badge.classList.add('nav-badge-hidden');
                }
            });

            try {
                localStorage.setItem('wishlist_count', count.toString());
            } catch (e) {
                console.warn('Could not save wishlist count to localStorage:', e);
            }
        });
    }

    showNotification(message, type = 'success') {
        // Створюємо notification елемент
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <svg class="notification-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    ${type === 'success' 
                        ? '<path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        : '<path d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                    }
                </svg>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Анімація появи
        setTimeout(() => notification.classList.add('show'), 10);

        // Видалення через 3 секунди
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getCookie(name) {
        if (name === 'csrftoken') {
            const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (metaToken) return metaToken;
            
            const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (inputToken) return inputToken;
        }
        
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Ініціалізація
document.addEventListener('DOMContentLoaded', () => {
    window.wishlistManager = new WishlistManager();
    
    // Обробка кнопок з підтвердженням
    document.addEventListener('click', (e) => {
        const confirmBtn = e.target.closest('[data-confirm]');
        if (confirmBtn) {
            const message = confirmBtn.dataset.confirm;
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        }
    });
});

