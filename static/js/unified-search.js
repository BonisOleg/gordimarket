/**
 * UNIFIED SEARCH MODULE
 * Об'єднує live-search.js та mobile-search.js
 * Підтримує desktop autocomplete та mobile search toggle
 */

(function() {
    'use strict';

    class UnifiedSearch {
        constructor() {
            // Desktop elements
            this.searchInput = document.getElementById('searchInput');
            this.autocomplete = document.getElementById('searchAutocomplete');
            
            // Mobile elements
            this.mobileSearchToggle = document.getElementById('mobileSearchToggle');
            this.mobileSearchForm = document.getElementById('mobileSearchForm');
            this.mobileSearchClose = document.getElementById('mobileSearchClose');
            this.mobileSearchInput = document.getElementById('mobileSearchInput');
            this.logo = document.querySelector('.logo');
            this.headerContent = document.querySelector('.header-content');
            
            // State
            this.isMobileSearchOpen = false;
            this.debounceTimer = null;
            this.currentRequest = null;
            this.lastQuery = '';
            this.searchCache = new Map();
            this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
            
            this.init();
        }

        init() {
            this.initDesktopSearch();
            this.initMobileSearch();
        }

        // ==================== DESKTOP SEARCH ====================
        
        initDesktopSearch() {
            if (!this.searchInput || !this.autocomplete) return;
            
            this.searchInput.addEventListener('input', (e) => {
                this.handleDesktopSearch(e.target.value);
            });
            
            // Close autocomplete on outside click
            document.addEventListener('click', (e) => {
                if (!this.searchInput.contains(e.target) && !this.autocomplete.contains(e.target)) {
                    this.autocomplete.classList.remove('active');
                }
            });
            
            // Close on Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.autocomplete.classList.remove('active');
                }
            });
        }

        handleDesktopSearch(query) {
            query = query.trim();
            
            clearTimeout(this.debounceTimer);
            
            // Cancel previous request
            if (this.currentRequest) {
                this.currentRequest.abort();
                this.currentRequest = null;
            }
            
            if (query.length < 2) {
                this.autocomplete.innerHTML = '';
                this.autocomplete.classList.remove('active');
                this.lastQuery = '';
                return;
            }
            
            this.debounceTimer = setTimeout(() => {
                this.lastQuery = query;
                this.performSearch(query);
            }, 400);
        }

        async performSearch(query) {
            // Check cache
            const cacheKey = query.toLowerCase();
            const cached = this.searchCache.get(cacheKey);
            
            if (cached && (Date.now() - cached.timestamp < this.CACHE_DURATION)) {
                this.displayResults(cached.data);
                return;
            }
            
            // Clean old cache entries
            if (this.searchCache.size > 50) {
                this.cleanCache();
            }
            
            // Create AbortController
            const controller = new AbortController();
            this.currentRequest = controller;
            
            try {
                const response = await fetch(`/api/search/autocomplete/?q=${encodeURIComponent(query)}`, {
                    signal: controller.signal
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                
                if (query !== this.lastQuery) return;
                
                this.currentRequest = null;
                
                // Cache results
                this.searchCache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
                
                this.displayResults(data);
            } catch (err) {
                this.currentRequest = null;
                
                if (err.name === 'AbortError') return;
                
                console.error('Search error:', err);
                
                if (query === this.lastQuery) {
                    this.autocomplete.innerHTML = '<div class="autocomplete-empty">Нічого не знайдено</div>';
                    this.autocomplete.classList.add('active');
                }
            }
        }

        displayResults(data) {
            if (data.results && data.results.length > 0) {
                this.autocomplete.innerHTML = data.results.map(item => {
                    const imageHtml = item.image 
                        ? `<img src="${item.image}" alt="${item.name}" loading="lazy" width="50" height="50">` 
                        : '<div class="autocomplete-placeholder">📦</div>';
                    return `
                        <a href="${item.url}" class="autocomplete-item" data-product-url="${item.url}">
                            ${imageHtml}
                            <span class="autocomplete-name">${item.name}</span>
                            <span class="autocomplete-price">${item.price} ₴</span>
                        </a>
                    `;
                }).join('');
                this.autocomplete.classList.add('active');
                
                this.autocomplete.querySelectorAll('.autocomplete-item').forEach(item => {
                    item.addEventListener('click', function(e) {
                        e.preventDefault();
                        const url = this.getAttribute('data-product-url');
                        if (url) window.location.href = url;
                    });
                });
            } else {
                this.autocomplete.innerHTML = '<div class="autocomplete-empty">Нічого не знайдено</div>';
                this.autocomplete.classList.add('active');
            }
        }

        cleanCache() {
            const now = Date.now();
            for (const [key, value] of this.searchCache.entries()) {
                if (now - value.timestamp > this.CACHE_DURATION) {
                    this.searchCache.delete(key);
                }
            }
        }

        // ==================== MOBILE SEARCH ====================
        
        initMobileSearch() {
            if (!this.mobileSearchToggle || !this.mobileSearchForm) return;
            
            // Open search
            this.mobileSearchToggle.addEventListener('click', () => this.openMobileSearch());
            
            // Close search
            if (this.mobileSearchClose) {
                this.mobileSearchClose.addEventListener('click', () => this.closeMobileSearch());
            }
            
            // Close on ESC
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isMobileSearchOpen) {
                    this.closeMobileSearch();
                }
            });
            
            // Close on outside click (mobile only)
            document.addEventListener('click', (e) => {
                if (this.isMobileSearchOpen && 
                    window.innerWidth <= 768 && 
                    !this.mobileSearchForm.contains(e.target) && 
                    !this.mobileSearchToggle.contains(e.target)) {
                    this.closeMobileSearch();
                }
            });
            
            // Form submit validation
            if (this.mobileSearchForm.querySelector('.mobile-search-form')) {
                this.mobileSearchForm.querySelector('.mobile-search-form').addEventListener('submit', (e) => {
                    const query = this.mobileSearchInput.value.trim();
                    if (!query) {
                        e.preventDefault();
                        this.mobileSearchInput.focus();
                        return false;
                    }
                });
            }
            
            // Auto focus after transition
            this.mobileSearchForm.addEventListener('transitionend', () => {
                if (this.isMobileSearchOpen && this.mobileSearchInput) {
                    this.mobileSearchInput.focus();
                }
            });
            
            // Close on window resize
            window.addEventListener('resize', () => {
                if (window.innerWidth > 768 && this.isMobileSearchOpen) {
                    this.closeMobileSearch();
                }
            });
        }

        openMobileSearch() {
            if (this.isMobileSearchOpen) return;
            
            this.isMobileSearchOpen = true;
            
            // Add animation classes
            if (this.headerContent) this.headerContent.classList.add('search-mode');
            if (this.logo) this.logo.classList.add('logo-hidden');
            this.mobileSearchForm.classList.add('search-form-visible');
            this.mobileSearchToggle.classList.add('search-btn-hidden');
            
            // Accessibility
            this.mobileSearchToggle.setAttribute('aria-expanded', 'true');
            this.mobileSearchForm.setAttribute('aria-hidden', 'false');
            
            // Focus with delay for animation
            setTimeout(() => {
                if (this.mobileSearchInput) {
                    this.mobileSearchInput.focus();
                }
            }, 300);
        }

        closeMobileSearch() {
            if (!this.isMobileSearchOpen) return;
            
            this.isMobileSearchOpen = false;
            
            // Remove animation classes
            if (this.headerContent) this.headerContent.classList.remove('search-mode');
            if (this.logo) this.logo.classList.remove('logo-hidden');
            this.mobileSearchForm.classList.remove('search-form-visible');
            this.mobileSearchToggle.classList.remove('search-btn-hidden');
            
            // Accessibility
            this.mobileSearchToggle.setAttribute('aria-expanded', 'false');
            this.mobileSearchForm.setAttribute('aria-hidden', 'true');
            
            // Clear input
            if (this.mobileSearchInput) {
                this.mobileSearchInput.value = '';
                this.mobileSearchInput.blur();
            }
        }

        // ==================== PUBLIC API ====================
        
        clearCache() {
            this.searchCache.clear();
        }

        getCacheSize() {
            return this.searchCache.size;
        }

        // Mobile search API
        toggleMobileSearch() {
            if (this.isMobileSearchOpen) {
                this.closeMobileSearch();
            } else {
                this.openMobileSearch();
            }
        }

        isMobileSearchActive() {
            return this.isMobileSearchOpen;
        }
    }

    // Initialize on DOM ready
    let unifiedSearch = null;

    function initSearch() {
        if (!unifiedSearch) {
            unifiedSearch = new UnifiedSearch();
        }
        return unifiedSearch;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

    // Export for global use
    window.UnifiedSearch = UnifiedSearch;
    window.getSearchManager = () => {
        if (!unifiedSearch) {
            unifiedSearch = initSearch();
        }
        return unifiedSearch;
    };

    // Legacy compatibility
    window.MobileSearch = {
        open: () => window.getSearchManager().openMobileSearch(),
        close: () => window.getSearchManager().closeMobileSearch(),
        toggle: () => window.getSearchManager().toggleMobileSearch(),
        isOpen: () => window.getSearchManager().isMobileSearchActive()
    };
})();

