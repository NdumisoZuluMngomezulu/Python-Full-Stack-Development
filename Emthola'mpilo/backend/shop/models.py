from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=255, blank=True, default="")
    image_url = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Order(models.Model):
    customer_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    address = models.TextField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Client-supplied Idempotency-Key. Unique: the database guarantees one order per key, even under races.
    idempotency_key = models.CharField(max_length=64, unique=True)
    # SHA-256 of the normalised request, so a reused key with a different payload is detected.
    request_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Deliberately a plain number, not a ForeignKey: order history must survive a product being deleted,
    # and name/price are snapshotted at purchase time.
    product_id = models.BigIntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
