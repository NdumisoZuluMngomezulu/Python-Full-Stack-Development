import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','shop.settings')
import django; django.setup()
from store.models import Product
items=[
('Classic Hoodie','Soft everyday hoodie','599.00','Clothing','https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=700&q=80',15),
('Minimal Sneakers','Clean low-top sneakers','899.00','Footwear','https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80',12),
('Canvas Backpack','Simple backpack for work or school','449.00','Bags','https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=700&q=80',20),
('Ceramic Mug','Matte ceramic coffee mug','149.00','Home','https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=700&q=80',30),
]
for x in items: Product.objects.get_or_create(name=x[0],defaults={'description':x[1],'price':x[2],'category':x[3],'image':x[4],'stock':x[5]})
print('Seeded products')
