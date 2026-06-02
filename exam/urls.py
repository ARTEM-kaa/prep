"""
URL configuration for exam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from myapp.views import (
    ProductListView,
    UserLoginView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    OrderListView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
)

urlpatterns = [
    # Модуль 2:
    path('admin/', admin.site.urls),
    path("", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("products/", ProductListView.as_view(), name="product_list"),
    # Модуль 3:
    path("products/create/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    # Модуль 4:
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/create/", OrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/edit/", OrderUpdateView.as_view(), name="order_edit"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)