/**
 * Age Verification Modal (18+)
 * Generic — reads site name and logo from data attributes on <body>
 */

(function() {
  'use strict';

  const AGE_COOKIE_NAME = 'age_verified';
  const AGE_COOKIE_DAYS = 1;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  }

  function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=/;SameSite=Strict`;
  }

  function showAgeModal() {
    const body = document.body;
    const siteName = body.dataset.siteName || '';
    const logoUrl = body.dataset.logoUrl || '';
    const customText = body.dataset.ageVerificationText || '';

    const defaultText = 'Цей сайт містить матеріали для дорослих.<br>Щоб продовжити, підтвердіть, що вам виповнилося 18 років.';
    const modalText = customText || defaultText;

    const overlay = document.createElement('div');
    overlay.className = 'age-modal-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'age-modal-title');
    overlay.setAttribute('aria-describedby', 'age-modal-desc');

    overlay.innerHTML = `
      <div class="age-modal">
        <div class="age-modal__logo">
          ${logoUrl ? `<img src="${logoUrl}" alt="${siteName}" class="age-modal__logo-img">` : ''}
          ${siteName ? `<span class="age-modal__logo-text">${siteName}</span>` : ''}
        </div>
        <h2 class="age-modal__title" id="age-modal-title">УВАГА!</h2>
        <p class="age-modal__text" id="age-modal-desc">${modalText}</p>
        <div class="age-modal__buttons">
          <button class="age-modal__btn age-modal__btn--deny" id="ageDenyBtn" type="button">
            Ні, мені менше 18 років
          </button>
          <button class="age-modal__btn age-modal__btn--confirm" id="ageConfirmBtn" type="button">
            Так, мені вже є 18
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    document.addEventListener('keydown', preventEscape);

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        e.stopPropagation();
        e.preventDefault();
      }
    });

    document.getElementById('ageConfirmBtn').addEventListener('click', function() {
      setCookie(AGE_COOKIE_NAME, '1', AGE_COOKIE_DAYS);
      document.removeEventListener('keydown', preventEscape);

      overlay.style.animation = 'fadeOut 0.3s ease forwards';
      setTimeout(function() {
        overlay.remove();
        document.body.style.overflow = '';
      }, 300);
    });

    document.getElementById('ageDenyBtn').addEventListener('click', function() {
      window.location.href = 'https://www.google.com';
    });
  }

  function preventEscape(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  }

  function initAgeVerification() {
    if (document.body.dataset.ageVerification !== 'true') return;
    if (!getCookie(AGE_COOKIE_NAME)) {
      setTimeout(showAgeModal, 500);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAgeVerification);
  } else {
    initAgeVerification();
  }

})();
