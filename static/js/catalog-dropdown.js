'use strict';

(function () {
    function initCatalogDropdown() {
        var btn = document.getElementById('catalogToggleBtn');
        var dropdown = document.getElementById('catalogDropdown');
        var catalog = document.getElementById('navCatalog');
        if (!btn || !dropdown) return;

        var parentItems = catalog.querySelectorAll('.catalog-dropdown__parent-item');
        var subPanels = catalog.querySelectorAll('.catalog-dropdown__sub-panel');
        var activeParentId = null;

        function showDropdown() {
            dropdown.setAttribute('aria-hidden', 'false');
            btn.setAttribute('aria-expanded', 'true');
            catalog.classList.add('is-open');
            // Show first parent's subs by default
            if (parentItems.length && !activeParentId) {
                activateParent(parentItems[0].dataset.catId);
            }
        }

        function hideDropdown() {
            dropdown.setAttribute('aria-hidden', 'true');
            btn.setAttribute('aria-expanded', 'false');
            catalog.classList.remove('is-open');
            activeParentId = null;
            subPanels.forEach(function (p) {
                p.setAttribute('aria-hidden', 'true');
                p.classList.remove('is-active');
            });
            parentItems.forEach(function (p) {
                p.classList.remove('is-active');
            });
        }

        function activateParent(catId) {
            activeParentId = catId;
            parentItems.forEach(function (item) {
                item.classList.toggle('is-active', item.dataset.catId === catId);
            });
            subPanels.forEach(function (panel) {
                var isMatch = panel.dataset.parentId === catId;
                panel.classList.toggle('is-active', isMatch);
                panel.setAttribute('aria-hidden', isMatch ? 'false' : 'true');
            });
        }

        // Toggle on button click
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (catalog.classList.contains('is-open')) {
                hideDropdown();
            } else {
                showDropdown();
            }
        });

        // Hover on parent items
        parentItems.forEach(function (item) {
            item.addEventListener('mouseenter', function () {
                if (catalog.classList.contains('is-open')) {
                    activateParent(item.dataset.catId);
                }
            });
            item.addEventListener('focus', function () {
                if (catalog.classList.contains('is-open')) {
                    activateParent(item.dataset.catId);
                }
            });
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (!catalog.contains(e.target)) {
                hideDropdown();
            }
        });

        // Close on Escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                hideDropdown();
                btn.focus();
            }
        });
    }

    // Search toggle in nav bar
    function initNavSearch() {
        var toggleBtn = document.getElementById('headerSearchToggle');
        var container = document.getElementById('navSearchContainer');
        var closeBtn = document.getElementById('navSearchClose');
        var input = document.getElementById('navSearchInput');
        var mobileForm = document.getElementById('mobileSearchForm');
        var mobileClose = document.getElementById('mobileSearchClose');
        var mobileInput = document.getElementById('mobileSearchInput');

        var isMobile = function () {
            return window.innerWidth < 992;
        };

        if (toggleBtn) {
            toggleBtn.addEventListener('click', function () {
                if (isMobile()) {
                    if (mobileForm) {
                        var open = mobileForm.classList.toggle('is-open');
                        if (open && mobileInput) mobileInput.focus();
                    }
                } else {
                    if (container) {
                        var open = container.classList.toggle('is-open');
                        if (open && input) input.focus();
                    }
                }
            });
        }

        if (closeBtn && container) {
            closeBtn.addEventListener('click', function () {
                container.classList.remove('is-open');
            });
        }

        if (mobileClose && mobileForm) {
            mobileClose.addEventListener('click', function () {
                mobileForm.classList.remove('is-open');
            });
        }

        // Close search on outside click
        document.addEventListener('click', function (e) {
            if (container && !container.contains(e.target) && toggleBtn && !toggleBtn.contains(e.target)) {
                container.classList.remove('is-open');
            }
        });
    }

    function renderAutocomplete(results, box) {
        if (!results.length) {
            box.innerHTML = '<div class="autocomplete-empty">Нічого не знайдено</div>';
            box.classList.add('active');
            return;
        }
        var html = results.slice(0, 8).map(function (item) {
            var img = item.image
                ? '<img src="' + item.image + '" alt="" loading="lazy">'
                : '<div class="autocomplete-placeholder">📦</div>';
            var cat = item.category
                ? '<span class="autocomplete-category">' + item.category + '</span>'
                : '';
            return '<a href="' + item.url + '" class="autocomplete-item">' +
                img +
                '<div class="autocomplete-info">' +
                '<span class="autocomplete-name">' + item.name + '</span>' +
                cat +
                '</div>' +
                '<span class="autocomplete-price">' + item.price + ' ₴</span>' +
                '</a>';
        }).join('');
        box.innerHTML = html;
        box.classList.add('active');
    }

    function attachAutocomplete(input, box) {
        if (!input || !box) return;

        var timer = null;
        var controller = null;

        input.addEventListener('input', function () {
            clearTimeout(timer);
            if (controller) { controller.abort(); controller = null; }

            var q = input.value.trim();
            if (q.length < 2) {
                box.innerHTML = '';
                box.classList.remove('active');
                return;
            }
            timer = setTimeout(function () {
                controller = new AbortController();
                fetch('/api/search/autocomplete/?q=' + encodeURIComponent(q), {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    signal: controller.signal
                })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        renderAutocomplete(data.results || [], box);
                    })
                    .catch(function (err) {
                        if (err.name !== 'AbortError') { /* silent */ }
                    });
            }, 150);
        });

        document.addEventListener('click', function (e) {
            if (!box.contains(e.target) && e.target !== input) {
                box.innerHTML = '';
                box.classList.remove('active');
            }
        });
    }

    function initSearchAutocomplete() {
        attachAutocomplete(
            document.getElementById('navSearchInput'),
            document.getElementById('searchAutocomplete')
        );
    }

    function initMobileSearchAutocomplete() {
        var mobileInput = document.getElementById('mobileSearchInput');
        if (!mobileInput) return;

        var existing = document.getElementById('mobileSearchAutocomplete');
        if (!existing) {
            existing = document.createElement('div');
            existing.className = 'search-autocomplete';
            existing.id = 'mobileSearchAutocomplete';
            var inputGroup = mobileInput.closest('.mobile-search-input-group');
            if (inputGroup) {
                inputGroup.parentNode.insertBefore(existing, inputGroup.nextSibling);
            }
        }
        attachAutocomplete(mobileInput, existing);
    }

    document.addEventListener('DOMContentLoaded', function () {
        initCatalogDropdown();
        initNavSearch();
        initSearchAutocomplete();
        initMobileSearchAutocomplete();
    });
}());
