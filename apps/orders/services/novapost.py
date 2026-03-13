"""
Wrapper для Nova Poshta API v2.0 (api.novaposhta.ua)
"""
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from datetime import datetime


logger = logging.getLogger(__name__)


class NovaPostServiceError(Exception):
    """Помилка API Нової Пошти"""
    pass


class NovaPostService:
    """Wrapper для Nova Poshta API v2.0"""
    
    API_URL = "https://api.novaposhta.ua/v2.0/json/"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key:
            raise NovaPostServiceError("NOVAPOST_API_KEY не налаштований")
    
    def _request(self, model_name: str, called_method: str, properties: dict = None) -> dict:
        """
        Виконує запит до Nova Poshta API v2.0
        
        Args:
            model_name: Назва моделі (наприклад, "Address", "AddressGeneral")
            called_method: Назва методу (наприклад, "getCities", "getWarehouses")
            properties: Параметри запиту
        """
        payload = {
            "apiKey": self.api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": properties or {}
        }
        
        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get('success'):
                error_msg = result.get('errors', ['Невідома помилка API'])
                logger.warning(f"API error: {error_msg}")
                return {'success': False, 'data': [], 'errors': error_msg}
            
            return result
        except Exception as e:
            logger.error(f"Nova Poshta API request failed: {called_method}, error: {e}")
            return {'success': False, 'data': [], 'errors': [str(e)]}
    
    def search_cities(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Пошук міст за назвою для autocomplete.
        
        API: Address.getCities
        Returns: список міст з Ref та Description
        
        Результати кешуються на 24 години
        """
        # Перевірка кешу
        cache_key = f'np_cities:{query.lower()}:{limit}'
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"City cache hit for query='{query}'")
            return cached
        
        try:
            result = self._request(
                "Address",
                "getCities",
                {
                    "FindByString": query,
                    "Limit": limit
                }
            )
            cities = result.get('data', [])
            
            # Кешуємо результат на 24 години
            if cities:
                cache.set(cache_key, cities, 86400)
            
            return cities
        except Exception as e:
            logger.error(f"City search failed for query='{query}': {e}")
            return []
    
    def get_warehouses(self, city_ref: str, limit: int = 500) -> List[Dict]:
        """
        Отримує відділення/поштомати для обраного міста
        
        API: Address.getWarehouses
        Args:
            city_ref: Ref міста з методу getCities
            limit: Максимальна кількість результатів
        Returns: список відділень з Ref, Description, Address тощо
        
        Результати кешуються на 1 годину
        """
        # Перевірка кешу
        cache_key = f'np_warehouses:{city_ref}:{limit}'
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Warehouse cache hit for city_ref='{city_ref}'")
            return cached
        
        try:
            result = self._request(
                "Address",
                "getWarehouses",
                {"CityRef": city_ref, "Limit": limit}
            )
            warehouses = result.get('data', [])
            
            # Кешуємо результат на 1 годину
            if warehouses:
                cache.set(cache_key, warehouses, 3600)
            
            return warehouses
        except Exception as e:
            logger.error(f"Warehouses fetch failed for city_ref='{city_ref}': {e}")
            return []
    
    def get_sender_addresses(self) -> List[Dict]:
        """
        Отримує адреси відправника (власні відділення) 
        
        API: Address.getSenderAddresses
        Returns: список адрес відправника
        """
        try:
            result = self._request(
                "Address",
                "getSenderAddresses"
            )
            return result.get('data', [])
        except Exception as e:
            logger.error(f"Sender addresses fetch failed: {e}")
            return []
    
    def get_sender_contacts(self) -> List[Dict]:
        """
        Отримує контакти відправника
        
        API: ContactPerson.getSenderContactPersons
        Returns: список контактів відправника
        """
        try:
            result = self._request(
                "ContactPerson",
                "getSenderContactPersons"
            )
            return result.get('data', [])
        except Exception as e:
            logger.error(f"Sender contacts fetch failed: {e}")
            return []
    
    def get_counterparty(self) -> Dict:
        """
        Отримує дані контрагента (відправника)
        
        API: Counterparty.getCounterparties
        Returns: перший контрагент зі списку (власна компанія)
        """
        try:
            result = self._request(
                "Counterparty",
                "getCounterparties"
            )
            data = result.get('data', [])
            return data[0] if data else {}
        except Exception as e:
            logger.error(f"Counterparty fetch failed: {e}")
            return {}
    
    def create_shipment(
        self,
        recipient_city_ref: str,
        recipient_warehouse_ref: str,
        recipient_name: str,
        recipient_phone: str,
        sender_ref: str,
        sender_city_ref: str,
        sender_address_ref: str,
        sender_contact_ref: str,
        description: str = "Товари з інтернет-магазину",
        cost: str = "0",
        weight: str = "1000",
        seats_amount: str = "1",
        senders_phone: str = "0800000000"
    ) -> Dict:
        """
        Створення ТТН (Інтернет-документу)
        
        API: InternetDocument.save
        
        Args:
            recipient_city_ref: REF міста одержувача (обов'язково!)
            recipient_warehouse_ref: REF відділення одержувача (обов'язково!)
            recipient_name: ПІБ одержувача
            recipient_phone: Телефон одержувача
            sender_ref: REF контрагента (відправника)
            sender_city_ref: REF міста відправника (обов'язково!)
            sender_address_ref: REF адреси відправника
            sender_contact_ref: REF контакту відправника
            description: Опис вантажу
            cost: Вартість відправлення
            weight: Вага вантажу (у грамах)
            seats_amount: Кількість місць
            senders_phone: Телефон відправника
        
        Returns: dict з даними ТТН (документа) - можна отримати IntDocNumber
        
        Raises:
            NovaPostServiceError: Якщо є помилки валідації або API
        """
        # Валідація обов'язкових полів
        required_fields = {
            'recipient_city_ref': recipient_city_ref,
            'recipient_warehouse_ref': recipient_warehouse_ref,
            'recipient_name': recipient_name,
            'recipient_phone': recipient_phone,
            'sender_ref': sender_ref,
            'sender_city_ref': sender_city_ref,
            'sender_address_ref': sender_address_ref,
            'sender_contact_ref': sender_contact_ref,
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                raise NovaPostServiceError(f"Поле {field_name} є обов'язковим")
        
        # Формуємо payload для InternetDocument.save
        properties = {
            "PayerType": "Recipient",  # Платник - одержувач
            "PaymentMethod": "Cash",   # Спосіб оплати - готівка
            "DateTime": datetime.now().strftime("%d.%m.%Y"),
            "CargoType": "Parcel",     # Тип вантажу - посилка
            "ServiceType": "WarehouseWarehouse",  # З відділення в відділення
            "SeatsAmount": seats_amount,
            "Description": description,
            "Cost": str(cost),
            "Weight": str(weight),  # У грамах
            
            # Дані відправника (власні реквізити)
            "CitySender": sender_city_ref,  # REF міста відправника (ОБОВ'ЯЗКОВО!)
            "Sender": sender_ref,  # REF контрагента
            "SenderAddress": sender_address_ref,
            "ContactSender": sender_contact_ref,
            "SendersPhone": senders_phone,  # Телефон відправника
            
            # Дані одержувача - використовуємо REF!
            "RecipientCityRef": recipient_city_ref,
            "RecipientWarehouseRef": recipient_warehouse_ref,
            "RecipientName": recipient_name,
            "RecipientType": "PrivatePerson",
            "RecipientsPhone": recipient_phone,
        }
        
        try:
            result = self._request(
                "InternetDocument",
                "save",
                properties
            )
            
            if not result.get('success'):
                errors = result.get('errors', ['Невідома помилка при створенні ТТН'])
                raise NovaPostServiceError(f"Помилка створення ТТН: {'; '.join(errors)}")
            
            return result
        except Exception as e:
            logger.error(f"Shipment creation failed: {e}")
            if isinstance(e, NovaPostServiceError):
                raise
            raise NovaPostServiceError(f"Помилка при створенні ТТН: {str(e)}")
