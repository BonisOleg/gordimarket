/**
 * Динамічна пагінація для сторінки пошуку
 * Завантажує товари в реальному часі та оновлює лічильник
 */

(function() {
  // Перевіряємо чи є необхідні глобальні змінні
  if (!window.searchQuery || window.initialCount === undefined) {
    console.log('Search pagination: not initialized');
    return;
  }

  const query = window.searchQuery;
  const productsGrid = document.getElementById('searchProductsGrid');
  const resultsCount = document.getElementById('resultsCount');
  const searchLoading = document.getElementById('searchLoading');
  const searchPagination = document.getElementById('searchPagination');
  
  if (!productsGrid || !resultsCount) {
    console.error('Search pagination: required elements not found');
    return;
  }

  // Стан пагінації
  let currentPage = 1;
  let totalPages = 1;
  let totalCount = window.initialCount;
  let isLoading = false;
  let allProductsLoaded = false;

  /**
   * Оновлює лічильник результатів
   */
  function updateResultsCount(count) {
    totalCount = count;
    const plural = count % 10 === 1 && count % 100 !== 11 ? '' :
                   (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) ? 'и' : 'ів';
    resultsCount.textContent = `Знайдено ${count} товар${plural}`;
  }
  
  /**
   * Ініціалізує функціонал для доданих карток
   */
  function initializeProductCards() {
    // Ініціалізуємо таймери акцій
    const countdowns = productsGrid.querySelectorAll('[data-countdown]');
    countdowns.forEach(countdown => {
      updateCountdown(countdown);
      const interval = setInterval(() => {
        const stillActive = updateCountdown(countdown);
        if (!stillActive) clearInterval(interval);
      }, 1000);
    });
    
    // Ініціалізуємо кнопки списку бажань
    productsGrid.querySelectorAll('.product-card__wishlist').forEach(btn => {
      if (btn.hasAttribute('data-wishlist-initialized')) return;
      btn.setAttribute('data-wishlist-initialized', 'true');
    });
    
    // Використовуємо CartHandler для кнопок кошика
    if (window.cartHandler) {
      window.cartHandler.bindCartButtons();
    }
    
    // Оновлюємо стан wishlist кнопок
    if (window.wishlistManager) {
      window.wishlistManager.initializeWishlistState();
    }
  }
  
  /**
   * Оновлює таймер зворотного відліку
   */
  function updateCountdown(element) {
    const endTime = parseInt(element.dataset.countdown);
    if (!endTime) return false;
    
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
  
  
  function showToast(message, type = 'success') {
    if (window.Toast) {
      window.Toast.show(message, type);
    }
  }
  
  /**
   * Отримує CSRF токен з cookies
   */
  function getCookie(name) {
    if (name === 'csrftoken') {
      const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
      if (metaToken) return metaToken;
      
      const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      if (inputToken) return inputToken;
    }
    
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Створює HTML для картки товару
   */
  function createProductCard(product) {
    const imageHtml = product.image 
      ? `<img src="${product.image}" alt="${product.name}" loading="lazy" class="product-card__image" width="300" height="300">`
      : '<div class="product-card__placeholder">📦</div>';
    
    // Бейджі
    let badgesHtml = '';
    
    // Таймер акції
    if (product.is_sale && product.sale_end_timestamp) {
      badgesHtml += `<div class="sale-countdown" data-countdown="${product.sale_end_timestamp}">Завантаження...</div>`;
    }
    
    if (product.is_new) {
      badgesHtml += '<span class="product-badge product-badge--new">NEW</span>';
    }
    
    if (product.is_top) {
      badgesHtml += '<span class="product-badge product-badge--hit">ХІТ</span>';
    }
    
    // Ціна
    let priceHtml = '';
    if (product.is_sale && product.sale_price) {
      priceHtml = `
        <span class="product-card__price-current">${product.sale_price} ₴</span>
        <span class="product-card__price-old">${product.retail_price} ₴</span>
      `;
    } else {
      priceHtml = `<span class="product-card__price-current">${product.retail_price} ₴</span>`;
    }
    
    // Кнопка
    const buttonHtml = product.is_in_stock 
      ? `<button type="button" class="product-card__add-cart" data-product-id="${product.id}">До кошика</button>`
      : `<button type="button" class="product-card__add-cart product-card__add-cart--disabled" disabled>Немає в наявності</button>`;

    return `
      <article class="product-card" 
        data-sale-price="${product.is_sale ? product.sale_price : product.retail_price}"
        data-name="${product.name}"
        data-is-top="${product.is_top}"
        data-is-new="${product.is_new}"
        data-is-sale="${product.is_sale}"
        data-categories="">
        <div class="product-card__media">
          <a href="${product.url}">
            ${imageHtml}
          </a>
          
          <button 
            type="button"
            class="product-card__wishlist" 
            data-product-id="${product.id}" 
            aria-label="Додати в обране"
            title="Додати в обране">
            <span class="product-card__wishlist-icon">♡</span>
          </button>
          
          <div class="product-card__badges">
            ${badgesHtml}
          </div>
        </div>
        
        <div class="product-card__content">
          <h3 class="product-card__name">
            <a href="${product.url}" class="product-card__link">${product.name}</a>
          </h3>
          
          <div class="product-card__price">
            ${priceHtml}
          </div>
        </div>
        
        <div class="product-card__actions">
          ${buttonHtml}
        </div>
      </article>
    `;
  }

  /**
   * Завантажує товари для вказаної сторінки
   */
  async function loadPage(page) {
    if (isLoading) return;
    
    isLoading = true;
    if (searchLoading) searchLoading.style.display = 'block';

    try {
      const response = await fetch(`/api/search/paginated/?q=${encodeURIComponent(query)}&page=${page}&per_page=20`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Оновлюємо лічильник
      updateResultsCount(data.total_count);
      
      // Очищаємо сітку якщо це перша сторінка або нова сторінка
      if (page === 1 || page !== currentPage + 1) {
        productsGrid.innerHTML = '';
      }
      
      // Додаємо товари до сітки
      if (data.products && data.products.length > 0) {
        data.products.forEach(product => {
          const cardHtml = createProductCard(product);
          productsGrid.insertAdjacentHTML('beforeend', cardHtml);
        });
        
        // Ініціалізуємо функціонал після додавання карток
        initializeProductCards();
      } else if (page === 1) {
        productsGrid.innerHTML = '<div class="no-results">Товарів не знайдено</div>';
      }
      
      // Оновлюємо стан пагінації
      currentPage = data.current_page;
      totalPages = data.total_pages;
      allProductsLoaded = !data.has_next;
      
      // Оновлюємо пагінацію
      renderPagination(data);
      
    } catch (error) {
      console.error('Error loading search results:', error);
      resultsCount.textContent = 'Помилка завантаження результатів';
      if (page === 1) {
        productsGrid.innerHTML = '<div class="error-message">Помилка завантаження товарів. Спробуйте пізніше.</div>';
      }
    } finally {
      isLoading = false;
      if (searchLoading) searchLoading.style.display = 'none';
    }
  }

  /**
   * Створює HTML для пагінації
   */
  function renderPagination(data) {
    if (!searchPagination) return;
    
    if (data.total_pages <= 1) {
      searchPagination.innerHTML = '';
      return;
    }

    let paginationHtml = '<div class="pagination">';
    
    // Кнопка "Попередня"
    if (data.has_prev) {
      paginationHtml += `<button class="pagination__btn pagination__btn--prev" data-page="${data.current_page - 1}">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" fill="none"/>
        </svg>
        Назад
      </button>`;
    }
    
    // Номери сторінок
    paginationHtml += '<div class="pagination__numbers">';
    
    const maxVisible = 7;
    let startPage = Math.max(1, data.current_page - Math.floor(maxVisible / 2));
    let endPage = Math.min(data.total_pages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    // Перша сторінка
    if (startPage > 1) {
      paginationHtml += `<button class="pagination__number" data-page="1">1</button>`;
      if (startPage > 2) {
        paginationHtml += '<span class="pagination__ellipsis">...</span>';
      }
    }
    
    // Середні сторінки
    for (let i = startPage; i <= endPage; i++) {
      const isActive = i === data.current_page ? 'pagination__number--active' : '';
      paginationHtml += `<button class="pagination__number ${isActive}" data-page="${i}">${i}</button>`;
    }
    
    // Остання сторінка
    if (endPage < data.total_pages) {
      if (endPage < data.total_pages - 1) {
        paginationHtml += '<span class="pagination__ellipsis">...</span>';
      }
      paginationHtml += `<button class="pagination__number" data-page="${data.total_pages}">${data.total_pages}</button>`;
    }
    
    paginationHtml += '</div>';
    
    // Кнопка "Наступна"
    if (data.has_next) {
      paginationHtml += `<button class="pagination__btn pagination__btn--next" data-page="${data.current_page + 1}">
        Далі
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" fill="none"/>
        </svg>
      </button>`;
    }
    
    paginationHtml += '</div>';
    
    searchPagination.innerHTML = paginationHtml;
    
    // Додаємо обробники подій
    searchPagination.querySelectorAll('[data-page]').forEach(btn => {
      btn.addEventListener('click', function() {
        const page = parseInt(this.getAttribute('data-page'));
        if (page !== currentPage) {
          // Прокручуємо до початку результатів
          const searchResults = document.querySelector('.search-results');
          if (searchResults) {
            searchResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
          
          // Завантажуємо нову сторінку (очищення сітки відбудеться в loadPage)
          allProductsLoaded = false;
          loadPage(page);
        }
      });
    });
  }


  /**
   * Ініціалізація
   */
  function init() {
    const initialCards = productsGrid.querySelectorAll('.product-card');
    
    if (initialCards.length > 0) {
      // Є початкові товари від Django - просто ініціалізуємо функціонал
      initializeProductCards();
      updateResultsCount(window.initialCount || initialCards.length);
      
      // Завантажуємо дані для пагінації без очищення сітки
      fetchPaginationData();
    } else {
      // Немає товарів - завантажуємо з API
      loadPage(1);
    }
  }
  
  /**
   * Завантажує дані пагінації без очищення сітки
   */
  async function fetchPaginationData() {
    try {
      const response = await fetch(`/api/search/paginated/?q=${encodeURIComponent(query)}&page=1&per_page=20`);
      if (!response.ok) return;
      
      const data = await response.json();
      updateResultsCount(data.total_count);
      currentPage = 1;
      totalPages = data.total_pages;
      allProductsLoaded = !data.has_next;
      renderPagination(data);
    } catch (error) {
      console.error('Pagination data error:', error);
    }
  }

  // Запускаємо ініціалізацію
  if (query && productsGrid) {
    init();
  }
})();

