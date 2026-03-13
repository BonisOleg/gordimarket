document.addEventListener('DOMContentLoaded', function() {
    const phoneToggle = document.getElementById('phoneToggle');
    const phonePopup = document.getElementById('phonePopup');
    const phonePopupClose = document.getElementById('phonePopupClose');
    const phoneCopyBtn = document.getElementById('phoneCopyBtn');
    
    if (!phoneToggle || !phonePopup) return;
    
    phoneToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        phonePopup.classList.toggle('active');
    });
    
    if (phonePopupClose) {
        phonePopupClose.addEventListener('click', function(e) {
            e.stopPropagation();
            phonePopup.classList.remove('active');
        });
    }
    
    document.addEventListener('click', function(e) {
        if (!phonePopup.contains(e.target) && e.target !== phoneToggle) {
            phonePopup.classList.remove('active');
        }
    });
    
    if (phoneCopyBtn) {
        phoneCopyBtn.addEventListener('click', function() {
            const phoneNumber = (phonePopup && phonePopup.dataset.phone) || document.body.dataset.phoneRaw || '';
            
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(phoneNumber).then(function() {
                    const originalText = phoneCopyBtn.innerHTML;
                    phoneCopyBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M20 6L9 17L4 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Скопійовано!';
                    
                    setTimeout(function() {
                        phoneCopyBtn.innerHTML = originalText;
                    }, 2000);
                });
            } else {
                const textarea = document.createElement('textarea');
                textarea.value = phoneNumber;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                
                try {
                    document.execCommand('copy');
                    const originalText = phoneCopyBtn.innerHTML;
                    phoneCopyBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M20 6L9 17L4 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Скопійовано!';
                    
                    setTimeout(function() {
                        phoneCopyBtn.innerHTML = originalText;
                    }, 2000);
                } catch (err) {
                    console.error('Помилка копіювання:', err);
                }
                
                document.body.removeChild(textarea);
            }
        });
    }
});

