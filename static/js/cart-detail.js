/**
 * Cart Detail Page Handlers
 * Управління кошиком на сторінці перегляду
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        // Читаємо CSRF токен з cookie (для iOS Safari це надійніше)
        function getCSRFToken() {
            const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
            if (cookie) {
                return cookie.split('=')[1];
            }
            const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
            return metaToken || '';
        }
        
        const csrfToken = getCSRFToken();
        console.log('Cart detail CSRF token:', csrfToken ? csrfToken.substring(0, 10) + '...' : 'NOT FOUND');
        
        function updateCartDisplay(data) {
            if (data.subtotal) {
                document.querySelector('.cart-subtotal').textContent = data.subtotal + ' ₴';
            }
            if (data.total) {
                document.querySelector('.cart-grand-total').textContent = data.total + ' ₴';
            }
        }
        
        function updateQuantity(productId, quantity) {
            if (quantity < 1) return;
            
            fetch(`/cart/update/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ quantity })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            })
            .catch(error => console.error('Помилка при оновленні кількості:', error));
        }
        
        document.querySelectorAll('.qty-minus').forEach(btn => {
            btn.addEventListener('click', function() {
                const productId = this.dataset.productId;
                const input = document.getElementById(`quantity-${productId}`);
                const currentVal = parseInt(input.value);
                if (currentVal > 1) {
                    updateQuantity(productId, currentVal - 1);
                }
            });
        });
        
        document.querySelectorAll('.qty-plus').forEach(btn => {
            btn.addEventListener('click', function() {
                const productId = this.dataset.productId;
                const max = parseInt(this.dataset.max);
                const input = document.getElementById(`quantity-${productId}`);
                const currentVal = parseInt(input.value);
                if (currentVal < max) {
                    updateQuantity(productId, currentVal + 1);
                }
            });
        });
        
        function removeCartItem(button) {
            const productId = button.dataset.productId;
            const productName = button.dataset.productName;
            
            if (!confirm(`Видалити ${productName} з кошика?`)) return;
            
            fetch(`/cart/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            })
            .catch(error => console.error('Помилка при видаленні товару:', error));
        }
        
        document.querySelectorAll('.remove-from-cart, .item-remove').forEach(button => {
            button.addEventListener('click', function() {
                removeCartItem(this);
            });
        });
        
        const applyPromoBtn = document.querySelector('.apply-promo');
        if (applyPromoBtn) {
            applyPromoBtn.addEventListener('click', async function() {
                const code = document.getElementById('promoCodeInput').value.trim();
                const messageDiv = document.querySelector('.promo-message');
                
                if (!code) {
                    messageDiv.textContent = 'Введіть промокод';
                    messageDiv.className = 'promo-message error';
                    return;
                }
                
                try {
                    const response = await fetch('/cart/promo/apply/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify({ code })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        location.reload();
                    } else {
                        messageDiv.textContent = data.message;
                        messageDiv.className = 'promo-message error';
                    }
                } catch (error) {
                    console.error('Помилка при застосуванні промокоду:', error);
                    messageDiv.textContent = 'Помилка при застосуванні промокоду';
                    messageDiv.className = 'promo-message error';
                }
            });
            
            const promoInput = document.getElementById('promoCodeInput');
            if (promoInput) {
                promoInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        applyPromoBtn.click();
                    }
                });
            }
        }
        
        const removePromoBtn = document.querySelector('.remove-promo');
        if (removePromoBtn) {
            removePromoBtn.addEventListener('click', async function() {
                try {
                    const response = await fetch('/cart/promo/remove/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'same-origin'
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        location.reload();
                    }
                } catch (error) {
                    console.error('Помилка при видаленні промокоду:', error);
                }
            });
        }
    });
})();
