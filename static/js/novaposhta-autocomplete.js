class NovaPoshtaAutocomplete {
    constructor() {
        this.cityInput = document.querySelector('[data-type="city"]');
        this.warehouseInput = document.querySelector('[data-type="warehouse"]');
        this.cityRefInput = document.querySelector('input[name="nova_poshta_city_ref"]');
        this.warehouseRefInput = document.querySelector('input[name="nova_poshta_warehouse_ref"]');
        this.cityRef = null;
        this.debounceTimer = null;
        
        // Client-side кешування для мінімізації запитів
        this.citiesCache = new Map();
        this.warehousesCache = new Map();
        
        if (this.cityInput) {
            this.init();
        }
    }
    
    init() {
        this.createDropdowns();
        this.attachEvents();
    }
    
    createDropdowns() {
        // Dropdown для міста
        this.cityDropdown = this.createDropdownElement();
        this.cityInput.parentElement.style.position = 'relative';
        this.cityInput.parentElement.appendChild(this.cityDropdown);
        
        // Dropdown для відділення
        if (this.warehouseInput) {
            this.warehouseDropdown = this.createDropdownElement();
            this.warehouseInput.parentElement.style.position = 'relative';
            this.warehouseInput.parentElement.appendChild(this.warehouseDropdown);
        }
    }
    
    createDropdownElement() {
        const dropdown = document.createElement('div');
        dropdown.className = 'np-autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        return dropdown;
    }
    
    showLoading(dropdown) {
        dropdown.innerHTML = '<div style="padding: 15px; text-align: center; color: #999;"><span style="display: inline-block; width: 6px; height: 6px; background: #999; border-radius: 50%; margin: 0 3px; animation: pulse 1.5s infinite;"></span> Завантаження...</div>';
        dropdown.style.display = 'block';
    }
    
    showNoResults(dropdown, message) {
        dropdown.innerHTML = `<div style="padding: 15px; text-align: center; color: #999;">${message}</div>`;
        dropdown.style.display = 'block';
    }
    
    showError(dropdown, message) {
        dropdown.innerHTML = `<div style="padding: 15px; text-align: center; color: #e74c3c; font-weight: 500;">⚠ ${message}</div>`;
        dropdown.style.display = 'block';
    }
    
    attachEvents() {
        // Пошук міст
        this.cityInput.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            const query = e.target.value.trim();
            
            // Очищуємо REF при зміні тексту вручну
            if (this.cityRefInput) {
                this.cityRefInput.value = '';
            }
            
            if (query.length < 3) {
                this.hideDropdown(this.cityDropdown);
                return;
            }
            
            // Збільшений debounce для зменшення зайвих запитів
            this.debounceTimer = setTimeout(() => {
                this.searchCities(query);
            }, 500);
        });
        
        // Закриття при кліку поза dropdown
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.np-autocomplete')) {
                this.hideDropdown(this.cityDropdown);
                this.hideDropdown(this.warehouseDropdown);
            }
        });
        
        // Пошук та фільтрація відділень
        if (this.warehouseInput) {
            this.warehouseInput.addEventListener('focus', () => {
                if (this.cityRef) {
                    this.loadWarehouses(this.cityRef);
                }
            });
            
            // Фільтрація списку при введенні номера відділення
            this.warehouseInput.addEventListener('input', (e) => {
                // Очищуємо REF при зміні тексту вручну
                if (this.warehouseRefInput) {
                    this.warehouseRefInput.value = '';
                }
                this.filterWarehouses(e.target.value.trim());
            });
        }
    }
    
    async searchCities(query) {
        try {
            // Перевірка client-side кешу
            if (this.citiesCache.has(query)) {
                this.showCitiesDropdown(this.citiesCache.get(query));
                return;
            }
            
            // Показуємо індикатор завантаження
            this.showLoading(this.cityDropdown);
            
            const response = await fetch(`/orders/api/np/cities/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                // Зберігаємо в client-side кеш
                this.citiesCache.set(query, data.data);
                this.showCitiesDropdown(data.data);
            } else if (data.success && data.data.length === 0) {
                this.showNoResults(this.cityDropdown, 'Міста не знайдено');
            } else {
                this.showError(this.cityDropdown, 'Помилка завантаження');
            }
        } catch (error) {
            console.error('Nova Poshta cities error:', error);
            this.showError(this.cityDropdown, 'Помилка мережі');
        }
    }
    
    showCitiesDropdown(cities) {
        this.cityDropdown.innerHTML = '';
        
        cities.forEach(city => {
            const item = document.createElement('div');
            item.className = 'np-dropdown-item';
            item.textContent = city.label;
            item.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
            `;
            
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f5f5f5';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            item.addEventListener('click', () => {
                this.selectCity(city);
            });
            
            this.cityDropdown.appendChild(item);
        });
        
        this.cityDropdown.style.display = 'block';
    }
    
    selectCity(city) {
        this.cityInput.value = city.label;
        this.cityRef = city.ref;
        
        // Зберігаємо REF у hidden input
        if (this.cityRefInput) {
            this.cityRefInput.value = city.ref;
        }
        
        // Очищуємо помилку якщо була
        this.cityInput.classList.remove('invalid');
        const errorEl = this.cityInput.parentElement.querySelector('.error');
        if (errorEl) errorEl.remove();
        
        this.hideDropdown(this.cityDropdown);
        
        // Активувати поле відділення
        if (this.warehouseInput) {
            this.warehouseInput.disabled = false;
            this.warehouseInput.placeholder = 'Почніть вводити номер відділення...';
            this.warehouseInput.value = '';
            // Очищуємо REF відділення при зміні міста
            if (this.warehouseRefInput) {
                this.warehouseRefInput.value = '';
            }
            this.loadWarehouses(city.ref);
        }
    }
    
    async loadWarehouses(cityRef) {
        try {
            // Перевірка client-side кешу
            if (this.warehousesCache.has(cityRef)) {
                this.showWarehousesDropdown(this.warehousesCache.get(cityRef));
                return;
            }
            
            // Показуємо індикатор завантаження
            this.showLoading(this.warehouseDropdown);
            
            const response = await fetch(`/orders/api/np/warehouses/?city_ref=${encodeURIComponent(cityRef)}`);
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                // Зберігаємо в client-side кеш
                this.warehousesCache.set(cityRef, data.data);
                this.showWarehousesDropdown(data.data);
            } else if (data.success && data.data.length === 0) {
                this.showNoResults(this.warehouseDropdown, 'Відділення не знайдено');
            } else {
                this.showError(this.warehouseDropdown, 'Помилка завантаження');
            }
        } catch (error) {
            console.error('Nova Poshta warehouses error:', error);
            this.showError(this.warehouseDropdown, 'Помилка мережі');
        }
    }
    
    showWarehousesDropdown(warehouses) {
        this.warehouseDropdown.innerHTML = '';
        
        warehouses.forEach(wh => {
            const item = document.createElement('div');
            item.className = 'np-dropdown-item';
            item.textContent = wh.label;
            item.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
            `;
            
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f5f5f5';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            item.addEventListener('click', () => {
                this.selectWarehouse(wh);
            });
            
            this.warehouseDropdown.appendChild(item);
        });
        
        this.warehouseDropdown.style.display = 'block';
    }
    
    selectWarehouse(warehouse) {
        this.warehouseInput.value = warehouse.label;
        
        // Зберігаємо REF у hidden input
        if (this.warehouseRefInput) {
            this.warehouseRefInput.value = warehouse.ref;
        }
        
        // Очищуємо помилку якщо була
        this.warehouseInput.classList.remove('invalid');
        const errorEl = this.warehouseInput.parentElement.querySelector('.error');
        if (errorEl) errorEl.remove();
        
        this.hideDropdown(this.warehouseDropdown);
    }
    
    filterWarehouses(query) {
        // Якщо немає обраного міста або немає кешованих даних - нічого не робити
        if (!this.cityRef || !this.warehousesCache.has(this.cityRef)) {
            return;
        }
        
        // Отримуємо повний список відділень для цього міста з кешу
        const allWarehouses = this.warehousesCache.get(this.cityRef);
        
        // Якщо поле порожнє - показуємо повний список
        if (query.length === 0) {
            this.showWarehousesDropdown(allWarehouses);
            return;
        }
        
        // Фільтруємо список по номеру або за описом
        const queryLower = query.toLowerCase();
        const filtered = allWarehouses.filter(wh => {
            const numberMatch = wh.number && wh.number.includes(query);
            const labelMatch = wh.label && wh.label.toLowerCase().includes(queryLower);
            return numberMatch || labelMatch;
        });
        
        // Показуємо результати або повідомлення про відсутність результатів
        if (filtered.length === 0) {
            this.showNoResults(this.warehouseDropdown, 'За номером нічого не знайдено');
        } else {
            this.showWarehousesDropdown(filtered);
        }
    }
    
    hideDropdown(dropdown) {
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }
}

// Ініціалізація при завантаженні
document.addEventListener('DOMContentLoaded', () => {
    new NovaPoshtaAutocomplete();
});
