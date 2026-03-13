"""
Monobank Acquiring з idempotency та підтримкою race conditions
"""
import requests
import hashlib
import base64
import logging
from ecdsa import VerifyingKey, BadSignatureError
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger('apps.orders.monobank')


class MonobankService:
    """Monobank Acquiring з idempotency"""
    
    API_URL = "https://api.monobank.ua"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'X-Token': token,
            'Content-Type': 'application/json'
        }
    
    def create_invoice(self, order, webhook_url: str, redirect_url: str) -> Dict:
        """Створює рахунок для оплати"""
        from apps.orders.models import OrderItem
        
        # Формуємо basketOrder для ПРРО (якщо активовано)
        basket = []
        for item in order.items.all():
            basket.append({
                'name': item.product.name[:128],  # Max 128 символів
                'qty': item.quantity,
                'sum': int(item.price * 100),  # копійки
                'code': str(item.product.id),
            })
        
        data = {
            'amount': int(order.final_total * 100),  # копійки
            'ccy': 980,  # UAH
            'merchantPaymInfo': {
                'reference': order.order_number,
                'destination': f'Оплата замовлення {order.order_number}',
                'basketOrder': basket,
            },
            'redirectUrl': redirect_url,
            'webHookUrl': webhook_url,
            'validity': 3600,  # 1 година
        }
        
        try:
            response = requests.post(
                f"{self.API_URL}/api/merchant/invoice/create",
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Invoice created: {result.get('invoiceId')} for order {order.order_number}")
            return result
        except Exception as e:
            logger.error(f"Invoice creation failed for order {order.order_number}: {e}")
            raise
    
    def get_invoice_status(self, invoice_id: str) -> Dict:
        """Перевіряє статус рахунку (fallback)"""
        try:
            response = requests.get(
                f"{self.API_URL}/api/merchant/invoice/status",
                headers=self.headers,
                params={'invoiceId': invoice_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Status check failed for invoice {invoice_id}: {e}")
            raise
    
    def get_public_key(self) -> str:
        """Отримує публічний ключ для верифікації (кешується)"""
        cached_key = cache.get('monobank_public_key')
        if cached_key:
            return cached_key
        
        try:
            response = requests.get(
                f"{self.API_URL}/api/merchant/pubkey",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            public_key = response.json()['key']
            cache.set('monobank_public_key', public_key, 86400)  # 24 години
            logger.info("Monobank public key cached")
            return public_key
        except Exception as e:
            logger.error(f"Failed to get Monobank public key: {e}")
            raise
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Верифікує ECDSA підпис webhook"""
        try:
            # Декодуємо публічний ключ
            public_key_base64 = self.get_public_key()
            public_key_bytes = base64.b64decode(public_key_base64)
            public_key = VerifyingKey.from_pem(public_key_bytes.decode())
            
            # Декодуємо підпис
            signature_bytes = base64.b64decode(signature)
            
            # Верифікуємо
            public_key.verify(
                signature_bytes,
                body,
                sigdecode=lambda sig, order: sig,  # DER format
                hashfunc=hashlib.sha256
            )
            logger.info("Webhook signature verified successfully")
            return True
        except BadSignatureError:
            logger.error("Webhook signature verification FAILED - invalid signature")
            return False
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False
