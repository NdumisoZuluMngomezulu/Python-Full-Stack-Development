from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Product

DEMO = [
    ("Stoneware Mug", "Hand-glazed 350 ml mug, dishwasher safe.", "18.00", 40, "Kitchen"),
    ("Linen Apron", "Washed linen with deep front pocket.", "42.50", 25, "Kitchen"),
    ("Walnut Cutting Board", "Reversible end-grain board, 40 x 28 cm.", "79.00", 12, "Kitchen"),
    ("Wool Throw", "Merino blend throw, 130 x 180 cm.", "120.00", 8, "Home"),
    ("Brass Desk Lamp", "Adjustable arm, warm 2700K bulb included.", "95.00", 15, "Home"),
    ("Canvas Tote", "Heavy cotton tote with inner zip pocket.", "29.00", 60, "Accessories"),
]


class Command(BaseCommand):
    help = "Insert the demo catalogue if the shop has no products yet."

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write("Catalogue already has products; nothing to do.")
            return
        Product.objects.bulk_create(
            Product(
                name=name,
                description=description,
                price=Decimal(price),
                stock=stock,
                category=category,
                image_url=f"https://picsum.photos/seed/{name.replace(' ', '-')}/600/450",
            )
            for name, description, price, stock, category in DEMO
        )
        self.stdout.write(self.style.SUCCESS(f"Added {len(DEMO)} demo products."))
