/**
 * UNIFIED CART BADGE MODULE
 * Універсальний модуль для синхронізації badge корзини
 * Замінює: cart-badge-integration.js, mobile-cart-badge.js, частину cart.min.js
 */

(function() {
    'use strict';

    class CartBadgeManager {
        constructor() {
            this.desktopBadges = [];
            this.mobileBadges = [];
            this.currentCount = 0;
            this.eventBus = new EventTarget();
            
            this.init();
        }

        init() {
            // Знаходимо всі badge елементи (тільки cart, не wishlist)
            this.desktopBadges = document.querySelectorAll('.cart-badge, .header-cart-badge');
            this.mobileBadges = document.querySelectorAll('#mobileCartBadge, .mobile-cart-badge');
            
            // Отримуємо початкову кількість
            this.fetchCartCount().then(count => {
                this.updateAllBadges(count);
            });

            // Слухаємо події оновлення корзини
            this.bindEvents();
        }

        bindEvents() {
            // Custom event від cart операцій
            document.addEventListener('cart:updated', (event) => {
                const count = event.detail?.count || 0;
                this.updateAllBadges(count);
            });

            // Storage event для синхронізації між вкладками
            window.addEventListener('storage', (event) => {
                if (event.key === 'cart_count') {
                    const count = parseInt(event.newValue) || 0;
                    this.updateAllBadges(count);
                }
            });

            // Mutation observer для нових badge елементів
            const observer = new MutationObserver(() => {
                const newDesktop = document.querySelectorAll('.cart-badge, .header-cart-badge');
                const newMobile = document.querySelectorAll('#mobileCartBadge, .mobile-cart-badge');
                
                if (newDesktop.length > this.desktopBadges.length || 
                    newMobile.length > this.mobileBadges.length) {
                    this.desktopBadges = newDesktop;
                    this.mobileBadges = newMobile;
                    this.updateAllBadges(this.currentCount);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        updateAllBadges(count) {
            this.currentCount = count;
            
            // Оновлюємо desktop badges
            this.desktopBadges.forEach(badge => {
                this.updateBadge(badge, count);
            });

            // Оновлюємо mobile badges
            this.mobileBadges.forEach(badge => {
                this.updateBadge(badge, count, true);
            });

            // Зберігаємо в localStorage
            try {
                localStorage.setItem('cart_count', count.toString());
            } catch (e) {
                console.warn('Could not save to localStorage:', e);
            }

            // Dispatch custom event
            this.eventBus.dispatchEvent(new CustomEvent('badge:updated', { 
                detail: { count } 
            }));
        }

        updateBadge(badge, count, isMobile = false) {
            if (!badge) return;

            requestAnimationFrame(() => {
                if (count > 0) {
                    badge.textContent = count;
                    badge.classList.remove('nav-badge-hidden', 'hidden');
                } else {
                    badge.textContent = '';
                    badge.classList.add(isMobile ? 'nav-badge-hidden' : 'hidden');
                }
            });
        }

        async fetchCartCount() {
            try {
                const response = await fetch('/cart/api/count/', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    console.warn('Failed to fetch cart count');
                    return 0;
                }

                const data = await response.json();
                return data.count || 0;
            } catch (error) {
                console.error('Error fetching cart count:', error);
                return 0;
            }
        }

        // Public API
        refresh() {
            return this.fetchCartCount().then(count => {
                this.updateAllBadges(count);
                return count;
            });
        }

        getCount() {
            return this.currentCount;
        }

        on(event, callback) {
            this.eventBus.addEventListener(event, callback);
        }

        off(event, callback) {
            this.eventBus.removeEventListener(event, callback);
        }
    }

    // Ініціалізація при завантаженні
    let cartBadgeManager = null;

    function initCartBadge() {
        if (!cartBadgeManager) {
            cartBadgeManager = new CartBadgeManager();
        }
        return cartBadgeManager;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCartBadge);
    } else {
        initCartBadge();
    }

    // Експортуємо для глобального використання
    window.CartBadgeManager = CartBadgeManager;
    window.getCartBadgeManager = () => {
        if (!cartBadgeManager) {
            cartBadgeManager = initCartBadge();
        }
        return cartBadgeManager;
    };

    // Legacy compatibility - зберігаємо старий API
    window.updateMobileCartBadge = (count) => {
        const manager = window.getCartBadgeManager();
        manager.updateAllBadges(count);
    };
})();

