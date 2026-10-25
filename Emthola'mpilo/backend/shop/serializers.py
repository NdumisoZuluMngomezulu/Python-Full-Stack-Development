"""
JSON shapes are camelCase to match the original API (and the frontend): customerName, imageUrl, unitPrice, ...
"""
import re

from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import Order, OrderItem, Product

INT32_MAX = 2_147_483_647
INT64_MAX = 9_223_372_036_854_775_807

http_url = RegexValidator(r"^https?://\S+$", message="imageUrl must be http(s)", flags=re.IGNORECASE)


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    imageUrl = serializers.CharField(
        source="image_url", required=False, allow_blank=True, max_length=500, validators=[http_url]
    )

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "stock", "category", "imageUrl"]


class OrderItemSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id")
    productName = serializers.CharField(source="product_name")
    unitPrice = serializers.DecimalField(source="unit_price", max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ["id", "productId", "productName", "quantity", "unitPrice"]


class OrderSerializer(serializers.ModelSerializer):
    """Output only. The idempotency key and request hash are internal and never exposed."""
    customerName = serializers.CharField(source="customer_name")
    createdAt = serializers.DateTimeField(source="created_at")
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customerName", "email", "address", "total", "createdAt", "items"]


class OrderLineSerializer(serializers.Serializer):
    productId = serializers.IntegerField(max_value=INT64_MAX)
    quantity = serializers.IntegerField(min_value=1, max_value=INT32_MAX)


class OrderRequestSerializer(serializers.Serializer):
    """Input for POST /api/orders. Prices are deliberately not accepted: the server looks them up."""
    customerName = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=254)
    address = serializers.CharField(max_length=1000)
    items = OrderLineSerializer(many=True, allow_empty=False)
