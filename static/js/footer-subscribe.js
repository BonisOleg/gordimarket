/**
 * Обробка форми підписки на розсилку (десктоп і мобільна версії)
 */

document.addEventListener('DOMContentLoaded', function() {
    const desktopForm = document.getElementById('desktopSubscribeForm');
    if (desktopForm) {
        desktopForm.addEventListener('submit', handleSubscribe);
    }

    const mobileForm = document.getElementById('mobileSubscribeForm');
    if (mobileForm) {
        mobileForm.addEventListener('submit', handleSubscribe);
    }
});

function handleSubscribe(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('.btn-subscribe');
    const originalText = submitBtn.textContent;

    const formData = new FormData(form);
    const name = formData.get('name');
    const email = formData.get('email');
    const privacy = form.querySelector('input[name="privacy"]');

    if (!name || !email) {
        showMessage(form, 'Будь ласка, заповніть всі поля', 'error');
        return;
    }

    if (privacy && !privacy.checked) {
        showMessage(form, 'Необхідно дати згоду на обробку персональних даних', 'error');
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage(form, 'Введіть коректну email адресу', 'error');
        return;
    }

    submitBtn.textContent = 'Відправка...';
    submitBtn.disabled = true;

    // Замінити на реальний API endpoint:
    // fetch('/api/subscribe/', { method: 'POST', ... })
    setTimeout(() => {
        showMessage(form, 'Дякуємо за підписку! Перевірте свою пошту.', 'success');
        form.reset();
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }, 1500);
}

function showMessage(form, message, type) {
    const existingMessage = form.querySelector('.subscribe-message');
    if (existingMessage) {
        existingMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `subscribe-message subscribe-message--${type}`;
    messageDiv.textContent = message;

    const submitBtn = form.querySelector('.btn-subscribe');
    form.insertBefore(messageDiv, submitBtn);

    setTimeout(() => {
        messageDiv.classList.add('subscribe-message--fadeout');
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

/**
 * Обробка кнопки "Інформація" у футері
 */
document.addEventListener('DOMContentLoaded', function() {
    const infoToggle = document.getElementById('footerInfoToggle');
    const infoDropdown = document.getElementById('footerInfoDropdown');

    if (infoToggle && infoDropdown) {
        infoToggle.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', String(!isExpanded));
            infoDropdown.setAttribute('aria-hidden', String(isExpanded));
            infoDropdown.classList.toggle('footer-info-open', !isExpanded);
        });
    }
});
