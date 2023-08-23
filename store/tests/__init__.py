import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'books.settings')

django.setup()
