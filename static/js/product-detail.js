'use strict';

(function () {
    function initProductTabs() {
        var tabBtns = document.querySelectorAll('.tab-btn');
        var tabPanels = document.querySelectorAll('.tab-panel');
        if (!tabBtns.length) return;

        tabBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var tabId = this.dataset.tab;
                tabBtns.forEach(function (b) { b.classList.remove('active'); });
                tabPanels.forEach(function (p) { p.classList.remove('active'); });
                this.classList.add('active');
                var panel = document.getElementById(tabId);
                if (panel) panel.classList.add('active');
            });
        });
    }

    function initProductGallery() {
        var thumbnails = document.querySelectorAll('.thumbnail');
        var currentImage = document.getElementById('currentImage');
        if (!thumbnails.length || !currentImage) return;

        thumbnails.forEach(function (thumb) {
            thumb.addEventListener('click', function () {
                var imageUrl = this.dataset.image;
                if (imageUrl) currentImage.src = imageUrl;
                thumbnails.forEach(function (t) { t.classList.remove('active'); });
                this.classList.add('active');
            });
        });
    }

    function initQuantityControl() {
        var quantityInput = document.getElementById('productQuantity');
        var quantityBtns = document.querySelectorAll('.quantity-btn');
        if (!quantityInput || !quantityBtns.length) return;

        quantityBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var action = this.dataset.action;
                var value = parseInt(quantityInput.value, 10);
                var max = parseInt(quantityInput.max, 10);

                if (action === 'increase' && value < max) {
                    quantityInput.value = value + 1;
                } else if (action === 'decrease' && value > 1) {
                    quantityInput.value = value - 1;
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initProductTabs();
        initProductGallery();
        initQuantityControl();
    });
}());
