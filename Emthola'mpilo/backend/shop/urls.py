from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import OrderListCreateView, ProductViewSet

router = SimpleRouter(trailing_slash=False)  # /api/products, /api/products/3 — same paths as the original
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("orders", OrderListCreateView.as_view(), name="orders"),
    *router.urls,
]
