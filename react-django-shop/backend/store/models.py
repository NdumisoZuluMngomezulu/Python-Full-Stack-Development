from django.db import models
class Product(models.Model):
    name=models.CharField(max_length=120)
    description=models.TextField(blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    category=models.CharField(max_length=80,default='General')
    image=models.URLField(blank=True)
    stock=models.PositiveIntegerField(default=10)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
class Order(models.Model):
    customer_name=models.CharField(max_length=120)
    email=models.EmailField()
    total=models.DecimalField(max_digits=10,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
