import base64
from decimal import Decimal

from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Order, Product

ADMIN = {"SHOP_ADMIN_USER": "admin", "SHOP_ADMIN_PASSWORD": "correct-horse-battery"}
KEY = "order-key-0001"


def basic(user, password):
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def make_product(**kw):
    defaults = dict(name="Mug", description="A mug", price=Decimal("18.00"), stock=10, category="Kitchen")
    return Product.objects.create(**{**defaults, **kw})


@override_settings(**ADMIN)
class ProductApiTests(APITestCase):
    def setUp(self):
        self.mug = make_product(name="Stoneware Mug")
        self.tote = make_product(name="Canvas Tote", price=Decimal("29.00"), category="Accessories")

    def test_list_and_detail_are_public(self):
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)
        first = res.json()[0]
        self.assertEqual(set(first), {"id", "name", "description", "price", "stock", "category", "imageUrl"})
        self.assertEqual(first["price"], 18.0)  # a JSON number, not a string
        self.assertEqual(self.client.get(f"/api/products/{self.mug.id}").status_code, 200)
        self.assertEqual(self.client.get("/api/products/999999").status_code, 404)

    def test_search_is_case_insensitive_and_blank_returns_all(self):
        self.assertEqual([p["name"] for p in self.client.get("/api/products?q=MUG").json()], ["Stoneware Mug"])
        self.assertEqual(len(self.client.get("/api/products?q=").json()), 2)

    def test_writes_require_admin(self):
        body = {"name": "Tea Towel", "price": "12.00", "stock": 30, "category": "Kitchen"}
        res = self.client.post("/api/products", body, format="json")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {"error": "Authentication required."})
        self.assertNotIn("WWW-Authenticate", res.headers)  # no browser login dialog

        bad = self.client.post("/api/products", body, format="json", HTTP_AUTHORIZATION=basic("admin", "nope"))
        self.assertEqual(bad.status_code, 401)

        ok = self.client.post("/api/products", body, format="json",
                              HTTP_AUTHORIZATION=basic("admin", ADMIN["SHOP_ADMIN_PASSWORD"]))
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(Product.objects.count(), 3)

    def test_admin_can_update_and_delete(self):
        auth = {"HTTP_AUTHORIZATION": basic("admin", ADMIN["SHOP_ADMIN_PASSWORD"])}
        body = {"name": "Mug v2", "price": 20, "stock": 5, "category": "Kitchen", "imageUrl": "https://x.test/a.jpg"}
        res = self.client.put(f"/api/products/{self.mug.id}", body, format="json", **auth)
        self.assertEqual(res.status_code, 200)
        self.mug.refresh_from_db()
        self.assertEqual((self.mug.name, self.mug.stock, self.mug.image_url), ("Mug v2", 5, "https://x.test/a.jpg"))
        self.assertEqual(self.client.delete(f"/api/products/{self.mug.id}", **auth).status_code, 204)
        self.assertEqual(self.client.patch(f"/api/products/{self.tote.id}", {}, format="json", **auth).status_code, 405)

    def test_product_validation(self):
        auth = {"HTTP_AUTHORIZATION": basic("admin", ADMIN["SHOP_ADMIN_PASSWORD"])}
        for body in (
            {"name": " ", "price": 1, "stock": 1},
            {"name": "x", "price": -1, "stock": 1},
            {"name": "x", "price": 1, "stock": -1},
            {"name": "x", "price": 1, "stock": 1, "imageUrl": "javascript:alert(1)"},
        ):
            res = self.client.post("/api/products", body, format="json", **auth)
            self.assertEqual(res.status_code, 400, body)
            self.assertEqual(res.json()["error"], "Check your details and try again.")


@override_settings(**ADMIN)
class OrderApiTests(APITestCase):
    def setUp(self):
        self.mug = make_product(name="Stoneware Mug", price=Decimal("18.00"), stock=10)
        self.tote = make_product(name="Canvas Tote", price=Decimal("29.00"), stock=5)

    def order(self, items=None, key=KEY, **overrides):
        body = {
            "customerName": "Ada Lovelace",
            "email": "ada@example.com",
            "address": "1 Analytical Way",
            "items": items if items is not None else [{"productId": self.mug.id, "quantity": 2}],
            **overrides,
        }
        extra = {"HTTP_IDEMPOTENCY_KEY": key} if key is not None else {}
        return self.client.post("/api/orders", body, format="json", **extra)

    def stock(self, product):
        product.refresh_from_db()
        return product.stock

    def test_creates_order_and_decrements_stock(self):
        res = self.order([{"productId": self.mug.id, "quantity": 2}, {"productId": self.tote.id, "quantity": 1}])
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res["Idempotent-Replayed"], "false")
        data = res.json()
        self.assertEqual(data["total"], 65.0)  # 2 x 18 + 29, priced by the server
        self.assertEqual({i["productName"] for i in data["items"]}, {"Stoneware Mug", "Canvas Tote"})
        self.assertNotIn("idempotencyKey", data)
        self.assertEqual((self.stock(self.mug), self.stock(self.tote)), (8, 4))

    def test_client_cannot_set_prices(self):
        res = self.order([{"productId": self.mug.id, "quantity": 1, "unitPrice": 0.01}])
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["total"], 18.0)

    def test_same_key_same_order_replays(self):
        first = self.order()
        again = self.order()
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again["Idempotent-Replayed"], "true")
        self.assertEqual(again.json()["id"], first.json()["id"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.stock(self.mug), 8)  # decremented once, not twice

    def test_replay_judges_meaning_not_formatting(self):
        self.order([{"productId": self.mug.id, "quantity": 2}])
        same = self.order(
            [{"productId": self.mug.id, "quantity": 1}, {"productId": self.mug.id, "quantity": 1}],  # merged
            customerName="  Ada Lovelace ", email="ADA@Example.com", address=" 1 Analytical Way  ",
        )
        self.assertEqual(same.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

    def test_same_key_different_order_is_422(self):
        self.order()
        res = self.order([{"productId": self.mug.id, "quantity": 3}])
        self.assertEqual(res.status_code, 422)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.stock(self.mug), 8)

    def test_out_of_stock_saves_nothing_including_the_key(self):
        res = self.order([{"productId": self.tote.id, "quantity": 6}])
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json(), {"error": "Not enough stock for Canvas Tote"})
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.stock(self.tote), 5)
        # Restock, then retry with the very same key: it must work.
        self.tote.stock = 10
        self.tote.save()
        retry = self.order([{"productId": self.tote.id, "quantity": 6}])
        self.assertEqual(retry.status_code, 201)

    def test_failure_midway_rolls_back_earlier_lines(self):
        res = self.order([{"productId": self.mug.id, "quantity": 2}, {"productId": self.tote.id, "quantity": 99}])
        self.assertEqual(res.status_code, 409)
        self.assertEqual(self.stock(self.mug), 10)  # the mug line was rolled back too
        self.assertEqual(Order.objects.count(), 0)

    def test_unknown_product_is_400(self):
        res = self.order([{"productId": 424242, "quantity": 1}])
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {"error": "Unknown product 424242"})
        self.assertEqual(Order.objects.count(), 0)

    def test_key_is_required_and_validated(self):
        for key in (None, "short", "has spaces in it", "x" * 65):
            res = self.order(key=key)
            self.assertEqual(res.status_code, 400, key)
            self.assertIn("Idempotency-Key", res.json()["error"])
        self.assertEqual(Order.objects.count(), 0)

    def test_body_validation(self):
        for bad in (
            dict(email="not-an-email"),
            dict(customerName=" "),
            dict(address=""),
            dict(items=[]),
            dict(items=[{"productId": 1, "quantity": 0}]),
        ):
            res = self.order(**bad) if "items" not in bad else self.order(items=bad["items"])
            self.assertEqual(res.status_code, 400, bad)
            self.assertEqual(res.json()["error"], "Check your details and try again.")

    def test_listing_orders_is_admin_only(self):
        self.order()
        self.assertEqual(self.client.get("/api/orders").status_code, 401)
        res = self.client.get("/api/orders", HTTP_AUTHORIZATION=basic("admin", ADMIN["SHOP_ADMIN_PASSWORD"]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(len(res.json()[0]["items"]), 1)

    def test_order_history_survives_product_deletion(self):
        self.order()
        self.mug.delete()
        res = self.client.get("/api/orders", HTTP_AUTHORIZATION=basic("admin", ADMIN["SHOP_ADMIN_PASSWORD"]))
        self.assertEqual(res.json()[0]["items"][0]["productName"], "Stoneware Mug")
