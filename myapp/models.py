import os
from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal


# Модуль 1 весь файл

class Category(models.Model):
    """Категории товаров (справочник)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Производители товаров (справочник)"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Название производителя")

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Поставщики товаров (справочник)"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Название поставщика")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    def __str__(self):
        return self.name


class PickupPoint(models.Model):
    """Пункты выдачи заказов (справочник)"""
    address = models.TextField(unique=True, verbose_name="Адрес пункта выдачи")

    class Meta:
        verbose_name = "Пункт выдачи"
        verbose_name_plural = "Пункты выдачи"

    def __str__(self):
        return self.address[:50]


class User(AbstractUser):
    """Пользователи системы (расширенная модель)"""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('client', 'Авторизированный клиент'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client',verbose_name="Роль")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"


class Product(models.Model):
    """Товары (основная таблица)"""
    article = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    name = models.CharField(max_length=255, verbose_name="Наименование товара")
    unit = models.CharField(max_length=20, default="шт.", verbose_name="Единица измерения")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    discount = models.IntegerField(default=0, verbose_name="Скидка (%)")
    quantity = models.IntegerField(default=0, verbose_name="Количество на складе")
    description = models.TextField(blank=True, verbose_name="Описание товара")
    photo = models.ImageField(upload_to="products/", null=True, blank=True)
    
    # Внешние ключи (связи со справочниками)
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,  # Запрещаем удаление категории, если есть товары
        verbose_name="Категория"
    )
    manufacturer = models.ForeignKey(
        Manufacturer, 
        on_delete=models.PROTECT,
        verbose_name="Производитель"
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT,
        verbose_name="Поставщик"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.article} - {self.name}"

    @property
    def final_price(self):
        """Финальная цена с учетом скидки"""
        if self.discount:
            discount_factor = Decimal(100 - self.discount) / Decimal(100)
            return self.price * discount_factor
        return self.price
    
    def save(self, *args, **kwargs):
        """При обновлении фото — удаляем старое"""
        try:
            old_product = Product.objects.get(pk=self.pk)
            if old_product.photo and self.photo != old_product.photo:
                if os.path.isfile(old_product.photo.path):
                    os.remove(old_product.photo.path)
        except Product.DoesNotExist:
            pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """При удалении товара — удаляем его фото"""
        if self.photo and os.path.isfile(self.photo.path):
            os.remove(self.photo.path)
        super().delete(*args, **kwargs)


class Order(models.Model):
    """Заказы"""
    STATUS_CHOICES = [
        ('Новый', 'Новый'),
        ('Завершен', 'Завершен'),
    ]
    
    order_date = models.DateField(verbose_name="Дата заказа")
    delivery_date = models.DateField(verbose_name="Дата доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Новый', verbose_name="Статус")
    pickup_code = models.IntegerField(unique=True, verbose_name="Код для получения")
    
    # Внешние ключи
    pickup_point = models.ForeignKey(
        PickupPoint, 
        on_delete=models.PROTECT,
        verbose_name="Пункт выдачи"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name="Клиент"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} от {self.order_date}"


class OrderItem(models.Model):
    """Состав заказа (связующая таблица для 1НФ)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.IntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        unique_together = ['order', 'product']  # Один товар не может быть дважды в одном заказе

    def __str__(self):
        return f"{self.order} - {self.product.article} x{self.quantity}"
