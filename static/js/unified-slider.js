/**
 * UNIFIED SLIDER MODULE
 * Універсальний модуль для всіх слайдерів на сайті
 * Замінює: promotions-slider.js, top-products-slider.js, reviews-slider.js
 */

(function() {
    'use strict';

    class UnifiedSlider {
        constructor(config) {
            this.sliderId = config.sliderId;
            this.containerClass = config.containerClass || 'slider-container';
            this.prevBtnClass = config.prevBtnClass || 'prev-btn';
            this.nextBtnClass = config.nextBtnClass || 'next-btn';
            this.itemClass = config.itemClass || 'slide-item';
            this.desktopScroll = config.desktopScroll || 4;
            this.mobileScroll = config.mobileScroll || 2;
            this.gap = config.gap || { desktop: 15, mobile: 10 };
            this.enableSwipe = config.enableSwipe !== false;
            this.enableKeyboard = config.enableKeyboard !== false;
            this.updateButtons = config.updateButtons !== false;
            
            this.slider = null;
            this.container = null;
            this.prevBtn = null;
            this.nextBtn = null;
            this.mobilePrevBtn = null;
            this.mobileNextBtn = null;
            this.items = null;
            
            this.init();
        }

        init() {
            this.slider = document.getElementById(this.sliderId);
            if (!this.slider) {
                console.warn(`Slider #${this.sliderId} not found`);
                return;
            }

            this.container = this.slider.closest(`.${this.containerClass}`);
            if (!this.container) {
                console.warn(`Container .${this.containerClass} not found`);
                return;
            }

            this.prevBtn = this.container.querySelector(`.${this.prevBtnClass}`);
            this.nextBtn = this.container.querySelector(`.${this.nextBtnClass}`);
            this.mobilePrevBtn = this.container.querySelector('.promo-prev-btn-mobile');
            this.mobileNextBtn = this.container.querySelector('.promo-next-btn-mobile');
            this.items = this.slider.querySelectorAll(`.${this.itemClass}`);

            if (this.items.length === 0) {
                console.warn(`No items with class .${this.itemClass} found`);
                return;
            }

            this.bindEvents();
            if (this.updateButtons) {
                this.updateButtonStates();
            }
        }

        getScrollAmount() {
            const itemWidth = this.items[0].offsetWidth;
            const isMobile = window.innerWidth <= 768;
            const gap = isMobile ? this.gap.mobile : this.gap.desktop;
            const itemsToScroll = isMobile ? this.mobileScroll : this.desktopScroll;
            return (itemWidth + gap) * itemsToScroll;
        }

        scrollSlider(direction) {
            const scrollAmount = this.getScrollAmount();
            
            this.slider.scrollBy({
                left: direction === 'next' ? scrollAmount : -scrollAmount,
                behavior: 'smooth'
            });
        }

        updateButtonStates() {
            const isAtStart = this.slider.scrollLeft <= 0;
            const isAtEnd = this.slider.scrollLeft >= this.slider.scrollWidth - this.slider.clientWidth - 1;
            
            if (this.prevBtn && this.nextBtn) {
                this.prevBtn.disabled = isAtStart;
                this.prevBtn.classList.toggle('disabled', isAtStart);
                
                this.nextBtn.disabled = isAtEnd;
                this.nextBtn.classList.toggle('disabled', isAtEnd);
            }
            
            if (this.mobilePrevBtn && this.mobileNextBtn) {
                this.mobilePrevBtn.disabled = isAtStart;
                this.mobilePrevBtn.classList.toggle('disabled', isAtStart);
                
                this.mobileNextBtn.disabled = isAtEnd;
                this.mobileNextBtn.classList.toggle('disabled', isAtEnd);
            }
        }

        bindEvents() {
            if (this.prevBtn) {
                this.prevBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.prevBtn.disabled) {
                        this.scrollSlider('prev');
                    }
                });
            }
            
            if (this.nextBtn) {
                this.nextBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.nextBtn.disabled) {
                        this.scrollSlider('next');
                    }
                });
            }
            
            if (this.mobilePrevBtn) {
                this.mobilePrevBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.mobilePrevBtn.disabled) {
                        this.scrollSlider('prev');
                    }
                }, { passive: false });
            }
            
            if (this.mobileNextBtn) {
                this.mobileNextBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!this.mobileNextBtn.disabled) {
                        this.scrollSlider('next');
                    }
                }, { passive: false });
            }

            // Update button states on scroll (throttled)
            if (this.updateButtons) {
                let scrollTimeout;
                this.slider.addEventListener('scroll', () => {
                    if (scrollTimeout) return;
                    scrollTimeout = setTimeout(() => {
                        this.updateButtonStates();
                        scrollTimeout = null;
                    }, 100);
                }, { passive: true });
            }

            // Mouse drag
            if (this.enableSwipe) {
                let isDown = false;
                let startX = 0;
                let scrollLeft = 0;
                
                this.slider.addEventListener('mousedown', (e) => {
                    isDown = true;
                    startX = e.pageX - this.slider.offsetLeft;
                    scrollLeft = this.slider.scrollLeft;
                    this.slider.style.cursor = 'grabbing';
                });
                
                this.slider.addEventListener('mouseleave', () => {
                    isDown = false;
                    this.slider.style.cursor = 'grab';
                });
                
                this.slider.addEventListener('mouseup', () => {
                    isDown = false;
                    this.slider.style.cursor = 'grab';
                });
                
                this.slider.addEventListener('mousemove', (e) => {
                    if (!isDown) return;
                    e.preventDefault();
                    const x = e.pageX - this.slider.offsetLeft;
                    const walk = (x - startX) * 2;
                    this.slider.scrollLeft = scrollLeft - walk;
                });

                // Touch events
                let touchStartX = 0;
                let touchScrollLeft = 0;
                
                this.slider.addEventListener('touchstart', (e) => {
                    touchStartX = e.touches[0].pageX;
                    touchScrollLeft = this.slider.scrollLeft;
                }, { passive: true });
                
                this.slider.addEventListener('touchmove', (e) => {
                    const touchX = e.touches[0].pageX;
                    const walk = (touchX - touchStartX) * 2;
                    this.slider.scrollLeft = touchScrollLeft - walk;
                }, { passive: true });
            }

            // Keyboard navigation
            if (this.enableKeyboard) {
                this.slider.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        this.scrollSlider('prev');
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        this.scrollSlider('next');
                    }
                });
            }

            // Resize handler
            window.addEventListener('resize', () => {
                if (this.updateButtons) {
                    this.updateButtonStates();
                }
            });
        }
    }

    // Initialize all sliders on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Promotions slider (desktop)
        if (document.getElementById('promotionsSliderDesktop')) {
            new UnifiedSlider({
                sliderId: 'promotionsSliderDesktop',
                containerClass: 'promotions-slider-container',
                prevBtnClass: 'promo-prev-btn',
                nextBtnClass: 'promo-next-btn',
                itemClass: 'promo-card',
                desktopScroll: 4,
                mobileScroll: 2
            });
        }

        // Promotions slider
        if (document.getElementById('promotionsSlider')) {
            new UnifiedSlider({
                sliderId: 'promotionsSlider',
                containerClass: 'promotions-slider-container',
                prevBtnClass: 'promo-prev-btn',
                nextBtnClass: 'promo-next-btn',
                itemClass: 'promo-card',
                desktopScroll: 4,
                mobileScroll: 2
            });
        }

        // Top products slider
        if (document.getElementById('topProductsSlider')) {
            new UnifiedSlider({
                sliderId: 'topProductsSlider',
                containerClass: 'promotions-slider-container',
                prevBtnClass: 'promo-prev-btn',
                nextBtnClass: 'promo-next-btn',
                itemClass: 'promo-card',
                desktopScroll: 4,
                mobileScroll: 2
            });
        }

        // Reviews slider
        if (document.getElementById('reviewsSlider')) {
            new UnifiedSlider({
                sliderId: 'reviewsSlider',
                containerClass: 'reviews-slider-container',
                prevBtnClass: 'reviews-prev-btn',
                nextBtnClass: 'reviews-next-btn',
                itemClass: 'review-card',
                desktopScroll: 2,
                mobileScroll: 1,
                gap: { desktop: 24, mobile: 20 }
            });

            // Review "Read more" functionality
            document.querySelectorAll('.review-read-more').forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const textElement = this.previousElementSibling;
                    const card = this.closest('.review-card');
                    
                    if (textElement.classList.contains('collapsed')) {
                        textElement.classList.remove('collapsed');
                        textElement.classList.add('expanded');
                        card.classList.add('expanded');
                        this.textContent = 'Згорнути ↑';
                    } else {
                        textElement.classList.remove('expanded');
                        textElement.classList.add('collapsed');
                        card.classList.remove('expanded');
                        this.textContent = 'Читати далі →';
                    }
                });
            });
        }
    });

    // Export для глобального використання
    window.UnifiedSlider = UnifiedSlider;
})();

