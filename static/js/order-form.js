document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('orderForm');
    const submitBtn = document.getElementById('submitBtn');
    const deliveryRadios = document.querySelectorAll('input[name="delivery_method"]');
    const novaPoshtaFields = document.getElementById('novaPoshtaFields');
    const ukrposhtaFields = document.getElementById('ukrposhtaFields');
    const phoneInput = document.querySelector('input[name="phone"]');
    const emailInput = document.querySelector('input[name="email"]');
    
    if (!deliveryRadios.length || !form) return;
    
    function toggleDeliveryFields() {
        const selectedDelivery = document.querySelector('input[name="delivery_method"]:checked');
        
        if (!selectedDelivery) {
            novaPoshtaFields?.classList.remove('active');
            ukrposhtaFields?.classList.remove('active');
            return;
        }
        
        if (selectedDelivery.value === 'nova_poshta') {
            novaPoshtaFields?.classList.add('active');
            ukrposhtaFields?.classList.remove('active');
        } else if (selectedDelivery.value === 'ukrposhta') {
            ukrposhtaFields?.classList.add('active');
            novaPoshtaFields?.classList.remove('active');
        }
    }
    
    deliveryRadios.forEach(radio => {
        radio.addEventListener('change', toggleDeliveryFields);
    });
    
    toggleDeliveryFields();
    
    const paymentOnline = document.querySelector('input[name="payment_method"][value="online"]');
    const deliveryNP = document.querySelector('input[name="delivery_method"][value="nova_poshta"]');
    
    if (paymentOnline && !document.querySelector('input[name="payment_method"]:checked')) {
        paymentOnline.checked = true;
    }
    if (deliveryNP && !document.querySelector('input[name="delivery_method"]:checked')) {
        deliveryNP.checked = true;
        toggleDeliveryFields();
    }
    
    if (phoneInput) {
        if (!phoneInput.value || phoneInput.value === '+' || phoneInput.value === '') {
            phoneInput.value = '+380';
        }
        phoneInput.placeholder = '+380(__) ___-__-__';
        
        phoneInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.startsWith('3800')) {
                value = '380' + value.substring(4);
            } else if (value.startsWith('0') && !value.startsWith('380')) {
                value = '380' + value.substring(1);
            } else if (!value.startsWith('380')) {
                value = '380' + value;
            }
            
            if (value.length > 12) {
                value = value.substring(0, 12);
            }
            
            e.target.value = '+' + value;
        });
        
        phoneInput.addEventListener('keydown', (e) => {
            if (e.target.selectionStart < 4 && ['Backspace', 'Delete'].includes(e.key)) {
                e.preventDefault();
            }
        });
    }
    
    if (emailInput) {
        const validateEmail = () => {
            const value = emailInput.value.trim();
            let errorEl = emailInput.parentElement.querySelector('.error');
            
            if (value && !value.includes('@')) {
                emailInput.classList.add('invalid');
                if (!errorEl) {
                    errorEl = document.createElement('span');
                    errorEl.className = 'error';
                    emailInput.parentElement.appendChild(errorEl);
                }
                errorEl.textContent = 'Невірний формат email';
            } else {
                emailInput.classList.remove('invalid');
                if (errorEl) errorEl.remove();
            }
        };
        
        emailInput.addEventListener('blur', validateEmail);
        emailInput.addEventListener('input', validateEmail);
    }
    
    form.addEventListener('submit', (e) => {
        const deliveryMethod = document.querySelector('input[name="delivery_method"]:checked');
        
        if (deliveryMethod && deliveryMethod.value === 'nova_poshta') {
            const cityRef = document.querySelector('input[name="nova_poshta_city_ref"]');
            const warehouseRef = document.querySelector('input[name="nova_poshta_warehouse_ref"]');
            const cityInput = document.querySelector('input[name="nova_poshta_city"]');
            const warehouseInput = document.querySelector('input[name="nova_poshta_warehouse"]');
            
            let hasError = false;
            
            if (!cityRef || !cityRef.value) {
                if (cityInput) {
                    const errorEl = cityInput.parentElement.querySelector('.error') || document.createElement('div');
                    errorEl.className = 'error';
                    errorEl.textContent = 'Виберіть місто зі списку автодоповнення';
                    if (!cityInput.parentElement.querySelector('.error')) {
                        cityInput.parentElement.appendChild(errorEl);
                    }
                    cityInput.classList.add('invalid');
                }
                hasError = true;
            }
            
            if (!warehouseRef || !warehouseRef.value) {
                if (warehouseInput) {
                    const errorEl = warehouseInput.parentElement.querySelector('.error') || document.createElement('div');
                    errorEl.className = 'error';
                    errorEl.textContent = 'Виберіть відділення зі списку автодоповнення';
                    if (!warehouseInput.parentElement.querySelector('.error')) {
                        warehouseInput.parentElement.appendChild(errorEl);
                    }
                    warehouseInput.classList.add('invalid');
                }
                hasError = true;
            }
            
            if (hasError) {
                e.preventDefault();
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Оформити замовлення';
                }
                window.scrollTo({ top: 0, behavior: 'smooth' });
                return false;
            }
        }
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Обробка...';
        }
    });
});

