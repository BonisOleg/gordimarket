from django import forms
from django.core.validators import RegexValidator
from .models import Order


class OrderCreateForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r'^\+380\d{9}$',
        message='Введіть номер у форматі +380XXXXXXXXX'
    )
    
    phone = forms.CharField(
        label='Телефон',
        max_length=13,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'placeholder': '+380XXXXXXXXX',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'patronymic', 'phone', 'email',
            'payment_method', 'delivery_method',
            'nova_poshta_city', 'nova_poshta_city_ref',
            'nova_poshta_warehouse', 'nova_poshta_warehouse_ref',
            'ukrposhta_city', 'ukrposhta_address', 'ukrposhta_index',
            'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ім'я"}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Прізвище'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'По-батькові'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'payment_method': forms.RadioSelect(),
            'delivery_method': forms.RadioSelect(),
            'nova_poshta_city': forms.TextInput(attrs={
                'class': 'form-control np-autocomplete',
                'placeholder': 'Почніть вводити назву міста...',
                'autocomplete': 'off',
                'data-type': 'city'
            }),
            'nova_poshta_city_ref': forms.HiddenInput(),
            'nova_poshta_warehouse': forms.TextInput(attrs={
                'class': 'form-control np-autocomplete',
                'placeholder': 'Спочатку оберіть місто',
                'autocomplete': 'off',
                'data-type': 'warehouse',
                'disabled': 'disabled'
            }),
            'nova_poshta_warehouse_ref': forms.HiddenInput(),
            'ukrposhta_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Місто'}),
            'ukrposhta_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Вулиця, будинок, квартира'}),
            'ukrposhta_index': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ваш коментар до замовлення'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patronymic'].required = False
        self.fields['email'].required = False
        self.fields['notes'].required = False
        self.fields['nova_poshta_city'].required = False
        self.fields['nova_poshta_city_ref'].required = False
        self.fields['nova_poshta_warehouse'].required = False
        self.fields['nova_poshta_warehouse_ref'].required = False
        self.fields['ukrposhta_city'].required = False
        self.fields['ukrposhta_address'].required = False
        self.fields['ukrposhta_index'].required = False
        self.fields['payment_method'].required = True
        self.fields['delivery_method'].required = True
        self.fields['payment_method'].initial = 'online'
        self.fields['delivery_method'].initial = 'nova_poshta'
    
    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        
        if delivery_method == 'nova_poshta':
            if not cleaned_data.get('nova_poshta_city'):
                self.add_error('nova_poshta_city', 'Оберіть місто')
            if not cleaned_data.get('nova_poshta_city_ref'):
                self.add_error('nova_poshta_city', 'Виберіть місто зі списку')
            if not cleaned_data.get('nova_poshta_warehouse'):
                self.add_error('nova_poshta_warehouse', 'Оберіть відділення або поштомат')
            if not cleaned_data.get('nova_poshta_warehouse_ref'):
                self.add_error('nova_poshta_warehouse', 'Виберіть відділення зі списку')
        
        elif delivery_method == 'ukrposhta':
            if not cleaned_data.get('ukrposhta_city'):
                self.add_error('ukrposhta_city', "Вкажіть місто")
            if not cleaned_data.get('ukrposhta_address'):
                self.add_error('ukrposhta_address', 'Вкажіть адресу')
            if not cleaned_data.get('ukrposhta_index'):
                self.add_error('ukrposhta_index', 'Вкажіть поштовий індекс')
        
        return cleaned_data

