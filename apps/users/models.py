"""
Модель користувача (тільки для адміністраторів)
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Базова модель користувача для адміністраторів"""
    
    phone = models.CharField('Телефон', max_length=20, blank=True, default='')
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
    
    def __str__(self):
        return self.username
