import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS = ['testserver']
from pages.models import Product
from django.test import Client
p = Product.objects.first()
print('product', p.id if p else 'none')
client = Client()
r = client.get(f'/cart/add/{p.id}/')
print('add', r.status_code, getattr(r, 'url', None))
print('content', r.content.decode('utf-8', errors='replace')[:1000])
if r.status_code == 302:
    r2 = client.get(r.url)
    print('detail', r2.status_code)
    print('detail content', r2.content.decode('utf-8', errors='replace')[:1000])
