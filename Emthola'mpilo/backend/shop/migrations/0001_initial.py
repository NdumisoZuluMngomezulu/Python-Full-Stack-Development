import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("description", models.CharField(blank=True, default="", max_length=1000)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("stock", models.PositiveIntegerField(default=0)),
                ("category", models.CharField(blank=True, default="", max_length=255)),
                ("image_url", models.CharField(blank=True, default="", max_length=500)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("address", models.TextField()),
                ("total", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("idempotency_key", models.CharField(max_length=64, unique=True)),
                ("request_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.BigIntegerField()),
                ("product_name", models.CharField(max_length=255)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shop.order"
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
    ]
