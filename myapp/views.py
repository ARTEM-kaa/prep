from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View, DeleteView
from django.http import JsonResponse
from django.db import transaction
import random

from .forms import ProductForm, OrderForm
from .models import Product, Supplier, Category, Manufacturer, Order, OrderItem

# От сюда модуль 2

class UserLoginView(LoginView):
    template_name = "core/login.html"


class ProductListView(ListView):
    model = Product
    template_name = "core/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.all().select_related("supplier", "category", "manufacturer")
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(manufacturer__name__icontains=search_query)
                | Q(category__name__icontains=search_query)
            )
        supplier_id = self.request.GET.get("supplier", "")
        if supplier_id and supplier_id != "all":
            try:
                queryset = queryset.filter(supplier_id=int(supplier_id))
            except ValueError:
                pass
            
        # Фильтрация по диапазону скидок
        discount_filter = self.request.GET.get("discount_filter", "")
        if discount_filter == "0_13":
            queryset = queryset.filter(discount__gte=0, discount__lt=13)  # от 0 до 12.99% (целое число до 13)
        elif discount_filter == "13_30":
            queryset = queryset.filter(discount__gte=13, discount__lt=30) # от 13 до 29.99% (целое число до 30)
        elif discount_filter == "30_100":
            queryset = queryset.filter(discount__gte=30, discount__lte=100) # от 30 до 100%


        # Совместная сортировка по трем колонкам
        sort_fields = []
        
        # Проверяем сортировку по количеству
        sort_qty = self.request.GET.get("sort_qty", "")
        if sort_qty == "asc":
            sort_fields.append("quantity")
        elif sort_qty == "desc":
            sort_fields.append("-quantity")

        # Проверяем сортировку по цене
        sort_price = self.request.GET.get("sort_price", "")
        if sort_price == "asc":
            sort_fields.append("price")
        elif sort_price == "desc":
            sort_fields.append("-price")

        # Проверяем сортировку по скидке
        sort_discount = self.request.GET.get("sort_discount", "")
        if sort_discount == "asc":
            sort_fields.append("discount")
        elif sort_discount == "desc":
            sort_fields.append("-discount")

        # Если выбран хотя бы один тип сортировки, применяем их все вместе
        if sort_fields:
            queryset = queryset.order_by(*sort_fields)
            
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.all()
        context["current_search"] = self.request.GET.get("search", "")
        context["current_supplier"] = self.request.GET.get("supplier", "")
        context["current_sort"] = self.request.GET.get("sort", "")

        return context

# Конец модуля 2

# Начало модуль 3

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "admin"
    
    def handle_no_permission(self):
        messages.error(self.request, "Доступ запрещён. Требуются права администратора.")
        return redirect('product_list')


class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно добавлен")
        form.save()
        return redirect('product_list')


class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно обновлен")
        form.save()
        return redirect('product_list')
    

class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        try:
            product.delete()
            messages.success(request, "Товар успешно удалён")
        except Exception:
            messages.error(request, "Невозможно удалить товар, так как он присутствует в заказах")
        return redirect('product_list')
    
# Конец модуля 3

# Начало и до конца файла модуль 4
    
    
class ManagerOrAdminRequiredMixin(UserPassesTestMixin):
    """Миксин для менеджера и администратора"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "manager"]
    
    def handle_no_permission(self):
        messages.error(self.request, "Доступ запрещён. Требуются права менеджера или администратора.")
        return redirect('product_list')


class OrderListView(ManagerOrAdminRequiredMixin, ListView):
    """Список заказов (доступен менеджеру и администратору)"""
    model = Order
    template_name = "core/order_list.html"
    context_object_name = "orders"
    
    def get_queryset(self):
        return Order.objects.all().select_related('pickup_point', 'user').prefetch_related('items__product')


class OrderCreateView(AdminRequiredMixin, CreateView):
    """Создание заказа (только администратор)"""
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    
    @transaction.atomic
    def form_valid(self, form):
        # Генерируем уникальный код получения
        import random
        pickup_code = random.randint(100, 999)
        while Order.objects.filter(pickup_code=pickup_code).exists():
            pickup_code = random.randint(100, 999)
        
        # Создаём заказ (пока без товаров)
        order = form.save(commit=False)
        order.pickup_code = pickup_code
        order.user = self.request.user
        order.save()
        
        # Парсим артикулы
        items_str = self.request.POST.get('items', '').strip()
        items_added = 0
        errors = []
        
        if not items_str:
            order.delete()
            messages.error(self.request, "Заказ не создан: не указаны товары")
            return redirect('order_list')
        
        # Поддерживаем оба формата
        if ';' in items_str:
            pairs = items_str.split(';')
        else:
            parts = items_str.split(',')
            pairs = [f"{parts[i]},{parts[i+1]}" for i in range(0, len(parts) - 1, 2)]
        
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            
            pair_parts = pair.split(',')
            if len(pair_parts) != 2:
                errors.append(f"Неверный формат: '{pair}'. Ожидается 'артикул,количество'")
                continue
            
            article = pair_parts[0].strip()
            try:
                quantity = int(pair_parts[1].strip())
            except ValueError:
                errors.append(f"Неверное количество для товара '{article}': '{pair_parts[1]}'")
                continue
            
            if quantity <= 0:
                errors.append(f"Количество для товара '{article}' должно быть положительным")
                continue
            
            try:
                product = Product.objects.get(article=article)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )
                items_added += 1
            except Product.DoesNotExist:
                errors.append(f"Товар с артикулом '{article}' не найден")
        
        # Если есть ошибки или не добавлено ни одного товара
        if errors or items_added == 0:
            # Удаляем созданный заказ
            order.delete()
            for error in errors:
                messages.error(self.request, error)
            if items_added == 0 and not errors:
                messages.error(self.request, "Не добавлено ни одного товара")
            return redirect('order_create')
        
        messages.success(self.request, f"Заказ успешно добавлен. Добавлено товаров: {items_added}")
        return redirect('order_list')
    
    def form_invalid(self, form):
        """Если форма невалидна, показываем ошибки"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме")
        return super().form_invalid(form)


class OrderUpdateView(AdminRequiredMixin, UpdateView):
    """Редактирование заказа (только администратор)"""
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        
        # Формируем строку с артикулами для редактирования
        items = []
        for item in self.object.items.all():
            items.append(f"{item.product.article},{item.quantity}")
        context["items"] = "; ".join(items)
        
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        # Сохраняем старые позиции заказа на случай ошибки
        old_items = list(self.object.items.all())
        
        # Обновляем заказ
        order = form.save()
        
        # Временно удаляем старые позиции
        order.items.all().delete()
        
        # Парсим новые позиции
        items_str = self.request.POST.get('items', '').strip()
        items_added = 0
        errors = []
        new_items = []
        
        if items_str:
            # Поддерживаем оба формата
            if ';' in items_str:
                pairs = items_str.split(';')
            else:
                parts = items_str.split(',')
                pairs = [f"{parts[i]},{parts[i+1]}" for i in range(0, len(parts) - 1, 2)]
            
            for pair in pairs:
                pair = pair.strip()
                if not pair:
                    continue
                
                pair_parts = pair.split(',')
                if len(pair_parts) != 2:
                    errors.append(f"Неверный формат: '{pair}'. Ожидается 'артикул,количество'")
                    continue
                
                article = pair_parts[0].strip()
                try:
                    quantity = int(pair_parts[1].strip())
                except ValueError:
                    errors.append(f"Неверное количество для товара '{article}': '{pair_parts[1]}'")
                    continue
                
                if quantity <= 0:
                    errors.append(f"Количество для товара '{article}' должно быть положительным")
                    continue
                
                try:
                    product = Product.objects.get(article=article)
                    new_item = OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity
                    )
                    new_items.append(new_item)
                    items_added += 1
                except Product.DoesNotExist:
                    errors.append(f"Товар с артикулом '{article}' не найден")
        
        # Если есть ошибки или не добавлено ни одного товара
        if errors or items_added == 0:
            # Восстанавливаем старые позиции
            for old_item in old_items:
                OrderItem.objects.create(
                    order=order,
                    product=old_item.product,
                    quantity=old_item.quantity
                )
            
            # Выводим сообщения об ошибках
            for error in errors:
                messages.error(self.request, error)
            
            if items_added == 0 and not errors:
                messages.error(self.request, "Не добавлено ни одного товара. Заказ не изменён.")
            
            return redirect('order_edit', pk=order.pk)
        
        # Сохраняем новые позиции
        for new_item in new_items:
            new_item.save()
        
        messages.success(self.request, f"Заказ успешно обновлён. Добавлено товаров: {items_added}")
        return redirect('order_list')
    
    def form_invalid(self, form):
        """Если форма невалидна, показываем ошибки"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме")
        return super().form_invalid(form)


class OrderDeleteView(AdminRequiredMixin, DeleteView):
    """Удаление заказа (только администратор)"""
    model = Order
    success_url = reverse_lazy('order_list')
    
    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        order.delete()
        messages.success(request, "Заказ успешно удалён")
        return redirect('order_list')