import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Order, OrderItem

def product_json(p):
    return {'id':p.id,'name':p.name,'description':p.description,'price':float(p.price),'category':p.category,'image':p.image,'stock':p.stock}

def products(request):
    if request.method != 'GET': return JsonResponse({'error':'Method not allowed'},status=405)
    qs=Product.objects.all().order_by('-created_at')
    q=request.GET.get('q','').strip()
    category=request.GET.get('category','').strip()
    if q: qs=qs.filter(name__icontains=q)
    if category: qs=qs.filter(category__iexact=category)
    return JsonResponse({'products':[product_json(p) for p in qs],'categories':sorted(set(Product.objects.values_list('category',flat=True)))})

def product_detail(request,pk):
    try: p=Product.objects.get(pk=pk)
    except Product.DoesNotExist: return JsonResponse({'error':'Product not found'},status=404)
    return JsonResponse(product_json(p))

@csrf_exempt
def orders(request):
    if request.method=='GET':
        email=request.GET.get('email','').strip()
        qs=Order.objects.filter(email__iexact=email).prefetch_related('items__product')
        data=[]
        for o in qs:
            data.append({'id':o.id,'customer_name':o.customer_name,'email':o.email,'total':float(o.total),'created_at':o.created_at,'items':[{'product':i.product.name,'quantity':i.quantity,'price':float(i.price)} for i in o.items.all()]})
        return JsonResponse({'orders':data})
    if request.method=='POST':
        try: payload=json.loads(request.body)
        except json.JSONDecodeError: return JsonResponse({'error':'Invalid JSON'},status=400)
        name=str(payload.get('customer_name','')).strip(); email=str(payload.get('email','')).strip(); items=payload.get('items',[])
        if not name or not email or not items: return JsonResponse({'error':'Name, email and items are required'},status=400)
        total=Decimal('0'); prepared=[]
        for item in items:
            try: p=Product.objects.get(pk=int(item['product_id'])); qty=int(item['quantity'])
            except (Product.DoesNotExist,ValueError,KeyError): return JsonResponse({'error':'Invalid product'},status=400)
            if qty<1 or p.stock<qty: return JsonResponse({'error':f'Not enough stock for {p.name}'},status=400)
            total += p.price*qty; prepared.append((p,qty))
        order=Order.objects.create(customer_name=name,email=email,total=total)
        for p,qty in prepared:
            OrderItem.objects.create(order=order,product=p,quantity=qty,price=p.price)
            p.stock-=qty; p.save(update_fields=['stock'])
        return JsonResponse({'id':order.id,'total':float(total)},status=201)
    return JsonResponse({'error':'Method not allowed'},status=405)
