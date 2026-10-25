from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import IsAdmin
from .models import Order, Product
from .serializers import OrderRequestSerializer, OrderSerializer, ProductSerializer
from .services import place_order

READ_ONLY = ("GET", "HEAD", "OPTIONS")


class ProductViewSet(viewsets.ModelViewSet):
    """GET (list, search with ?q=, detail) is public. POST / PUT / DELETE need the admin."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    http_method_names = ["get", "post", "put", "delete", "head", "options"]  # no PATCH, as in the original

    def get_permissions(self):
        return [AllowAny()] if self.request.method in READ_ONLY else [IsAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            q = self.request.query_params.get("q", "").strip()
            if q:
                qs = qs.filter(name__icontains=q)
        return qs


class OrderListCreateView(APIView):
    """POST is public (needs an Idempotency-Key header). GET lists every order and is admin-only."""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsAdmin()]

    def get(self, request):
        orders = Order.objects.prefetch_related("items")
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        body = OrderRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        result = place_order(request.headers.get("Idempotency-Key"), body.validated_data)
        # 201 = order created, 200 = this key already produced the order (replay).
        return Response(
            OrderSerializer(result.order).data,
            status=200 if result.replayed else 201,
            headers={"Idempotent-Replayed": "true" if result.replayed else "false"},
        )
