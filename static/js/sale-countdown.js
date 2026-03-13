document.addEventListener('DOMContentLoaded', function() {
    const countdowns = document.querySelectorAll('[data-countdown]');
    
    if (countdowns.length === 0) return;
    
    function updateCountdown(element) {
        const endTime = parseInt(element.dataset.countdown);
        if (!endTime) return;
        
        const now = Date.now();
        const diff = endTime - now;
        
        if (diff <= 0) {
            element.textContent = '⏰ Завершено';
            element.classList.add('countdown-ended');
            return false;
        }
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        let text = '⏰ ';
        if (days > 0) {
            text += `${days}д ${hours}г`;
        } else if (hours > 0) {
            text += `${hours}г ${minutes}хв`;
        } else if (minutes > 0) {
            text += `${minutes}хв ${seconds}с`;
        } else {
            text += `${seconds}с`;
        }
        
        element.textContent = text;
        return true;
    }
    
    countdowns.forEach(countdown => {
        updateCountdown(countdown);
        
        const interval = setInterval(() => {
            const stillActive = updateCountdown(countdown);
            if (!stillActive) {
                clearInterval(interval);
            }
        }, 1000);
    });
});

