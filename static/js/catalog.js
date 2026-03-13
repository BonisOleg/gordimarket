'use strict';

class CatalogManager {
    constructor() {
        this.form = document.getElementById('filtersForm');
        this.sortInput = document.getElementById('sortInput');
        this.productsGrid = document.getElementById('productsGrid');
        this.skeletonGrid = document.getElementById('skeletonGrid');
        if (!this.form) return;

        this.init();
    }

    init() {
        this.restoreCheckboxState();
        this.bindFiltersToggle();
        this.bindSortDropdowns();
        this.bindFormSubmit();
        this.bindClearButtons();
        this.bindActiveFilterChips();
        this.initMobileFilters();
    }

    restoreCheckboxState() {
        var params = new URLSearchParams(window.location.search);
        this.form.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            var values = params.getAll(cb.name);
            if (values.indexOf(cb.value) !== -1) {
                cb.checked = true;
            }
        });
    }

    bindFiltersToggle() {
        var toggle = document.getElementById('filtersToggle');
        var content = document.getElementById('filtersContent');
        if (!toggle || !content) return;

        toggle.addEventListener('click', function () {
            toggle.classList.toggle('active');
            content.classList.toggle('active');
        });
    }

    bindSortDropdowns() {
        var self = this;

        this._bindSortDropdown(
            document.getElementById('desktopSortBtn'),
            document.getElementById('desktopSortDropdown'),
            '.sort-text'
        );

        this._bindSortDropdown(
            document.getElementById('sortSelectBtn'),
            document.getElementById('sortDropdown'),
            '.sort-select-text'
        );
    }

    _bindSortDropdown(btn, dropdown, textSelector) {
        if (!btn || !dropdown) return;
        var self = this;

        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            btn.classList.toggle('active');
        });

        dropdown.querySelectorAll('.sort-option').forEach(function (option) {
            option.addEventListener('click', function () {
                var value = option.dataset.value;
                self.sortInput.value = value;
                btn.querySelector(textSelector).textContent = option.textContent.trim();
                dropdown.classList.add('hidden');
                btn.classList.remove('active');
                self.submitForm();
            });
        });

        document.addEventListener('click', function (e) {
            if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.add('hidden');
                btn.classList.remove('active');
            }
        });
    }

    bindFormSubmit() {
        var self = this;
        var priceTimer = null;

        var priceMin = document.getElementById('priceMin');
        var priceMax = document.getElementById('priceMax');

        if (priceMin) {
            priceMin.addEventListener('input', function () {
                clearTimeout(priceTimer);
                priceTimer = setTimeout(function () { self.submitForm(); }, 800);
            });
        }
        if (priceMax) {
            priceMax.addEventListener('input', function () {
                clearTimeout(priceTimer);
                priceTimer = setTimeout(function () { self.submitForm(); }, 800);
            });
        }

        this.form.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            cb.addEventListener('change', function () {
                if (!self.isInMobileModal(cb)) {
                    self.submitForm();
                }
            });
        });
    }

    bindClearButtons() {
        var self = this;

        var clearBtn = document.getElementById('clearAllFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                self.clearAndSubmit();
            });
        }

        var clearActive = document.getElementById('clearActiveFilters');
        if (clearActive) {
            clearActive.addEventListener('click', function () {
                self.clearAndSubmit();
            });
        }
    }

    bindActiveFilterChips() {
        var self = this;
        document.querySelectorAll('.filter-chip .filter-chip__remove').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var chip = btn.closest('.filter-chip');
                var filterName = chip.dataset.filter;
                var filterValue = chip.dataset.value;

                if (filterName === 'price') {
                    var priceMin = document.getElementById('priceMin');
                    var priceMax = document.getElementById('priceMax');
                    if (priceMin) priceMin.value = '';
                    if (priceMax) priceMax.value = '';
                } else {
                    self.form.querySelectorAll('input[name="' + filterName + '"]').forEach(function (input) {
                        if (input.type === 'checkbox' && input.value === filterValue) {
                            input.checked = false;
                        }
                    });
                }
                self.submitForm();
            });
        });
    }

    clearAndSubmit() {
        this.form.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
            cb.checked = false;
        });
        var priceMin = document.getElementById('priceMin');
        var priceMax = document.getElementById('priceMax');
        if (priceMin) priceMin.value = '';
        if (priceMax) priceMax.value = '';
        this.sortInput.value = 'default';
        this.submitForm();
    }

    submitForm() {
        this.showSkeleton(true);

        var formData = new FormData(this.form);
        var params = new URLSearchParams();

        for (var pair of formData.entries()) {
            var value = pair[1].toString().trim();
            if (value && value !== '0' && value !== 'default') {
                params.append(pair[0], value);
            }
        }

        var sort = this.sortInput.value;
        if (sort && sort !== 'default') {
            params.set('sort', sort);
        }

        var qs = params.toString();
        window.location.href = window.location.pathname + (qs ? '?' + qs : '');
    }

    showSkeleton(show) {
        if (!this.productsGrid || !this.skeletonGrid) return;
        if (show) {
            this.productsGrid.classList.add('hidden');
            this.skeletonGrid.classList.remove('hidden');
        } else {
            this.productsGrid.classList.remove('hidden');
            this.skeletonGrid.classList.add('hidden');
        }
    }

    isInMobileModal(element) {
        return element.closest('.mobile-filters-modal') !== null;
    }

    initMobileFilters() {
        var self = this;
        var modal = document.getElementById('mobileFiltersModal');
        var openBtn = document.getElementById('mobileFiltersBtn');
        if (!modal || !openBtn) return;

        var modalContent = modal.querySelector('.modal-filters__content');
        var closeBtn = modal.querySelector('.modal-filters__close');
        var applyBtn = modal.querySelector('.modal-filters__apply');
        var clearBtn = modal.querySelector('.modal-filters__clear');

        openBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            self.openMobileModal(modal);
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                self.closeMobileModal(modal);
            });
        }

        modal.addEventListener('click', function (e) {
            if (modalContent && !modalContent.contains(e.target)) {
                self.closeMobileModal(modal);
            }
        });

        if (applyBtn) {
            applyBtn.addEventListener('click', function () {
                self.syncMobileToForm(modal);
                self.closeMobileModal(modal);
                self.submitForm();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                modal.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
                modal.querySelectorAll('input[type="number"]').forEach(function (inp) { inp.value = ''; });
                self.syncMobileToForm(modal);
                self.closeMobileModal(modal);
                self.clearAndSubmit();
            });
        }
    }

    openMobileModal(modal) {
        var filtersContent = document.getElementById('filtersContent');
        var modalBody = modal.querySelector('.modal-filters__body');
        if (!filtersContent || !modalBody) return;

        var clone = filtersContent.cloneNode(true);
        var actionsGroup = clone.querySelector('.filter-group--actions');
        if (actionsGroup) actionsGroup.remove();

        var filtersGrid = clone.querySelector('.filters-grid');
        modalBody.innerHTML = filtersGrid ? filtersGrid.innerHTML : '';

        modalBody.querySelectorAll('input').forEach(function (input) {
            var original;
            if (input.name && input.type === 'checkbox') {
                var sel = '#filtersContent input[name="' + input.name + '"][value="' + CSS.escape(input.value) + '"]';
                original = document.querySelector(sel);
                if (original) input.checked = original.checked;
            } else if (input.id) {
                original = document.getElementById(input.id);
                if (original) input.value = original.value;
            }
        });

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    syncMobileToForm(modal) {
        var modalBody = modal.querySelector('.modal-filters__body');
        if (!modalBody) return;

        modalBody.querySelectorAll('input').forEach(function (input) {
            var original;
            if (input.name && input.type === 'checkbox') {
                var sel = '#filtersContent input[name="' + input.name + '"][value="' + CSS.escape(input.value) + '"]';
                original = document.querySelector(sel);
                if (original) original.checked = input.checked;
            } else if (input.id) {
                original = document.getElementById(input.id);
                if (original) original.value = input.value;
            }
        });
    }

    closeMobileModal(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('filtersForm')) {
        new CatalogManager();
    }
});
