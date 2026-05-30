from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import render  # noqa: F401
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

# from .forms import ProductForm
from .models import Product, Supplier


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
        sort = self.request.GET.get("sort", "")
        if sort == "asc":
            queryset = queryset.order_by("quantity")
        elif sort == "desc":
            queryset = queryset.order_by("-quantity")
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.all()
        context["current_search"] = self.request.GET.get("search", "")
        context["current_supplier"] = self.request.GET.get("supplier", "")
        context["current_sort"] = self.request.GET.get("sort", "")

        return context


# class AdminRequiredMixin(UserPassesTestMixin):
#     def test_func(self):
#         return (
#             self.request.user.is_authenticated
#             and self.request.user.role
#             and self.request.user.role.name == "admin"
#         )


# class ProductCreateUpdateMixin:
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["all_suppliers"] = Supplier.objects.all()
#         return context


# class ProductCreateView(AdminRequiredMixin, ProductCreateUpdateMixin, CreateView):
#     model = Product
#     form_class = ProductForm
#     template_name = "core/product_form.html"
#     success_url = reverse_lazy("product_list")

#     def form_valid(self, form):
#         messages.success(self.request, "Товар успешно добавлен")
#         return super().form_valid(form)


# class ProductUpdateView(AdminRequiredMixin, ProductCreateUpdateMixin, UpdateView):
#     model = Product
#     form_class = ProductForm
#     template_name = "core/product_form.html"
#     success_url = reverse_lazy("product_list")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["is_edit"] = True
#         return context

#     def form_valid(self, form):
#         messages.success(self.request, "Товар успешно обновлен")
#         return super().form_valid(form)