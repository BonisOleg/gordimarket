from django.contrib import admin
from django.contrib.auth.models import Group

# Приховуємо Groups з адмінки
admin.site.unregister(Group)
