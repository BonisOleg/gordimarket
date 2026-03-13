class MobileCatalog {
    constructor() {
        this.catalogBtn = document.getElementById('catalogMenuBtn');
        this.catalog = document.getElementById('mobile-catalog');
        this.overlay = document.getElementById('mobile-catalog-overlay');
        this.closeBtn = document.getElementById('mobile-catalog-close');
        this.body = document.body;
        this.isOpen = false;
        this.init();
    }

    init() {
        if (!this.catalog || !this.overlay || !this.catalogBtn) return;
        this.bindEvents();
    }

    bindEvents() {
        if (this.catalogBtn) {
            this.catalogBtn.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                this.openCatalog();
            });
        }

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', e => {
                e.preventDefault();
                this.closeCatalog();
            });
        }

        if (this.overlay) {
            this.overlay.addEventListener('click', () => {
                this.closeCatalog();
            });
        }

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeCatalog();
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth >= 992 && this.isOpen) {
                this.closeCatalog();
            }
        });

        const categoryToggles = document.querySelectorAll('.mobile-category-toggle');
        categoryToggles.forEach(toggle => {
            toggle.addEventListener('click', e => {
                e.preventDefault();
                this.toggleCategory(toggle);
            });
        });
    }

    toggleCategory(toggle) {
        const item = toggle.closest('.mobile-category-item');
        const subcategories = item.querySelector('.mobile-subcategories-list');
        const isActive = item.classList.contains('active');

        document.querySelectorAll('.mobile-category-item.active').forEach(activeItem => {
            if (activeItem !== item) {
                activeItem.classList.remove('active');
            }
        });

        if (isActive) {
            item.classList.remove('active');
        } else {
            item.classList.add('active');
        }
    }

    openCatalog() {
        this.isOpen = true;
        this.catalog.classList.add('active');
        this.overlay.classList.add('active');
        this.body.style.overflow = 'hidden';
        this.body.style.position = 'fixed';
        this.body.style.width = '100%';
        this.body.style.top = `-${window.scrollY}px`;
    }

    closeCatalog() {
        const scrollY = Math.abs(parseInt(this.body.style.top || '0'));
        this.isOpen = false;
        this.catalog.classList.remove('active');
        this.overlay.classList.remove('active');
        this.body.style.overflow = '';
        this.body.style.position = '';
        this.body.style.width = '';
        this.body.style.top = '';
        window.scrollTo(0, scrollY);

        document.querySelectorAll('.mobile-category-item.active').forEach(item => {
            item.classList.remove('active');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MobileCatalog();
});

