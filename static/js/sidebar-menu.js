/**
 * Sidebar Menu - Правильна логіка кліків
 * 
 * ЛОГІКА:
 * 1. Клік по НАЗВІ категорії → перехід на сторінку (показує ВСІ товари)
 * 2. Клік по СТРІЛЦІ → розгортання/згортання підменю
 * 3. Клік по підрозділу → перехід на сторінку підрозділу
 * 4. Активна категорія автоматично розгорнута
 */

(function() {
    'use strict';
    
    function initSidebarMenu() {
        const sidebar = document.querySelector('.sidebar-menu');
        if (!sidebar) {
            return;
        }
        
        const itemsWithChildren = sidebar.querySelectorAll('.sidebar-menu__item.has-children');
        
        console.log('Sidebar: Знайдено', itemsWithChildren.length, 'категорій з підрозділами');
        
        itemsWithChildren.forEach((item, index) => {
            const link = item.querySelector('.sidebar-menu__link');
            const arrow = item.querySelector('.sidebar-menu__arrow');
            const text = item.querySelector('.sidebar-menu__text');
            const submenu = item.querySelector('.sidebar-menu__submenu');
            
            if (!link || !submenu || !arrow) {
                console.warn('Sidebar: Не знайдено елементів для категорії', index);
                return;
            }
            
            // ВАЖЛИВО: Блокуємо перехід по всьому link
            link.addEventListener('click', function(e) {
                e.preventDefault();
            });
            
            // Клік по СТРІЛЦІ → розгортання підменю
            arrow.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('Sidebar: Клік по стрілці категорії', index);
                
                const isOpen = item.classList.contains('menu-open');
                
                // Закриваємо всі інші категорії
                itemsWithChildren.forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('menu-open')) {
                        closeSubmenu(otherItem);
                    }
                });
                
                // Перемикаємо поточну категорію
                if (isOpen) {
                    closeSubmenu(item);
                } else {
                    openSubmenu(item);
                }
            });
            
            // Клік по ТЕКСТУ категорії → перехід на сторінку
            if (text) {
                text.style.cursor = 'pointer';
                text.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('Sidebar: Перехід на сторінку категорії', link.href);
                    // Дозволяємо перехід
                    window.location.href = link.href;
                });
            }
            
            // Підрозділи працюють як звичайні посилання
            const subLinks = submenu.querySelectorAll('.submenu__link');
            subLinks.forEach(subLink => {
                subLink.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('Sidebar: Перехід на підрозділ');
                    // НЕ блокуємо перехід - працює за замовчуванням
                });
            });
        });
        
        // Автоматично відкриваємо активну категорію при завантаженні
        setTimeout(() => {
            const activeItem = sidebar.querySelector('.sidebar-menu__item.active.has-children');
            if (activeItem) {
                console.log('Sidebar: Відкриваємо активну категорію');
                openSubmenu(activeItem);
            }
        }, 100);
        
        // Закриваємо всі підменю при кліку поза sidebar
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.sidebar-menu')) {
                itemsWithChildren.forEach(item => {
                    if (item.classList.contains('menu-open')) {
                        closeSubmenu(item);
                    }
                });
            }
        });
        
        /**
         * Відкриває підменю
         */
        function openSubmenu(item) {
            const submenu = item.querySelector('.sidebar-menu__submenu');
            const arrow = item.querySelector('.sidebar-menu__arrow');
            
            if (!submenu) return;
            
            item.classList.add('menu-open');
            submenu.style.maxHeight = submenu.scrollHeight + 'px';
            
            if (arrow) {
                arrow.style.transform = 'rotate(90deg)';
            }
        }
        
        /**
         * Закриває підменю
         */
        function closeSubmenu(item) {
            const submenu = item.querySelector('.sidebar-menu__submenu');
            const arrow = item.querySelector('.sidebar-menu__arrow');
            
            if (!submenu) return;
            
            item.classList.remove('menu-open');
            submenu.style.maxHeight = '0';
            
            if (arrow) {
                arrow.style.transform = 'rotate(0deg)';
            }
        }
        
        // Оновлюємо maxHeight при зміні розміру вікна
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                itemsWithChildren.forEach(item => {
                    if (item.classList.contains('menu-open')) {
                        const submenu = item.querySelector('.sidebar-menu__submenu');
                        if (submenu) {
                            submenu.style.maxHeight = submenu.scrollHeight + 'px';
                        }
                    }
                });
            }, 250);
        });
    }
    
    // Ініціалізація
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSidebarMenu);
    } else {
        initSidebarMenu();
    }
    
})();
