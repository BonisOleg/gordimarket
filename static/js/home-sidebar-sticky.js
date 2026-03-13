/**
 * Home Sidebar Sticky Behavior
 * 
 * Управляє sticky поведінкою sidebar на головній сторінці:
 * - Sidebar залишається статичним при скролі
 * - Зупиняється перед секцією "Відгуки користувачів"
 * - На інших сторінках працює стандартний sticky до футера
 */

(function() {
    'use strict';
    
    /**
     * Ініціалізація sticky поведінки для головної сторінки
     */
    function initHomeSidebarSticky() {
        // Перевіряємо чи ми на головній сторінці
        const sidebar = document.querySelector('.home-catalog-sidebar');
        const reviewsSection = document.querySelector('.reviews-section');
        
        if (!sidebar) {
            // Якщо немає .home-catalog-sidebar, виходимо
            return;
        }
        
        // Якщо немає секції відгуків, sidebar працює до футера (стандартно)
        if (!reviewsSection) {
            console.log('Home Sidebar: Секція відгуків не знайдена, sticky до футера');
            return;
        }
        
        console.log('Home Sidebar: Ініціалізація sticky з обмеженням до секції відгуків');
        
        const layoutGrid = document.querySelector('.layout-grid');
        
        if (!layoutGrid) {
            console.warn('Home Sidebar: Layout grid не знайдено');
            return;
        }
        
        // Змінні для відстеження
        let ticking = false;
        
        /**
         * Обчислює і застосовує правильну позицію sidebar
         */
        function updateSidebarPosition() {
            const sidebarRect = sidebar.getBoundingClientRect();
            const reviewsRect = reviewsSection.getBoundingClientRect();
            const layoutRect = layoutGrid.getBoundingClientRect();
            
            const sidebarHeight = sidebar.offsetHeight;
            const viewportHeight = window.innerHeight;
            const scrollY = window.scrollY || window.pageYOffset;
            
            // Відстань від низу sidebar до верху секції відгуків
            const sidebarBottom = sidebarRect.bottom;
            const reviewsTop = reviewsRect.top;
            const distanceToReviews = reviewsTop - sidebarBottom;
            
            // Обчислюємо абсолютну позицію секції відгуків на сторінці
            const reviewsAbsoluteTop = scrollY + reviewsRect.top;
            
            // Обчислюємо позицію де sidebar має зупинитися (перед секцією відгуків)
            const layoutTopOffset = layoutGrid.offsetTop;
            const stopPosition = reviewsAbsoluteTop - layoutTopOffset - sidebarHeight - 40; // 40px відступ
            
            // Якщо sidebar наближається до секції відгуків (менше 40px) і секція видима
            if (distanceToReviews <= 40 && reviewsRect.top < viewportHeight) {
                // Змінюємо на absolute позицію і фіксуємо на місці
                if (!sidebar.classList.contains('sidebar-stopped')) {
                    sidebar.classList.add('sidebar-stopped');
                    sidebar.style.position = 'absolute';
                    sidebar.style.top = stopPosition + 'px';
                    console.log('Home Sidebar: Зупинено перед секцією відгуків на позиції', stopPosition);
                }
            } else {
                // Повертаємо sticky поведінку (прибираємо inline стилі, щоб працював CSS)
                if (sidebar.classList.contains('sidebar-stopped')) {
                    sidebar.classList.remove('sidebar-stopped');
                    sidebar.style.position = '';
                    sidebar.style.top = '';
                    console.log('Home Sidebar: Повернено sticky поведінку');
                }
            }
            
            ticking = false;
        }
        
        /**
         * Оптимізований scroll handler з requestAnimationFrame
         */
        function onScroll() {
            if (!ticking) {
                window.requestAnimationFrame(updateSidebarPosition);
                ticking = true;
            }
        }
        
        /**
         * Обробка зміни розміру вікна
         */
        let resizeTimeout;
        function onResize() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                updateSidebarPosition();
            }, 150);
        }
        
        // Підписуємось на події
        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onResize);
        
        // Початкове обчислення
        setTimeout(updateSidebarPosition, 100);
        
        // Повторне обчислення після завантаження всіх ресурсів
        window.addEventListener('load', () => {
            setTimeout(updateSidebarPosition, 200);
        });
        
        console.log('Home Sidebar: Ініціалізовано успішно');
    }
    
    // Ініціалізація при завантаженні DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHomeSidebarSticky);
    } else {
        initHomeSidebarSticky();
    }
    
})();

