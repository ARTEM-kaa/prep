import csv
import os
import shutil
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files import File
from datetime import datetime

from myapp.models import (
    Category, Manufacturer, Supplier, PickupPoint,
    Product, User, Order, OrderItem
)


class Command(BaseCommand):
    help = 'Импорт данных из CSV файлов (3NF compliant)'

    def handle(self, *args: Any, **options: Any) -> str | None:
        base_path = "part_1/add_2/import/"
        media_path = "media/products/"
        
        # Создаем папку для фото, если её нет
        os.makedirs(media_path, exist_ok=True)
        
        with transaction.atomic():
            
            # ============================================
            # 1. Импорт справочников
            # ============================================
            
            # 1.1 Категории
            self.stdout.write("📁 Импорт категорий...")
            with open(os.path.join(base_path, "categories.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj, created = Category.objects.get_or_create(name=row["name"])
                    self.stdout.write(f"   {'[СОЗДАНА]' if created else '[ЕСТЬ]'} {obj.name}")
            
            # 1.2 Производители
            self.stdout.write("\n📁 Импорт производителей...")
            with open(os.path.join(base_path, "manufacturers.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj, created = Manufacturer.objects.get_or_create(name=row["name"])
                    self.stdout.write(f"   {'[СОЗДАН]' if created else '[ЕСТЬ]'} {obj.name}")
            
            # 1.3 Поставщики
            self.stdout.write("\n📁 Импорт поставщиков...")
            with open(os.path.join(base_path, "suppliers.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj, created = Supplier.objects.get_or_create(name=row["name"])
                    self.stdout.write(f"   {'[СОЗДАН]' if created else '[ЕСТЬ]'} {obj.name}")
            
            # 1.4 Пункты выдачи
            self.stdout.write("\n📁 Импорт пунктов выдачи...")
            with open(os.path.join(base_path, "pickup_points.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj, created = PickupPoint.objects.get_or_create(address=row["address"])
                    self.stdout.write(f"   {'[СОЗДАН]' if created else '[ЕСТЬ]'} {obj.address[:40]}...")
            
            # ============================================
            # 2. Импорт пользователей
            # ============================================
            
            self.stdout.write("\n👤 Импорт пользователей...")
            with open(os.path.join(base_path, "users.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user, created = User.objects.get_or_create(
                        username=row["login"],
                        defaults={
                            "full_name": row["full_name"],
                            "role": row["role"],
                        }
                    )
                    if created:
                        user.set_password(str(row["password"]).strip())
                        user.save()
                        self.stdout.write(f"   [СОЗДАН] {user.full_name} (роль: {user.role})")
                    else:
                        self.stdout.write(f"   [ЕСТЬ] {user.full_name}")
            
            # ============================================
            # 3. Импорт товаров (с копированием фото)
            # ============================================
            
            self.stdout.write("\n📦 Импорт товаров...")
            with open(os.path.join(base_path, "products.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Получаем ID из справочников
                    category = Category.objects.get(name=row["category"])
                    manufacturer = Manufacturer.objects.get(name=row["manufacturer"])
                    supplier = Supplier.objects.get(name=row["supplier"])
                    
                    # Обработка фото
                    photo_file = row.get("photo", "")
                    if photo_file and isinstance(photo_file, str):
                        photo_file = photo_file.strip()
                    else:
                        photo_file = ""
                    
                    # Создаем или обновляем товар (сначала без фото)
                    product, created = Product.objects.update_or_create(
                        article=row["article"],
                        defaults={
                            "name": row["name"],
                            "unit": row.get("unit", "шт."),
                            "price": Decimal(row["price"]),
                            "discount": int(row.get("discount", 0)),
                            "quantity": int(row.get("quantity", 0)),
                            "description": row.get("description", ""),
                            "category": category,
                            "manufacturer": manufacturer,
                            "supplier": supplier,
                        }
                    )
                    
                    # Обрабатываем фото отдельно (исправленная часть!)
                    if photo_file:
                        src_path = os.path.join(media_path, photo_file)
                        if os.path.exists(src_path):
                            dst_full_path = os.path.join(media_path, photo_file)
                            
                            if not os.path.exists(dst_full_path):
                                shutil.copy2(src_path, dst_full_path)
                                self.stdout.write(f"      └─ Скопировано фото: {photo_file}")
                            
                            # Сохраняем фото — передаём ТОЛЬКО имя файла
                            with open(dst_full_path, 'rb') as f_img:
                                from django.core.files import File as DjangoFile
                                product.photo.save(photo_file, DjangoFile(f_img), save=True)
                                self.stdout.write(f"      └─ Фото привязано: {photo_file}")
                        else:
                            self.stdout.write(f"      └─ ⚠️ Файл не найден: {src_path}")
                    
                    self.stdout.write(f"   {'[СОЗДАН]' if created else '[ОБНОВЛЕН]'} {product.article} - {product.name}")
            
            # ============================================
            # 4. Импорт заказов (с парсингом items)
            # ============================================
            
            self.stdout.write("\n📋 Импорт заказов...")
            with open(os.path.join(base_path, "orders.csv"), encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Получаем пункт выдачи
                    pickup_point = PickupPoint.objects.get(address=row["pickup_point_address"])
                    
                    # Получаем пользователя
                    user = User.objects.get(full_name=row["client_full_name"])
                    
                    # Преобразуем даты из DD.MM.YYYY в YYYY-MM-DD
                    try:
                        order_date = datetime.strptime(row["order_date"], "%d.%m.%Y").date()
                        delivery_date = datetime.strptime(row["delivery_date"], "%d.%m.%Y").date()
                    except ValueError as e:
                        self.stdout.write(self.style.ERROR(f"   ❌ Ошибка формата даты: {e}"))
                        continue
                    
                    # Создаём заказ
                    order, created = Order.objects.get_or_create(
                        order_date=order_date,
                        delivery_date=delivery_date,
                        pickup_point=pickup_point,
                        user=user,
                        defaults={
                            "pickup_code": int(row["pickup_code"]),
                            "status": row["status"],
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"   [СОЗДАН] Заказ от {order.order_date} (клиент: {user.full_name})")
                        
                        # Разбираем состав заказа
                        items_str = row["items"].strip('"')
                        items_parts = items_str.split(",")
                        
                        for i in range(0, len(items_parts), 2):
                            article = items_parts[i].strip()
                            quantity = int(items_parts[i + 1].strip())
                            
                            try:
                                product = Product.objects.get(article=article)
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity
                                )
                                self.stdout.write(f"      └─ Товар: {article}, кол-во: {quantity}")
                            except Product.DoesNotExist:
                                self.stdout.write(self.style.ERROR(f"      └─ ❌ Товар '{article}' не найден!"))
                    else:
                        self.stdout.write(f"   [ЕСТЬ] Заказ от {order.order_date}")
            
            self.stdout.write(self.style.SUCCESS("\n✅ Импорт данных успешно завершен!"))