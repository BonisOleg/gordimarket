from django import forms
from django.core.exceptions import ValidationError
from .models import Product


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        retail_price = cleaned_data.get('retail_price')
        sale_price = cleaned_data.get('sale_price')
        
        if sale_price and sale_price >= retail_price:
            raise ValidationError({
                'sale_price': 'Акційна ціна повинна бути меншою за роздрібну'
            })
        
        return cleaned_data
