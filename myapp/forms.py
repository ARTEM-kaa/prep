from django import forms
from .models import Product, Order
from PIL import Image
import os


class ProductForm(forms.ModelForm):
    """Форма для добавления и редактирования товара (Модуль 3)"""
    
    class Meta:
        model = Product
        fields = [
            "article",
            "name",
            "unit",
            "price",
            "discount",
            "quantity",
            "description",
            "photo",
            "category",
            "manufacturer",
            "supplier",  # ← ИСПРАВЛЕНО: выбираем из существующих поставщиков
        ]
        labels = {
            "article": "Артикул",
            "name": "Наименование товара",
            "unit": "Единица измерения",
            "price": "Цена",
            "discount": "Действующая скидка (%)",
            "quantity": "Количество на складе",
            "description": "Описание товара",
            "photo": "Фото товара",
            "category": "Категория товара",
            "manufacturer": "Производитель",
            "supplier": "Поставщик",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "article": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control", "placeholder": "шт., кг, л"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "manufacturer": forms.Select(attrs={"class": "form-control"}),
            "supplier": forms.Select(attrs={"class": "form-control"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем пустые в выпадающие списки
        self.fields['category'].empty_label = "Выберите категорию"
        self.fields['manufacturer'].empty_label = "Выберите производителя"
        self.fields['supplier'].empty_label = "Выберите поставщика"
        
        # Делаем поля обязательными
        self.fields['article'].required = True
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['manufacturer'].required = True
        self.fields['supplier'].required = True
        self.fields['price'].required = True

    def clean_price(self):
        """Проверка: цена не может быть отрицательной"""
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Цена не может быть отрицательной")
        return price

    def clean_quantity(self):
        """Проверка: количество не может быть отрицательным"""
        qty = self.cleaned_data.get("quantity")
        if qty is not None and qty < 0:
            raise forms.ValidationError("Количество не может быть отрицательным")
        return qty

    def clean_discount(self):
        """Проверка: скидка от 0 до 100 процентов"""
        discount = self.cleaned_data.get("discount")
        if discount is not None and (discount < 0 or discount > 100):
            raise forms.ValidationError("Скидка должна быть от 0 до 100 процентов")
        return discount
    
    def clean_photo(self):
        """Проверка размеров фото (300x200)"""
        photo = self.cleaned_data.get('photo')
        
        if not photo:
            return photo
        
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Файл слишком большой. Максимальный размер 5 МБ")
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(photo.name)[1].lower()
        if ext not in valid_extensions:
            raise forms.ValidationError("Поддерживаются только форматы: JPG, JPEG, PNG, GIF")
        
        try:
            img = Image.open(photo)
            width, height = img.size
            
            # Проверяем размеры
            if width != 300 or height != 200:
                raise forms.ValidationError(
                    f"Размер фото должен быть 300x200 пикселей. "
                    f"Текущий размер: {width}x{height}"
                )
        except Exception as e:
            raise forms.ValidationError(f"Ошибка обработки изображения: {e}")
        
        return photo


# Добавьте в конец forms.py:

class OrderForm(forms.ModelForm):
    """Форма для добавления и редактирования заказа (Модуль 4)"""
    
    class Meta:
        model = Order
        fields = [
            'status',
            'pickup_point',
            'order_date',
            'delivery_date',
        ]
        labels = {
            'status': 'Статус заказа',
            'pickup_point': 'Адрес пункта выдачи',
            'order_date': 'Дата заказа',
            'delivery_date': 'Дата доставки',
        }
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'pickup_point': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_delivery_date(self):
        """Проверка: дата доставки не может быть раньше даты заказа"""
        order_date = self.cleaned_data.get('order_date')
        delivery_date = self.cleaned_data.get('delivery_date')
        
        if order_date and delivery_date and delivery_date < order_date:
            raise forms.ValidationError("Дата доставки не может быть раньше даты заказа")
        return delivery_date