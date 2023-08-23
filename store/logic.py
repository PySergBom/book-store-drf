from django.db.models import Avg

from store.models import UserBookRelation


def set_rating(book):
    rating = UserBookRelation.objects.filter(book=book).aggregate(rating_book=Avg('rate')).get('rating_book')  #rating_book любое название переменной
    book.rating = rating
    book.save()
