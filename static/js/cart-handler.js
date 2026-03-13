/**
 * Cart Handler - Універсальний обробник додавання в кошик
 */

(function() {
    'use strict';

    class CartHandler {
        constructor() {
            this.isProcessing = new Set(); // Відслідковування товарів, що обробляються
            this.init();
        }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.bindCartButtons();
            });
        } else {
            this.bindCartButtons();
        }
    }

    bindCartButtons() {
        const buttons = document.querySelectorAll('.product-card__add-cart, .btn-add-cart, .add-to-cart, .promo-add-cart');
        
        buttons.forEach(button => {
            if (button.disabled || button.hasAttribute('data-cart-initialized')) return;
            
            button.setAttribute('data-cart-initialized', 'true');
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.addToCart(button);
            });
        });
    }

    async addToCart(button) {
        const productId = button.dataset.productId;
        
        if (!productId) {
            console.error('Product ID not found');
            return;
        }

        // Запобігаємо одночасній обробці одного товару
        if (this.isProcessing.has(productId)) {
            console.warn(`Product ${productId} is already being processed`);
            return;
        }

        if (button.disabled) return;
        
        // Позначаємо товар як "в процесі обробки"
        this.isProcessing.add(productId);
        button.disabled = true;
        const originalHTML = button.innerHTML;
        button.innerHTML = 'Додається...';

        const quantityInput = document.getElementById('productQuantity');
        const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;

        // Retry logic для iOS Safari
        let retryCount = 0;
        const maxRetries = 1;

        const performFetch = async () => {
            try {
                const response = await fetch(`/cart/add/${productId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ quantity })
                });

                // Перевіряємо HTTP статус ПЕРЕД парсингом JSON
                if (!response.ok) {
                    // Парсимо JSON для помилок
                    try {
                        const data = await response.json();
                        const errorMessage = data.message || 'Помилка при додаванні в кошик';
                        if (window.Toast) {
                            window.Toast.error(errorMessage);
                        }
                    } catch (jsonError) {
                        // Якщо не можемо спарсити JSON (наприклад, 403 повертає HTML)
                        console.error('Failed to parse error response:', response.status, jsonError);
                        if (window.Toast) {
                            const statusMessage = response.status === 403 
                                ? 'Проблема з безпекою запиту. Спробуйте оновити сторінку.'
                                : `Помилка сервера (${response.status})`;
                            window.Toast.error(statusMessage);
                        }
                    }
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                    this.isProcessing.delete(productId);
                    return;
                }

                // Парсимо JSON тільки для успішних відповідей
                const data = await response.json();

                // Обробляємо успішну відповідь
                if (data.success) {
                    if (window.Toast) {
                        window.Toast.success('Товар додано в кошик');
                    }
                    
                    document.dispatchEvent(new CustomEvent('cart:updated', {
                        detail: { count: data.cart_count }
                    }));

                    button.innerHTML = '✓ Додано';
                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                        button.disabled = false;
                        // Видаляємо товар з набору "в процесі"
                        this.isProcessing.delete(productId);
                    }, 2000);
                } else {
                    // success: false при статусі 200 (рідкісний випадок)
                    const errorMessage = data.message || 'Помилка додавання';
                    if (window.Toast) {
                        window.Toast.error(errorMessage);
                    }
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                    this.isProcessing.delete(productId);
                }
            } catch (error) {
                // Retry logic для iOS Safari - повторимо один раз при помилці мережи
                if (retryCount < maxRetries && error.message.includes('Failed')) {
                    retryCount++;
                    console.warn(`Network error, retrying... (${retryCount}/${maxRetries})`);
                    await new Promise(resolve => setTimeout(resolve, 500)); // 500ms затримка перед retry
                    return performFetch();
                }

                // Тепер тут СПРАВДІ тільки помилки мережи або JSON парсингу
                console.error('Cart add error:', {
                    message: error.message,
                    stack: error.stack,
                    productId: productId,
                    timestamp: new Date().toISOString(),
                    retryCount: retryCount
                });
                if (window.Toast) {
                    window.Toast.error('Помилка з\'єднання. Перевірте інтернет.');
                }
                button.innerHTML = originalHTML;
                button.disabled = false;
                this.isProcessing.delete(productId);
            }
        };

        return performFetch();
    }

    getCSRFToken() {
        // Спочатку намагаємося прочитати з cookie (для iOS Safari)
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (cookie) {
            const token = cookie.split('=')[1];
            console.log('CSRF from cookie:', token.substring(0, 10) + '...');
            return token;
        }
        
        // Fallback на meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (metaToken) {
            console.log('CSRF from meta:', metaToken.substring(0, 10) + '...');
            return metaToken;
        }
        
        // Fallback на hidden input
        const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (inputToken) {
            console.log('CSRF from input:', inputToken.substring(0, 10) + '...');
            return inputToken;
        }
        
        console.error('CSRF token not found!');
        return '';
    }
    }

    const cartHandler = new CartHandler();
    
    window.CartHandler = CartHandler;
    window.cartHandler = cartHandler;
})();

