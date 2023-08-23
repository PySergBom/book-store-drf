# Generated by Django 4.1.6 on 2023-03-09 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_book_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='rating',
            field=models.DecimalField(decimal_places=2, default=None, max_digits=3, null=True),
        ),
    ]
