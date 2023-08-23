from django.contrib import admin
from django.contrib.admin import ModelAdmin

from store.models import Book, UserBookRelation


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = ('name', 'author')


@admin.register(UserBookRelation)
class UserBookRelationsAdmin(ModelAdmin):
    list_display = ('user', 'book', 'like', 'in_bookmarks', 'rate')
