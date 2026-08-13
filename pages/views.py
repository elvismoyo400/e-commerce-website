from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Order, OrderItem, ContactInquiry  # add ContactInquiry
from .forms import ContactForm  # add this
from .cart import Cart

def home(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        products = Product.objects.all()
    
    featured_products = products[:3]
    trending_products = products.order_by('-created_at')[:4]
    cart = Cart(request)
    
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'trending_products': trending_products,
        'query': query,
        'cart_count': len(cart)
    })

def products(request):
    query = request.GET.get('q')
    if query:
        all_products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        all_products = Product.objects.all()
    cart = Cart(request)
    return render(request, 'products.html', {
        'products': all_products, 
        'query': query,
        'cart_count': len(cart)
    })

def about(request):
    cart = Cart(request)
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            
            # Email notification
            subject = f'New Parts Inquiry from {inquiry.name}'
            email_body = f"""
New contact form submission:

Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone or 'Not provided'}

Message:
{inquiry.message}

Submitted: {inquiry.created_at.strftime('%Y-%m-%d %H:%M')}
            """
            try:
                send_mail(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    ['sales@mobileparts.co.zw'],  # Change to your email
                    fail_silently=True,
                )
            except:
                pass  # Don't break if email fails

            messages.success(request, 'Thanks! We will contact you within 2 hours.')
            return redirect('pages:about')  # Use your actual URL name
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'about.html', {
        'cart_count': len(cart),
        'form': form
    })

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    messages.success(request, f'{product.name} added to cart')
    return redirect('pages:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('pages:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart.html', {'cart': cart, 'cart_count': len(cart)})

def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity'))
    if quantity > 0:
        cart.update(product, quantity)
    else:
        cart.remove(product)
    return redirect('pages:cart_detail')

def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('pages:products')
    
    if request.method == 'POST':
        order = Order.objects.create(
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            city=request.POST['city'],
            payment_method=request.POST['payment_method'],
            total=cart.get_total_price()
        )
        
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
            product = item['product']
            product.stock -= item['quantity']
            product.save()
        
        cart.clear()
        return render(request, 'checkout_success.html', {'order': order, 'cart_count': 0})
    
    return render(request, 'checkout.html', {'cart': cart, 'cart_count': len(cart)})